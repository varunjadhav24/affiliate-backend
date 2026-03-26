from datetime import datetime
from celery_app import celery_app

def _log_agent(agent_name, action, input_summary, result_summary):
    from app.db.session import SessionLocal
    from app.models.agent_log import AgentLog
    db = SessionLocal()
    try:
        db.add(AgentLog(agent_name=agent_name, action=action,
                        input_summary=input_summary, result_summary=result_summary,
                        timestamp=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

@celery_app.task(name="tasks.run_research_agent", bind=True, max_retries=3)
def run_research_agent(self):
    try:
        from app.agents.research_agent import ResearchAgent
        result = ResearchAgent().run({"completed": False, "messages": []})
        _log_agent("ResearchAgent", "run_research_agent", "{}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("ResearchAgent", "run_research_agent", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_business_case_agent", bind=True, max_retries=3)
def run_business_case_agent(self, niche_id: int):
    try:
        from app.agents.business_case_agent import BusinessCaseAgent
        result = BusinessCaseAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("BusinessCaseAgent", "run_business_case_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("BusinessCaseAgent", "run_business_case_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_site_builder_agent", bind=True, max_retries=3)
def run_site_builder_agent(self, niche_id: int, rebuild: bool = False):
    try:
        from app.agents.site_builder_agent import SiteBuilderAgent
        result = SiteBuilderAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("SiteBuilderAgent", "run_site_builder_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("SiteBuilderAgent", "run_site_builder_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_link_builder_agent", bind=True, max_retries=3)
def run_link_builder_agent(self, niche_id: int):
    try:
        from app.agents.link_builder_agent import LinkBuilderAgent
        result = LinkBuilderAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("LinkBuilderAgent", "run_link_builder_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("LinkBuilderAgent", "run_link_builder_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_ads_manager_agent", bind=True, max_retries=3)
def run_ads_manager_agent(self, niche_id: int):
    try:
        from app.agents.ads_manager_agent import AdsManagerAgent
        result = AdsManagerAgent().run({"niche_id": niche_id, "completed": False, "messages": []})
        _log_agent("AdsManagerAgent", "run_ads_manager_agent", f"niche_id={niche_id}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("AdsManagerAgent", "run_ads_manager_agent", f"niche_id={niche_id}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(name="tasks.run_controller_agent", bind=True, max_retries=3)
def run_controller_agent(self):
    try:
        from app.agents.controller_agent import ControllerAgent
        result = ControllerAgent().run({"completed": False, "messages": []})
        _log_agent("ControllerAgent", "run_controller_agent", "{}", str(result.get("messages")))
        return {"success": True}
    except Exception as exc:
        _log_agent("ControllerAgent", "run_controller_agent", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=120)

@celery_app.task(name="tasks.check_link_freshness", bind=True, max_retries=2)
def check_link_freshness(self):
    try:
        from datetime import timedelta
        from app.db.session import SessionLocal
        from app.models.affiliate_link import AffiliateLink
        db = SessionLocal()
        stale_threshold = datetime.utcnow() - timedelta(hours=48)
        stale = (db.query(AffiliateLink.niche_id)
                 .filter(AffiliateLink.status == "active",
                         (AffiliateLink.last_checked == None) | (AffiliateLink.last_checked < stale_threshold))
                 .distinct().all())
        db.close()
        triggered = []
        for (niche_id,) in stale:
            run_link_builder_agent.delay(niche_id=niche_id)
            triggered.append(niche_id)
        _log_agent("LinkBuilderAgent", "check_link_freshness", "{}", f"triggered: {triggered}")
        return {"success": True, "triggered_niches": triggered}
    except Exception as exc:
        _log_agent("LinkBuilderAgent", "check_link_freshness", "{}", f"ERROR: {exc}")
        raise self.retry(exc=exc, countdown=300)
