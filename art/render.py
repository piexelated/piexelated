#!/usr/bin/env python3
"""Renders the profile banner into ../assets.

Needs google-chrome and ImageMagick (magick). Run: python3 art/render.py
Libron is bundled under the SIL Open Font License (art/fonts/OFL.txt).
"""
import subprocess
import tempfile
from pathlib import Path

ART_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ART_DIR.parent / "assets"
BANNER_PHOTOS_DIR = ART_DIR / "banner"
FONTS_DIR = ART_DIR / "fonts"

DEVICE_SCALE = 2
BANNER_SIZE = (1280, 320)
BANNER_NAME = "Piexel"
BANNER_TAGLINE = "Building stuff"
BANNER_PHOTOS = ("autumn", "peak", "crystal", "taiga")
BANNER_SLICE_EDGES_PCT = (0, 36, 58, 79, 100)
BANNER_SLICE_SKEW_PCT = 3.5
# Each slice reaches slightly under its left neighbour so anti-aliased diagonal edges leave no hairline gap.
BANNER_SEAM_OVERLAP_PCT = 0.4
WEBP_QUALITY = 86

BASE_STYLE = f"""
@font-face {{ font-family: Libron; font-weight: 700; src: url('{(FONTS_DIR / "Libron-Bold.ttf").as_uri()}'); }}
@font-face {{ font-family: Libron; font-style: italic; src: url('{(FONTS_DIR / "Libron-Italic.ttf").as_uri()}'); }}
html, body {{ margin: 0; background: transparent; }}
body {{ -webkit-font-smoothing: antialiased; }}
.serif {{ font-family: Libron, serif; }}
"""


def banner_slice_html(position: int, photo_name: str) -> str:
    is_first = position == 0
    is_last = position == len(BANNER_PHOTOS) - 1
    top_left = 0 if is_first else BANNER_SLICE_EDGES_PCT[position] - BANNER_SEAM_OVERLAP_PCT
    bottom_left = 0 if is_first else top_left - BANNER_SLICE_SKEW_PCT
    top_right = BANNER_SLICE_EDGES_PCT[position + 1]
    bottom_right = 100 if is_last else top_right - BANNER_SLICE_SKEW_PCT
    box_left = min(top_left, bottom_left)
    box_width = top_right - box_left

    def within_box(x: float) -> str:
        return f"{(x - box_left) / box_width * 100:.3f}%"

    photo_url = (BANNER_PHOTOS_DIR / f"{photo_name}.jpg").as_uri()
    clip = f"polygon({within_box(top_left)} 0, {within_box(top_right)} 0, {within_box(bottom_right)} 100%, {within_box(bottom_left)} 100%)"
    return f"<div class=\"slice\" style=\"left: {box_left}%; width: {box_width}%; background-image: url('{photo_url}'); clip-path: {clip};\"></div>"


def banner_html() -> str:
    slices = "".join(banner_slice_html(position, photo) for position, photo in enumerate(BANNER_PHOTOS))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_STYLE}
.banner {{ width: {BANNER_SIZE[0]}px; height: {BANNER_SIZE[1]}px; border-radius: 16px; overflow: hidden; position: relative; background: #0b1018; }}
.slice {{ position: absolute; top: 0; bottom: 0; background-size: cover; background-position: center; filter: contrast(1.08) saturate(1.12); }}
.shade {{
  position: absolute; inset: 0;
  background: radial-gradient(70% 120% at 0% 100%, rgba(3,6,12,.78) 0%, rgba(3,6,12,.4) 50%, transparent 80%),
              linear-gradient(0deg, rgba(3,6,12,.45) 0%, transparent 50%);
}}
.text {{ position: absolute; left: 46px; bottom: 44px; color: #fff; }}
h1 {{ margin: 0; font-size: 77px; font-weight: 700; letter-spacing: -.6px; line-height: 1; }}
p {{ margin: 8px 0 0; font-size: 26px; font-style: italic; color: rgba(255,255,255,.9); }}
</style></head><body>
<div class="banner">{slices}<div class="shade"></div><div class="text serif">
  <h1>{BANNER_NAME}</h1><p>{BANNER_TAGLINE}</p>
</div></div></body></html>"""


def screenshot_to_webp(html: str, size: tuple[int, int], output_path: Path, work_dir: Path) -> None:
    page_path = work_dir / f"{output_path.stem}.html"
    png_path = work_dir / f"{output_path.stem}.png"
    page_path.write_text(html)
    subprocess.run(
        [
            "google-chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--allow-file-access-from-files", "--virtual-time-budget=3000",
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
    with tempfile.TemporaryDirectory() as work:
        screenshot_to_webp(banner_html(), BANNER_SIZE, ASSETS_DIR / "banner.webp", Path(work))


if __name__ == "__main__":
    main()
