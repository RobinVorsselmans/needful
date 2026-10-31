"""Huisstijl uit het prototype: kleuren, lettertypes en een paar CSS-klassen (nf-*). kunnen we nog bespreken en veranderen"""

from nicegui import ui

INK = "#141413"  # bijna zwart: tekst, donkere knoppen
PAPER = "#FFFDF3"  # crème: achtergrond van de vragen
YELLOW = "#FFD23F"  # accent, achtergrond van het advies
GOLD = "#E0A800"  # het puntje in het logo op de crème
MUTED = "#5F5C55"  # grijze bijtekst
LINE = "#E6E2D8"  # lege stukjes, voortgangsbalk, randjes
GREEN = "#ACFAD3"  # lenen
PINK = "#FFE3EA"  # huren

FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
)  # maybe we need to download these and put them inside the project folder

CSS = f"""
body {{ font-family: 'Space Grotesk',
system-ui, sans-serif; color: {INK}; }}
.nicegui-content {{ padding: 0; }}
.nf-frame {{
  width: 100%; max-width: 430px; min-height:
100vh; margin: 0 auto;
  padding: 56px 24px 32px; box-sizing:
border-box; gap: 20px;
}}
.nf-mono {{ font-family: 'IBM Plex Mono',
monospace; font-size: 11px; letter-spacing:
1px; }}
.nf-h1 {{ margin: 0; font-size: 38px;
line-height: 1.05; font-weight: 700;
letter-spacing: -0.5px; }}
.nf-mark {{ background: {YELLOW}; color:
{INK}; padding: 0 6px; }}
.nf-btn {{
  border-radius: 14px; min-height: 56px;
font-size: 17px; font-weight: 500;
  padding: 0 20px; border: 2px solid {INK};
}}
.nf-choice {{ background: transparent;
color: {INK}; }}
.nf-choice.nf-selected {{ background: {INK};
color: {PAPER}; }}
.nf-dark {{ background: {INK}; color:
{PAPER}; font-weight: 700; }}
.nf-yellow {{ background: {YELLOW}; color:
{INK}; font-weight: 700; border-color:
{YELLOW}; }}
.nf-tip {{ background: #FFF3C4;
border-radius: 12px; padding: 14px 16px;
font-size: 14px; }}
.nf-row {{ width: 100%; padding: 12px 14px;
border-radius: 12px; }}
.nf-back {{ color: {MUTED}; font-size: 15px;
text-decoration: none; padding: 12px 0; }}
"""

# nf-tip background hardcoded, move to top


def apply_theme(background: str = PAPER) -> None:
    """Lettertypes, CSS en achtergrondkleur voor de huidige pagina"""
    ui.add_head_html(f'<link rel="stylesheet" href="{FONTS}">')
    ui.add_css(CSS)
    ui.query("body").style(f"background: {background}")
