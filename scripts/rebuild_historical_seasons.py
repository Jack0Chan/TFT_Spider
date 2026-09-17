#!/usr/bin/env python3
"""Create self-contained official-data archives for TFT S1 through S9.5."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEASONS = ROOT / "seasons"
TEMPLATE = ROOT / "scripts" / "historical_season_main.py"
IMAGE_TEMPLATE = ROOT / "scripts" / "generate_readme_images.py"
README_GENERATOR = ROOT / "scripts" / "generate_season_readmes.py"
RESTORED_AT = "2026-09-17"

CONFIGS = (
    ("s1", "初代赛季", "9.21", "9.21-2019.S1", False),
    ("s2", "元素崛起", "9.22", "9.22-2019.S2", False),
    ("s3", "银河战争", "10.6", "10.6-2020.S3", False),
    ("s3.5", "再战星海", "10.12", "10.12-2020.S3", False),
    ("s4", "命运之轮", "10.19", "10.19-2020.S4", False),
    ("s4.5", "瑞兽闹新春", "11.2", "11.2-2021.S4", False),
    ("s5", "光明与黑暗", "11.9", "11.9-2021.S5", False),
    ("s5.5", "英雄之黎明", "11.15", "11.15-2021.S5", False),
    ("s6", "双城之战", "11.22", "11.22-2021.S6", False),
    ("s6.5", "霓虹之夜", "12.4", "12.4-2022.S6", True),
    ("s7", "巨龙之境", "12.11", "12.11-2022.S7", True),
    ("s7.5", "隐秘海域", "12.17", "12.17-2022.S7", True),
    ("s9", "符文大陆传奇", "13.12", "13.12-2023.S9", True),
    ("s9.5", "志在天际", "13.18", "13.18-2023.S9", True),
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def config_for(item) -> dict:
    season, title, version, archive_path, has_hex = item
    base = f"https://game.gtimg.cn/images/lol/act/img/tft/js/{archive_path}"
    urls = {kind: f"{base}/{kind}.js" for kind in ("chess", "race", "job", "equip")}
    if has_hex:
        urls["hex"] = f"{base}/hex.js"
    result = {
        "season": season,
        "title": title,
        "version": version,
        "archive_path": archive_path,
        "restored_at": RESTORED_AT,
        "urls": urls,
    }
    if not has_hex:
        result["hex_note"] = (
            "S1-S5.5 尚未引入强化符文；S6 的腾讯历史强化符文文件未公开保留"
            if season == "s6"
            else "该赛季尚未引入强化符文系统"
        )
    return result


def prepare(destination: Path, config: dict) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE, destination / "main.py")
    shutil.copy2(ROOT / ".gitignore", destination / ".gitignore")
    shutil.copy2(ROOT / "LICENSE", destination / "LICENSE")
    write_text(destination / "requirements.txt", "requests==2.32.3\nPillow==10.3.0\n")
    write_text(
        destination / "season_config.json",
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
    )
    scripts = destination / "scripts"
    scripts.mkdir(exist_ok=True)
    shutil.copy2(IMAGE_TEMPLATE, scripts / "generate_readme_images.py")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--season", action="append", help="Only rebuild this season")
    args = parser.parse_args()
    selected = {item.lower() for item in args.season or []}
    for item in CONFIGS:
        config = config_for(item)
        if selected and config["season"] not in selected:
            continue
        destination = SEASONS / config["season"]
        print(f"\n=== {config['season']} {config['title']} ===", flush=True)
        prepare(destination, config)
        subprocess.run(
            [sys.executable, "main.py", "--workers", str(args.workers)],
            cwd=destination,
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_readme_images.py",
                "--season",
                config["season"],
            ],
            cwd=destination,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(README_GENERATOR), "--season", config["season"]],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
