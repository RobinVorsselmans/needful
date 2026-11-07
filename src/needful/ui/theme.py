"""Huisstijl uit het prototype: kleuren, lettertypes en een paar CSS-klassen (nf-*).

Kunnen we nog bespreken en veranderen.
"""

from nicegui import ui

INK = "#141413"  # bijna zwart: tekst, donkere knoppen
PAPER = "#FFFDF3"  # crème: achtergrond van de vragen
YELLOW = "#FFD23F"  # accent, achtergrond van het advies
GOLD = "#E0A800"  # het puntje in het logo op de crème
MUTED = "#5F5C55"  # grijze bijtekst
LINE = "#E6E2D8"  # lege stukjes, voortgangsbalk, randjes
GREEN = "#ACFAD3"  # lenen
PINK = "#FFE3EA"  # huren
TIP = "#FFF3C4"  # achtergrond van tipkaders
FAINT = "#B8B5AD"  # bijtekst op donkere achtergrond
SOFT = "#D6D3CB"  # leestekst op donkere achtergrond
MINT = "#3DD598"  # kaartpunt lenen, winnend alternatief in het advies
ROSE = "#FFB3C7"  # kaartpunt huren
MAP = "#ECEAE2"  # achtergrond van de voorbeeldkaart

FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
)  # maybe we need to download these and put them inside the project folder (PWA offline)

CSS = f"""
body {{ font-family: 'Space Grotesk', system-ui, sans-serif; color: {INK}; }}
.nicegui-content {{ padding: 0; }}
.nf-frame {{
  width: 100%; max-width: 430px; min-height: 100vh; margin: 0 auto;
  padding: 56px 24px 32px; box-sizing: border-box; gap: 20px;
}}
.nf-mono {{ font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 1px; }}
.nf-h1 {{ margin: 0; font-size: 38px; line-height: 1.05; font-weight: 700; letter-spacing: -0.5px; }}
.nf-mark {{ background: {YELLOW}; color: {INK}; padding: 0 6px; }}
.nf-btn {{
  border-radius: 14px; min-height: 56px; font-size: 17px; font-weight: 500;
  padding: 0 20px; border: 2px solid {INK};
}}
.nf-choice {{ background: transparent; color: {INK}; }}
.nf-choice.nf-selected {{ background: {INK}; color: {PAPER}; }}
.nf-dark {{ background: {INK}; color: {PAPER}; font-weight: 700; }}
.nf-yellow {{ background: {YELLOW}; color: {INK}; font-weight: 700; border-color: {YELLOW}; }}
.nf-tip {{ background: {TIP}; border-radius: 12px; padding: 14px 16px; font-size: 14px; }}
.nf-row {{ width: 100%; padding: 12px 14px; border-radius: 12px; }}
.nf-back {{ color: {MUTED}; font-size: 15px; text-decoration: none; padding: 12px 0; }}

/* Tekststijlen (na .nf-h1 en .nf-btn, zodat ze die kunnen overschrijven) */
.nf-display {{ font-size: 46px; letter-spacing: -1px; }}
.nf-lead {{ font-size: 17px; line-height: 1.45; }}
.nf-btn-sm {{ min-height: 48px; font-size: 16px; border-radius: 12px; }}
.nf-bar {{ height: 6px; border-radius: 3px; }}
.nf-mic {{ width: 96px; height: 96px; background: {INK}; color: {YELLOW};
box-shadow: 0 0 0 12px {TIP}; font-size: 24px; }}
.nf-body {{ font-size: 15px; line-height: 1.45; }}
.nf-big {{ font-size: 44px; font-weight: 700; letter-spacing: -1px; line-height: 1; }}

/* Vraag 3: voorbeeldkaart en lijst met alternatieven (klasse-naam eindigt op de soort) */
.nf-map {{
  position: relative; overflow: hidden; width: 100%; height: 190px;
  border-radius: 14px; background: {MAP}; border: 2px solid {LINE};
}}
.nf-map-me {{
  position: absolute; left: 48%; top: 42%; width: 22px; height: 22px;
  border-radius: 50%; background: {INK}; border: 3px solid {YELLOW};
}}
.nf-pin {{
  position: absolute; width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;
}}
.nf-map-note {{ position: absolute; right: 10px; bottom: 8px; font-size: 10px; color: {MUTED}; }}
.nf-pin-lenen {{ background: {MINT}; }}
.nf-pin-huren {{ background: {ROSE}; }}
.nf-pin-tweedehands {{ background: {LINE}; }}
.nf-row-lenen {{ background: {GREEN}; }}
.nf-row-huren {{ background: {PINK}; }}
.nf-row-tweedehands {{ border: 2px solid {LINE}; }}

/* Vraag 4 en advies: kaders en vergelijking */
.nf-card-line {{ border: 2px solid {INK}; }}
.nf-card-dark {{ background: {INK}; color: {PAPER}; border-radius: 16px; padding: 18px 20px; }}
.nf-compare {{ opacity: 0.8; }}
.nf-compare-win {{ font-size: 18px; font-weight: 700; color: {MINT}; }}

/* In jouw buurt: één label per mogelijkheid (klasse-naam eindigt op de tag) */
.nf-tag {{
  font-size: 12px; font-weight: 500; padding: 2px 10px; border-radius: 999px; color: {INK};
  white-space: nowrap;
}}
.nf-tag-kopen {{ background: {TIP}; }}
.nf-tag-huren {{ background: {PINK}; }}
.nf-tag-lenen {{ background: {GREEN}; }}
.nf-tag-tweedehands {{ background: {LINE}; }}
.nf-tag-herstellen {{ border: 1px solid {INK}; }}
.nf-tag-alternatief {{ background: {MINT}; }}
.nf-tag-ander {{ background: {MINT}; }}
.nf-tag-laten {{ background: {YELLOW}; }}
/* Alles op een rij: wat het advies aanraadt en wat jij koos */
.nf-advised {{ color: {MINT}; }}
.nf-chosen {{ color: {YELLOW}; }}
.nf-link {{ color: {INK}; }}

/* Tekstkleuren */
.nf-muted {{ color: {MUTED}; }}
.nf-faint {{ color: {FAINT}; }}
.nf-soft {{ color: {SOFT}; }}
.nf-on-dark {{ color: {PAPER}; }}
"""


def apply_theme(background: str = PAPER) -> None:
    """Lettertypes, CSS en achtergrondkleur voor de huidige pagina."""
    ui.add_head_html(f'<link rel="stylesheet" href="{FONTS}">')
    ui.add_css(CSS)
    ui.query("body").style(f"background: {background}")
