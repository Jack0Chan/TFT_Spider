#!/usr/bin/env python3
"""Generate one deterministic season overview image from archived TFT data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tft_data"
IMAGE_DIR = ROOT / "tft_images"
README_IMAGE_DIR = ROOT / "readme_images"
FONT_CANDIDATES = (
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
COST_COLORS = {
    1: ("#4b5563", "#d1d5db"),
    2: ("#176b45", "#4ade80"),
    3: ("#185b8d", "#60a5fa"),
    4: ("#71368a", "#d084f5"),
    5: ("#8a6418", "#f6c453"),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def font(size: int):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def fit_text(draw, text, max_width, start_size):
    for size in range(start_size, 13, -1):
        selected = font(size)
        if draw.textbbox((0, 0), text, font=selected)[2] <= max_width:
            return selected
    return font(13)


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = max(0, (resized.width - size[0]) // 2)
    top = max(0, (resized.height - size[1]) // 2)
    return resized.crop((left, top, left + size[0], top + size[1]))


def hex_count(raw: dict) -> int:
    values = raw.get("hex", [])
    if (
        isinstance(values, list)
        and len(values) == 5
        and isinstance(values[4], dict)
    ):
        return len(values[4])
    return len(values)


def season_context():
    raw = read_json(DATA_DIR / "tft_raw_data.json")
    processed = read_json(DATA_DIR / "tft_processed_data.json")
    errors_path = DATA_DIR / "image_download_errors.json"
    errors = read_json(errors_path) if errors_path.exists() else []
    config = raw["version_config"]
    season_full = config["赛季名称"]
    season, title = season_full.split("-", 1)
    image_counts = {
        path.name: sum(1 for item in path.iterdir() if item.is_file())
        for path in sorted(IMAGE_DIR.iterdir())
        if path.is_dir()
    }
    return raw, processed, errors, image_counts, season.upper(), title, config


def choose_champions(processed, count=12):
    eligible = [
        item
        for item in processed["chess_name_info"].values()
        if str(item.get("price")) in {"1", "2", "3", "4", "5"}
        and has_landscape_chess_image(item)
    ]
    eligible.sort(
        key=lambda item: (
            int(item["price"]),
            str(item.get("TFTID") or item.get("chessId") or ""),
        )
    )
    if len(eligible) <= count:
        return eligible
    indexes = [round(i * (len(eligible) - 1) / (count - 1)) for i in range(count)]
    return [eligible[index] for index in indexes]


def trait_map(processed):
    result = {name: [] for name in processed["chess_name_info"]}
    for group in ("race_chess", "job_chess"):
        for trait, names in processed[group].items():
            for name in names:
                if name in result:
                    result[name].append(trait)
    return result


def find_chess_image(champion: dict):
    candidates = [champion.get("TFTID"), champion.get("chessId")]
    for identifier in candidates:
        if identifier is None:
            continue
        matches = sorted((IMAGE_DIR / "chess").glob(f"{identifier}-*"))
        if matches:
            return matches[0]
    return None


def has_landscape_chess_image(champion: dict) -> bool:
    """Reject missing/square assets so skill icons never enter README cards."""
    path = find_chess_image(champion)
    if path is None:
        return False
    try:
        with Image.open(path) as image:
            return image.width / image.height >= 1.3
    except OSError:
        return False


def draw_overview():
    raw, processed, errors, counts, season, title, config = season_context()
    canvas = Image.new("RGB", (2048, 1152), "#151322")
    draw = ImageDraw.Draw(canvas)
    white, muted, green = "#f4f1ff", "#aaa5bd", "#35d47c"

    draw.rectangle((0, 0, 2048, 86), fill="#211d31")
    draw.text((36, 22), "TFT_Spider", font=font(36), fill=white)
    draw.text((1780, 28), "赛季数据快照", font=font(24), fill=muted)

    draw.rectangle((0, 86, 238, 1152), fill="#1d192b")
    draw.text((28, 124), season, font=font(40), fill=green)
    draw.text((28, 180), title, font=fit_text(draw, title, 185, 28), fill=white)
    draw.text((28, 230), f"版本 {config['版本信息']}", font=font(22), fill=muted)
    draw.text((28, 265), config["爬取日期"], font=font(19), fill=muted)
    draw.line((28, 310, 210, 310), fill="#39344c", width=2)

    labels = [
        ("棋子", len(processed["chess_name_info"])),
        ("羁绊", len(raw["race"])),
        ("职业", len(raw["job"])),
        ("装备", len(raw["equip"])),
        ("强化符文", hex_count(raw)),
    ]
    if "task" in raw:
        labels.append(("英雄任务", len(raw["task"])))
    if "bless" in raw:
        labels.append(("神祇祝福", len(raw["bless"])))
    if "elf" in raw:
        labels.append(("仙灵 Wisp", len(raw["elf"].get("wisps", []))))
    y = 344
    for label, value in labels:
        draw.text((28, y), label, font=font(20), fill=muted)
        draw.text((182, y), str(value), font=font(20), fill=green, anchor="ra")
        y += 46

    draw.text((28, 1040), "腾讯官方数据", font=font(18), fill=muted)
    draw.text((28, 1072), "目录独立归档", font=font(18), fill=muted)

    draw.text((275, 118), f"{season} · {title}", font=font(40), fill=white)
    draw.text(
        (275, 174),
        f"已归档 {sum(counts.values()):,} 张图片  ·  官方不可用链接 {len(errors)} 个",
        font=font(22),
        fill=muted,
    )
    draw.rectangle((275, 218, 1998, 220), fill="#383248")

    traits = trait_map(processed)
    champions = choose_champions(processed)
    card_w, card_h, image_h = 410, 258, 190
    x0, y0, gap_x, gap_y = 275, 246, 22, 22
    for index, champion in enumerate(champions):
        row, col = divmod(index, 4)
        x = x0 + col * (card_w + gap_x)
        y = y0 + row * (card_h + gap_y)
        cost = int(champion["price"])
        card_color, accent_color = COST_COLORS[cost]
        draw.rounded_rectangle(
            (x, y, x + card_w, y + card_h),
            8,
            fill=card_color,
            outline=accent_color,
            width=4,
        )
        image_path = find_chess_image(champion)
        if image_path:
            with Image.open(image_path) as source:
                canvas.paste(cover(source, (card_w - 8, image_h - 4)), (x + 4, y + 4))
        draw.rectangle(
            (x + 4, y + image_h - 45, x + card_w - 4, y + image_h),
            fill="#17131f",
        )
        name = champion["displayName"]
        draw.text(
            (x + 18, y + image_h - 37),
            name,
            font=fit_text(draw, name, 270, 24),
            fill=white,
        )
        draw.text(
            (x + card_w - 18, y + image_h - 37),
            f"{cost} 金币",
            font=font(20),
            fill=accent_color,
            anchor="ra",
        )
        trait_text = " · ".join(traits.get(name, [])[:3]) or "特殊单位"
        draw.text(
            (x + 18, y + image_h + 18),
            trait_text,
            font=fit_text(draw, trait_text, card_w - 36, 19),
            fill=white,
        )

    README_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(README_IMAGE_DIR / "tft_web.png", optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", help="校验当前目录的赛季，例如 s18")
    args = parser.parse_args()
    raw = read_json(DATA_DIR / "tft_raw_data.json")
    actual = raw["version_config"]["赛季名称"].split("-", 1)[0].lower()
    if args.season and args.season.lower() != actual:
        raise SystemExit(f"当前数据是 {actual}，不是 {args.season}")
    draw_overview()
    print(f"generated {README_IMAGE_DIR / 'tft_web.png'}")


if __name__ == "__main__":
    main()
