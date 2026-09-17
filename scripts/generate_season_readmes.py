#!/usr/bin/env python3
"""Generate the same README structure for every archived TFT season."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEASONS = ROOT / "seasons"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def season_key(path: Path):
    match = re.fullmatch(r"s(\d+)(?:\.(\d+))?", path.name)
    return tuple(int(value or 0) for value in match.groups()) if match else (999, 0)


def hex_count(raw: dict) -> int:
    values = raw.get("hex", [])
    if (
        isinstance(values, list)
        and len(values) == 5
        and isinstance(values[4], dict)
    ):
        return len(values[4])
    return len(values)


def image_count(season_dir: Path) -> int:
    image_dir = season_dir / "tft_images"
    return sum(1 for path in image_dir.rglob("*") if path.is_file())


def command_for(season_dir: Path) -> str:
    if (season_dir / "season_config.json").exists():
        return "python main.py --workers 24"
    if season_dir.name in {"s16", "s17", "s18"}:
        return f"python main.py --season {season_dir.name}"
    return "python main.py"


def create_readme(season_dir: Path) -> None:
    raw = read_json(season_dir / "tft_data" / "tft_raw_data.json")
    processed = read_json(season_dir / "tft_data" / "tft_processed_data.json")
    config = raw["version_config"]
    season, title = config["赛季名称"].split("-", 1)
    error_path = season_dir / "tft_data" / "image_download_errors.json"
    errors = read_json(error_path) if error_path.exists() else None
    source = (
        "腾讯官方历史静态接口恢复"
        if (season_dir / "season_config.json").exists()
        else "仓库历史赛季快照"
    )
    error_value = str(len(errors)) if errors is not None else "未单独审计"
    note = config.get("强化符文说明")
    note_block = f"\n> 强化符文说明：{note}\n" if note else ""
    optional_files = []
    if error_path.exists():
        optional_files.append("- 图片错误审计：`tft_data/image_download_errors.json`")
    if (season_dir / "season_config.json").exists():
        optional_files.append("- 历史接口配置：`season_config.json`")
    optional_block = "\n".join(optional_files)
    if optional_block:
        optional_block += "\n"

    text = f"""# TFT_Spider — {season.upper()} {title}

{source}。数据版本 `{config['版本信息']}`，快照日期 `{config['爬取日期']}`。
{note_block}
<img src="readme_images/tft_web.png" width="70%" alt="{season.upper()} 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | {len(processed['chess_name_info'])} |
| 种族羁绊 | {len(raw['race'])} |
| 职业羁绊 | {len(raw['job'])} |
| 装备 | {len(raw['equip'])} |
| 强化符文 | {hex_count(raw)} |
| 已归档图片 | {image_count(season_dir)} |
| 官方失效图片链接 | {error_value} |

## 目录

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
{optional_block}- 图片目录：`tft_images/`
- README 图片生成器：`scripts/generate_readme_images.py`

## 使用

```bash
pip install -r requirements.txt
{command_for(season_dir)}
python scripts/generate_readme_images.py --season {season}
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
"""
    (season_dir / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", action="append", help="只生成指定赛季")
    args = parser.parse_args()
    selected = {value.lower() for value in args.season or []}
    season_dirs = sorted(
        (path for path in SEASONS.iterdir() if path.is_dir()), key=season_key
    )
    for season_dir in season_dirs:
        if selected and season_dir.name.lower() not in selected:
            continue
        create_readme(season_dir)
        print(f"generated {season_dir / 'README.md'}")


if __name__ == "__main__":
    main()
