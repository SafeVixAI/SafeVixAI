# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "frontend" / "public"
ICONS = PUBLIC / "icons"
SCREENSHOTS = PUBLIC / "screenshots"


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def generate_icons() -> None:
    source = Image.open(ICONS / "icon-512.png").convert("RGBA")
    for size in (72, 96, 128, 144, 152, 192, 384, 512):
        source.resize((size, size), Image.Resampling.LANCZOS).save(
            ICONS / f"icon-{size}.png",
            optimize=True,
        )

    source.resize((180, 180), Image.Resampling.LANCZOS).save(
        ICONS / "apple-touch-icon.png",
        optimize=True,
    )
    source.resize((48, 48), Image.Resampling.LANCZOS).save(
        ICONS / "favicon.png",
        optimize=True,
    )


def generate_dashboard_screenshot() -> None:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1280, 720), "#0A0E14")
    draw = ImageDraw.Draw(canvas)

    font_big = load_font("arialbd.ttf", 60)
    font_med = load_font("arialbd.ttf", 30)
    font_small = load_font("arial.ttf", 24)

    for x in range(0, 1280, 40):
        draw.line((x, 0, x, 720), fill="#111827")
    for y in range(0, 720, 40):
        draw.line((0, y, 1280, y), fill="#111827")

    icon = Image.open(ICONS / "icon-192.png").convert("RGBA")
    canvas.paste(icon, (72, 74), icon)
    draw.text((300, 90), "SafeVixAI", fill="#F8FAFC", font=font_big)
    draw.text((304, 165), "AI-powered road safety command center", fill="#94A3B8", font=font_small)

    cards = [
        (80, 300, 350, 500, "#7F1D1D", "SOS", "Emergency dispatch"),
        (400, 300, 670, 500, "#064E3B", "Locator", "Hospitals nearby"),
        (720, 300, 990, 500, "#1E3A8A", "DriveLegal", "MV Act challans"),
        (1040, 300, 1200, 500, "#3B0764", "AI", "RAG assistant"),
    ]
    for x1, y1, x2, y2, color, title, subtitle in cards:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=color, outline="#334155", width=2)
        draw.text((x1 + 28, y1 + 45), title, fill="#FFFFFF", font=font_med)
        draw.text((x1 + 28, y1 + 105), subtitle, fill="#CBD5E1", font=font_small)

    draw.rounded_rectangle((80, 585, 1200, 650), radius=20, fill="#111827", outline="#1A5C38", width=2)
    draw.text(
        (115, 603),
        "Offline-ready PWA with SOS queue, share target, shortcuts, and first-aid cache",
        fill="#00C896",
        font=font_small,
    )
    canvas.save(SCREENSHOTS / "dashboard.png", optimize=True)


if __name__ == "__main__":
    generate_icons()
    generate_dashboard_screenshot()
    print("Generated PWA icons and dashboard screenshot.")
