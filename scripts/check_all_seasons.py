#!/usr/bin/env python3
"""Run a read-only smoke test for every archived season."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SEASONS = ROOT / "seasons"
RAW_KEYS = {"version_config", "chess", "race", "job", "equip", "hex"}
PROCESSED_KEYS = {
    "all_chess_name",
    "all_race_name",
    "all_job_name",
    "job_chess",
    "race_chess",
    "price_chess",
    "chess_name_info",
}


def season_key(path: Path):
    match = re.fullmatch(r"s(\d+)(?:\.(\d+))?", path.name)
    if not match:
        return (999, 0)
    return tuple(int(value or 0) for value in match.groups())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compile_python(path: Path) -> None:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def run_help(path: Path, cwd: Path) -> None:
    subprocess.run(
        [sys.executable, str(path), "--help"],
        cwd=cwd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def verify_image(path: Path) -> None:
    with Image.open(path) as image:
        image.verify()


def check_season(season_dir: Path, full_images: bool) -> tuple[int, int]:
    required = (
        season_dir / "main.py",
        season_dir / "requirements.txt",
        season_dir / "README.md",
        season_dir / "tft_web.png",
        season_dir / "tft_data" / "tft_raw_data.json",
        season_dir / "tft_data" / "tft_processed_data.json",
        season_dir / "tft_data" / "TFTData.py",
        season_dir / "scripts" / "generate_readme_images.py",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"缺少文件：{', '.join(missing)}")

    raw = load_json(required[4])
    processed = load_json(required[5])
    if not RAW_KEYS.issubset(raw):
        raise RuntimeError(f"原始数据缺少字段：{sorted(RAW_KEYS - raw.keys())}")
    if not PROCESSED_KEYS.issubset(processed):
        raise RuntimeError(
            f"处理数据缺少字段：{sorted(PROCESSED_KEYS - processed.keys())}"
        )
    actual = raw["version_config"]["赛季名称"].split("-", 1)[0].lower()
    if actual != season_dir.name.lower():
        raise RuntimeError(f"目录为 {season_dir.name}，数据却是 {actual}")
    if not processed["chess_name_info"]:
        raise RuntimeError("处理后的棋子数据为空")

    for path in season_dir.rglob("*.py"):
        compile_python(path)
    run_help(season_dir / "main.py", season_dir)
    run_help(season_dir / "scripts" / "generate_readme_images.py", season_dir)

    verify_image(season_dir / "tft_web.png")
    image_files = [path for path in (season_dir / "tft_images").rglob("*") if path.is_file()]
    if not image_files:
        raise RuntimeError("图片归档为空")
    if full_images:
        for path in image_files:
            verify_image(path)
    return len(processed["chess_name_info"]), len(image_files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="只校验 README 图片，不逐张解码完整图片归档",
    )
    args = parser.parse_args()
    season_dirs = sorted(
        (path for path in SEASONS.iterdir() if path.is_dir()), key=season_key
    )
    if len(season_dirs) != 25:
        raise SystemExit(f"应有 25 个赛季目录，实际为 {len(season_dirs)}")

    for season_dir in season_dirs:
        try:
            chess_count, image_count = check_season(season_dir, not args.quick)
        except Exception as exc:
            raise SystemExit(f"FAIL {season_dir.name}: {exc}") from exc
        print(f"PASS {season_dir.name:<5} 棋子 {chess_count:>3}  图片 {image_count:>4}")
    print(f"全部通过：{len(season_dirs)} 个赛季")


if __name__ == "__main__":
    main()
