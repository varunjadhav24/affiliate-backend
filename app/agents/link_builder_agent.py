"""
Link Builder Agent — finds Amazon.de products for approved niches.

Uses SerpAPI Google Shopping to find Amazon.de products.
When Amazon PA-API credentials are available, swap search_products()
with pa_api_search_products() — rest of pipeline stays identical.
"""

import logging
import re
from datetime import datetime
from itertools import groupby

from app.agents.base import AgentState, BaseAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

NICHE_SEARCH_TERMS = {
    "model-building": [
        "Revell Modellbausatz site:amazon.de",
        "Modellbau Werkzeug Set site:amazon.de",
        "Airbrush Set Modellbau site:amazon.de",
    ],
    "aquaristics": [
        "Aquarium Starter Set site:amazon.de",
        "Aquarium Filter site:amazon.de",
        "Aquarium LED Beleuchtung site:amazon.de",
    ],
    "cycling-accessories": [
        "Fahrradhelm Herren site:amazon.de",
        "Fahrrad GPS Computer site:amazon.de",
        "Fahrrad Satteltasche site:amazon.de",
    ],
    "knitting-wool": [
        "Merino Wolle Stricken site:amazon.de",
        "Stricknadeln Set site:amazon.de",
        "Wolle Set Anfänger site:amazon.de",
    ],
    "camping-gear": [
        "Schlafsack Camping site:amazon.de",
        "Zelt 2 Personen leicht site:amazon.de",
        "Camping Kocher Set site:amazon.de",
    ],
    "board-games": [
        "Catan Brettspiel site:amazon.de",
        "Brettspiel Erwachsene site:amazon.de",
        "Kartenspiel Familie site:amazon.de",
    ],
    "fishing-accessories": [
        "Angelrute Set Anfänger site:amazon.de",
        "Angelrolle Freilauf site:amazon.de",
        "Kunstköder Set site:amazon.de",
    ],
    "photography-gear": [
        "Kamera Stativ site:amazon.de",
        "Kamera Tasche site:amazon.de",
        "ND Filter Set site:amazon.de",
    ],
    "climbing-gear": [
        "Kletterschuhe Herren site:amazon.de",
        "Kletterausrüstung Set site:amazon.de",
        "Sicherungsgerät Klettern site:amazon.de",
    ],
    "sewing-beginners": [
        "Nähmaschine Anfänger site:amazon.de",
        "Nähset Anfänger site:amazon.de",
        "Schnittmuster Anfänger site:amazon.de",
    ],
    "adult-crafting": [
        "Diamond Painting Set site:amazon.de",
        "Malen nach Zahlen Erwachsene site:amazon.de",
        "Bastelset Erwachsene site:amazon.de",
    ],
    "diy-home-improvement": [
        "Akku Schrauber Set site:amazon.de",
        "Bohrmaschine Schlagbohrmaschine site:amazon.de",
        "Werkzeugset Heimwerker site:amazon.de",
    ],
    "yoga-accessories": [
        "Yogamatte rutschfest site:amazon.de",
        "Yoga Block Kork site:amazon.de",
        "Yoga Set Anfänger site:amazon.de",
    ],
    "garden-tools": [
        "Gartenwerkzeug Set site:amazon.de",
        "Hochbeet Bausatz Holz site:amazon.de",
        "Bewässerungssystem Garten site:amazon.de",
    ],
    "electronics-diy": [
        "Arduino Starter Kit site:amazon.de",
        "Raspberry Pi Set site:amazon.de",
        "Lötkolben Set Anfänger site:amazon.de",
    ],
}

ASIN_PATTERN = re.compile(r'/dp/([A-Z0-9]{10})')


def extract_asin(url: str) -> str | None:
    match = ASIN_PATTERN.search(url)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Step 1 — load niches from DB
# ---------------------------------------------------------------------------
def load_approved_niches(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche

    logger.info("[LinkBuilderAgent] load_approved_niches — starting")
    db = SessionLocal()
    try:
        if state.get("niche_id"):
            niches = db.query(Niche).filter(Niche.id == state["niche_id"]).all()
        else:
            niches = db.query(Niche).filter(
                Niche.status.in_(["approved", "discovered"])
            ).all()

        niche_list = [
            {"id": n.id, "name": n.name, "subdomain": n.subdomain}
            for n in niches
        ]
        logger.info(f"  Found {len(niche_list)} niches to process")
    finally:
        db.close()

    state["affiliate_products"] = niche_list
    state["messages"] = state.get("messages", []) + [
        f"Loaded {len(niche_list)} niches"
    ]
    return state


# ---------------------------------------------------------------------------
# Step 2 — search Amazon.de products via SerpAPI organic search
# ---------------------------------------------------------------------------
def search_products(state: AgentState) -> AgentState:
    import requests

    logger.info("[LinkBuilderAgent] search_products — starting")
    niche_list = state.get("affiliate_products", [])
    all_products = []

    for niche in niche_list:
        niche_name = niche["name"]
        search_terms = NICHE_SEARCH_TERMS.get(niche_name, [f"{niche_name} site:amazon.de"])
        niche_products = []

        logger.info(f"  Searching products for niche: {niche_name}")

        for term in search_terms[:3]:
            try:
                # Use organic search targeting Amazon.de directly
                params = {
                    "engine": "google",
                    "q": term,
                    "gl": "de",
                    "hl": "de",
                    "num": 5,
                    "api_key": settings.SERPAPI_KEY,
                }
                resp = requests.get(
                    "https://serpapi.com/search", params=params, timeout=20
                )
                resp.raise_for_status()
                data = resp.json()

                organic = data.get("organic_results", [])
                for item in organic:
                    link = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")

                    # Only Amazon.de product pages
                    if "amazon.de" not in link:
                        continue
                    if "/dp/" not in link and "/gp/product/" not in link:
                        continue

                    asin = extract_asin(link)

                    # Try to extract price from snippet
                    price = None
                    price_match = re.search(r'(\d+[.,]\d{2})\s*€|€\s*(\d+[.,]\d{2})', snippet)
                    if price_match:
                        raw = price_match.group(1) or price_match.group(2)
                        try:
                            price = float(raw.replace(".", "").replace(",", "."))
                        except ValueError:
                            pass

                    # Extract rating from snippet
                    rating = None
                    rating_match = re.search(r'(\d[.,]\d)\s*von\s*5|(\d[.,]\d)\s*Sterne', snippet)
                    if rating_match:
                        raw_r = rating_match.group(1) or rating_match.group(2)
                        try:
                            rating = float(raw_r.replace(",", "."))
                        except ValueError:
                            pass

                    niche_products.append({
                        "niche_id": niche["id"],
                        "niche_name": niche_name,
                        "product_name": title.replace(" - Amazon.de", "").replace(" | Amazon.de", "").strip(),
                        "asin": asin,
                        "link_url": link,
                        "price": price,
                        "rating": rating,
                    })
                    logger.info(
                        f"    ✓ {title[:50]} | ASIN={asin} | €{price} | ⭐{rating}"
                    )

                # Also check Google Shopping results
                shopping = data.get("shopping_results", [])
                for item in shopping[:3]:
                    source = item.get("source", "")
                    link = item.get("link", "") or item.get("product_link", "")
                    if "amazon" not in source.lower() and "amazon" not in link.lower():
                        continue

                    title = item.get("title", "")
                    asin = extract_asin(link)

                    price_str = item.get("price", "0")
                    try:
                        price = float(
                            price_str.replace("€", "").replace(".", "")
                            .replace(",", ".").strip()
                        )
                    except (ValueError, AttributeError):
                        price = None

                    rating_raw = item.get("rating")
                    try:
                        rating = float(rating_raw) if rating_raw else None
                    except (ValueError, TypeError):
                        rating = None

                    niche_products.append({
                        "niche_id": niche["id"],
                        "niche_name": niche_name,
                        "product_name": title,
                        "asin": asin,
                        "link_url": link,
                        "price": price,
                        "rating": rating,
                    })
                    logger.info(
                        f"    ✓ [shop] {title[:50]} | ASIN={asin} | €{price} | ⭐{rating}"
                    )

            except Exception as e:
                logger.warning(f"    ✗ Search error for '{term}': {e}")

        # Deduplicate by ASIN within this niche
        seen_asins = set()
        seen_titles = set()
        deduped = []
        for p in niche_products:
            key = p.get("asin") or p.get("product_name", "")[:40]
            if key and key not in seen_asins and p["product_name"] not in seen_titles:
                seen_asins.add(key)
                seen_titles.add(p["product_name"])
                deduped.append(p)

        logger.info(f"  → {len(deduped)} unique Amazon products for {niche_name}")
        all_products.extend(deduped)

    state["affiliate_products"] = all_products
    state["messages"] = state.get("messages", []) + [
        f"Found {len(all_products)} Amazon.de products"
    ]
    logger.info(f"[LinkBuilderAgent] search_products — done ({len(all_products)} products)")
    return state


# ---------------------------------------------------------------------------
# Step 3 — score and filter
# ---------------------------------------------------------------------------
def score_and_filter(state: AgentState) -> AgentState:
    logger.info("[LinkBuilderAgent] score_and_filter — starting")
    products = state.get("affiliate_products", [])

    for p in products:
        score = 0
        price = p.get("price") or 0
        rating = p.get("rating") or 0

        # Price sweet spot €20-€200
        if 20 <= price <= 50:
            score += 3
        elif 50 < price <= 150:
            score += 5
        elif 150 < price <= 300:
            score += 4
        elif price > 300:
            score += 2
        elif 5 <= price < 20:
            score += 1

        # Rating bonus
        if rating >= 4.5:
            score += 3
        elif rating >= 4.0:
            score += 2
        elif rating >= 3.5:
            score += 1

        # Has ASIN = proper affiliate link possible
        if p.get("asin"):
            score += 2

        p["product_score"] = score

    # Sort and keep top 10 per niche
    products.sort(key=lambda x: (x["niche_id"], -x["product_score"]))
    filtered = []
    for niche_id, group in groupby(products, key=lambda x: x["niche_id"]):
        top = list(group)[:10]
        filtered.extend(top)
        logger.info(f"  Niche {niche_id}: kept {len(top)} products")

    state["affiliate_products"] = filtered
    state["messages"] = state.get("messages", []) + [
        f"Filtered to {len(filtered)} top products"
    ]
    logger.info(f"[LinkBuilderAgent] score_and_filter — done ({len(filtered)} kept)")
    return state


# ---------------------------------------------------------------------------
# Step 4 — generate affiliate links and persist
# ---------------------------------------------------------------------------
def generate_links(state: AgentState) -> AgentState:
    import urllib.parse
    from app.db.session import SessionLocal
    from app.models.affiliate_link import AffiliateLink

    logger.info("[LinkBuilderAgent] generate_links — starting")
    products = state.get("affiliate_products", [])
    partner_tag = settings.AMAZON_PARTNER_TAG

    if not partner_tag or partner_tag in ("your_amazon_partner_tag", "your-associate-tag-21", ""):
        partner_tag = "affiliate-21"
        logger.warning("  AMAZON_PARTNER_TAG not set — using placeholder 'affiliate-21'")

    db = SessionLocal()
    saved = 0
    updated = 0

    try:
        for p in products:
            asin = p.get("asin")

            # Build proper affiliate URL
            if asin:
                params = urllib.parse.urlencode({"tag": partner_tag, "linkCode": "ogi"})
                affiliate_url = f"https://www.amazon.de/dp/{asin}?{params}"
            else:
                raw_url = p.get("link_url", "")
                if raw_url and not raw_url.startswith("?"):
                    sep = "&" if "?" in raw_url else "?"
                    affiliate_url = f"{raw_url}{sep}tag={partner_tag}"
                else:
                    # Skip products with no usable URL
                    logger.warning(f"  Skipping (no URL): {p.get('product_name', '')[:40]}")
                    continue

            # Upsert: update if exists, insert if new
            existing = db.query(AffiliateLink).filter(
                AffiliateLink.niche_id == p["niche_id"],
                AffiliateLink.product_name == p["product_name"],
            ).first()

            if existing:
                existing.price = p.get("price")
                existing.rating = p.get("rating")
                existing.link_url = affiliate_url
                existing.last_checked = datetime.utcnow()
                updated += 1
            else:
                link = AffiliateLink(
                    niche_id=p["niche_id"],
                    product_name=p["product_name"],
                    asin=asin,
                    link_url=affiliate_url,
                    price=p.get("price"),
                    rating=p.get("rating"),
                    status="active",
                    last_checked=datetime.utcnow(),
                )
                db.add(link)
                saved += 1
                logger.info(
                    f"  ✓ {p['product_name'][:55]} | "
                    f"ASIN={asin} | €{p.get('price')} | ⭐{p.get('rating')}"
                )

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"[LinkBuilderAgent] DB error: {e}")
        state["error"] = f"DB persist failed: {e}"
    finally:
        db.close()

    state["links_created"] = saved
    state["completed"] = True
    state["messages"] = state.get("messages", []) + [
        f"Saved {saved} new links, updated {updated} existing"
    ]
    logger.info(
        f"[LinkBuilderAgent] generate_links — done. "
        f"saved={saved}, updated={updated}"
    )
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    logger.error(f"[LinkBuilderAgent] Terminal error: {state.get('error')}")
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class LinkBuilderAgent(BaseAgent):
    name = "LinkBuilderAgent"

    def build(self):
        return self

    def run(self, initial_state: AgentState) -> AgentState:
        state = initial_state

        state = load_approved_niches(state)
        if state.get("error"):
            return handle_error(state)

        state = search_products(state)
        if state.get("error"):
            return handle_error(state)

        state = score_and_filter(state)
        if state.get("error"):
            return handle_error(state)

        state = generate_links(state)
        return state