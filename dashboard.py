"""
Generates a standalone HTML dashboard from the current snapshot.
Output: docs/index.html  (GitHub Pages serves the docs/ folder)
"""

from datetime import date
from pathlib import Path
from typing import Optional
import json

from config import BASE_DIR

DOCS_DIR = BASE_DIR / "docs"
OUTPUT_FILE = DOCS_DIR / "index.html"


def _format_price(amount: Optional[int]) -> str:
    if amount is None:
        return "Prijs onbekend"
    return "€ " + f"{amount:,.0f}".replace(",", ".")


def _card(listing: dict) -> str:
    lid       = listing.get("id", "")
    address   = listing.get("address", "Adres onbekend")
    city      = listing.get("city", "")
    price     = listing.get("price_formatted") or _format_price(listing.get("price"))
    surface   = listing.get("surface_m2")
    rooms     = listing.get("rooms")
    ltype     = listing.get("listing_type", "Woning")
    thumb     = listing.get("thumbnail_url", "")
    url       = listing.get("funda_url", "#")
    region    = listing.get("region", "")

    specs_parts = []
    if surface:
        specs_parts.append(f"{surface} m²")
    if rooms:
        specs_parts.append(f"{rooms} kamers")
    specs_html = " · ".join(specs_parts) if specs_parts else ""

    img_html = (
        f'<img src="{thumb}" alt="foto" loading="lazy" />'
        if thumb else
        '<div class="no-photo">Geen foto</div>'
    )

    type_class = "badge-commercial" if ltype == "Bedrijfsvastgoed" else "badge-woning"

    # store data attributes for JS filtering
    price_raw = listing.get("price") or 0

    return f"""
    <article class="card"
             data-region="{region}"
             data-type="{ltype}"
             data-price="{price_raw}"
             data-id="{lid}">
      <a href="{url}" target="_blank" class="card-img-link">
        {img_html}
      </a>
      <div class="card-body">
        <p class="card-address">{address}</p>
        <p class="card-city">{city}</p>
        <p class="card-price">{price}</p>
        <div class="card-meta">
          <span class="specs">{specs_html}</span>
          <span class="badge {type_class}">{ltype}</span>
        </div>
        <a href="{url}" target="_blank" class="btn-funda">Bekijk op Funda →</a>
      </div>
    </article>"""


def build_dashboard(listings: list[dict]) -> str:
    today = date.today().strftime("%d-%m-%Y")
    count = len(listings)

    # collect unique regions for filter buttons
    regions = sorted({l.get("region", "") for l in listings if l.get("region")})

    cards_html = "\n".join(_card(l) for l in listings) if listings else (
        '<p class="empty">Geen objecten gevonden in de huidige snapshot.</p>'
    )

    region_buttons = "\n".join(
        f'<button class="filter-btn" data-filter="region" data-value="{r}">'
        f'{r.replace("-", " ").title()}</button>'
        for r in regions
    )

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vastgoedmonitor | Lammers Beton</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f0ece6;
      color: #2c2c2c;
      min-height: 100vh;
    }}

    /* ── Header ── */
    header {{
      background: #1a1a1a;
      padding: 32px 24px 24px;
      text-align: center;
    }}
    header h1 {{
      color: #fff;
      font-size: clamp(20px, 4vw, 28px);
      font-weight: 700;
      letter-spacing: 0.3px;
    }}
    header p {{
      color: #a09080;
      font-size: 13px;
      margin-top: 6px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}

    /* ── Accent bar ── */
    .accent-bar {{
      background: #b5a48a;
      padding: 10px 24px;
      text-align: center;
      font-size: 12px;
      color: #fff;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }}

    /* ── Controls ── */
    .controls {{
      max-width: 1200px;
      margin: 28px auto 0;
      padding: 0 16px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}

    .controls input[type="search"] {{
      flex: 1 1 220px;
      padding: 10px 14px;
      border: 1.5px solid #d4ccc2;
      border-radius: 8px;
      font-size: 14px;
      background: #fff;
      outline: none;
      transition: border-color .2s;
    }}
    .controls input[type="search"]:focus {{ border-color: #b5a48a; }}

    .controls select {{
      padding: 10px 14px;
      border: 1.5px solid #d4ccc2;
      border-radius: 8px;
      font-size: 14px;
      background: #fff;
      cursor: pointer;
      outline: none;
    }}
    .controls select:focus {{ border-color: #b5a48a; }}

    .filter-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .filter-btn {{
      padding: 7px 14px;
      border: 1.5px solid #b5a48a;
      border-radius: 20px;
      background: #fff;
      color: #6b5e4e;
      font-size: 12px;
      cursor: pointer;
      transition: background .15s, color .15s;
      text-transform: capitalize;
    }}
    .filter-btn:hover,
    .filter-btn.active {{
      background: #b5a48a;
      color: #fff;
    }}
    .filter-btn.clear-btn {{
      border-color: #ccc;
      color: #888;
    }}
    .filter-btn.clear-btn:hover {{
      background: #eee;
      color: #333;
    }}

    /* ── Stats bar ── */
    .stats {{
      max-width: 1200px;
      margin: 16px auto 0;
      padding: 0 16px;
      font-size: 13px;
      color: #7a6e62;
    }}
    .stats strong {{ color: #2c2c2c; }}

    /* ── Grid ── */
    .grid {{
      max-width: 1200px;
      margin: 20px auto 48px;
      padding: 0 16px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 20px;
    }}

    /* ── Card ── */
    .card {{
      background: #e8e0d5;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(0,0,0,.07);
      transition: transform .2s, box-shadow .2s;
      display: flex;
      flex-direction: column;
    }}
    .card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(0,0,0,.12);
    }}
    .card.hidden {{ display: none; }}

    .card-img-link {{ display: block; overflow: hidden; height: 200px; background: #ccc8c0; }}
    .card-img-link img {{
      width: 100%; height: 100%;
      object-fit: cover;
      display: block;
      transition: transform .3s;
    }}
    .card:hover .card-img-link img {{ transform: scale(1.04); }}
    .no-photo {{
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      color: #8a7d6e; font-size: 13px;
    }}

    .card-body {{
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }}
    .card-address {{
      font-size: 15px;
      font-weight: 700;
      line-height: 1.3;
      color: #1a1a1a;
    }}
    .card-city {{
      font-size: 13px;
      color: #7a6e62;
    }}
    .card-price {{
      font-size: 18px;
      font-weight: 800;
      color: #1a1a1a;
      margin: 4px 0;
    }}
    .card-meta {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-top: 2px;
    }}
    .specs {{
      font-size: 12px;
      color: #7a6e62;
    }}
    .badge {{
      font-size: 11px;
      padding: 3px 9px;
      border-radius: 4px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .badge-woning {{ background: #d4e8d4; color: #2d5a2d; }}
    .badge-commercial {{ background: #d4dce8; color: #2d3d5a; }}

    .btn-funda {{
      display: inline-block;
      margin-top: 10px;
      padding: 9px 16px;
      background: #b5a48a;
      color: #fff;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
      border-radius: 6px;
      transition: background .2s;
      text-align: center;
    }}
    .btn-funda:hover {{ background: #9d8e77; }}

    /* ── Empty / no results ── */
    .empty, .no-results {{
      grid-column: 1/-1;
      text-align: center;
      padding: 60px 20px;
      color: #7a6e62;
      font-size: 16px;
    }}

    /* ── Footer ── */
    footer {{
      background: #1a1a1a;
      color: #666;
      text-align: center;
      padding: 18px;
      font-size: 11px;
    }}
  </style>
</head>
<body>

<header>
  <h1>Vastgoedmonitor</h1>
  <p>Lammers Beton &nbsp;·&nbsp; Boven €2.500.000 &nbsp;·&nbsp; Bijgewerkt op {today}</p>
</header>

<div class="accent-bar">
  Noord-Brabant &nbsp;·&nbsp; Limburg &nbsp;·&nbsp; Zuid-Holland &nbsp;·&nbsp; Utrecht &nbsp;·&nbsp; Gelderland
</div>

<div class="controls">
  <input type="search" id="search" placeholder="Zoek op adres of stad…" autocomplete="off">
  <select id="sort">
    <option value="default">Sortering: standaard</option>
    <option value="price-asc">Prijs: laag → hoog</option>
    <option value="price-desc">Prijs: hoog → laag</option>
  </select>
  <div class="filter-chips">
    {region_buttons}
    <button class="filter-btn clear-btn" id="clear-filters">✕ Wis filters</button>
  </div>
</div>

<div class="stats" id="stats">
  <strong id="visible-count">{count}</strong> van <strong>{count}</strong> objecten zichtbaar
</div>

<main class="grid" id="grid">
  {cards_html}
</main>

<footer>
  Automatisch gegenereerd op {today} &nbsp;|&nbsp; Lammers Beton vastgoedmonitor
</footer>

<script>
(function () {{
  const grid      = document.getElementById('grid');
  const cards     = Array.from(grid.querySelectorAll('.card'));
  const searchEl  = document.getElementById('search');
  const sortEl    = document.getElementById('sort');
  const statsEl   = document.getElementById('visible-count');
  const clearBtn  = document.getElementById('clear-filters');

  let activeRegion = null;

  function applyFilters() {{
    const q = searchEl.value.toLowerCase().trim();

    cards.forEach(card => {{
      const address = (card.querySelector('.card-address')?.textContent || '').toLowerCase();
      const city    = (card.querySelector('.card-city')?.textContent    || '').toLowerCase();
      const region  = card.dataset.region || '';

      const matchSearch = !q || address.includes(q) || city.includes(q);
      const matchRegion = !activeRegion || region === activeRegion;

      card.classList.toggle('hidden', !(matchSearch && matchRegion));
    }});

    applySort();
    updateStats();
  }}

  function applySort() {{
    const val = sortEl.value;
    if (val === 'default') return;

    const visible = cards.filter(c => !c.classList.contains('hidden'));
    visible.sort((a, b) => {{
      const pa = parseInt(a.dataset.price) || 0;
      const pb = parseInt(b.dataset.price) || 0;
      return val === 'price-asc' ? pa - pb : pb - pa;
    }});
    visible.forEach(c => grid.appendChild(c));
  }}

  function updateStats() {{
    const visibleCount = cards.filter(c => !c.classList.contains('hidden')).length;
    statsEl.textContent = visibleCount;

    let noResults = grid.querySelector('.no-results');
    if (visibleCount === 0 && cards.length > 0) {{
      if (!noResults) {{
        noResults = document.createElement('p');
        noResults.className = 'no-results';
        noResults.textContent = 'Geen objecten gevonden voor deze zoekopdracht.';
        grid.appendChild(noResults);
      }}
    }} else if (noResults) {{
      noResults.remove();
    }}
  }}

  // Region filter buttons
  document.querySelectorAll('.filter-btn[data-filter="region"]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      if (activeRegion === btn.dataset.value) {{
        activeRegion = null;
        btn.classList.remove('active');
      }} else {{
        document.querySelectorAll('.filter-btn[data-filter="region"]').forEach(b => b.classList.remove('active'));
        activeRegion = btn.dataset.value;
        btn.classList.add('active');
      }}
      applyFilters();
    }});
  }});

  clearBtn.addEventListener('click', () => {{
    activeRegion = null;
    searchEl.value = '';
    sortEl.value = 'default';
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    cards.forEach(c => c.classList.remove('hidden'));
    // restore original DOM order
    cards.forEach(c => grid.appendChild(c));
    updateStats();
  }});

  searchEl.addEventListener('input', applyFilters);
  sortEl.addEventListener('change', applyFilters);

  updateStats();
}})();
</script>

</body>
</html>"""


def save_dashboard(listings: list[dict]) -> Path:
    DOCS_DIR.mkdir(exist_ok=True)
    html = build_dashboard(listings)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    return OUTPUT_FILE
