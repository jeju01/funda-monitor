"""
Builds the HTML email body for the weekly real estate report.
Uses HTML tables for layout (CSS grid is unreliable in email clients).
"""

from datetime import date, timedelta
from typing import Optional

from config import (
    COLOR_ACCENT,
    COLOR_BODY_BG,
    COLOR_BUTTON_TEXT,
    COLOR_CARD_BG,
    COLOR_HEADER_BG,
    COLOR_HEADER_TEXT,
    COLOR_TEXT,
    REPORT_TITLE,
)


def _date_range_label() -> str:
    today = date.today()
    week_ago = today - timedelta(days=7)
    months_nl = {
        1: "jan", 2: "feb", 3: "mrt", 4: "apr", 5: "mei", 6: "jun",
        7: "jul", 8: "aug", 9: "sep", 10: "okt", 11: "nov", 12: "dec",
    }
    return (
        f"{week_ago.day} {months_nl[week_ago.month]} – "
        f"{today.day} {months_nl[today.month]} {today.year}"
    )


def _thumbnail_block(url: Optional[str]) -> str:
    if url:
        return (
            f'<img src="{url}" alt="foto" width="280" height="180" '
            f'style="display:block;width:100%;height:180px;object-fit:cover;'
            f'border-radius:6px 6px 0 0;" />'
        )
    return (
        '<div style="width:100%;height:180px;background:#c9bfb2;border-radius:6px 6px 0 0;'
        'display:flex;align-items:center;justify-content:center;">'
        '<span style="color:#8a7d6e;font-size:13px;font-family:sans-serif;">Geen foto beschikbaar</span>'
        "</div>"
    )


def _listing_card(listing: dict) -> str:
    thumb = _thumbnail_block(listing.get("thumbnail_url"))
    address = listing.get("address", "Adres onbekend")
    city = listing.get("city", "")
    price = listing.get("price_formatted", "Prijs onbekend")
    surface = listing.get("surface_m2")
    rooms = listing.get("rooms")
    listing_type = listing.get("listing_type", "Woning")
    url = listing.get("funda_url", "#")

    specs_parts = []
    if surface:
        specs_parts.append(f"{surface} m²")
    if rooms:
        specs_parts.append(f"{rooms} kamers")
    specs = " &nbsp;·&nbsp; ".join(specs_parts) if specs_parts else "&nbsp;"

    type_color = "#6b8c6e" if listing_type == "Woning" else "#6e7a8c"

    return f"""
<td style="padding:10px;vertical-align:top;width:50%;">
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background:{COLOR_CARD_BG};border-radius:8px;overflow:hidden;
                box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <tr>
      <td style="padding:0;">{thumb}</td>
    </tr>
    <tr>
      <td style="padding:16px 16px 6px;">
        <p style="margin:0 0 4px;font-size:15px;font-weight:700;
                  color:{COLOR_TEXT};font-family:sans-serif;line-height:1.3;">
          {address}
        </p>
        <p style="margin:0 0 10px;font-size:13px;color:#6b6255;font-family:sans-serif;">
          {city}
        </p>
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="background:{COLOR_ACCENT};border-radius:4px;padding:5px 10px;">
              <span style="color:{COLOR_BUTTON_TEXT};font-size:14px;font-weight:700;
                           font-family:sans-serif;">{price}</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td style="padding:8px 16px 4px;">
        <p style="margin:0;font-size:12px;color:#7a6e62;font-family:sans-serif;">{specs}</p>
      </td>
    </tr>
    <tr>
      <td style="padding:4px 16px 12px;">
        <span style="display:inline-block;background:{type_color};color:#fff;
                     font-size:11px;border-radius:3px;padding:2px 7px;
                     font-family:sans-serif;">{listing_type}</span>
      </td>
    </tr>
    <tr>
      <td style="padding:0 16px 16px;">
        <a href="{url}" target="_blank"
           style="display:inline-block;background:{COLOR_ACCENT};color:{COLOR_BUTTON_TEXT};
                  text-decoration:none;font-size:13px;font-weight:600;
                  border-radius:5px;padding:9px 16px;font-family:sans-serif;">
          Bekijk op Funda →
        </a>
      </td>
    </tr>
  </table>
</td>"""


def _cards_grid(listings: list[dict]) -> str:
    rows_html = []
    for i in range(0, len(listings), 2):
        left = _listing_card(listings[i])
        right = _listing_card(listings[i + 1]) if i + 1 < len(listings) else "<td></td>"
        rows_html.append(f"<tr>{left}{right}</tr>")
    return "\n".join(rows_html)


def build_html_report(new_listings: list[dict]) -> str:
    date_range = _date_range_label()
    today_str = date.today().strftime("%d-%m-%Y")
    count = len(new_listings)

    if count == 0:
        count_line = (
            '<p style="font-size:16px;color:#7a6e62;text-align:center;'
            'font-family:sans-serif;margin:0 0 30px;">Geen nieuw aanbod deze week.</p>'
        )
        grid_html = ""
    else:
        count_line = (
            f'<p style="font-size:16px;color:{COLOR_TEXT};text-align:center;'
            f'font-family:sans-serif;margin:0 0 30px;">'
            f'<strong>{count}</strong> nieuw object{"en" if count != 1 else ""} gevonden deze week</p>'
        )
        grid_html = f"""
<table cellpadding="0" cellspacing="0" border="0" width="100%"
       style="max-width:640px;margin:0 auto;">
  {_cards_grid(new_listings)}
</table>"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{REPORT_TITLE}</title>
</head>
<body style="margin:0;padding:0;background:{COLOR_BODY_BG};">

  <!-- Header -->
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background:{COLOR_HEADER_BG};">
    <tr>
      <td style="padding:32px 24px;text-align:center;">
        <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;
                   color:{COLOR_HEADER_TEXT};font-family:sans-serif;
                   letter-spacing:0.5px;">
          Nieuw vastgoedaanbod
        </h1>
        <p style="margin:0;font-size:13px;color:#a09080;font-family:sans-serif;
                  letter-spacing:1px;text-transform:uppercase;">
          Lammers Beton &nbsp;·&nbsp; {date_range}
        </p>
      </td>
    </tr>
  </table>

  <!-- Subheader bar -->
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background:{COLOR_ACCENT};">
    <tr>
      <td style="padding:10px 24px;text-align:center;">
        <span style="font-size:12px;color:#fff;font-family:sans-serif;
                     text-transform:uppercase;letter-spacing:1px;">
          Boven €2.500.000 &nbsp;·&nbsp; Noord-Brabant · Limburg · Zuid-Holland · Utrecht · Gelderland
        </span>
      </td>
    </tr>
  </table>

  <!-- Body -->
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background:{COLOR_BODY_BG};">
    <tr>
      <td style="padding:32px 16px 8px;text-align:center;">
        {count_line}
      </td>
    </tr>
    <tr>
      <td style="padding:0 8px 32px;">
        {grid_html}
      </td>
    </tr>
  </table>

  <!-- Footer -->
  <table cellpadding="0" cellspacing="0" border="0" width="100%"
         style="background:{COLOR_HEADER_BG};margin-top:0;">
    <tr>
      <td style="padding:20px 24px;text-align:center;">
        <p style="margin:0;font-size:11px;color:#707070;font-family:sans-serif;">
          Automatisch gegenereerd op {today_str} &nbsp;|&nbsp; Lammers Beton vastgoedmonitor
        </p>
      </td>
    </tr>
  </table>

</body>
</html>"""


def build_plain_fallback(new_listings: list[dict]) -> str:
    lines = [
        "NIEUW VASTGOEDAANBOD BOVEN €2.500.000",
        "=" * 40,
        "",
    ]
    if not new_listings:
        lines.append("Geen nieuw aanbod deze week.")
    else:
        lines.append(f"{len(new_listings)} nieuwe object(en) gevonden:\n")
        for l in new_listings:
            lines.append(f"  {l.get('address', '')} – {l.get('city', '')}")
            lines.append(f"  Prijs: {l.get('price_formatted', '')}")
            lines.append(f"  Type:  {l.get('listing_type', '')}")
            if l.get("surface_m2"):
                lines.append(f"  Opp.:  {l['surface_m2']} m²")
            lines.append(f"  URL:   {l.get('funda_url', '')}")
            lines.append("")
    lines.append("—")
    lines.append(f"Lammers Beton vastgoedmonitor | {date.today().strftime('%d-%m-%Y')}")
    return "\n".join(lines)
