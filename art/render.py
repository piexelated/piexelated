#!/usr/bin/env python3
"""Renders the profile banner and project cards into ../assets.

Needs google-chrome and ImageMagick (magick). Run: python3 art/render.py
"""
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

ART_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ART_DIR.parent / "assets"
CARDS_DIR = ASSETS_DIR / "cards"

DEVICE_SCALE = 2
BANNER_SIZE = (1280, 320)
CARD_SLOT_SIZE = (360, 180)
CARD_GAP_PX = 12
WEBP_QUALITY = 86

LANGUAGE_COLORS = {
    "C": "#555555",
    "Python": "#3572A5",
    "Kotlin": "#A97BFF",
    "TypeScript": "#3178C6",
}

CARD_COLORS = {"surface": "#151b23", "border": "#3d444d", "title": "#f0f6fc", "text": "#9198a1", "muted": "#768390"}


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    kind: str
    description: str
    languages: tuple[str, ...]


PROJECTS = [
    Project("zfan", "zfan", "Kernel driver · TUI", "Fan control for HP ZBook laptops on Linux.", ("Python", "C")),
    Project("codex-provider", "Codex Provider", "IntelliJ plugin", "Your ChatGPT account in JetBrains AI Assistant.", ("Kotlin",)),
    Project("paperback-suwayomi", "Suwayomi for Paperback", "Paperback extension", "Read manga from your own Suwayomi server on iOS.", ("TypeScript",)),
]

BASE_STYLE = """
html, body { margin: 0; background: transparent; }
body { font-family: 'Adwaita Sans', 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
.mono { font-family: 'Adwaita Mono', monospace; }
"""


def banner_html() -> str:
    photo_url = (ART_DIR / "banner-photo.jpg").as_uri()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_STYLE}
.banner {{
  width: {BANNER_SIZE[0]}px; height: {BANNER_SIZE[1]}px; border-radius: 16px; overflow: hidden; position: relative;
  background: url('{photo_url}') center / cover;
}}
.shade {{ position: absolute; inset: 0; background: linear-gradient(90deg, rgba(4,8,16,.78) 0%, rgba(4,8,16,.45) 38%, rgba(4,8,16,0) 66%); }}
.text {{ position: absolute; left: 64px; top: 50%; transform: translateY(-50%); color: #fff; }}
h1 {{ margin: 0; font-size: 76px; font-weight: 800; letter-spacing: -2px; line-height: 1; }}
p {{ margin: 14px 0 0; font-size: 19px; letter-spacing: .5px; color: rgba(255,255,255,.82); }}
</style></head><body>
<div class="banner"><div class="shade"></div><div class="text">
  <h1>Piexel</h1><p class="mono">Minecraft worldgen · Linux tinkering</p>
</div></div></body></html>"""


def card_width() -> int:
    slot_count = len(PROJECTS)
    return (slot_count * CARD_SLOT_SIZE[0] - (slot_count - 1) * CARD_GAP_PX) // slot_count


def card_offset(position: int) -> int:
    # GitHub strips CSS, so the README places the cards edge to edge and the gaps are
    # transparent space baked into each image. A card shifts right with its position so
    # the outer cards stay flush with the banner edges.
    return position * (card_width() + CARD_GAP_PX - CARD_SLOT_SIZE[0])


def card_html(project: Project, position: int) -> str:
    accent = LANGUAGE_COLORS[project.languages[0]]
    languages = "".join(
        f'<span class="lang"><i style="background:{LANGUAGE_COLORS[language]}"></i>{language}</span>'
        for language in project.languages
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_STYLE}
.card {{
  box-sizing: border-box; width: {card_width()}px; height: {CARD_SLOT_SIZE[1]}px; padding: 20px 22px;
  margin-left: {card_offset(position)}px;
  border: 1px solid {CARD_COLORS['border']}; border-radius: 12px; background: {CARD_COLORS['surface']};
  position: relative; overflow: hidden; display: flex; flex-direction: column;
}}
.card::before {{ content: ''; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: linear-gradient(90deg, {accent}, transparent 80%); }}
.kind {{ font-size: 13px; letter-spacing: 1.1px; text-transform: uppercase; color: {CARD_COLORS['muted']}; }}
.name {{ margin-top: 7px; font-size: 24px; font-weight: 700; letter-spacing: -.4px; color: {CARD_COLORS['title']}; white-space: nowrap; }}
.name span {{ color: {CARD_COLORS['muted']}; font-weight: 400; font-size: 20px; }}
.desc {{ margin-top: 6px; font-size: 16px; line-height: 1.38; color: {CARD_COLORS['text']}; text-wrap: balance; }}
.langs {{ margin-top: auto; font-size: 14px; color: {CARD_COLORS['text']}; display: flex; gap: 16px; }}
.lang i {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }}
</style></head><body>
<div class="card">
  <div class="kind mono">{project.kind}</div>
  <div class="name">{project.name} <span>↗</span></div>
  <div class="desc">{project.description}</div>
  <div class="langs mono">{languages}</div>
</div></body></html>"""


def screenshot_to_webp(html: str, size: tuple[int, int], output_path: Path, work_dir: Path) -> None:
    page_path = work_dir / f"{output_path.stem}.html"
    png_path = work_dir / f"{output_path.stem}.png"
    page_path.write_text(html)
    subprocess.run(
        [
            "google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={work_dir / 'chrome-profile'}",
            f"--force-device-scale-factor={DEVICE_SCALE}",
            "--default-background-color=00000000",
            f"--window-size={size[0]},{size[1]}",
            f"--screenshot={png_path}",
            page_path.as_uri(),
        ],
        check=True, capture_output=True, timeout=60,
    )
    subprocess.run(["magick", str(png_path), "-quality", str(WEBP_QUALITY), str(output_path)], check=True)
    print(f"wrote {output_path.relative_to(ASSETS_DIR.parent)}")


def main() -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        work_dir = Path(work)
        screenshot_to_webp(banner_html(), BANNER_SIZE, ASSETS_DIR / "banner.webp", work_dir)
        for position, project in enumerate(PROJECTS):
            output_path = CARDS_DIR / f"{project.slug}.webp"
            screenshot_to_webp(card_html(project, position), CARD_SLOT_SIZE, output_path, work_dir)


if __name__ == "__main__":
    main()
