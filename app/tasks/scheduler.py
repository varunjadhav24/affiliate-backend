from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "run-controller-agent-every-6h": {
        "task": "tasks.run_controller_agent",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"expires": 3600},
    },
    "check-link-freshness-daily": {
        "task": "tasks.check_link_freshness",
        "schedule": crontab(minute=0, hour=3),
        "options": {"expires": 7200},
    },
}
