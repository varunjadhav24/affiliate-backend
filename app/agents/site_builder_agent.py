"""
Site Builder Agent — generates German SEO content for affiliate sites.

Current mode: Template-based German content (no API cost)
Upgrade path: Replace generate_content() with GPT-4o version when credits available.

Generates per niche:
  - 1 homepage (Startseite)
  - 3 product review pages (Testbericht)
  - 1 buying guide (Kaufratgeber)
  - 1 top-10 list page (Top 10)

All pages are saved to the `pages` table with status='published'.
"""

import logging
from datetime import datetime

from app.agents.base import AgentState, BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# German SEO templates per page type
# ---------------------------------------------------------------------------

def render_homepage(niche_name: str, subdomain: str, products: list) -> str:
    display_name = niche_name.replace("-", " ").title()
    product_list = ""
    for i, p in enumerate(products[:5], 1):
        price_str = f"€{p['price']}" if p.get("price") else "Preis prüfen"
        rating_str = f"⭐ {p['rating']}" if p.get("rating") else ""
        product_list += f"""
        <div class="product-card">
            <h3>{i}. {p['product_name']}</h3>
            <p class="price">{price_str} {rating_str}</p>
            <a href="{p['link_url']}" class="btn" target="_blank" rel="nofollow">
                Auf Amazon ansehen →
            </a>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} Zubehör kaufen — Die besten Produkte im Test 2024</title>
    <meta name="description" content="Die besten {display_name} Produkte im Vergleich. 
    Expertenempfehlungen, ehrliche Tests und günstige Preise für Anfänger und Profis.">
</head>
<body>
    <header>
        <h1>🏆 Die besten {display_name} Produkte 2024</h1>
        <p>Unabhängige Tests und Empfehlungen für Einsteiger und Fortgeschrittene</p>
    </header>
    <main>
        <section class="intro">
            <h2>Warum {display_name}?</h2>
            <p>{display_name} ist eines der beliebtesten Hobbys in Deutschland. 
            Ob Anfänger oder erfahrener Enthusiast — die richtige Ausrüstung macht den Unterschied.
            Wir haben die besten Produkte für Sie getestet und verglichen.</p>
        </section>
        <section class="top-products">
            <h2>Unsere Top-Empfehlungen</h2>
            {product_list if product_list else '<p>Produkte werden geladen...</p>'}
        </section>
        <section class="categories">
            <h2>Weitere Ratgeber</h2>
            <ul>
                <li><a href="/kaufratgeber">{display_name} Kaufratgeber für Anfänger</a></li>
                <li><a href="/top10">Die 10 besten {display_name} Produkte</a></li>
                <li><a href="/testberichte">Alle Testberichte im Überblick</a></li>
            </ul>
        </section>
    </main>
    <footer>
        <p>* Affiliate-Links: Bei einem Kauf über unsere Links erhalten wir eine kleine Provision. 
        Der Preis für Sie bleibt gleich.</p>
    </footer>
</body>
</html>"""


def render_product_review(niche_name: str, product: dict) -> str:
    display_name = niche_name.replace("-", " ").title()
    product_name = product.get("product_name", "Produkt")
    price_str = f"€{product['price']}" if product.get("price") else "Preis auf Amazon prüfen"
    rating = product.get("rating", 0) or 0
    stars = "⭐" * int(rating) if rating else "⭐⭐⭐⭐"
    asin = product.get("asin", "")

    pros = [
        f"Ideal für {display_name}-Enthusiasten",
        "Gutes Preis-Leistungs-Verhältnis",
        "Schnelle Lieferung über Amazon Prime",
        "Hohe Kundenzufriedenheit",
    ]
    cons = [
        "Für absolute Profis ggf. zu einfach",
        "Zubehör separat erhältlich",
    ]

    pros_html = "".join(f"<li>✅ {p}</li>" for p in pros)
    cons_html = "".join(f"<li>❌ {p}</li>" for p in cons)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product_name} im Test — Lohnt sich der Kauf? (2024)</title>
    <meta name="description" content="{product_name} Testbericht: Alle Vor- und Nachteile, 
    Preis-Leistungs-Check und unsere Empfehlung für {display_name}-Fans.">
</head>
<body>
    <article>
        <header>
            <h1>{product_name} — Testbericht & Erfahrungen</h1>
            <div class="rating">Bewertung: {stars} ({rating}/5)</div>
            <div class="price">Aktueller Preis: <strong>{price_str}</strong></div>
        </header>
        <section class="summary">
            <h2>Kurzbewertung</h2>
            <p>Das <strong>{product_name}</strong> ist eine ausgezeichnete Wahl für alle 
            {display_name}-Begeisterten. In unserem ausführlichen Test haben wir alle 
            wichtigen Eigenschaften unter die Lupe genommen.</p>
        </section>
        <section class="pros-cons">
            <div class="pros">
                <h3>Vorteile</h3>
                <ul>{pros_html}</ul>
            </div>
            <div class="cons">
                <h3>Nachteile</h3>
                <ul>{cons_html}</ul>
            </div>
        </section>
        <section class="verdict">
            <h2>Unser Fazit</h2>
            <p>Wer auf der Suche nach einem zuverlässigen {display_name}-Produkt ist, 
            liegt mit dem {product_name} richtig. Das Preis-Leistungs-Verhältnis überzeugt, 
            besonders für Einsteiger und Fortgeschrittene.</p>
            <a href="{product.get('link_url', '#')}" class="cta-button" 
               target="_blank" rel="nofollow">
                Jetzt auf Amazon kaufen — {price_str}
            </a>
        </section>
        {'<div class="asin">ASIN: ' + asin + '</div>' if asin else ''}
    </article>
    <footer>
        <p>* Affiliate-Link: Wir erhalten eine Provision bei Kauf über diesen Link.</p>
    </footer>
</body>
</html>"""


def render_buying_guide(niche_name: str, products: list) -> str:
    display_name = niche_name.replace("-", " ").title()

    checklist_items = [
        "Qualität und Verarbeitung der Materialien",
        "Preis-Leistungs-Verhältnis",
        "Bewertungen anderer Käufer",
        "Kompatibilität mit vorhandenem Zubehör",
        "Lieferumfang und Garantie",
    ]
    checklist_html = "".join(f"<li>☑ {item}</li>" for item in checklist_items)

    product_list_html = ""
    for i, p in enumerate(products[:3], 1):
        price_str = f"€{p['price']}" if p.get("price") else "Preis prüfen"
        product_list_html += f"""
        <div class="recommended-product">
            <span class="rank">#{i}</span>
            <strong>{p['product_name']}</strong>
            <span class="price">{price_str}</span>
            <a href="{p['link_url']}" target="_blank" rel="nofollow">Ansehen →</a>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} Kaufratgeber 2024 — Was Sie wissen müssen</title>
    <meta name="description" content="Der ultimative {display_name} Kaufratgeber: 
    Worauf Sie achten müssen, welche Produkte sich lohnen und wo Sie am günstigsten kaufen.">
</head>
<body>
    <article>
        <header>
            <h1>{display_name} kaufen: Der große Ratgeber 2024</h1>
            <p>Alles was Sie vor dem Kauf wissen müssen — von Experten zusammengefasst</p>
        </header>
        <section>
            <h2>Worauf sollten Sie achten?</h2>
            <p>Beim Kauf von {display_name}-Produkten gibt es einige wichtige Kriterien, 
            die über Qualität und Zufriedenheit entscheiden. Wir haben die wichtigsten 
            Punkte für Sie zusammengefasst:</p>
            <ul class="checklist">{checklist_html}</ul>
        </section>
        <section>
            <h2>Für wen eignet sich welches Produkt?</h2>
            <h3>Einsteiger</h3>
            <p>Als Anfänger empfehlen wir günstigere Einsteigermodelle, um zunächst 
            Erfahrungen zu sammeln. Diese sind benutzerfreundlich und bieten ein gutes 
            Preis-Leistungs-Verhältnis.</p>
            <h3>Fortgeschrittene</h3>
            <p>Für erfahrene {display_name}-Enthusiasten lohnt sich die Investition in 
            hochwertigere Produkte, die mehr Funktionen und bessere Materialqualität bieten.</p>
        </section>
        <section>
            <h2>Unsere Top-Empfehlungen</h2>
            {product_list_html if product_list_html else '<p>Empfehlungen werden geladen...</p>'}
        </section>
        <section>
            <h2>Häufige Fragen (FAQ)</h2>
            <details>
                <summary>Wo kaufe ich {display_name}-Produkte am günstigsten?</summary>
                <p>Amazon.de bietet meist die besten Preise mit schneller Lieferung und 
                kostenlosem Rückgaberecht. Viele Produkte sind bei Prime-Mitgliedschaft 
                am nächsten Tag lieferbar.</p>
            </details>
            <details>
                <summary>Welche Marken sind bei {display_name} empfehlenswert?</summary>
                <p>Es gibt viele gute Anbieter — entscheidend ist das 
                Preis-Leistungs-Verhältnis und die Kundenbewertungen auf Amazon.</p>
            </details>
        </section>
    </article>
    <footer>
        <p>* Affiliate-Links: Wir erhalten eine Provision bei Kauf über unsere Links.</p>
    </footer>
</body>
</html>"""


def render_top10(niche_name: str, products: list) -> str:
    display_name = niche_name.replace("-", " ").title()

    items_html = ""
    for i, p in enumerate(products[:10], 1):
        price_str = f"€{p['price']}" if p.get("price") else "Preis prüfen"
        rating_str = f"⭐ {p['rating']}/5" if p.get("rating") else "⭐⭐⭐⭐"
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        items_html += f"""
        <div class="top-item">
            <div class="rank">{medal}</div>
            <div class="product-info">
                <h3>{p['product_name']}</h3>
                <div class="meta">
                    <span class="price">{price_str}</span>
                    <span class="rating">{rating_str}</span>
                </div>
                <a href="{p['link_url']}" class="buy-btn" target="_blank" rel="nofollow">
                    Auf Amazon ansehen →
                </a>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Die 10 besten {display_name} Produkte 2024 — Vergleich & Test</title>
    <meta name="description" content="Die 10 besten {display_name} Produkte im großen 
    Vergleich 2024. Testsieger, Preis-Leistungs-Sieger und Geheimtipps.">
</head>
<body>
    <article>
        <header>
            <h1>Die 10 besten {display_name} Produkte 2024</h1>
            <p>Unser großer Produktvergleich — getestet und bewertet</p>
        </header>
        <section class="ranking">
            {items_html if items_html else '<p>Produkte werden geladen...</p>'}
        </section>
        <section class="conclusion">
            <h2>Unser Fazit</h2>
            <p>Die Auswahl des richtigen {display_name}-Produkts hängt von Ihren 
            persönlichen Anforderungen und Ihrem Budget ab. Alle oben genannten Produkte 
            haben wir sorgfältig geprüft und können sie empfehlen.</p>
        </section>
    </article>
    <footer>
        <p>* Affiliate-Links: Wir erhalten eine Provision bei Kauf über unsere Links.</p>
    </footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Step 1 — load approved niches and their affiliate links
# ---------------------------------------------------------------------------
def load_niche_data(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.niche import Niche
    from app.models.affiliate_link import AffiliateLink

    logger.info("[SiteBuilderAgent] load_niche_data — starting")
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

            products = [
                {
                    "product_name": lnk.product_name,
                    "asin": lnk.asin,
                    "link_url": lnk.link_url,
                    "price": lnk.price,
                    "rating": lnk.rating,
                }
                for lnk in links
            ]

            niche_data.append({
                "id": niche.id,
                "name": niche.name,
                "subdomain": niche.subdomain,
                "products": products,
            })
            logger.info(
                f"  Loaded: {niche.name} | {len(products)} products"
            )

    finally:
        db.close()

    state["pages_generated"] = niche_data
    state["messages"] = state.get("messages", []) + [
        f"Loaded {len(niche_data)} niches for site building"
    ]
    logger.info(f"[SiteBuilderAgent] load_niche_data — done ({len(niche_data)} niches)")
    return state


# ---------------------------------------------------------------------------
# Step 2 — generate pages using templates
# ---------------------------------------------------------------------------
def generate_content(state: AgentState) -> AgentState:
    logger.info("[SiteBuilderAgent] generate_content — starting")
    niche_data = state.get("pages_generated", [])
    all_pages = []

    for niche in niche_data:
        name = niche["name"]
        subdomain = niche["subdomain"]
        products = niche["products"]

        logger.info(f"  Generating pages for: {name}")

        pages = []

        # 1. Homepage
        pages.append({
            "niche_id": niche["id"],
            "page_type": "homepage",
            "url": f"https://{subdomain}.{state.get('base_domain', 'starterkit.de')}/",
            "content": render_homepage(name, subdomain, products),
            "title": f"{name.replace('-', ' ').title()} — Startseite",
        })

        # 2. Product reviews (up to 3)
        for i, product in enumerate(products[:3], 1):
            slug = product["product_name"][:40].lower().replace(" ", "-").replace(",", "")
            pages.append({
                "niche_id": niche["id"],
                "page_type": "review",
                "url": f"https://{subdomain}.starterkit.de/testbericht/{slug}/",
                "content": render_product_review(name, product),
                "title": f"{product['product_name'][:50]} — Testbericht",
            })

        # 3. Buying guide
        pages.append({
            "niche_id": niche["id"],
            "page_type": "buying_guide",
            "url": f"https://{subdomain}.starterkit.de/kaufratgeber/",
            "content": render_buying_guide(name, products),
            "title": f"{name.replace('-', ' ').title()} Kaufratgeber 2024",
        })

        # 4. Top 10 list
        pages.append({
            "niche_id": niche["id"],
            "page_type": "top10",
            "url": f"https://{subdomain}.starterkit.de/top10/",
            "content": render_top10(name, products),
            "title": f"Die 10 besten {name.replace('-', ' ').title()} Produkte",
        })

        logger.info(f"  ✓ Generated {len(pages)} pages for {name}")
        all_pages.extend(pages)

    state["pages_generated"] = all_pages
    state["messages"] = state.get("messages", []) + [
        f"Generated {len(all_pages)} pages across all niches"
    ]
    logger.info(f"[SiteBuilderAgent] generate_content — done ({len(all_pages)} pages)")
    return state


# ---------------------------------------------------------------------------
# Step 3 — persist pages to DB
# ---------------------------------------------------------------------------
def publish_pages(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal
    from app.models.page import Page
    from app.models.niche import Niche

    logger.info("[SiteBuilderAgent] publish_pages — starting")
    pages = state.get("pages_generated", [])
    db = SessionLocal()
    saved = 0
    updated = 0

    try:
        for page_data in pages:
            existing = db.query(Page).filter(
                Page.niche_id == page_data["niche_id"],
                Page.page_type == page_data["page_type"],
                Page.url == page_data["url"],
            ).first()

            if existing:
                existing.content = page_data["content"]
                existing.published_at = datetime.utcnow()
                existing.status = "published"
                updated += 1
            else:
                page = Page(
                    niche_id=page_data["niche_id"],
                    page_type=page_data["page_type"],
                    url=page_data["url"],
                    content=page_data["content"],
                    published_at=datetime.utcnow(),
                    status="published",
                )
                db.add(page)
                saved += 1
                logger.info(
                    f"  ✓ Published: [{page_data['page_type']}] {page_data['url']}"
                )

            # Update niche status to 'live'
            niche = db.query(Niche).filter(
                Niche.id == page_data["niche_id"]
            ).first()
            if niche and niche.status in ("approved", "discovered"):
                niche.status = "live"

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"[SiteBuilderAgent] DB error: {e}")
        state["error"] = f"DB persist failed: {e}"
    finally:
        db.close()

    state["pages_published"] = saved
    state["completed"] = True
    state["messages"] = state.get("messages", []) + [
        f"Published {saved} new pages, updated {updated} existing"
    ]
    logger.info(
        f"[SiteBuilderAgent] publish_pages — done. "
        f"saved={saved}, updated={updated}"
    )
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    logger.error(f"[SiteBuilderAgent] Terminal error: {state.get('error')}")
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class — plain pipeline, GPT-4o upgrade-ready
# ---------------------------------------------------------------------------
class SiteBuilderAgent(BaseAgent):
    name = "SiteBuilderAgent"

    def build(self):
        return self

    def run(self, initial_state: AgentState) -> AgentState:
        state = initial_state

        state = load_niche_data(state)
        if state.get("error"):
            return handle_error(state)

        state = generate_content(state)
        if state.get("error"):
            return handle_error(state)

        state = publish_pages(state)
        return state