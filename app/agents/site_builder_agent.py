"""
Site Builder Agent — generates story-driven German advertorial content using GPT-4o.

Each niche gets a fully personalized advertorial page with:
  - German author persona (name, age, profession, city)
  - Personal story (emotional, authentic, 5 paragraphs)
  - 2 pull quotes
  - Product grid with Amazon affiliate images
  - Bundle section (5 products, add-all-to-cart)
  - 3 verified buyer reviews
  - 3 FAQ questions
  - Impressum + Datenschutz pages
  - DE/EN language toggle
"""

import json
import logging
import os
from datetime import datetime

from app.agents.base import AgentState, BaseAgent

logger = logging.getLogger(__name__)

AFFILIATE_TAG = "starterkit03-21"
BASE_DOMAIN = "bestehobby.de"

# ---------------------------------------------------------------------------
# Amazon image widget URL helper
# ---------------------------------------------------------------------------
def amazon_img(asin: str) -> str:
    return f"https://ws-eu.amazon-adsystem.com/widgets/q?_encoding=UTF8&ASIN={asin}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=SL250&tag=starterkit03-21"

def amazon_link(asin: str) -> str:
    return f"https://www.amazon.de/dp/{asin}?tag={AFFILIATE_TAG}"

def amazon_bundle_url(asins: list) -> str:
    params = "&".join(
        f"ASIN.{i+1}={asin}&Quantity.{i+1}=1"
        for i, asin in enumerate(asins[:5])
    )
    return f"https://www.amazon.de/gp/aws/cart/add.html?{params}&tag={AFFILIATE_TAG}"

# ---------------------------------------------------------------------------
# Unsplash hero images per niche
# ---------------------------------------------------------------------------
NICHE_IMAGES = {
    "model-building":     "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&auto=format&fit=crop",
    "aquaristics":        "https://images.unsplash.com/photo-1524704654690-b56c05c78a00?w=1200&auto=format&fit=crop",
    "fishing-accessories":"https://images.unsplash.com/photo-1652210145257-7dc5b40a34c3?w=1200&auto=format&fit=crop",
    "camping-gear":       "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=1200&auto=format&fit=crop",
    "photography-gear":   "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=1200&auto=format&fit=crop",
    "yoga-accessories":   "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&auto=format&fit=crop",
    "cycling-accessories":"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&auto=format&fit=crop",
    "knitting-wool":      "https://images.unsplash.com/photo-1582454235043-9fb646a80e0b?w=1200&auto=format&fit=crop",
    "board-games":        "https://images.unsplash.com/photo-1611996575749-79a3a250f948?w=1200&auto=format&fit=crop",
    "garden-tools":       "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1200&auto=format&fit=crop",
    "electronics-diy":    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&auto=format&fit=crop",
    "climbing-gear":      "https://images.unsplash.com/photo-1522163182402-834f871fd851?w=1200&auto=format&fit=crop",
    "sewing-beginners":   "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&auto=format&fit=crop",
    "diy-home-improvement":"https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=1200&auto=format&fit=crop",
    "adult-crafting":     "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?w=1200&auto=format&fit=crop",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=1200&auto=format&fit=crop"

# ---------------------------------------------------------------------------
# GPT-4o story generation
# ---------------------------------------------------------------------------
def generate_story_with_gpt4o(niche_name: str, products: list) -> dict:
    """Generate full advertorial content using GPT-4o."""
    import openai

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    display_name = niche_name.replace("-", " ").title()

    product_list_str = "\n".join(
        f"- ASIN: {p['asin']} | Name: {p['product_name']} | Price: €{p.get('price', '?')}"
        for p in products[:5]
    )

    prompt = f"""Du bist ein professioneller deutscher Content-Writer für Affiliate-Marketing.

Erstelle einen vollständigen deutschen Advertorial-Artikel für die Nische: "{display_name}"

Die folgenden Amazon.de Produkte sollen empfohlen werden:
{product_list_str}

Schreibe eine ECHTE, emotionale, persönliche Geschichte einer deutschen Person (45-55 Jahre alt), 
die dieses Hobby entdeckt hat und wie es ihr Leben verändert hat.

Antworte NUR mit einem gültigen JSON-Objekt (kein Markdown, keine Erklärungen):

{{
  "author_name": "Vollständiger Name (typisch deutsch)",
  "author_age": 52,
  "author_profession": "Beruf",
  "author_city": "Deutsche Stadt",
  "author_initials": "XX",
  "headline": "Emotionale, persönliche Überschrift (max 80 Zeichen)",
  "headline_en": "English translation of headline",
  "subtitle": "Untertitel der Geschichte (max 120 Zeichen)",
  "subtitle_en": "English translation",
  "story_p1": "Erster Absatz - Problem/Situation (150-200 Wörter)",
  "story_p1_en": "English translation",
  "story_p2": "Zweiter Absatz - Wendepunkt (150-200 Wörter)",
  "story_p2_en": "English translation",
  "story_p3": "Dritter Absatz - Entdeckung (150-200 Wörter)",
  "story_p3_en": "English translation",
  "story_p4": "Vierter Absatz - Ergebnis/Transformation (150-200 Wörter)",
  "story_p4_en": "English translation",
  "pull_quote_1": "Einprägsames Zitat aus der Geschichte (max 150 Zeichen)",
  "pull_quote_1_en": "English translation",
  "pull_quote_2": "Zweites einprägsames Zitat (max 150 Zeichen)",
  "pull_quote_2_en": "English translation",
  "highlight_tip": "Praktischer Tipp für Anfänger (max 200 Zeichen)",
  "highlight_tip_en": "English translation",
  "products": [
    {{
      "asin": "ASIN aus der Liste",
      "name_de": "Produktname auf Deutsch",
      "name_en": "Product name in English",
      "price": "€XX,XX",
      "stars": "4.5",
      "description_de": "Kurze Produktbeschreibung (max 100 Zeichen)",
      "description_en": "Short product description"
    }}
  ],
  "bundle_title_de": "Titel des Starter-Bundles",
  "bundle_title_en": "Bundle title in English",
  "bundle_desc_de": "Beschreibung des Bundles (max 200 Zeichen)",
  "bundle_desc_en": "Bundle description in English",
  "reviews": [
    {{
      "initials": "MK",
      "name": "Deutscher Name, Stadt",
      "date_de": "März 2026",
      "date_en": "March 2026",
      "stars": 5,
      "text_de": "Authentische Bewertung (100-150 Wörter)",
      "text_en": "English translation"
    }},
    {{
      "initials": "SB",
      "name": "Deutscher Name, Stadt",
      "date_de": "Februar 2026",
      "date_en": "February 2026",
      "stars": 5,
      "text_de": "Authentische Bewertung (100-150 Wörter)",
      "text_en": "English translation"
    }},
    {{
      "initials": "TF",
      "name": "Deutscher Name, Stadt",
      "date_de": "Januar 2026",
      "date_en": "January 2026",
      "stars": 4,
      "text_de": "Authentische Bewertung (100-150 Wörter)",
      "text_en": "English translation"
    }}
  ],
  "faqs": [
    {{
      "q_de": "Häufige Anfängerfrage?",
      "q_en": "English question?",
      "a_de": "Hilfreiche Antwort (100-150 Wörter)",
      "a_en": "English answer"
    }},
    {{
      "q_de": "Zweite Anfängerfrage?",
      "q_en": "English question?",
      "a_de": "Hilfreiche Antwort (100-150 Wörter)",
      "a_en": "English answer"
    }},
    {{
      "q_de": "Dritte Anfängerfrage?",
      "q_en": "English question?",
      "a_de": "Hilfreiche Antwort (100-150 Wörter)",
      "a_en": "English answer"
    }}
  ],
  "cta_title_de": "Abschließender Call-to-Action Titel",
  "cta_title_en": "CTA title in English",
  "cta_text_de": "Abschließender Text (max 200 Zeichen)",
  "cta_text_en": "CTA text in English"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.8,
        )
        raw = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        logger.error(f"GPT-4o error for {niche_name}: {e}")
        return None

# ---------------------------------------------------------------------------
# HTML template renderer
# ---------------------------------------------------------------------------
def render_advertorial(niche_name: str, story: dict, products: list, hero_image: str) -> str:
    """Render advertorial using Ananya's HTML template."""
    import os
    from app.config.niche_authors import NICHE_AUTHORS

    display_name = niche_name.replace("-", " ").title()
    asins = [p["asin"] for p in products[:5] if p.get("asin")]
    bundle_url = amazon_bundle_url(asins)
    author_avatar = NICHE_AUTHORS.get(niche_name, NICHE_AUTHORS.get("model-building", ""))

    # Load template
    template_path = os.path.join(os.path.dirname(__file__), "../templates/advertorial.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Build replacements
    replacements = {
        "{{lang}}": "de",
        "{{niche_name}}": display_name,
        "{{headline}}": story.get("headline", ""),
        "{{subtitle}}": story.get("subtitle", ""),
        "{{hero_image_url}}": hero_image,
        "{{author_name}}": story.get("author_name", "Klaus Weber"),
        "{{author_profession}}": story.get("author_profession", ""),
        "{{author_city}}": story.get("author_city", ""),
        "{{author_avatar_url}}": author_avatar,
        "{{story_p1}}": story.get("story_p1", ""),
        "{{story_p2}}": story.get("story_p2", ""),
        "{{story_p3}}": story.get("story_p3", ""),
        "{{story_p4}}": story.get("story_p4", ""),
        "{{story_p5}}": story.get("story_p4", ""),
        "{{pull_quote_1}}": story.get("pull_quote_1", ""),
        "{{pull_quote_2}}": story.get("pull_quote_2", ""),
        "{{highlight_tip}}": story.get("highlight_tip", ""),
        "{{bundle_cart_url}}": bundle_url,
        "{{bundle_title}}": story.get("bundle_title_de", "Starter Bundle"),
        "{{bundle_desc}}": story.get("bundle_desc_de", ""),
        "{{cta_title}}": story.get("cta_title_de", "Bereit loszulegen?"),
        "{{cta_text}}": story.get("cta_text_de", ""),
    }

    # Add products 1-5
    for i, p in enumerate(products[:5], 1):
        asin = p.get("asin", "")
        replacements[f"{{{{product_{i}_asin}}}}"] = asin or ""
        replacements[f"{{{{product_{i}_name}}}}"] = p.get("product_name", "")
        replacements[f"{{{{product_{i}_price}}}}"] = p.get("price", "Preis prüfen")
        replacements[f"{{{{product_{i}_stars}}}}"] = str(p.get("rating", 4.0) or 4.0)
        replacements[f"{{{{product_{i}_image_url}}}}"] = p.get("image_url", "")

    # Fill empty product slots
    for i in range(len(products[:5]) + 1, 6):
        replacements[f"{{{{product_{i}_asin}}}}"] = ""
        replacements[f"{{{{product_{i}_name}}}}"] = ""
        replacements[f"{{{{product_{i}_price}}}}"] = ""
        replacements[f"{{{{product_{i}_stars}}}}"] = ""
        replacements[f"{{{{product_{i}_image_url}}}}"] = ""

    # Add reviews
    reviews = story.get("reviews", [{}, {}, {}])
    for i, r in enumerate(reviews[:3], 1):
        replacements[f"{{{{review_{i}_name}}}}"] = r.get("name", "").split(",")[0].strip()
        replacements[f"{{{{review_{i}_city}}}}"] = r.get("name", "").split(",")[1].strip() if "," in r.get("name","") else ""
        replacements[f"{{{{review_{i}_initials}}}}"] = r.get("initials", "KW")
        replacements[f"{{{{review_{i}_date}}}}"] = r.get("date_de", "")
        replacements[f"{{{{review_{i}_text}}}}"] = r.get("text_de", "")
        replacements[f"{{{{review_{i}_stars}}}}"] = "★" * r.get("stars", 5)

    # Add pros/cons
    pros = ["Perfekt für Anfänger", "Gutes Preis-Leistungs-Verhältnis", "Sofort einsatzbereit"]
    cons = ["Für absolute Profis ggf. zu einfach", "Zubehör separat erhältlich", "Englische Anleitung"]
    for i, p in enumerate(pros, 1):
        replacements[f"{{{{pro_{i}_de}}}}"] = p
        replacements[f"{{{{pro_{i}_en}}}}"] = p
    for i, c in enumerate(cons, 1):
        replacements[f"{{{{con_{i}_de}}}}"] = c
        replacements[f"{{{{con_{i}_en}}}}"] = c

    # Bundle description
    replacements["{{bundle_description}}"] = story.get("bundle_desc_de", f"Alle empfohlenen Produkte für {display_name} — zusammengestellt von {story.get('author_name', 'unserem Experten')}")
    replacements["{{bundle_description_en}}"] = story.get("bundle_desc_en", f"All recommended products for {display_name}")

    # Add FAQs
    faqs = story.get("faqs", [{}, {}, {}])
    for i, faq in enumerate(faqs[:3], 1):
        replacements[f"{{{{faq_{i}_q}}}}"] = faq.get("q_de", "")
        replacements[f"{{{{faq_{i}_a}}}}"] = faq.get("a_de", "")

    # Apply all replacements
    for key, value in replacements.items():
        template = template.replace(key, str(value) if value else "")

    return template


IMPRESSUM_HTML = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>Impressum — BesteHobby.de</title>
<style>body{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px 24px;color:#333}h1{color:#2d6a4f}h2{color:#1a1a2e;margin:20px 0 8px;font-size:17px}p{margin-bottom:12px;line-height:1.7}a{color:#2d6a4f}.back{display:inline-block;background:#1a1a2e;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-bottom:24px;font-size:14px}</style>
</head><body>
<a href="/" class="back">← Zurück</a>
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 TMG</h2>
<p>BesteHobby.de<br>Musterstraße 1<br>80331 München<br>Deutschland</p>
<h2>Kontakt</h2><p>E-Mail: kontakt@bestehobby.de</p>
<h2>Affiliate-Hinweis</h2>
<p>Diese Website enthält Affiliate-Links zu Amazon.de. Als Amazon-Partner verdienen wir an qualifizierten Käufen. Der Preis bleibt unverändert.</p>
</body></html>"""

DATENSCHUTZ_HTML = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>Datenschutz — BesteHobby.de</title>
<style>body{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px 24px;color:#333}h1{color:#2d6a4f}h2{color:#1a1a2e;margin:20px 0 8px;font-size:17px}p{margin-bottom:12px;line-height:1.7}a{color:#2d6a4f}.back{display:inline-block;background:#1a1a2e;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-bottom:24px;font-size:14px}</style>
</head><body>
<a href="/" class="back">← Zurück</a>
<h1>Datenschutzerklärung</h1>
<h2>1. Datenschutz auf einen Blick</h2>
<p>Wir behandeln Ihre Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften.</p>
<h2>2. Datenerfassung</h2>
<p>Diese Website erfasst keine personenbezogenen Daten ohne Ihre Zustimmung.</p>
<h2>3. Amazon Affiliate Links</h2>
<p>Diese Website enthält Links zu Amazon.de. Als Amazon-Partner nehmen wir am Partnerprogramm teil.</p>
<h2>4. Kontakt</h2><p>kontakt@bestehobby.de</p>
</body></html>"""

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
                Niche.status.in_(["approved", "discovered", "live"])
            ).all()

        niche_data = []
        for niche in niches:
            links = db.query(AffiliateLink).filter(
                AffiliateLink.niche_id == niche.id,
                AffiliateLink.status == "active",
                AffiliateLink.asin != None,
                AffiliateLink.link_url.like("https://%"),
            ).limit(5).all()

            products = [
                {
                    "product_name": lnk.product_name,
                    "asin": lnk.asin,
                    "link_url": lnk.link_url,
                    "price": f"€{lnk.price}" if lnk.price else "Preis prüfen",
                    "rating": lnk.rating,
                    "image_url": lnk.image_url,
                }
                for lnk in links
            ]

            niche_data.append({
                "id": niche.id,
                "name": niche.name,
                "subdomain": niche.subdomain,
                "products": products,
            })
            logger.info(f"  Loaded: {niche.name} | {len(products)} products")

    finally:
        db.close()

    state["pages_generated"] = niche_data
    state["messages"] = state.get("messages", []) + [
        f"Loaded {len(niche_data)} niches for site building"
    ]
    logger.info(f"[SiteBuilderAgent] load_niche_data — done ({len(niche_data)} niches)")
    return state


# ---------------------------------------------------------------------------
# Step 2 — generate story content with GPT-4o
# ---------------------------------------------------------------------------
def generate_content(state: AgentState) -> AgentState:
    logger.info("[SiteBuilderAgent] generate_content — starting with GPT-4o")
    niche_data = state.get("pages_generated", [])
    all_pages = []

    for niche in niche_data:
        name = niche["name"]
        products = niche["products"]
        hero_image = NICHE_IMAGES.get(name, DEFAULT_IMAGE)

        logger.info(f"  Generating story for: {name}")

        # Generate story with GPT-4o
        story = generate_story_with_gpt4o(name, products)

        if not story:
            logger.warning(f"  GPT-4o failed for {name} — skipping")
            continue

        # Render the full advertorial HTML
        html_content = render_advertorial(name, story, products, hero_image)

        # Homepage (main advertorial)
        all_pages.append({
            "niche_id": niche["id"],
            "page_type": "homepage",
            "url": f"https://{niche['subdomain']}/",
            "content": html_content,
            "story_json": json.dumps(story, ensure_ascii=False),
        })

        # Impressum page
        all_pages.append({
            "niche_id": niche["id"],
            "page_type": "impressum",
            "url": f"https://{niche['subdomain']}/impressum",
            "content": IMPRESSUM_HTML,
            "story_json": None,
        })

        # Datenschutz page
        all_pages.append({
            "niche_id": niche["id"],
            "page_type": "datenschutz",
            "url": f"https://{niche['subdomain']}/datenschutz",
            "content": DATENSCHUTZ_HTML,
            "story_json": None,
        })

        logger.info(f"  ✓ Generated 3 pages for {name}")
        all_pages.extend([])

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
                logger.info(f"  ✓ Published: [{page_data['page_type']}] {page_data['url']}")

            # Update niche status to live
            niche = db.query(Niche).filter(Niche.id == page_data["niche_id"]).first()
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
    logger.info(f"[SiteBuilderAgent] publish_pages — done. saved={saved}, updated={updated}")
    return state


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
def handle_error(state: AgentState) -> AgentState:
    logger.error(f"[SiteBuilderAgent] Terminal error: {state.get('error')}")
    state["completed"] = True
    return state


# ---------------------------------------------------------------------------
# Agent class
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
