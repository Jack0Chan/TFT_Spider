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
IMAGE_TEMPLATE = SEASONS / "s18" / "scripts" / "generate_readme_images.py"
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


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_readme(destination: Path, config: dict) -> None:
    raw = read_json(destination / "tft_data" / "tft_raw_data.json")
    errors = read_json(destination / "tft_data" / "image_download_errors.json")
    counts = {key: len(raw[key]) for key in ("chess", "race", "job", "equip", "hex")}
    note = config.get("hex_note")
    note_block = f"\n> 强化符文：{note}\n" if note else ""
    text = f"""# TFT_Spider — {config['season'].upper()} {config['title']}

腾讯官方历史版本 `{config['archive_path']}` 的自包含恢复快照，数据版本
`{config['version']}`，于 `{config['restored_at']}` 恢复并校验。
{note_block}
<img src="readme_images/tft_web.png" width="70%">

## 内容

| 类型 | 数量 |
| --- | ---: |
| 棋子 | {counts['chess']} |
| 种族羁绊 | {counts['race']} |
| 职业羁绊 | {counts['job']} |
| 装备 | {counts['equip']} |
| 强化符文 | {counts['hex']} |
| 官方失效图片链接 | {len(errors)} |

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
- 图片错误审计：`tft_data/image_download_errors.json`
- 图片目录：`tft_images/`

## 重新构建

```bash
pip install -r requirements.txt
python main.py --workers 24
python scripts/generate_readme_images.py --season {config['season']}
```

数据来源：[腾讯官方云顶之弈历史静态资源](https://game.gtimg.cn/)

<img src="readme_images/terminal.png" width="60%">
"""
    write_text(destination / "README.md", text)


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


def patch_image_generator(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '("强化符文", len(raw["hex"][4]))',
        '("强化符文", len(raw["hex"]))',
    )
    text = text.replace('"分支独立归档"', '"目录独立归档"')
    text = text.replace(
        'f"$ python main.py --season {season.lower()} --workers 12"',
        'f"$ python main.py --workers 24"',
    )
    text = text.replace(
        'eligible.sort(key=lambda item: (int(item["price"]), int(item.get("TFTID", 0))))',
        'eligible.sort(key=lambda item: (int(item["price"]), str(item.get("TFTID") or item.get("chessId") or "")))',
    )
    text = text.replace(
        'matches = sorted((IMAGE_DIR / "chess").glob(f"{tft_id}-*"))\n'
        '    return matches[0] if matches else None',
        'matches = sorted((IMAGE_DIR / "chess").glob(f"{tft_id}-*"))\n'
        '    if not matches:\n'
        '        matches = sorted((IMAGE_DIR / "skill").glob(f"{tft_id}-*"))\n'
        '    return matches[0] if matches else None',
    )
    path.write_text(text, encoding="utf-8")


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
        patch_image_generator(destination / "scripts" / "generate_readme_images.py")
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
        make_readme(destination, config)


if __name__ == "__main__":
    main()
