import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def simulate_match(match_id: int):
    """
    Заготовка задачи для симуляции матча.
    Реализация симулятора и расписание матчей будут добавлены позже.
    """
    # TODO: добавить доступ к БД и логику симуляции.
    return {"match_id": match_id, "result": "0-0"}