"""
Controller Agent — orchestrates all other agents every 6 hours.

Decision logic:
  1. Check system health — find what needs attention
  2. Trigger Research Agent if no new niches in 7 days
  3. Trigger Link Builder for niches with no/stale links
  4. Trigger Business Case for niches with no financial model
  5. Trigger Site Builder for approved niches with no pages
  6. Check campaign performance and raise alerts
  7. Persist all decisions to agent_logs and alerts tables
"""

import logging
from datetime import datetime, timedelta

from app.agents.base import AgentState, BaseAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 1 — assess full system health
# ---------------------------------------------------------------------------
def assess_system_health(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche
    from app.models.page import Page
    from app.models.affiliate_link import AffiliateLink
    from app.models.campaign import Campaign
    from app.models.agent_log import AgentLog
    from app.models.alert import Alert

    logger.info("[ControllerAgent] assess_system_health — starting")
    db = SessionLocal()

    health = {
        # Niche discovery
        "needs_research": False,
        "days_since_last_research": 0,
        # Link building
        "niches_without_links": [],
        "niches_with_stale_links": [],
        # Business case
        "niches_without_financial_model": [],
        # Site building
        "niches_without_pages": [],
        # Campaigns
        "low_roas_campaigns": [],
        "paused_campaigns": [],
        # Alerts
        "unresolved_critical_alerts": 0,
        # Summary
        "actions_needed": [],
    }

    try:
        now = datetime.utcnow()

        # ── Research: when was the last research run? ─────────────────────
        last_research = (
            db.query(AgentLog)
            .filter(AgentLog.agent_name == "ResearchAgent")
            .order_by(AgentLog.timestamp.desc())
            .first()
        )
        if not last_research:
            health["needs_research"] = True
            health["days_since_last_research"] = 999
            health["actions_needed"].append("research")
            logger.info("  ⚠ No research has ever run — triggering")
        else:
            days_ago = (now - last_research.timestamp).days
            health["days_since_last_research"] = days_ago
            if days_ago >= 7:
                health["needs_research"] = True
                health["actions_needed"].append("research")
                logger.info(f"  ⚠ Last research was {days_ago} days ago — triggering")
            else:
                logger.info(f"  ✓ Research ran {days_ago} days ago — OK")

        # ── All discovered/approved niches ────────────────────────────────
        niches = db.query(Niche).filter(
            Niche.status.in_(["discovered", "approved", "live"])
        ).all()
        logger.info(f"  Found {len(niches)} active niches")

        for niche in niches:
            # Check affiliate links
            link_count = db.query(AffiliateLink).filter(
                AffiliateLink.niche_id == niche.id,
                AffiliateLink.status == "active",
            ).count()

            if link_count == 0:
                health["niches_without_links"].append(niche.id)
                if "links" not in health["actions_needed"]:
                    health["actions_needed"].append("links")
                logger.info(f"  ⚠ {niche.name}: no affiliate links")
            else:
                # Check for stale links (not checked in 48h)
                stale_threshold = now - timedelta(hours=48)
                stale_count = db.query(AffiliateLink).filter(
                    AffiliateLink.niche_id == niche.id,
                    AffiliateLink.status == "active",
                    (AffiliateLink.last_checked == None) |
                    (AffiliateLink.last_checked < stale_threshold),
                ).count()
                if stale_count > 0:
                    health["niches_with_stale_links"].append(niche.id)
                    logger.info(f"  ⚠ {niche.name}: {stale_count} stale links")

            # Check budget allocation (proxy for business case having run)
            from app.models.budget_allocation import BudgetAllocation
            has_budget = db.query(BudgetAllocation).filter(
                BudgetAllocation.niche_id == niche.id
            ).first()
            if not has_budget:
                health["niches_without_financial_model"].append(niche.id)
                if "business_case" not in health["actions_needed"]:
                    health["actions_needed"].append("business_case")
                logger.info(f"  ⚠ {niche.name}: no financial model")

            # Check pages
            page_count = db.query(Page).filter(
                Page.niche_id == niche.id,
                Page.status == "published",
            ).count()
            if page_count == 0 and link_count > 0:
                # Has products but no pages — ready to build
                health["niches_without_pages"].append(niche.id)
                if "site_build" not in health["actions_needed"]:
                    health["actions_needed"].append("site_build")
                logger.info(f"  ⚠ {niche.name}: has links but no pages")
            else:
                logger.info(f"  ✓ {niche.name}: {link_count} links, {page_count} pages")

        # ── Campaign health ───────────────────────────────────────────────
        from app.models.campaign import Campaign
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).all()

        for campaign in campaigns:
            if campaign.roas is not None and campaign.roas < 0.8:
                health["low_roas_campaigns"].append({
                    "id": campaign.id,
                    "niche_id": campaign.niche_id,
                    "roas": campaign.roas,
                    "budget": campaign.budget,
                })
                if "ads_optimise" not in health["actions_needed"]:
                    health["actions_needed"].append("ads_optimise")
                logger.info(
                    f"  ⚠ Campaign {campaign.id}: low ROAS {campaign.roas}x"
                )

        # ── Unresolved critical alerts ────────────────────────────────────
        critical_count = db.query(Alert).filter(
            Alert.resolved == False,
            Alert.severity == "critical",
        ).count()
        health["unresolved_critical_alerts"] = critical_count
        if critical_count > 0:
            logger.info(f"  ⚠ {critical_count} unresolved critical alerts")

    except Exception as e:
        logger.error(f"[ControllerAgent] Health check error: {e}")
        state["error"] = f"Health check failed: {e}"
    finally:
        db.close()

    state["next_action"] = health["actions_needed"][0] if health["actions_needed"] else "idle"
    state["messages"] = state.get("messages", []) + [
        f"Health check done. Actions needed: {health['actions_needed'] or ['none']}"
    ]
    state["keyword_data"] = health  # reuse field to pass health data
    logger.info(
        f"[ControllerAgent] assess_system_health — done. "
        f"Actions: {health['actions_needed'] or ['none']}"
    )
    return state


# ---------------------------------------------------------------------------
# Step 2 — execute all needed actions
# ---------------------------------------------------------------------------
def execute_actions(state: AgentState) -> AgentState:
    health = state.get("keyword_data", {})
    actions = health.get("actions_needed", [])

    if not actions:
        logger.info("[ControllerAgent] execute_actions — nothing to do, system healthy ✓")
        state["messages"] = state.get("messages", []) + ["System healthy — no actions needed"]
        return state

    logger.info(f"[ControllerAgent] execute_actions — executing: {actions}")

    # Import tasks here to avoid circular imports
    from app.tasks.agent_tasks import (
        run_research_agent,
        run_link_builder_agent,
        run_business_case_agent,
        run_site_builder_agent,
        run_ads_manager_agent,
    )

    dispatched = []

    # Research — runs once for all niches
    if "research" in actions:
        task = run_research_agent.delay()
        dispatched.append(f"research:{task.id}")
        logger.info(f"  → Dispatched ResearchAgent task {task.id}")

    # Link building — per niche
    niches_for_links = (
        health.get("niches_without_links", []) +
        health.get("niches_with_stale_links", [])
    )
    for niche_id in set(niches_for_links):
        task = run_link_builder_agent.delay(niche_id=niche_id)
        dispatched.append(f"links:{niche_id}:{task.id}")
        logger.info(f"  → Dispatched LinkBuilderAgent for niche {niche_id}")

    # Business case — per niche
    for niche_id in health.get("niches_without_financial_model", []):
        task = run_business_case_agent.delay(niche_id=niche_id)
        dispatched.append(f"business_case:{niche_id}:{task.id}")
        logger.info(f"  → Dispatched BusinessCaseAgent for niche {niche_id}")

    # Site building — per niche (only if has links)
    for niche_id in health.get("niches_without_pages", []):
        task = run_site_builder_agent.delay(niche_id=niche_id)
        dispatched.append(f"site_build:{niche_id}:{task.id}")
        logger.info(f"  → Dispatched SiteBuilderAgent for niche {niche_id}")

    # Ads optimisation — per campaign
    if "ads_optimise" in actions:
        for campaign in health.get("low_roas_campaigns", []):
            task = run_ads_manager_agent.delay(niche_id=campaign["niche_id"])
            dispatched.append(f"ads:{campaign['niche_id']}:{task.id}")
            logger.info(
                f"  → Dispatched AdsManagerAgent for niche {campaign['niche_id']} "
                f"(ROAS {campaign['roas']}x)"
            )

    state["messages"] = state.get("messages", []) + [
        f"Dispatched {len(dispatched)} tasks: {dispatched}"
    ]
    state["keyword_data"] = {**health, "dispatched_tasks": dispatched}
    logger.info(
        f"[ControllerAgent] execute_actions — done. "
        f"Dispatched {len(dispatched)} tasks"
    )
    return state


# ---------------------------------------------------------------------------
# Step 3 — raise alerts for anything that needs human attention
# ---------------------------------------------------------------------------
def raise_alerts(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.alert import Alert

    logger.info("[ControllerAgent] raise_alerts — starting")
    health = state.get("keyword_data", {})
    db = SessionLocal()
    alerts_created = 0

    try:
        now = datetime.utcnow()

        # Alert: low ROAS campaigns
        for campaign in health.get("low_roas_campaigns", []):
            existing = db.query(Alert).filter(
                Alert.type == "low_roas",
                Alert.niche_id == campaign["niche_id"],
                Alert.resolved == False,
            ).first()
            if not existing:
                db.add(Alert(
                    type="low_roas",
                    message=(
                        f"Campaign for niche {campaign['niche_id']} has low ROAS: "
                        f"{campaign['roas']}x (threshold: 0.8x). "
                        f"Budget: €{campaign['budget']}/mo. Consider pausing."
                    ),
                    severity="warning",
                    niche_id=campaign["niche_id"],
                    resolved=False,
                    created_at=now,
                ))
                alerts_created += 1

        # Alert: niches with no links after 24h
        for niche_id in health.get("niches_without_links", []):
            existing = db.query(Alert).filter(
                Alert.type == "no_affiliate_links",
                Alert.niche_id == niche_id,
                Alert.resolved == False,
            ).first()
            if not existing:
                db.add(Alert(
                    type="no_affiliate_links",
                    message=(
                        f"Niche {niche_id} has no affiliate links. "
                        f"Link Builder Agent has been triggered automatically."
                    ),
                    severity="info",
                    niche_id=niche_id,
                    resolved=False,
                    created_at=now,
                ))
                alerts_created += 1

        # Alert: no research in 14+ days
        days = health.get("days_since_last_research", 0)
        if days >= 14:
            existing = db.query(Alert).filter(
                Alert.type == "no_recent_research",
                Alert.resolved == False,
            ).first()
            if not existing:
                db.add(Alert(
                    type="no_recent_research",
                    message=(
                        f"No niche research has run in {days} days. "
                        f"Research Agent has been triggered automatically."
                    ),
                    severity="warning",
                    niche_id=None,
                    resolved=False,
                    created_at=now,
                ))
                alerts_created += 1

        db.commit()
        logger.info(f"  Created {alerts_created} new alerts")

    except Exception as e:
        db.rollback()
        logger.error(f"[ControllerAgent] Alert creation error: {e}")
    finally:
        db.close()

    state["messages"] = state.get("messages", []) + [
        f"Created {alerts_created} new alerts"
    ]
    logger.info(f"[ControllerAgent] raise_alerts — done ({alerts_created} alerts)")
    return state


# ---------------------------------------------------------------------------
# Step 4 — log the controller run to agent_logs
# ---------------------------------------------------------------------------
def log_run(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.agent_log import AgentLog

    health = state.get("keyword_data", {})
    actions = health.get("actions_needed", [])
    dispatched = health.get("dispatched_tasks", [])

    db = SessionLocal()
    try:
        db.add(AgentLog(
            agent_name="ControllerAgent",
            action="orchestration_run",
            input_summary="Scheduled 6-hour health check",
            result_summary=(
                f"Actions needed: {actions or ['none']}. "
                f"Tasks dispatched: {len(dispatched)}. "
                f"Messages: {state.get('messages', [])}"
            ),
            timestamp=datetime.utcnow(),
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[ControllerAgent] Log error: {e}")
    finally:
        db.close()

    state["completed"] = True
    logger.info("[ControllerAgent] log_run — done")
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.agent_log import AgentLog
    from app.models.alert import Alert

    logger.error(f"[ControllerAgent] Terminal error: {state.get('error')}")

    db = SessionLocal()
    try:
        db.add(AgentLog(
            agent_name="ControllerAgent",
            action="orchestration_error",
            input_summary="Scheduled 6-hour health check",
            result_summary=f"ERROR: {state.get('error')}",
            timestamp=datetime.utcnow(),
        ))
        db.add(Alert(
            type="controller_error",
            message=f"Controller Agent failed: {state.get('error')}",
            severity="critical",
            niche_id=None,
            resolved=False,
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"[ControllerAgent] Error handler DB error: {e}")
    finally:
        db.close()

    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class ControllerAgent(BaseAgent):
    name = "ControllerAgent"

    def build(self):
        return self

    def run(self, initial_state: AgentState) -> AgentState:
        state = initial_state

        state = assess_system_health(state)
        if state.get("error"):
            return handle_error(state)

        state = execute_actions(state)
        if state.get("error"):
            return handle_error(state)

        state = raise_alerts(state)
        if state.get("error"):
            return handle_error(state)

        state = log_run(state)
        return state