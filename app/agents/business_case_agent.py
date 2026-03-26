"""
Business Case Agent — builds a financial model for each approved niche.

v2: Improved revenue model using realistic traffic/conversion assumptions
for German affiliate sites in their growth phase (months 3-12).
"""

import logging
from datetime import datetime

from app.agents.base import AgentState, BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Amazon.de commission rates by niche
# ---------------------------------------------------------------------------
COMMISSION_RATES = {
    "model-building":       0.07,
    "aquaristics":          0.07,
    "cycling-accessories":  0.05,
    "knitting-wool":        0.07,
    "camping-gear":         0.05,
    "board-games":          0.07,
    "fishing-accessories":  0.05,
    "photography-gear":     0.03,
    "climbing-gear":        0.05,
    "sewing-beginners":     0.07,
    "adult-crafting":       0.07,
    "diy-home-improvement": 0.05,
    "yoga-accessories":     0.05,
    "garden-tools":         0.05,
    "electronics-diy":      0.03,
}

# Realistic average order values for each niche (not cheapest product — full basket)
REALISTIC_AOV = {
    "model-building":       55.0,   # Kits + paints + tools
    "aquaristics":          85.0,   # Tank + filter + lighting
    "cycling-accessories":  75.0,   # Helmet + lock + bag
    "knitting-wool":        40.0,   # Wool + needles
    "camping-gear":         90.0,   # Sleeping bag + mat
    "board-games":          45.0,   # 1-2 games
    "fishing-accessories":  60.0,   # Rod + reel + lures
    "photography-gear":     120.0,  # Tripod + filters + bag
    "climbing-gear":        110.0,  # Harness + shoes
    "sewing-beginners":     80.0,   # Machine or fabric bundle
    "adult-crafting":       35.0,   # Diamond painting set
    "diy-home-improvement": 95.0,   # Power tool
    "yoga-accessories":     50.0,   # Mat + blocks + strap
    "garden-tools":         70.0,   # Tool set
    "electronics-diy":      65.0,   # Arduino/Pi kit
}

# German affiliate site benchmarks (realistic for month 6-12)
ORGANIC_TRAFFIC_BY_SCORE = {
    # score range: (min_visitors, max_visitors) per month at month 6
    (8, 10):  (4000, 6000),
    (7, 8):   (2000, 4000),
    (6, 7):   (1000, 2000),
    (5, 6):   (500,  1000),
    (4, 5):   (200,  500),
    (0, 4):   (50,   200),
}

# Affiliate site conversion benchmarks
PAGE_CTR_TO_AMAZON = 0.08      # 8% of visitors click an affiliate link
AMAZON_CONVERSION_RATE = 0.10  # 10% of clicks result in a purchase (Amazon is trusted)

# Google Ads benchmarks for German hobby niches
AVG_CPC_EUR = 0.35             # €0.35 avg CPC (hobby keywords are cheap in DE)
LANDING_PAGE_CVR = 0.03        # 3% of ad visitors buy


# ---------------------------------------------------------------------------
# Step 1 — load niche data
# ---------------------------------------------------------------------------
def load_niche_data(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche
    from app.models.affiliate_link import AffiliateLink

    logger.info("[BusinessCaseAgent] load_niche_data — starting")
    db = SessionLocal()

    try:
        if state.get("niche_id"):
            niches = db.query(Niche).filter(Niche.id == state["niche_id"]).all()
        else:
            niches = db.query(Niche).filter(
                Niche.status.in_(["approved", "discovered"])
            ).all()

        niche_data = []
        for niche in niches:
            links = db.query(AffiliateLink).filter(
                AffiliateLink.niche_id == niche.id,
                AffiliateLink.status == "active",
            ).all()

            # Use realistic AOV, not just the cheapest scraped price
            realistic_aov = REALISTIC_AOV.get(niche.name, 60.0)

            niche_data.append({
                "id": niche.id,
                "name": niche.name,
                "subdomain": niche.subdomain,
                "score": niche.score or 0,
                "go_no_go": niche.go_no_go,
                "recommended_budget": niche.recommended_budget or 100,
                "product_count": len(links),
                "avg_order_value": realistic_aov,
                "has_products": len(links) > 0,
            })
            logger.info(
                f"  Loaded: {niche.name} | score={niche.score} | "
                f"{len(links)} products | AOV=€{realistic_aov}"
            )

    finally:
        db.close()

    state["keyword_data"] = niche_data
    state["messages"] = state.get("messages", []) + [
        f"Loaded {len(niche_data)} niches"
    ]
    logger.info(f"[BusinessCaseAgent] load_niche_data — done ({len(niche_data)} niches)")
    return state


# ---------------------------------------------------------------------------
# Step 2 — compute financial model
# ---------------------------------------------------------------------------
def compute_financials(state: AgentState) -> AgentState:
    logger.info("[BusinessCaseAgent] compute_financials — starting")
    niche_data = state.get("keyword_data", [])
    financial_models = []

    for niche in niche_data:
        name = niche["name"]
        score = niche["score"]
        aov = niche["avg_order_value"]
        monthly_budget = niche["recommended_budget"]
        commission_rate = COMMISSION_RATES.get(name, 0.05)

        # ── Organic traffic (month 6 estimate) ───────────────────────────
        monthly_visitors = 200  # default
        for (low, high), (min_v, max_v) in ORGANIC_TRAFFIC_BY_SCORE.items():
            if low <= score < high:
                monthly_visitors = (min_v + max_v) // 2
                break

        # ── Organic affiliate revenue ─────────────────────────────────────
        affiliate_clicks = round(monthly_visitors * PAGE_CTR_TO_AMAZON)
        affiliate_purchases = round(affiliate_clicks * AMAZON_CONVERSION_RATE)
        organic_revenue = round(affiliate_purchases * aov * commission_rate, 2)

        # ── Google Ads revenue ────────────────────────────────────────────
        ad_clicks = round(monthly_budget / AVG_CPC_EUR)
        ad_purchases = round(ad_clicks * LANDING_PAGE_CVR)
        ads_revenue = round(ad_purchases * aov * commission_rate, 2)
        roas = round(ads_revenue / monthly_budget, 2) if monthly_budget > 0 else 0

        # ── Combined ──────────────────────────────────────────────────────
        total_revenue = round(organic_revenue + ads_revenue, 2)
        total_costs = monthly_budget  # only ad spend counted as direct cost
        monthly_profit = round(total_revenue - total_costs, 2)

        # Payback: recoup 3 months of ad spend from profit
        initial_investment = monthly_budget * 3
        if monthly_profit > 0:
            payback_months = round(initial_investment / monthly_profit, 1)
        else:
            payback_months = 999

        # ── Year 1 projections (SEO grows traffic) ────────────────────────
        # Traffic doubles by month 12 as SEO matures
        year1_organic_revenue = round(organic_revenue * 12 * 1.5, 2)  # 1.5x avg factor
        year1_ads_revenue = round(ads_revenue * 12, 2)
        year1_total_revenue = round(year1_organic_revenue + year1_ads_revenue, 2)
        year1_ad_spend = round(monthly_budget * 12, 2)
        year1_profit = round(year1_total_revenue - year1_ad_spend, 2)

        # ── Recommendation ────────────────────────────────────────────────
        if roas >= 1.2 and total_revenue >= 80:
            recommendation = "strong_go"
            reasoning = f"ROAS {roas}x, €{total_revenue}/mo, Y1 profit estimate €{year1_profit}"
        elif roas >= 0.8 and total_revenue >= 40:
            recommendation = "go"
            reasoning = f"Profitable mix of organic+paid, €{total_revenue}/mo at month 6"
        elif total_revenue >= 25:
            recommendation = "go_with_caution"
            reasoning = f"Low ROAS ({roas}x) but organic potential. Reduce ad spend."
        else:
            recommendation = "no_go"
            reasoning = f"Revenue too low (€{total_revenue}/mo). Insufficient market size."

        model = {
            "niche_id": niche["id"],
            "niche_name": name,
            "avg_order_value": aov,
            "commission_rate_pct": round(commission_rate * 100, 1),
            "monthly_budget": monthly_budget,
            # Organic
            "estimated_monthly_visitors": monthly_visitors,
            "affiliate_clicks": affiliate_clicks,
            "affiliate_purchases": affiliate_purchases,
            "organic_revenue": organic_revenue,
            # Paid
            "ad_clicks": ad_clicks,
            "ad_purchases": ad_purchases,
            "ads_revenue": ads_revenue,
            "roas": roas,
            # Combined
            "total_monthly_revenue": total_revenue,
            "monthly_profit": monthly_profit,
            "payback_months": payback_months,
            # Year 1
            "year1_total_revenue": year1_total_revenue,
            "year1_profit": year1_profit,
            # Decision
            "recommendation": recommendation,
            "reasoning": reasoning,
        }

        financial_models.append(model)
        logger.info(
            f"  ✓ {name} | "
            f"organic=€{organic_revenue}/mo | ads=€{ads_revenue}/mo | "
            f"total=€{total_revenue}/mo | ROAS={roas}x | "
            f"Y1=€{year1_total_revenue} | {recommendation}"
        )

    state["keyword_data"] = financial_models
    state["messages"] = state.get("messages", []) + [
        f"Computed financials for {len(financial_models)} niches"
    ]
    logger.info("[BusinessCaseAgent] compute_financials — done")
    return state


# ---------------------------------------------------------------------------
# Step 3 — persist to DB and create approvals
# ---------------------------------------------------------------------------
def persist_and_create_approvals(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche
    from app.models.approval import Approval
    from app.models.budget_allocation import BudgetAllocation

    logger.info("[BusinessCaseAgent] persist_and_create_approvals — starting")
    models = state.get("keyword_data", [])
    db = SessionLocal()
    niches_updated = 0
    approvals_created = 0

    try:
        for model in models:
            niche = db.query(Niche).filter(Niche.id == model["niche_id"]).first()
            if not niche:
                continue

            # Update niche record
            niche.recommended_budget = model["monthly_budget"]
            niche.go_no_go = (
                "go" if model["recommendation"] in ("strong_go", "go", "go_with_caution")
                else "no_go"
            )
            niches_updated += 1

            # Upsert budget allocation
            alloc = db.query(BudgetAllocation).filter(
                BudgetAllocation.niche_id == niche.id
            ).first()
            if not alloc:
                db.add(BudgetAllocation(
                    niche_id=niche.id,
                    allocated=model["monthly_budget"],
                    spent=0.0,
                    updated_at=datetime.utcnow(),
                ))
            else:
                alloc.allocated = model["monthly_budget"]
                alloc.updated_at = datetime.utcnow()

            # Create approval for go niches
            if model["recommendation"] in ("strong_go", "go"):
                existing = db.query(Approval).filter(
                    Approval.niche_id == niche.id,
                    Approval.action_type == "launch_site",
                    Approval.status == "pending",
                ).first()
                if not existing:
                    db.add(Approval(
                        action_type="launch_site",
                        description=(
                            f"Launch '{niche.name}' affiliate site. "
                            f"Financial model: €{model['total_monthly_revenue']}/mo revenue at month 6, "
                            f"ROAS {model['roas']}x, "
                            f"Year 1 revenue estimate €{model['year1_total_revenue']}, "
                            f"payback in {model['payback_months']} months. "
                            f"{model['reasoning']}"
                        ),
                        niche_id=niche.id,
                        status="pending",
                        created_at=datetime.utcnow(),
                    ))
                    approvals_created += 1
                    logger.info(f"  ✓ Approval queued: {niche.name} ({model['recommendation']})")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"[BusinessCaseAgent] DB error: {e}")
        state["error"] = f"DB persist failed: {e}"
    finally:
        db.close()

    state["completed"] = True
    state["messages"] = state.get("messages", []) + [
        f"Updated {niches_updated} niches, created {approvals_created} approvals"
    ]
    logger.info(
        f"[BusinessCaseAgent] persist_and_create_approvals — done. "
        f"niches_updated={niches_updated}, approvals_created={approvals_created}"
    )
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    logger.error(f"[BusinessCaseAgent] Terminal error: {state.get('error')}")
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class BusinessCaseAgent(BaseAgent):
    name = "BusinessCaseAgent"

    def build(self):
        return self

    def run(self, initial_state: AgentState) -> AgentState:
        state = initial_state

        state = load_niche_data(state)
        if state.get("error"):
            return handle_error(state)

        state = compute_financials(state)
        if state.get("error"):
            return handle_error(state)

        state = persist_and_create_approvals(state)
        return state