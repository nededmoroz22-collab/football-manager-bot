# main.py
import os
import asyncio
import datetime
import random
import logging
from contextlib import contextmanager

# optional: load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "").rstrip("/") or None

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("football-manager")
log.info("Starting football manager bot")
if not BOT_TOKEN:
    log.warning("BOT_TOKEN not set. Set BOT_TOKEN env var before running.")

# Database setup
Base = declarative_base()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

@contextmanager
def get_session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    club_id = Column(Integer, nullable=True)

class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    owner_id = Column(Integer, nullable=True)
    budget = Column(Integer, default=1_000_000)
    rating = Column(Float, default=50.0)

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    club_id = Column(Integer, nullable=True)
    rating = Column(Integer, default=50)
    value = Column(Integer, default=100_000)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    home_club_id = Column(Integer)
    away_club_id = Column(Integer)
    scheduled_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="scheduled")  # scheduled / played / cancelled
    home_goals = Column(Integer, default=0)
    away_goals = Column(Integer, default=0)
    is_friendly = Column(Boolean, default=False)

def create_tables():
    Base.metadata.create_all(bind=engine)

# Game logic
def compute_club_rating_from_players(players):
    if not players:
        return 35.0
    return sum((p.rating or 0) for p in players) / max(1, len(players))

def simulate_match_logic(home_rating, away_rating):
    diff = home_rating - away_rating
    home_expected = max(0.1, 0.8 + home_rating / 100.0 + diff / 150.0)
    away_expected = max(0.1, 0.8 + away_rating / 100.0 - diff / 150.0)
    hg = max(0, int(round(random.gauss(home_expected, 1.0))))
    ag = max(0, int(round(random.gauss(away_expected, 1.0))))
    return hg, ag

async def process_scheduled_matches():
    now = datetime.datetime.utcnow()
    with get_session() as s:
        matches = s.query(Match).filter(Match.status == "scheduled", Match.scheduled_time <= now).all()
        for m in matches:
            try:
                home_players = s.query(Player).filter(Player.club_id == m.home_club_id).all()
                away_players = s.query(Player).filter(Player.club_id == m.away_club_id).all()
                home_rating = compute_club_rating_from_players(home_players)
                away_rating = compute_club_rating_from_players(away_players)
                hg, ag = simulate_match_logic(home_rating, away_rating)
                m.home_goals = hg
                m.away_goals = ag
                m.status = "played"
                # small rating adjustment
                delta = 1.0 if hg > ag else (-1.0 if hg < ag else 0.2)
                home_club = s.get(Club, m.home_club_id)
                away_club = s.get(Club, m.away_club_id)
                if home_club:
                    home_club.rating = max(1.0, (home_club.rating or 50.0) + delta)
                if away_club:
                    away_club.rating = max(1.0, (away_club.rating or 50.0) - delta)
                s.commit()
                log.info("Played match %s: %s %d-%d %s", m.id, m.home_club_id, hg, ag, m.away_club_id)
            except Exception:
                log.exception("Error processing match %s", getattr(m, "id", "?"))
                s.rollback()

# Bot handlers
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    with get_session() as s:
        db_user = s.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username or user.full_name)
            s.add(db_user)
            s.commit()
    await update.message.reply_text(
        "
