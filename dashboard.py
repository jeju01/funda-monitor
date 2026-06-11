"""
Genereert docs/index.html — volledig dashboard met real-time filters,
dual-range prijsschuifbalk, straalfilter, bron- en landsfilter.
"""

import json
from datetime import date
from pathlib import Path
from typing import Optional

from config import BASE_DIR, CENTER_ADDRESS, DEFAULT_RADIUS_KM, MIN_PRICE

DOCS_DIR = BASE_DIR / "docs"
OUTPUT_FILE = DOCS_DIR / "index.html"


def _fmt_price(amount: Optional[int]) -> str:
    if amount is None:
        return "Prijs onbekend"
    return "€ " + f"{amount:,.0f}".replace(",", ".")


def _card(l: dict) -> str:
    thumb = l.get("thumbnail_url") or ""
    img = (f'<img src="{thumb}" alt="foto" loading="lazy" />'
           if thumb else '<div class="no-photo">Geen foto</div>')

    specs = " · ".join(filter(None, [
        f"{l['surface_m2']} m²" if l.get("surface_m2") else "",
        f"{l['rooms']} kamers" if l.get("rooms") else "",
    ]))

    type_cls = "badge-commercial" if l.get("listing_type") == "Bedrijfsvastgoed" else "badge-woning"
    source = l.get("source", "Onbekend")
    country = l.get("country", "NL")
    source_cls = f"source-{source.lower().replace(' ', '-')}"
    price_raw = l.get("price") or 0
    lat = l.get("lat") or "null"
    lon = l.get("lon") or "null"

    return f"""<article class="card"
  data-price="{price_raw}"
  data-source="{source}"
  data-country="{country}"
  data-lat="{lat}"
  data-lon="{lon}"
  data-id="{l.get('id','')}">
  <a href="{l.get('funda_url','#')}" target="_blank" class="card-img">{img}</a>
  <div class="card-body">
    <div class="card-tags">
      <span class="source-badge {source_cls}">{source}</span>
      <span class="country-badge">{country}</span>
    </div>
    <p class="card-address">{l.get('address','')}</p>
    <p class="card-city">{l.get('city','')}</p>
    <p class="card-price">{l.get('price_formatted') or _fmt_price(l.get('price'))}</p>
    <div class="card-meta">
      <span class="specs">{specs}</span>
      <span class="badge {type_cls}">{l.get('listing_type','Woning')}</span>
    </div>
    <p class="card-distance"></p>
    <a href="{l.get('funda_url','#')}" target="_blank" class="btn-funda">Bekijk op {source} →</a>
  </div>
</article>"""


def _source_options(listings: list[dict]) -> str:
    sources = sorted({l.get("source", "Onbekend") for l in listings})
    opts = '<option value="">Alle bronnen</option>'
    for s in sources:
        opts += f'<option value="{s}">{s}</option>'
    return opts


def _country_options(listings: list[dict]) -> str:
    countries = sorted({l.get("country", "NL") for l in listings})
    labels = {"NL": "Nederland", "BE": "België"}
    opts = '<option value="">Alle landen</option>'
    for c in countries:
        opts += f'<option value="{c}">{labels.get(c, c)}</option>'
    return opts


def build_dashboard(listings: list[dict]) -> str:
    today = date.today().strftime("%d-%m-%Y")
    count = len(listings)
    cards_html = "\n".join(_card(l) for l in listings) if listings else (
        '<p class="empty">Geen objecten in de huidige snapshot.</p>')

    prices = [l.get("price") or 0 for l in listings]
    slider_min = 0  # altijd vanaf €0, gebruiker filtert zelf via schuifbalk
    slider_max = max(prices, default=20_000_000)
    slider_max = ((slider_max // 500_000) + 1) * 500_000

    listings_json = json.dumps([
        {"id": l.get("id"), "lat": l.get("lat"), "lon": l.get("lon"),
         "price": l.get("price", 0), "price_fmt": l.get("price_formatted", ""),
         "address": l.get("address", ""), "city": l.get("city", ""),
         "source": l.get("source", ""), "country": l.get("country", "NL"),
         "url": l.get("funda_url", "")}
        for l in listings
        if l.get("lat") and l.get("lon")
    ])

    def js_price(v):
        return "€ " + f"{v:,.0f}".replace(",", ".")

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Vastgoedmonitor | Lammers Beton</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css"/>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif;background:#f5f1ec;color:#2c2c2c;min-height:100vh}}

    /* ── Hero header ── */
    .hero{{
      padding:48px 24px 40px;text-align:center;
      position:relative;overflow:hidden;background:#08080e
    }}
    .hero-bg{{
      position:absolute;inset:-40px 0;
      background:url("Kantoor afbeelding.png") center 30% / 100% auto no-repeat;
      will-change:transform;z-index:0
    }}
    .hero-overlay{{
      position:absolute;inset:0;z-index:1;
      background:linear-gradient(to bottom,rgba(8,8,14,.58) 0%,rgba(6,6,12,.80) 100%)
    }}
    .hero > *:not(.hero-bg):not(.hero-overlay){{position:relative;z-index:2}}
    .hero-eyebrow{{
      display:inline-flex;align-items:center;gap:7px;
      background:rgba(181,164,138,.18);border:1px solid rgba(181,164,138,.3);
      border-radius:20px;padding:4px 14px;margin-bottom:18px;
      font-size:11px;font-weight:600;letter-spacing:1.2px;
      text-transform:uppercase;color:#c9b99e
    }}
    .hero-eyebrow svg{{opacity:.8}}
    .hero h1{{
      color:#fff;font-size:clamp(26px,5vw,42px);font-weight:700;
      letter-spacing:-0.5px;line-height:1.15;margin-bottom:10px
    }}
    .hero h1 span{{color:#b5a48a}}
    .hero-sub{{color:#a09080;font-size:14px;letter-spacing:.3px}}
    .hero-stats{{
      display:inline-flex;gap:0;margin-top:28px;
      background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
      border-radius:12px;overflow:hidden
    }}
    .hero-stat{{padding:12px 24px;text-align:center;border-right:1px solid rgba(255,255,255,.08)}}
    .hero-stat:last-child{{border-right:none}}
    .hero-stat strong{{display:block;font-size:20px;font-weight:700;color:#fff;line-height:1}}
    .hero-stat span{{font-size:11px;color:#8a7d6e;text-transform:uppercase;letter-spacing:.8px;margin-top:3px;display:block}}

    /* ── Filter card ── */
    .filter-card{{
      max-width:1100px;margin:-20px auto 0;padding:0 20px;position:relative;z-index:10
    }}
    .filter-inner{{
      background:#fff;border-radius:16px;
      box-shadow:0 8px 40px rgba(0,0,0,.12),0 2px 8px rgba(0,0,0,.06);
      padding:20px 24px 16px
    }}
    .filter-row{{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}}
    .filter-row+.filter-row{{margin-top:12px;padding-top:12px;border-top:1px solid #f0ece6}}
    .filter-group{{display:flex;flex-direction:column;gap:5px;flex:1 1 150px}}
    .filter-group label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#b5a48a}}
    .filter-group select,
    .filter-group input[type=text],
    .filter-group input[type=number]{{
      padding:9px 12px;border:1.5px solid #ede8e2;border-radius:9px;
      font-size:13px;background:#faf8f5;outline:none;transition:all .2s;width:100%;color:#2c2c2c
    }}
    .filter-group select:focus,
    .filter-group input:focus{{border-color:#b5a48a;background:#fff;box-shadow:0 0 0 3px rgba(181,164,138,.12)}}

    /* ── Dual range slider ── */
    .slider-block{{background:#faf8f5;border:1.5px solid #ede8e2;border-radius:10px;padding:12px 14px 10px;flex:0 1 360px;min-width:240px}}
    .slider-block > label{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#b5a48a;display:block;margin-bottom:8px}}
    .price-inputs-row{{display:flex;gap:8px;margin-bottom:8px;align-items:center}}
    .price-inputs-row input[type=number]{{
      flex:1;padding:7px 10px;border:1.5px solid #ede8e2;border-radius:7px;
      font-size:13px;font-weight:600;background:#fff;outline:none;
      transition:all .2s;-moz-appearance:textfield;min-width:0;color:#2c2c2c
    }}
    .price-inputs-row input[type=number]::-webkit-outer-spin-button,
    .price-inputs-row input[type=number]::-webkit-inner-spin-button{{-webkit-appearance:none}}
    .price-inputs-row input[type=number]:focus{{border-color:#b5a48a;box-shadow:0 0 0 3px rgba(181,164,138,.12)}}
    .price-inputs-row span{{font-size:12px;color:#ccc;flex-shrink:0}}
    .range-wrap{{position:relative;height:22px;margin-top:2px}}
    .range-wrap input[type=range]{{
      position:absolute;width:100%;height:4px;top:50%;transform:translateY(-50%);
      -webkit-appearance:none;appearance:none;background:transparent;pointer-events:none;outline:none
    }}
    .range-wrap input[type=range]::-webkit-slider-thumb{{
      -webkit-appearance:none;appearance:none;width:18px;height:18px;border-radius:50%;
      background:#b5a48a;border:2px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.2);
      pointer-events:all;cursor:pointer;transition:transform .15s
    }}
    .range-wrap input[type=range]::-webkit-slider-thumb:hover{{transform:scale(1.15)}}
    .range-wrap input[type=range]::-moz-range-thumb{{
      width:18px;height:18px;border-radius:50%;background:#b5a48a;
      border:2px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.2);pointer-events:all;cursor:pointer
    }}
    .range-track{{position:absolute;top:50%;transform:translateY(-50%);width:100%;height:4px;border-radius:2px;background:#e8e0d5;pointer-events:none}}
    .range-fill{{position:absolute;top:0;height:100%;border-radius:2px;background:linear-gradient(90deg,#c9b89e,#b5a48a)}}

    /* ── Radius ── */
    .radius-toggle{{display:flex;align-items:center;gap:7px;font-size:13px;cursor:pointer;user-select:none;font-weight:500;color:#5a5040}}
    .radius-toggle input{{accent-color:#b5a48a;width:15px;height:15px;cursor:pointer}}
    .radius-section{{background:#faf8f5;border:1.5px solid #ede8e2;border-radius:10px;padding:14px 16px;display:none;flex-direction:column;gap:12px;margin-top:4px}}
    .radius-section.open{{display:flex}}
    .radius-hint{{font-size:11px;color:#b5a48a;margin-top:2px}}

    .btn-apply{{
      padding:10px 22px;background:linear-gradient(135deg,#c9b89e,#b5a48a);
      color:#fff;border:none;border-radius:9px;font-size:13px;font-weight:600;
      cursor:pointer;transition:all .2s;white-space:nowrap;
      box-shadow:0 2px 8px rgba(181,164,138,.4)
    }}
    .btn-apply:hover{{transform:translateY(-1px);box-shadow:0 4px 14px rgba(181,164,138,.5)}}
    .btn-clear{{
      padding:10px 16px;background:transparent;color:#aaa;
      border:1.5px solid #e8e0d5;border-radius:9px;font-size:13px;cursor:pointer;transition:all .2s
    }}
    .btn-clear:hover{{background:#f5f1ec;color:#666;border-color:#ccc}}
    .btn-clear-gebied{{
      padding:10px 16px;background:transparent;color:#aaa;
      border:1.5px solid #e8e0d5;border-radius:9px;font-size:13px;cursor:pointer;transition:all .2s
    }}
    .btn-clear-gebied:hover{{background:#f5f1ec;color:#666;border-color:#ccc}}

    /* ── Tab knoppen ── */
    .hero-tabs{{display:flex;gap:10px;margin-top:28px;justify-content:center}}
    .tab-btn{{
      padding:11px 32px;border-radius:50px;font-size:14px;font-weight:600;
      cursor:pointer;transition:all .2s;border:2px solid rgba(181,164,138,.4);
      background:rgba(255,255,255,.07);color:#c9b99e;letter-spacing:.3px
    }}
    .tab-btn:hover{{background:rgba(255,255,255,.12);border-color:rgba(181,164,138,.7)}}
    .tab-btn.active{{
      background:#b5a48a;border-color:#b5a48a;color:#fff;
      box-shadow:0 4px 16px rgba(181,164,138,.45)
    }}

    /* ── Stats bar ── */
    .stats-bar{{max-width:1100px;margin:28px auto 0;padding:0 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}}
    .stats-bar p{{font-size:13px;color:#8a7d6e}}
    .stats-bar strong{{color:#2c2c2c;font-weight:600}}

    /* ── Grid ── */
    .grid{{max-width:1100px;margin:14px auto 56px;padding:0 20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px}}

    /* ── Card ── */
    .card{{
      background:#fff;border-radius:14px;overflow:hidden;
      box-shadow:0 2px 12px rgba(0,0,0,.06);
      display:flex;flex-direction:column;transition:transform .2s,box-shadow .25s
    }}
    .card:hover{{transform:translateY(-4px);box-shadow:0 12px 32px rgba(0,0,0,.11)}}
    .card.hidden{{display:none}}
    .card-img{{display:block;overflow:hidden;height:200px;background:#e8e0d5}}
    .card-img img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .4s}}
    .card:hover .card-img img{{transform:scale(1.06)}}
    .no-photo{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#b5a48a;font-size:13px;letter-spacing:.3px}}
    .card-body{{padding:14px;display:flex;flex-direction:column;gap:5px;flex:1}}
    .card-tags{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:3px}}
    .source-badge{{font-size:10px;padding:2px 8px;border-radius:3px;font-weight:700;text-transform:uppercase;letter-spacing:.4px}}
    .source-funda{{background:#ff6b00;color:#fff}}
    .source-immoweb{{background:#003da5;color:#fff}}
    .source-onbekend{{background:#888;color:#fff}}
    .country-badge{{font-size:10px;padding:2px 7px;border-radius:3px;background:#e0d8cc;color:#5a5040;font-weight:600}}
    .card-address{{font-size:14px;font-weight:700;line-height:1.3;color:#1a1a1a}}
    .card-city{{font-size:12px;color:#7a6e62}}
    .card-price{{font-size:17px;font-weight:800;color:#1a1a1a;margin:3px 0}}
    .card-meta{{display:flex;align-items:center;justify-content:space-between;gap:8px}}
    .specs{{font-size:11px;color:#7a6e62}}
    .badge{{font-size:11px;padding:2px 8px;border-radius:4px;font-weight:600}}
    .badge-woning{{background:#d4e8d4;color:#2d5a2d}}
    .badge-commercial{{background:#d4dce8;color:#2d3d5a}}
    .card-distance{{font-size:11px;color:#b5a48a;font-weight:600;min-height:14px}}
    .btn-funda{{display:block;margin-top:10px;padding:9px 16px;background:#b5a48a;color:#fff;text-decoration:none;font-size:13px;font-weight:600;border-radius:6px;transition:background .2s;text-align:center}}
    .btn-funda:hover{{background:#9d8e77}}
    .empty,.no-results{{grid-column:1/-1;text-align:center;padding:60px 20px;color:#9a8e82;font-size:15px}}

    /* ── Kaart ── */
    #map{{height:520px;width:100%;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
    .map-toolbar{{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}}
    .map-toolbar p{{font-size:13px;color:#8a7d6e;flex:1}}
    .btn-draw{{
      display:inline-flex;align-items:center;gap:7px;
      padding:10px 20px;background:linear-gradient(135deg,#c9b89e,#b5a48a);
      color:#fff;border:none;border-radius:9px;font-size:13px;font-weight:600;
      cursor:pointer;transition:all .2s;box-shadow:0 2px 8px rgba(181,164,138,.4)
    }}
    .btn-draw:hover{{transform:translateY(-1px);box-shadow:0 4px 14px rgba(181,164,138,.5)}}
    .btn-draw svg{{flex-shrink:0}}
    .btn-draw-clear{{
      padding:10px 16px;background:transparent;color:#aaa;
      border:1.5px solid #e8e0d5;border-radius:9px;font-size:13px;
      cursor:pointer;transition:all .2s;display:none
    }}
    .btn-draw-clear.visible{{display:inline-block}}
    .btn-draw-clear:hover{{background:#f5f1ec;color:#666}}
    .map-result-pill{{
      display:none;align-items:center;gap:6px;
      background:#1a1a1a;color:#fff;border-radius:50px;
      padding:8px 18px;font-size:13px;font-weight:600
    }}
    .map-result-pill.visible{{display:inline-flex}}
    .map-result-pill span{{color:#b5a48a}}
    .leaflet-draw-toolbar a{{background-color:#b5a48a!important}}
    .leaflet-popup-content-wrapper{{border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.15)}}
    .map-popup{{font-family:-apple-system,sans-serif;min-width:180px}}
    .map-popup strong{{display:block;font-size:13px;color:#1a1a1a;margin-bottom:2px}}
    .map-popup .mp-city{{font-size:11px;color:#9a8e82;margin-bottom:6px}}
    .map-popup .mp-price{{font-size:15px;font-weight:800;color:#1a1a1a;margin-bottom:8px}}
    .map-popup a{{
      display:block;text-align:center;padding:7px 12px;
      background:#b5a48a;color:#fff;text-decoration:none;
      border-radius:6px;font-size:12px;font-weight:600
    }}
    footer{{
      background:linear-gradient(135deg,#1a1a1a,#2e2620);
      color:#5a5040;text-align:center;padding:24px;font-size:11px;
      letter-spacing:.5px
    }}
  </style>
</head>
<body>

<!-- Hero -->
<div class="hero">
  <div class="hero-bg" id="hero-bg"></div>
  <div class="hero-overlay"></div>
  <div class="hero-eyebrow">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
    Vastgoedmonitor
  </div>
  <h1>Lammers <span>Beton</span></h1>
  <p class="hero-sub">Nederland &amp; België · Funda · Immoweb · Bijgewerkt {today}</p>
  <div class="hero-tabs">
    <button class="tab-btn active" id="tab-algemeen" onclick="switchTab('algemeen')">Algemeen</button>
    <button class="tab-btn" id="tab-gebied" onclick="switchTab('gebied')">Gebied</button>
  </div>
</div>

<!-- Filter card -->
<div class="filter-card">
  <div class="filter-inner">

    <!-- ALGEMEEN filters -->
    <div id="panel-algemeen">
      <div class="filter-row">
        <div class="filter-group" style="flex:2 1 220px">
          <label>Zoeken</label>
          <input type="text" id="search" placeholder="Adres, stad of regio…" autocomplete="off">
        </div>
        <div class="filter-group">
          <label>Bron</label>
          <select id="filter-source">{_source_options(listings)}</select>
        </div>
        <div class="filter-group">
          <label>Land</label>
          <select id="filter-country">{_country_options(listings)}</select>
        </div>
        <div class="filter-group">
          <label>Sortering</label>
          <select id="sort">
            <option value="default">Standaard</option>
            <option value="price-asc">Prijs laag → hoog</option>
            <option value="price-desc">Prijs hoog → laag</option>
            <option value="dist-asc">Afstand dichtbij → ver</option>
          </select>
        </div>
      </div>
      <div class="filter-row">
        <div class="slider-block">
          <label>Prijsrange</label>
          <div class="price-inputs-row">
            <input type="number" id="input-min" value="{slider_min}" step="50000" min="{slider_min}" max="{slider_max}" placeholder="Min">
            <span>—</span>
            <input type="number" id="input-max" value="{slider_max}" step="50000" min="{slider_min}" max="{slider_max}" placeholder="Max">
          </div>
          <div class="range-wrap">
            <div class="range-track"><div class="range-fill" id="range-fill"></div></div>
            <input type="range" id="slider-min" min="{slider_min}" max="{slider_max}" step="50000" value="{slider_min}">
            <input type="range" id="slider-max" min="{slider_min}" max="{slider_max}" step="50000" value="{slider_max}">
          </div>
        </div>
        <div class="filter-group" style="justify-content:flex-end;flex:0 1 auto">
          <label>&nbsp;</label>
          <button class="btn-clear" id="btn-clear">Wis filters</button>
        </div>
      </div>
    </div>

    <!-- GEBIED kaart -->
    <div id="panel-gebied" style="display:none">
      <div class="map-toolbar">
        <p id="map-hint">Teken een gebied op de kaart om panden te filteren.</p>
        <div class="map-result-pill" id="map-result-pill">
          <span id="map-result-count">0</span> panden in getekend gebied
        </div>
        <button class="btn-draw" id="btn-draw">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/></svg>
          Teken gebied
        </button>
        <button class="btn-draw-clear" id="btn-draw-clear">✕ Wis gebied</button>
      </div>
      <div id="map"></div>
    </div>

  </div>
</div>

<div class="stats-bar">
  <p><strong id="visible-count2">{count}</strong> van <strong>{count}</strong> objecten zichtbaar</p>
</div>

<main class="grid" id="grid">
  {cards_html}
</main>

<footer>Automatisch gegenereerd op {today} &nbsp;|&nbsp; Lammers Beton vastgoedmonitor</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>

<script>
(function(){{
  const SLIDER_MIN_VAL = {slider_min};
  const SLIDER_MAX_VAL = {slider_max};
  const grid      = document.getElementById('grid');
  const cards     = Array.from(grid.querySelectorAll('.card'));
  const searchEl  = document.getElementById('search');
  const sortEl    = document.getElementById('sort');
  const srcEl     = document.getElementById('filter-source');
  const cntryEl   = document.getElementById('filter-country');
  const sMin      = document.getElementById('slider-min');
  const sMax      = document.getElementById('slider-max');
  const inputMin  = document.getElementById('input-min');
  const inputMax  = document.getElementById('input-max');
  const fill      = document.getElementById('range-fill');
  const statsEl   = document.getElementById('visible-count');
  const clearBtn  = document.getElementById('btn-clear');

  let centerLat = null, centerLon = null;
  let activeTab = 'algemeen';

  // ── Kaart ──
  const GEO_LISTINGS = {listings_json};
  let map = null, drawnLayer = null, currentDrawHandler = null;
  let inPolygonIds = null; // null = geen filter, anders Set van listing IDs

  // Ray casting point-in-polygon (lon=x, lat=y voor correcte geografische oriëntatie)
  function pointInPolygon(lat, lon, poly) {{
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {{
      const xi = poly[i].lng, yi = poly[i].lat;
      const xj = poly[j].lng, yj = poly[j].lat;
      if (((yi > lat) !== (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi))
        inside = !inside;
    }}
    return inside;
  }}

  function onPolygonCreated(latlngs) {{
    // Bouw lookup lat/lon per listing ID
    const geoById = {{}};
    GEO_LISTINGS.forEach(l => {{ if (l.lat && l.lon) geoById[l.id] = {{lat: l.lat, lon: l.lon}}; }});

    inPolygonIds = new Set();
    GEO_LISTINGS.forEach(l => {{
      if (!l.lat || !l.lon) return;
      if (pointInPolygon(l.lat, l.lon, latlngs)) inPolygonIds.add(String(l.id));
    }});

    const count = inPolygonIds.size;
    document.getElementById('map-result-count').textContent = count;
    document.getElementById('map-result-pill').classList.add('visible');
    document.getElementById('btn-draw-clear').classList.add('visible');
    document.getElementById('map-hint').textContent =
      count > 0
        ? `${{count}} pand${{count === 1 ? '' : 'en'}} gevonden — zie Algemeen tabblad.`
        : 'Geen panden in dit gebied. Teken een groter gebied.';

    // Schakel terug naar Algemeen en pas filter toe
    switchTab('algemeen');
  }}

  function clearPolygonFilter() {{
    inPolygonIds = null;
    if (drawnLayer) drawnLayer.clearLayers();
    document.getElementById('map-result-pill').classList.remove('visible');
    document.getElementById('btn-draw-clear').classList.remove('visible');
    document.getElementById('map-hint').textContent = 'Teken een gebied op de kaart om panden te filteren.';
    applyFilters();
  }}

  function initMap() {{
    if (map) return;
    map = L.map('map').setView([51.5, 5.0], 7);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '© OpenStreetMap', maxZoom: 18
    }}).addTo(map);

    // Markers per listing
    const srcColors = {{ Funda: '#ff6b00', Immoweb: '#003da5' }};
    GEO_LISTINGS.forEach(l => {{
      if (!l.lat || !l.lon) return;
      const color = srcColors[l.source] || '#b5a48a';
      const icon = L.divIcon({{
        className: '',
        html: `<div style="width:10px;height:10px;border-radius:50%;background:${{color}};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)"></div>`,
        iconSize: [10,10], iconAnchor: [5,5]
      }});
      L.marker([l.lat, l.lon], {{icon}}).addTo(map)
        .bindPopup(`<div class="map-popup">
          <strong>${{l.address}}</strong>
          <div class="mp-city">${{l.city}} · ${{l.country}}</div>
          <div class="mp-price">${{l.price_fmt || 'Prijs onbekend'}}</div>
          <a href="${{l.url}}" target="_blank">Bekijk op ${{l.source}} →</a>
        </div>`, {{maxWidth:220}});
    }});

    // Laag voor getekende vormen
    drawnLayer = new L.FeatureGroup().addTo(map);

    // Event: tekenen voltooid → verwerk polygon
    map.on(L.Draw.Event.CREATED, e => {{
      drawnLayer.clearLayers();
      drawnLayer.addLayer(e.layer);
      // Cursor terug naar normaal
      if (currentDrawHandler) {{ currentDrawHandler.disable(); currentDrawHandler = null; }}
      map.getContainer().style.cursor = '';
      // Verwerk de polygon
      const latlngs = e.layer.getLatLngs()[0]; // eerste ring
      onPolygonCreated(latlngs);
    }});

    // Knop: start tekenmodus
    document.getElementById('btn-draw').addEventListener('click', () => {{
      if (currentDrawHandler) {{ currentDrawHandler.disable(); }}
      currentDrawHandler = new L.Draw.Polygon(map, {{
        shapeOptions: {{ color: '#b5a48a', fillOpacity: 0.15, weight: 2 }},
        allowIntersection: false,
        showArea: false
      }});
      currentDrawHandler.enable();
      document.getElementById('map-hint').textContent = 'Klik om punten te plaatsen · dubbelklik om de vorm te sluiten.';
    }});

    // Knop: wis gebied
    document.getElementById('btn-draw-clear').addEventListener('click', clearPolygonFilter);
  }}

  // ── Tab wisselen ──
  window.switchTab = function(tab) {{
    activeTab = tab;
    document.getElementById('panel-algemeen').style.display = tab === 'algemeen' ? '' : 'none';
    document.getElementById('panel-gebied').style.display   = tab === 'gebied'   ? '' : 'none';
    document.getElementById('tab-algemeen').classList.toggle('active', tab === 'algemeen');
    document.getElementById('tab-gebied').classList.toggle('active', tab === 'gebied');
    if (tab === 'gebied') {{ setTimeout(initMap, 50); }}
    applyFilters();
  }};

  // ── Prijsopmaak ──
  function fmtPrice(v) {{
    return '€ ' + Math.round(v).toLocaleString('nl-NL');
  }}

  // ── Slider + invoervelden synchroon houden ──
  function updateSlider() {{
    let lo = parseInt(sMin.value);
    let hi = parseInt(sMax.value);
    if (lo > hi) {{ [lo, hi] = [hi, lo]; sMin.value = lo; sMax.value = hi; }}
    inputMin.value = lo;
    inputMax.value = hi;
    const pct1 = (lo - SLIDER_MIN_VAL) / (SLIDER_MAX_VAL - SLIDER_MIN_VAL) * 100;
    const pct2 = (hi - SLIDER_MIN_VAL) / (SLIDER_MAX_VAL - SLIDER_MIN_VAL) * 100;
    fill.style.left  = pct1 + '%';
    fill.style.width = (pct2 - pct1) + '%';
    applyFilters();
  }}

  function updateFromInput() {{
    let lo = parseInt(inputMin.value) || SLIDER_MIN_VAL;
    let hi = parseInt(inputMax.value) || SLIDER_MAX_VAL;
    lo = Math.max(SLIDER_MIN_VAL, Math.min(lo, SLIDER_MAX_VAL));
    hi = Math.max(SLIDER_MIN_VAL, Math.min(hi, SLIDER_MAX_VAL));
    if (lo > hi) lo = hi;
    sMin.value = lo;
    sMax.value = hi;
    const pct1 = (lo - SLIDER_MIN_VAL) / (SLIDER_MAX_VAL - SLIDER_MIN_VAL) * 100;
    const pct2 = (hi - SLIDER_MIN_VAL) / (SLIDER_MAX_VAL - SLIDER_MIN_VAL) * 100;
    fill.style.left  = pct1 + '%';
    fill.style.width = (pct2 - pct1) + '%';
    applyFilters();
  }}

  sMin.addEventListener('input', updateSlider);
  sMax.addEventListener('input', updateSlider);
  inputMin.addEventListener('input', updateFromInput);
  inputMax.addEventListener('input', updateFromInput);
  inputMin.addEventListener('change', updateFromInput);
  inputMax.addEventListener('change', updateFromInput);

  // ── Overige filters — direct, zonder knop ──
  searchEl.addEventListener('input', applyFilters);
  srcEl.addEventListener('change', applyFilters);
  cntryEl.addEventListener('change', applyFilters);
  sortEl.addEventListener('change', applyFilters);

  // ── Haversine ──
  function haversine(lat1, lon1, lat2, lon2) {{
    const R = 6371, d2r = Math.PI/180;
    const dLat = (lat2-lat1)*d2r, dLon = (lon2-lon1)*d2r;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*d2r)*Math.cos(lat2*d2r)*Math.sin(dLon/2)**2;
    return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
  }}

  // ── Geocodeer middelpunt ──
  async function geocodeCenter() {{
    const {{centerEl, radStatus}} = getRadEls();
    if (!centerEl) return;
    radStatus.textContent = 'Adres opzoeken…';
    const url = 'https://nominatim.openstreetmap.org/search?q=' + encodeURIComponent(centerEl.value) + '&format=json&limit=1';
    try {{
      const data = await fetch(url, {{headers:{{'Accept-Language':'nl'}}}}).then(r=>r.json());
      if (data.length) {{
        centerLat = parseFloat(data[0].lat);
        centerLon = parseFloat(data[0].lon);
        radStatus.textContent = '✓ ' + data[0].display_name.split(',').slice(0,2).join(',');
        applyFilters();
      }} else {{
        radStatus.textContent = '✗ Adres niet gevonden';
      }}
    }} catch(e) {{ radStatus.textContent = '✗ Fout bij opzoeken'; }}
  }}

  // ── Straalfilter (Gebied-tab) ──
  // Elementen bestaan alleen als de Gebied-tab actief is — haal ze op bij gebruik
  function getRadEls() {{
    return {{
      centerEl: document.getElementById('center-address'),
      radiusEl: document.getElementById('radius-km'),
      applyBtn: document.getElementById('btn-apply'),
      radStatus: document.getElementById('radius-status'),
    }};
  }}

  document.addEventListener('click', e => {{
    if (e.target && e.target.id === 'btn-apply') geocodeCenter();
  }});
  document.addEventListener('keydown', e => {{
    if (e.key === 'Enter' && document.activeElement?.id === 'center-address') geocodeCenter();
  }});
  document.addEventListener('change', e => {{
    if (e.target && e.target.id === 'radius-km' && centerLat) applyFilters();
  }});

  // ── Filters toepassen ──
  function applyFilters() {{
    const q      = searchEl.value.toLowerCase().trim();
    const src    = srcEl.value;
    const cntry  = cntryEl.value;
    const pLo    = parseInt(sMin.value) || SLIDER_MIN_VAL;
    const pHi    = parseInt(sMax.value) || SLIDER_MAX_VAL;
    const useRad  = activeTab === 'gebied' && centerLat !== null;
    const radKmEl = document.getElementById('radius-km');
    const radKm   = radKmEl ? (parseFloat(radKmEl.value) || 999) : 999;

    cards.forEach(card => {{
      const addr   = (card.querySelector('.card-address')?.textContent||'').toLowerCase();
      const city   = (card.querySelector('.card-city')?.textContent||'').toLowerCase();
      const price  = parseInt(card.dataset.price) || 0;
      const csrc   = card.dataset.source||'';
      const ccntry = card.dataset.country||'';
      const clat   = parseFloat(card.dataset.lat);
      const clon   = parseFloat(card.dataset.lon);

      // Prijs: listings zonder prijs (0) altijd tonen
      const mPrice   = price === 0 || (price >= pLo && price <= pHi);
      const mSearch  = !q || addr.includes(q) || city.includes(q);
      const mSrc     = !src   || csrc   === src;
      const mCntry   = !cntry || ccntry === cntry;
      const mPolygon = !inPolygonIds || inPolygonIds.has(String(card.dataset.id));

      let mDist = true;
      let distKm = null;
      if (useRad && !isNaN(clat) && !isNaN(clon)) {{
        distKm = haversine(centerLat, centerLon, clat, clon);
        mDist = distKm <= radKm;
      }} else if (useRad) {{
        mDist = false;
      }}

      card.classList.toggle('hidden', !(mPrice && mSearch && mSrc && mCntry && mDist && mPolygon));


      const dEl = card.querySelector('.card-distance');
      if (dEl) dEl.textContent = distKm !== null ? distKm.toFixed(1)+' km van middelpunt' : '';
    }});

    applySort();
    updateStats();
  }}

  function applySort() {{
    const val = sortEl.value;
    if (val === 'default') return;
    const visible = cards.filter(c=>!c.classList.contains('hidden'));
    visible.sort((a,b) => {{
      if (val==='price-asc')  return (parseInt(a.dataset.price)||0)-(parseInt(b.dataset.price)||0);
      if (val==='price-desc') return (parseInt(b.dataset.price)||0)-(parseInt(a.dataset.price)||0);
      if (val==='dist-asc') {{
        const da = parseFloat(a.querySelector('.card-distance')?.textContent)||9999;
        const db = parseFloat(b.querySelector('.card-distance')?.textContent)||9999;
        return da-db;
      }}
      return 0;
    }});
    visible.forEach(c=>grid.appendChild(c));
  }}

  function updateStats() {{
    const n = cards.filter(c=>!c.classList.contains('hidden')).length;
    statsEl.textContent = n;
    const s2 = document.getElementById('visible-count2');
    if (s2) s2.textContent = n;
    let nr = grid.querySelector('.no-results');
    if (n===0 && cards.length>0) {{
      if (!nr) {{ nr=document.createElement('p'); nr.className='no-results'; nr.textContent='Geen objecten gevonden.'; grid.appendChild(nr); }}
    }} else if (nr) nr.remove();
  }}

  // ── Alles wissen ──
  clearBtn.addEventListener('click', () => {{
    searchEl.value=''; srcEl.value=''; cntryEl.value=''; sortEl.value='default';
    sMin.value=SLIDER_MIN_VAL; sMax.value=SLIDER_MAX_VAL;
    inputMin.value=SLIDER_MIN_VAL; inputMax.value=SLIDER_MAX_VAL;
    radToggle.checked=false; radSection.classList.remove('open');
    centerLat=null; centerLon=null; radStatus.textContent='';
    updateSlider();
    cards.forEach(c=>{{ c.classList.remove('hidden'); const d=c.querySelector('.card-distance'); if(d) d.textContent=''; }});
    cards.forEach(c=>grid.appendChild(c));
    updateStats();
  }});

  // ── Parallax hero ──
  const heroBg = document.getElementById('hero-bg');
  if (heroBg) {{
    window.addEventListener('scroll', () => {{
      heroBg.style.transform = `translateY(${{window.scrollY * 0.35}}px)`;
    }}, {{passive: true}});
  }}

  // Init
  updateSlider();
}})();
</script>
</body>
</html>"""


def save_dashboard(listings: list[dict]) -> Path:
    DOCS_DIR.mkdir(exist_ok=True)
    html = build_dashboard(listings)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    return OUTPUT_FILE
