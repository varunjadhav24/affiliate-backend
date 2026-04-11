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
    display_name = niche_name.replace("-", " ").title()
    asins = [p["asin"] for p in products[:5] if p.get("asin")]
    bundle_url = amazon_bundle_url(asins)

    # Build product grid HTML (DE and EN versions for toggle)
    def product_card(p, lang="de"):
        asin = p.get("asin", "")
        name = p.get(f"name_{lang}", p.get("name_de", p.get("product_name", "Produkt")))
        price = p.get("price", "Preis prüfen")
        stars = float(p.get("stars", 4.0))
        full_stars = int(stars)
        star_html = "★" * full_stars + "☆" * (5 - full_stars)
        img_url = p.get("image_url") or (amazon_img(asin) if asin else "")
        link = p.get("link_url", amazon_link(asin) if asin else "#")
        if not link or link.startswith("?"):
            link = "#"
        desc = p.get(f"description_{lang}", "")
        return f"""<div class="product-mini-card">
          <div class="img-wrap"><img src="{img_url}" alt="{name}" loading="lazy" /></div>
          <div class="mini-stars">{star_html}</div>
          <div class="mini-name">{name}</div>
          <div class="mini-desc">{desc}</div>
          <div class="mini-price">{price}</div>
          <a href="{link}" class="mini-btn" target="_blank" rel="nofollow sponsored">{"Ansehen →" if lang == "de" else "View →"}</a>
        </div>"""

    products_grid_de = "\n".join(product_card(p, "de") for p in products[:4])
    products_grid_en = "\n".join(product_card(p, "en") for p in products[:4])

    # Bundle products
    def bundle_prod(p, lang="de"):
        asin = p.get("asin", "") or ""
        name = p.get(f"name_{lang}", p.get("name_de", p.get("product_name", "")))
        price = p.get("price", "")
        img = p.get("image_url") or (amazon_img(asin) if asin else "")
        return f"""<div class="bundle-product-img-wrap">
          <div class="bpimg">{"<img src=\"" + img + "\" alt=\"" + name + "\" loading=\"lazy\" />" if img else "<div style=\"background:#f0f7f4;width:100%;height:80px;border-radius:4px;\"></div>"}</div>
          <div class="bp-name">{name}</div>
          <div class="bp-price">{price}</div>
        </div>"""

    bundle_prods_de = "\n".join(bundle_prod(p, "de") for p in products[:5])
    bundle_prods_en = "\n".join(bundle_prod(p, "en") for p in products[:5])

    # Reviews
    def review_html(r, lang="de"):
        stars = "★" * r.get("stars", 5) + "☆" * (5 - r.get("stars", 5))
        text = r.get(f"text_{lang}", r.get("text_de", ""))
        date = r.get(f"date_{lang}", r.get("date_de", ""))
        verified = "✓ Verifizierter Kauf" if lang == "de" else "✓ Verified purchase"
        return f"""<div class="comment">
          <div class="comment-header">
            <div class="comment-avatar">{r.get('initials','?')}</div>
            <div>
              <div class="comment-name">{r.get('name','')}</div>
              <div class="comment-date">{date}</div>
              <div class="comment-verified">{verified}</div>
            </div>
          </div>
          <div class="comment-stars">{stars}</div>
          <p class="comment-text">{text}</p>
        </div>"""

    reviews_de = "\n".join(review_html(r, "de") for r in story.get("reviews", []))
    reviews_en = "\n".join(review_html(r, "en") for r in story.get("reviews", []))

    # FAQs
    def faq_html(f, lang="de"):
        q = f.get(f"q_{lang}", "")
        a = f.get(f"a_{lang}", "")
        return f"""<div class="faq-item">
          <div class="faq-q">{q}</div>
          <div class="faq-a">{a}</div>
        </div>"""

    faqs_de = "\n".join(faq_html(f, "de") for f in story.get("faqs", []))
    faqs_en = "\n".join(faq_html(f, "en") for f in story.get("faqs", []))

    author_name = story.get("author_name", "Klaus Weber")
    author_initials = story.get("author_initials", "KW")
    author_meta_de = f"Verifizierter Käufer · {story.get('author_profession','')} aus {story.get('author_city','')} · April 2026"
    author_meta_en = f"Verified Buyer · {story.get('author_profession','')} from {story.get('author_city','')} · April 2026"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{story.get('headline', display_name)} — BesteHobby.de</title>
<meta name="description" content="{story.get('subtitle', '')}">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Georgia,serif;background:#fff;color:#2c2c2c}}
.top-bar{{background:#1a1a2e;color:#fff;padding:10px 24px;font-family:Arial,sans-serif;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
.top-bar a{{color:#fff;text-decoration:none;font-weight:bold;font-size:16px}}
.top-bar-right{{display:flex;align-items:center;gap:12px}}
.sponsored-badge{{background:#e8a000;color:#000;padding:3px 10px;border-radius:3px;font-size:11px;font-weight:bold}}
.lang-toggle{{display:flex;border:1px solid rgba(255,255,255,0.3);border-radius:5px;overflow:hidden}}
.lang-btn{{padding:5px 12px;font-size:12px;font-family:Arial,sans-serif;font-weight:bold;cursor:pointer;border:none;transition:background 0.2s}}
.lang-btn.active{{background:#e8a000;color:#000}}
.lang-btn:not(.active){{background:transparent;color:#fff}}
.hero-image{{width:100vw;height:440px;object-fit:cover;object-position:center 30%;display:block;position:relative;left:50%;right:50%;margin-left:-50vw;margin-right:-50vw}}
.page{{max-width:800px;margin:0 auto;padding:0 24px 80px}}
.hero{{padding:36px 0 28px;border-bottom:1px solid #e0e0e0}}
.category{{font-family:Arial,sans-serif;font-size:12px;color:#e8a000;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}}
.hero h1{{font-size:32px;line-height:1.3;color:#1a1a1a;margin-bottom:18px;font-weight:normal}}
.hero .subtitle{{font-size:19px;color:#555;line-height:1.6;margin-bottom:24px;font-style:italic}}
.author-row{{display:flex;align-items:center;gap:14px}}
.author-avatar-circle{{width:56px;height:56px;border-radius:50%;background:#2d6a4f;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:bold;font-size:18px;font-family:Arial;flex-shrink:0;border:2px solid #e8a000}}
.author-info{{font-family:Arial,sans-serif;font-size:13px}}
.author-info strong{{color:#1a1a1a;display:block;font-size:15px}}
.author-info span{{color:#888}}
.article-body{{padding:32px 0;font-size:18px;line-height:1.9;color:#2c2c2c}}
.article-body p{{margin-bottom:24px}}
.drop-cap::first-letter{{font-size:68px;line-height:0.8;float:left;margin:6px 10px 0 0;color:#2d6a4f;font-weight:bold}}
.pull-quote{{border-left:4px solid #e8a000;padding:18px 28px;margin:36px 0;background:#fffdf0;border-radius:0 8px 8px 0}}
.pull-quote p{{font-size:22px;font-style:italic;color:#444;margin:0;line-height:1.55}}
.inline-image{{width:100%;border-radius:8px;margin:28px 0 8px;object-fit:cover;max-height:380px}}
.inline-image-caption{{font-family:Arial,sans-serif;font-size:13px;color:#999;text-align:center;margin-bottom:28px;font-style:italic}}
.section-heading{{font-family:Arial,sans-serif;font-size:24px;font-weight:bold;color:#1a1a1a;margin:40px 0 20px;padding-bottom:12px;border-bottom:3px solid #2d6a4f}}
.highlight-box{{background:#f0f7f4;border-left:4px solid #2d6a4f;padding:20px 24px;margin:28px 0;border-radius:0 8px 8px 0;font-family:Arial,sans-serif;font-size:16px;color:#2c2c2c;line-height:1.7}}
.product-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:28px 0}}
.product-mini-card{{border:1px solid #dde8e2;border-radius:10px;padding:16px;background:#f7fbf9;font-family:Arial,sans-serif;text-align:center}}
.img-wrap{{width:100%;height:150px;display:flex;align-items:center;justify-content:center;background:#fff;border-radius:6px;margin-bottom:10px;border:1px solid #eee;overflow:hidden}}
.img-wrap img{{max-width:100%;max-height:140px;object-fit:contain}}
.mini-stars{{color:#e8a000;font-size:14px;margin-bottom:4px}}
.mini-name{{font-size:13px;color:#1a1a1a;font-weight:bold;margin-bottom:4px;line-height:1.4}}
.mini-desc{{font-size:12px;color:#777;margin-bottom:6px;line-height:1.4}}
.mini-price{{font-size:16px;font-weight:bold;color:#cc3300;margin-bottom:10px}}
.mini-btn{{display:inline-block;background:#e8a000;color:#000;padding:6px 16px;border-radius:4px;font-size:13px;font-weight:bold;text-decoration:none}}
.bundle-box{{background:#1a1a2e;border-radius:14px;padding:36px;margin:36px 0;font-family:Arial,sans-serif;color:#fff}}
.bundle-badge{{background:#e8a000;color:#000;font-size:12px;font-weight:bold;padding:4px 14px;border-radius:20px;display:inline-block;margin-bottom:16px;text-transform:uppercase;letter-spacing:1px}}
.bundle-box h3{{font-size:24px;margin-bottom:8px;font-family:Georgia,serif;color:#fff}}
.bundle-subtitle{{font-size:15px;color:rgba(255,255,255,0.7);margin-bottom:28px;line-height:1.6}}
.bundle-products{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:28px}}
.bundle-product-img-wrap{{text-align:center}}
.bpimg{{width:100%;aspect-ratio:1;background:#fff;border-radius:8px;padding:6px;margin-bottom:6px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.bpimg img{{max-width:100%;max-height:80px;object-fit:contain}}
.bp-name{{font-size:11px;color:rgba(255,255,255,0.8);line-height:1.3}}
.bp-price{{font-size:13px;font-weight:bold;color:#e8a000;margin-top:3px}}
.bundle-divider{{border:none;border-top:1px solid rgba(255,255,255,0.15);margin:20px 0}}
.bundle-total-row{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:15px;color:rgba(255,255,255,0.7)}}
.bundle-total-row.main{{font-size:20px;color:#fff;font-weight:bold;margin-bottom:6px}}
.total-val{{color:#e8a000;font-size:24px;font-weight:bold}}
.bundle-savings-pill{{background:#2d6a4f;color:#fff;font-size:13px;padding:6px 16px;border-radius:20px;display:inline-block;margin-bottom:24px}}
.bundle-cta{{display:block;text-align:center;background:#e8a000;color:#000;padding:18px;border-radius:8px;font-weight:bold;font-size:18px;text-decoration:none;margin-top:16px}}
.bundle-cta-note{{font-size:12px;color:rgba(255,255,255,0.5);text-align:center;margin-top:10px}}
.trust-bar{{display:flex;flex-wrap:wrap;gap:16px;padding:20px;margin:32px 0;font-family:Arial,sans-serif;background:#fafafa;border-radius:8px;border:1px solid #e0e0e0}}
.trust-item{{font-size:13px;color:#555;display:flex;align-items:center;gap:8px}}
.trust-dot{{width:10px;height:10px;border-radius:50%;background:#2d6a4f;flex-shrink:0}}
.pros-cons{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:28px 0;font-family:Arial,sans-serif}}
.pros{{background:#f0f7f4;border-radius:8px;padding:20px}}
.cons{{background:#fff7f0;border-radius:8px;padding:20px}}
.pros h4{{color:#2d6a4f;margin-bottom:12px;font-size:15px}}
.cons h4{{color:#cc6600;margin-bottom:12px;font-size:15px}}
.pros ul,.cons ul{{list-style:none}}
.pros ul li,.cons ul li{{font-size:14px;color:#444;padding:4px 0 4px 20px;position:relative}}
.pros ul li::before{{content:"+";position:absolute;left:0;color:#2d6a4f;font-weight:bold}}
.cons ul li::before{{content:"−";position:absolute;left:0;color:#cc6600;font-weight:bold}}
.faq-item{{border-bottom:1px solid #e0e0e0;padding:20px 0;font-family:Arial,sans-serif}}
.faq-q{{font-size:16px;font-weight:bold;color:#1a1a1a;margin-bottom:10px}}
.faq-a{{font-size:15px;color:#555;line-height:1.7}}
.comment{{padding:20px;border:1px solid #e0e0e0;border-radius:8px;margin-bottom:16px;background:#fafafa;font-family:Arial,sans-serif}}
.comment-header{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
.comment-avatar{{width:44px;height:44px;border-radius:50%;background:#2d6a4f;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:14px;flex-shrink:0}}
.comment-name{{font-weight:bold;font-size:15px;color:#1a1a1a}}
.comment-date{{font-size:12px;color:#999}}
.comment-verified{{font-size:11px;color:#2d6a4f;font-weight:bold;margin-top:2px}}
.comment-stars{{color:#e8a000;font-size:14px;margin-bottom:8px}}
.comment-text{{font-size:15px;color:#444;line-height:1.7}}
.final-cta{{background:#f0f7f4;border:2px solid #2d6a4f;padding:36px;border-radius:12px;text-align:center;margin:40px 0;font-family:Arial,sans-serif}}
.final-cta h3{{font-size:24px;margin-bottom:12px;font-family:Georgia,serif;color:#1a1a1a}}
.final-cta p{{font-size:15px;color:#555;margin-bottom:24px;line-height:1.7}}
.final-cta a{{display:inline-block;background:#e8a000;color:#000;padding:16px 40px;border-radius:8px;font-weight:bold;font-size:17px;text-decoration:none}}
.footer-legal{{font-family:Arial,sans-serif;font-size:12px;color:#aaa;padding:24px 0;border-top:1px solid #e0e0e0;line-height:2}}
.footer-legal a{{color:#777;text-decoration:none;cursor:pointer}}
[data-lang]{{display:none}}
[data-lang].active{{display:block}}
[data-lang-inline]{{display:none}}
[data-lang-inline].active{{display:inline}}
@media(max-width:600px){{
  .hero h1{{font-size:24px}}
  .article-body{{font-size:16px}}
  .hero-image{{height:260px}}
  .bundle-products{{grid-template-columns:repeat(3,1fr)}}
  .pros-cons{{grid-template-columns:1fr}}
  .product-grid{{grid-template-columns:1fr 1fr}}
}}
</style>
</head>
<body>

<div class="top-bar">
  <a href="/">BesteHobby.de</a>
  <div class="top-bar-right">
    <span class="sponsored-badge" id="badge-text">Anzeige</span>
    <div class="lang-toggle">
      <button class="lang-btn active" id="btn-de" onclick="setLang('de')">🇩🇪 DE</button>
      <button class="lang-btn" id="btn-en" onclick="setLang('en')">🇬🇧 EN</button>
    </div>
  </div>
</div>

<img class="hero-image" src="{hero_image}" alt="{display_name}" />

<div class="page">
  <div class="hero">
    <div class="category">
      <span data-lang="de" class="active">{display_name} · Persönlicher Erfahrungsbericht</span>
      <span data-lang="en">{display_name} · Personal Story</span>
    </div>
    <h1>
      <span data-lang="de" class="active">{story.get('headline', '')}</span>
      <span data-lang="en">{story.get('headline_en', '')}</span>
    </h1>
    <p class="subtitle">
      <span data-lang="de" class="active">{story.get('subtitle', '')}</span>
      <span data-lang="en">{story.get('subtitle_en', '')}</span>
    </p>
    <div class="author-row">
      <div class="author-avatar-circle">{author_initials}</div>
      <div class="author-info">
        <strong>{author_name}</strong>
        <span data-lang="de" class="active">{author_meta_de}</span>
        <span data-lang="en">{author_meta_en}</span>
      </div>
    </div>
  </div>

  <div class="article-body">
    <p class="drop-cap">
      <span data-lang="de" class="active">{story.get('story_p1','')}</span>
      <span data-lang="en">{story.get('story_p1_en','')}</span>
    </p>
    <p>
      <span data-lang="de" class="active">{story.get('story_p2','')}</span>
      <span data-lang="en">{story.get('story_p2_en','')}</span>
    </p>

    <div class="pull-quote"><p>
      <span data-lang="de" class="active">{story.get('pull_quote_1','')}</span>
      <span data-lang="en">{story.get('pull_quote_1_en','')}</span>
    </p></div>

    <p>
      <span data-lang="de" class="active">{story.get('story_p3','')}</span>
      <span data-lang="en">{story.get('story_p3_en','')}</span>
    </p>

    <img class="inline-image" src="{hero_image}" alt="{display_name}" />
    <p class="inline-image-caption">
      <span data-lang="de" class="active">{author_name} — {story.get('author_city','')}</span>
      <span data-lang="en">{author_name} — {story.get('author_city','')}</span>
    </p>

    <p>
      <span data-lang="de" class="active">{story.get('story_p4','')}</span>
      <span data-lang="en">{story.get('story_p4_en','')}</span>
    </p>

    <div class="pull-quote"><p>
      <span data-lang="de" class="active">{story.get('pull_quote_2','')}</span>
      <span data-lang="en">{story.get('pull_quote_2_en','')}</span>
    </p></div>

    <div class="highlight-box">
      <span data-lang="de" class="active">{story.get('highlight_tip','')}</span>
      <span data-lang="en">{story.get('highlight_tip_en','')}</span>
    </div>

    <h2 class="section-heading">
      <span data-lang="de" class="active">Die Produkte die ich empfehle</span>
      <span data-lang="en">The products I recommend</span>
    </h2>

    <div class="product-grid" data-lang="de" class="active" id="grid-de">
      {products_grid_de}
    </div>
    <div class="product-grid" data-lang="en" id="grid-en">
      {products_grid_en}
    </div>

    <p>
      <span data-lang="de" class="active">Alle fünf Produkte funktionieren perfekt zusammen. Am besten bestellt ihr sie als Bundle:</span>
      <span data-lang="en">All five products work perfectly together. Best to order them as a bundle:</span>
    </p>

    <div class="bundle-box">
      <span class="bundle-badge">
        <span data-lang="de" class="active">⭐ Empfohlenes Starter-Bundle</span>
        <span data-lang="en">⭐ Recommended Starter Bundle</span>
      </span>
      <h3>
        <span data-lang="de" class="active">{story.get('bundle_title_de','Das komplette Starter-Bundle')}</span>
        <span data-lang="en">{story.get('bundle_title_en','The Complete Starter Bundle')}</span>
      </h3>
      <p class="bundle-subtitle">
        <span data-lang="de" class="active">{story.get('bundle_desc_de','')}</span>
        <span data-lang="en">{story.get('bundle_desc_en','')}</span>
      </p>

      <div class="bundle-products" data-lang="de" id="bprods-de">{bundle_prods_de}</div>
      <div class="bundle-products" data-lang="en" id="bprods-en">{bundle_prods_en}</div>

      <hr class="bundle-divider" />
      <div class="bundle-savings-pill">
        <span data-lang="de" class="active">🎯 Alles zusammen — sofort in den Warenkorb</span>
        <span data-lang="en">🎯 All together — add to cart in one click</span>
      </div>

      <a href="{bundle_url}" class="bundle-cta" target="_blank" rel="nofollow sponsored">
        <span data-lang="de" class="active">🛒 Jetzt alle Produkte auf Amazon in den Warenkorb</span>
        <span data-lang="en">🛒 Add all products to Amazon cart now</span>
      </a>
      <p class="bundle-cta-note">
        <span data-lang="de" class="active">* Öffnet Amazon.de mit allen Produkten bereits im Warenkorb</span>
        <span data-lang="en">* Opens Amazon.de with all products already in your cart</span>
      </p>
    </div>

    <div class="trust-bar">
      <div class="trust-item"><div class="trust-dot"></div>
        <span data-lang="de" class="active">Verifizierte Amazon-Käufe</span>
        <span data-lang="en">Verified Amazon purchases</span>
      </div>
      <div class="trust-item"><div class="trust-dot"></div>
        <span data-lang="de" class="active">Alle Produkte sofort lieferbar</span>
        <span data-lang="en">All products available immediately</span>
      </div>
      <div class="trust-item"><div class="trust-dot"></div>
        <span data-lang="de" class="active">Persönlich getestet</span>
        <span data-lang="en">Personally tested</span>
      </div>
      <div class="trust-item"><div class="trust-dot"></div>
        <span data-lang="de" class="active">Zuletzt aktualisiert April 2026</span>
        <span data-lang="en">Last updated April 2026</span>
      </div>
    </div>

    <h2 class="section-heading">
      <span data-lang="de" class="active">Häufige Fragen</span>
      <span data-lang="en">Frequently Asked Questions</span>
    </h2>
    <div id="faqs-de" data-lang="de">{faqs_de}</div>
    <div id="faqs-en" data-lang="en">{faqs_en}</div>

    <h2 class="section-heading">
      <span data-lang="de" class="active">Was andere sagen</span>
      <span data-lang="en">What others say</span>
    </h2>
    <div id="reviews-de" data-lang="de">{reviews_de}</div>
    <div id="reviews-en" data-lang="en">{reviews_en}</div>

    <div class="final-cta">
      <h3>
        <span data-lang="de" class="active">{story.get('cta_title_de','Bereit loszulegen?')}</span>
        <span data-lang="en">{story.get('cta_title_en','Ready to get started?')}</span>
      </h3>
      <p>
        <span data-lang="de" class="active">{story.get('cta_text_de','')}</span>
        <span data-lang="en">{story.get('cta_text_en','')}</span>
      </p>
      <a href="{bundle_url}" target="_blank" rel="nofollow sponsored">
        <span data-lang="de" class="active">🛒 Jetzt Bundle auf Amazon kaufen →</span>
        <span data-lang="en">🛒 Buy bundle on Amazon now →</span>
      </a>
    </div>
  </div>

  <div class="footer-legal">
    <span data-lang="de" class="active">
      * Affiliate-Links: Bei einem Kauf über unsere Links erhalten wir eine kleine Provision. Der Preis bleibt unverändert.
      <a href="/impressum">Impressum</a> · <a href="/datenschutz">Datenschutzerklärung</a> · © 2026 BesteHobby.de
    </span>
    <span data-lang="en">
      * Affiliate links: We earn a small commission when you buy through our links. The price remains unchanged.
      <a href="/impressum">Imprint</a> · <a href="/datenschutz">Privacy Policy</a> · © 2026 BesteHobby.de
    </span>
  </div>
</div>

<script>
function setLang(lang) {{
  document.querySelectorAll('[data-lang]').forEach(el => {{
    el.classList.toggle('active', el.getAttribute('data-lang') === lang);
  }});
  document.getElementById('btn-de').classList.toggle('active', lang === 'de');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');
  document.getElementById('badge-text').textContent = lang === 'de' ? 'Anzeige' : 'Advertisement';
  document.documentElement.lang = lang;
}}
setLang('de');
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Impressum page
# ---------------------------------------------------------------------------
IMPRESSUM_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Impressum — BesteHobby.de</title>
<style>body{{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px 24px;color:#333}}h1{{color:#2d6a4f;margin-bottom:24px}}h2{{color:#1a1a2e;margin:28px 0 12px;font-size:18px}}p{{margin-bottom:14px;line-height:1.7}}a{{color:#2d6a4f}}.back{{display:inline-block;background:#1a1a2e;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-bottom:28px;font-size:14px}}</style>
</head>
<body>
<a href="/" class="back">← Zurück</a>
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 TMG</h2>
<p>BesteHobby.de<br>Musterstraße 1<br>80331 München<br>Deutschland</p>
<h2>Kontakt</h2>
<p>E-Mail: kontakt@bestehobby.de</p>
<h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
<p>BesteHobby.de Redaktion<br>Musterstraße 1<br>80331 München</p>
<h2>Affiliate-Hinweis</h2>
<p>Diese Website enthält Affiliate-Links zu Amazon.de. Als Amazon-Partner verdienen wir an qualifizierten Käufen. Der Preis für den Käufer bleibt dabei unverändert.</p>
<h2>Haftungsausschluss</h2>
<p>Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen.</p>
</body></html>"""

DATENSCHUTZ_HTML = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Datenschutzerklärung — BesteHobby.de</title>
<style>body{{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:40px 24px;color:#333}}h1{{color:#2d6a4f;margin-bottom:24px}}h2{{color:#1a1a2e;margin:28px 0 12px;font-size:18px}}p{{margin-bottom:14px;line-height:1.7}}a{{color:#2d6a4f}}.back{{display:inline-block;background:#1a1a2e;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;margin-bottom:28px;font-size:14px}}</style>
</head>
<body>
<a href="/" class="back">← Zurück</a>
<h1>Datenschutzerklärung</h1>
<h2>1. Datenschutz auf einen Blick</h2>
<p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie unsere Website besuchen.</p>
<h2>2. Allgemeine Hinweise</h2>
<p>Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.</p>
<h2>3. Datenerfassung</h2>
<p>Diese Website erfasst keine personenbezogenen Daten ohne Ihre ausdrückliche Zustimmung. Beim Besuch der Website werden keine Tracking-Cookies gesetzt.</p>
<h2>4. Amazon Affiliate Links</h2>
<p>Diese Website enthält Links zu Amazon.de. Wenn Sie auf diese Links klicken, verlassen Sie unsere Website. Amazon hat eigene Datenschutzrichtlinien. Als Amazon-Partner nehmen wir am Partnerprogramm teil und verdienen an qualifizierten Käufen.</p>
<h2>5. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Verarbeitung Ihrer personenbezogenen Daten. Kontakt: kontakt@bestehobby.de</p>
</body></html>"""


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
