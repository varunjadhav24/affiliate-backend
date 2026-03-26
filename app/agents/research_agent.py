"""
Research Agent — discovers profitable hobby niches in Germany.

Flow:
  fetch_keyword_data → fetch_trend_data → score_locally → rank_and_persist

Scoring is done locally using trend interest + commercial signals.
GPT-4o scoring can be re-enabled later by setting USE_GPT_SCORING=true in .env
"""

import json
import logging
from datetime import datetime

from app.agents.base import AgentState, BaseAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

SEED_KEYWORDS = [
    "Modellbau", "Aquaristik", "Heimwerken", "Gartengeräte",
    "Klettern Ausrüstung", "Angeln Zubehör", "Fotografie Zubehör",
    "Fahrrad Zubehör", "Camping Ausrüstung", "Yoga Zubehör",
    "Stricken Wolle", "Basteln Erwachsene", "Brettspiele",
    "Elektronik Basteln", "Nähen Anfänger",
]

# Niche metadata: English name + subdomain slug for each seed keyword
NICHE_META = {
    "Modellbau":            {"niche_name": "model-building",       "subdomain": "modellbau"},
    "Aquaristik":           {"niche_name": "aquaristics",          "subdomain": "aquaristik"},
    "Heimwerken":           {"niche_name": "diy-home-improvement",  "subdomain": "heimwerken"},
    "Gartengeräte":         {"niche_name": "garden-tools",         "subdomain": "gartengeraete"},
    "Klettern Ausrüstung":  {"niche_name": "climbing-gear",        "subdomain": "klettern"},
    "Angeln Zubehör":       {"niche_name": "fishing-accessories",  "subdomain": "angeln"},
    "Fotografie Zubehör":   {"niche_name": "photography-gear",     "subdomain": "fotografie"},
    "Fahrrad Zubehör":      {"niche_name": "cycling-accessories",  "subdomain": "fahrrad"},
    "Camping Ausrüstung":   {"niche_name": "camping-gear",         "subdomain": "camping"},
    "Yoga Zubehör":         {"niche_name": "yoga-accessories",     "subdomain": "yoga"},
    "Stricken Wolle":       {"niche_name": "knitting-wool",        "subdomain": "stricken"},
    "Basteln Erwachsene":   {"niche_name": "adult-crafting",       "subdomain": "basteln"},
    "Brettspiele":          {"niche_name": "board-games",          "subdomain": "brettspiele"},
    "Elektronik Basteln":   {"niche_name": "electronics-diy",      "subdomain": "elektronik-basteln"},
    "Nähen Anfänger":       {"niche_name": "sewing-beginners",     "subdomain": "naehen"},
}

# Known high-affiliate-potential niches in Germany (boosts score)
HIGH_AFFILIATE_NICHES = {
    "Modellbau", "Aquaristik", "Fahrrad Zubehör", "Fotografie Zubehör",
    "Camping Ausrüstung", "Klettern Ausrüstung", "Angeln Zubehör",
}


# ---------------------------------------------------------------------------
# Step 1 — fetch keyword + SERP data
# ---------------------------------------------------------------------------
def fetch_keyword_data(state: AgentState) -> AgentState:
    import requests

    logger.info("[ResearchAgent] fetch_keyword_data — starting")
    keyword_data = []

    for keyword in SEED_KEYWORDS:
        try:
            params = {
                "engine": "google",
                "q": f"{keyword} kaufen empfehlung",
                "gl": "de", "hl": "de", "num": 10,
                "api_key": settings.SERPAPI_KEY,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            organic = data.get("organic_results", [])
            ads = data.get("ads", [])
            related = data.get("related_searches", [])
            shopping = data.get("shopping_results", [])

            competitor_domains = [
                r.get("displayed_link", "").split("/")[0]
                for r in organic[:5] if r.get("displayed_link")
            ]

            keyword_data.append({
                "keyword": keyword,
                "has_ads": len(ads) > 0,
                "ad_count": len(ads),
                "has_shopping": len(shopping) > 0,
                "shopping_count": len(shopping),
                "organic_count": len(organic),
                "competitor_domains": competitor_domains,
                "related_searches": [r.get("query", "") for r in related[:5]],
                "top_result_title": organic[0].get("title", "") if organic else "",
            })
            logger.info(f"  ✓ {keyword} — {len(organic)} organic, {len(ads)} ads, {len(shopping)} shopping")

        except Exception as e:
            logger.warning(f"  ✗ SerpAPI error for '{keyword}': {e}")
            keyword_data.append({
                "keyword": keyword, "has_ads": False, "ad_count": 0,
                "has_shopping": False, "shopping_count": 0,
                "organic_count": 0, "competitor_domains": [],
                "related_searches": [], "top_result_title": "",
            })

    state["keyword_data"] = keyword_data
    state["messages"] = state.get("messages", []) + [
        f"Fetched SERP data for {len(keyword_data)} keywords"
    ]
    logger.info(f"[ResearchAgent] fetch_keyword_data — done ({len(keyword_data)} keywords)")
    return state


# ---------------------------------------------------------------------------
# Step 2 — fetch Google Trends data
# ---------------------------------------------------------------------------
def fetch_trend_data(state: AgentState) -> AgentState:
    import requests

    logger.info("[ResearchAgent] fetch_trend_data — starting")
    keyword_data = state.get("keyword_data", [])
    trend_data = []

    for item in keyword_data:
        keyword = item["keyword"]
        try:
            params = {
                "engine": "google_trends", "q": keyword,
                "geo": "DE", "date": "today 12-m",
                "api_key": settings.SERPAPI_KEY,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            values = []
            for point in timeline:
                for v in point.get("values", []):
                    try:
                        values.append(int(v.get("extracted_value", 0)))
                    except (ValueError, TypeError):
                        pass

            avg_interest = round(sum(values) / len(values), 1) if values else 0

            # Detect upward trend: compare last 3 months vs first 3 months
            trend_direction = "stable"
            if len(values) >= 6:
                early = sum(values[:3]) / 3
                recent = sum(values[-3:]) / 3
                if recent > early * 1.1:
                    trend_direction = "growing"
                elif recent < early * 0.9:
                    trend_direction = "declining"

            trend_data.append({
                "keyword": keyword,
                "avg_interest_12m": avg_interest,
                "trend_direction": trend_direction,
                "data_points": len(values),
            })
            logger.info(f"  ✓ {keyword} — avg interest: {avg_interest} ({trend_direction})")

        except Exception as e:
            logger.warning(f"  ✗ Trends error for '{keyword}': {e}")
            trend_data.append({
                "keyword": keyword, "avg_interest_12m": 0,
                "trend_direction": "unknown", "data_points": 0,
            })

    state["trend_data"] = trend_data
    state["messages"] = state.get("messages", []) + [
        f"Fetched trend data for {len(trend_data)} keywords"
    ]
    logger.info("[ResearchAgent] fetch_trend_data — done")
    return state


# ---------------------------------------------------------------------------
# Step 3 — local scoring algorithm (no GPT required)
# ---------------------------------------------------------------------------
def score_locally(state: AgentState) -> AgentState:
    """
    Score each niche 0-10 using:
      - Trend interest (40%) — higher avg interest = better
      - Commercial signals (30%) — ads + shopping results = buyer intent
      - Affiliate potential (20%) — known high-value niches get a boost
      - Trend direction (10%) — growing niches score higher
    """
    logger.info("[ResearchAgent] score_locally — starting")

    keyword_data = state.get("keyword_data", [])
    trend_data = state.get("trend_data", [])
    trend_map = {t["keyword"]: t for t in trend_data}

    scored = []
    for kw in keyword_data:
        keyword = kw["keyword"]
        trend = trend_map.get(keyword, {})
        meta = NICHE_META.get(keyword, {
            "niche_name": keyword.lower().replace(" ", "-"),
            "subdomain": keyword.lower().replace(" ", "-"),
        })

        avg_interest = trend.get("avg_interest_12m", 0)
        trend_direction = trend.get("trend_direction", "stable")
        has_ads = kw.get("has_ads", False)
        ad_count = kw.get("ad_count", 0)
        has_shopping = kw.get("has_shopping", False)
        shopping_count = kw.get("shopping_count", 0)

        # Component 1: trend interest score (0-4)
        trend_score = min(avg_interest / 100 * 4, 4.0)

        # Component 2: commercial intent score (0-3)
        commercial_score = 0.0
        if has_ads:
            commercial_score += 1.5
            commercial_score += min(ad_count * 0.3, 0.9)
        if has_shopping:
            commercial_score += 0.6
        commercial_score = min(commercial_score, 3.0)

        # Component 3: affiliate potential (0-2)
        affiliate_score = 2.0 if keyword in HIGH_AFFILIATE_NICHES else 1.0

        # Component 4: trend direction (0-1)
        direction_score = {"growing": 1.0, "stable": 0.5, "declining": 0.1, "unknown": 0.3}.get(trend_direction, 0.3)

        total_score = round(trend_score + commercial_score + affiliate_score + direction_score, 2)
        total_score = min(total_score, 10.0)

        go_no_go = "go" if total_score >= 5.0 else "no_go"

        # Recommended budget: proportional to score
        recommended_budget = round(total_score * 20, 0)  # €100-200 for top niches

        scored.append({
            "keyword": keyword,
            "niche_name": meta["niche_name"],
            "subdomain": meta["subdomain"],
            "score": total_score,
            "go_no_go": go_no_go,
            "recommended_budget": recommended_budget,
            "avg_trend_interest": avg_interest,
            "trend_direction": trend_direction,
            "has_ads": has_ads,
            "reasoning": (
                f"Trend interest {avg_interest}/100, "
                f"{'ads present' if has_ads else 'no ads'}, "
                f"trend is {trend_direction}"
            ),
        })
        logger.info(
            f"  ✓ {meta['niche_name']}: score={total_score} | "
            f"{go_no_go} | trend={avg_interest} | budget=€{recommended_budget}"
        )

    state["keyword_data"] = scored
    state["messages"] = state.get("messages", []) + [
        f"Locally scored {len(scored)} niches"
    ]
    logger.info("[ResearchAgent] score_locally — done")
    return state


# ---------------------------------------------------------------------------
# Step 4 — rank and persist to DB
# ---------------------------------------------------------------------------
def rank_and_persist(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche

    logger.info("[ResearchAgent] rank_and_persist — starting")

    scored = state.get("keyword_data", [])
    if not scored:
        state["error"] = "No scored niches to persist"
        state["completed"] = True
        return state

    sorted_niches = sorted(scored, key=lambda x: x.get("score", 0), reverse=True)

    db = SessionLocal()
    saved = 0
    skipped = 0

    try:
        for niche_data in sorted_niches:
            name = niche_data.get("niche_name") or niche_data.get("keyword", "unknown")
            subdomain = niche_data.get("subdomain", name.lower().replace(" ", "-"))

            existing = db.query(Niche).filter(Niche.name == name).first()
            if existing:
                logger.info(f"  ~ Skipping existing: {name}")
                skipped += 1
                continue

            niche = Niche(
                name=name,
                subdomain=subdomain,
                score=niche_data.get("score", 0.0),
                status="discovered",
                go_no_go=niche_data.get("go_no_go", "no_go"),
                recommended_budget=float(niche_data.get("recommended_budget", 0)),
                created_at=datetime.utcnow(),
            )
            db.add(niche)
            saved += 1
            logger.info(
                f"  ✓ Saved: {name} | score={niche_data.get('score')} "
                f"| {niche_data.get('go_no_go')} | €{niche_data.get('recommended_budget')}"
            )

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"[ResearchAgent] DB error: {e}")
        state["error"] = f"DB persist failed: {e}"
    finally:
        db.close()

    if sorted_niches:
        best = sorted_niches[0]
        state["niche_name"] = best.get("niche_name", "")
        state["score"] = best.get("score", 0.0)

    state["completed"] = True
    state["messages"] = state.get("messages", []) + [
        f"Persisted {saved} new niches, skipped {skipped} existing"
    ]
    logger.info(
        f"[ResearchAgent] rank_and_persist — done. "
        f"saved={saved}, skipped={skipped}"
    )
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    logger.error(f"[ResearchAgent] Terminal error: {state.get('error')}")
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class — plain pipeline, no LangGraph
# ---------------------------------------------------------------------------
class ResearchAgent(BaseAgent):
    name = "ResearchAgent"

    def build(self):
        return self

    def run(self, initial_state: AgentState) -> AgentState:
        state = initial_state

        state = fetch_keyword_data(state)
        if state.get("error"):
            return handle_error(state)

        state = fetch_trend_data(state)
        if state.get("error"):
            return handle_error(state)

        state = score_locally(state)
        if state.get("error"):
            return handle_error(state)

        state = rank_and_persist(state)
        return state