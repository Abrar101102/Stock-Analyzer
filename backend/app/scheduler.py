from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.fundamental_ingestiion_job import run__fundamental_ingestion

def start_scheduler():
  scheduler = BackgroundScheduler()
  scheduler.add_job(
    run__fundamental_ingestion,
    trigger="cron",
    hour = 2,
    minute = 0
    )
  scheduler.start()