from aiogram import types, Router
from .db import get_pool
import asyncpg

router = Router()

@router.message(commands=["start"])
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id FROM users WHERE tg_id=$1", tg_id)
        if not row:
            await conn.execute("INSERT INTO users(tg_id, username) VALUES($1,$2)", tg_id, username)
            await message.reply("Регистрация завершена. Вызовите /clubs чтобы выбрать клуб.")
        else:
            await message.reply("Вы уже зарегистрированы. /clubs — список клубов.")

@router.message(commands=["clubs"])
async def cmd_clubs(message: types.Message):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, owner_id, league FROM clubs ORDER BY league, name")
        text_lines = ["Клубы:"]
        for r in rows:
            status = "свободен" if r["owner_id"] is None else "занят"
            text_lines.append(f"{r['id']}. {r['name']} ({r['league']}) — {status}")
        await message.reply("\n".join(text_lines))

@router.message(commands=["choose"])
async def cmd_choose(message: types.Message):
    args = message.get_args().strip()
    if not args:
        await message.reply("Использование: /choose <club_id>")
        return
    try:
        club_id = int(args.split()[0])
    except ValueError:
        await message.reply("Неверный id клуба")
        return

    tg_id = message.from_user.id
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id FROM users WHERE tg_id=$1", tg_id)
        if not user:
            await message.reply("Сначала нужно /start")
            return
        user_id = user["id"]
        try:
            # Атомарный UPDATE: установим владельца только если owner_id IS NULL
            row = await conn.fetchrow("""
                UPDATE clubs
                SET owner_id = $1
                WHERE id = $2 AND owner_id IS NULL
                RETURNING id, name
            """, user_id, club_id)
            if row:
                await message.reply(f"Вы успешно выбрали клуб: {row['name']}")
            else:
                await message.reply("Клуб уже занят или не найден.")
        except asyncpg.PostgresError as e:
            await message.reply("Ошибка базы данных. Попробуйте позже.")