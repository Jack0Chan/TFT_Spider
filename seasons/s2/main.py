#!/usr/bin/env python3
"""Rebuild one archived TFT season from its pinned Tencent endpoints."""

from __future__ import annotations

import argparse
import io
import json
import os
import pprint
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image


ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "season_config.json"
DATA_DIR = ROOT / "tft_data"
IMAGE_DIR = ROOT / "tft_images"
TIMEOUT = 30


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def fetch_json(url: str):
    last_error = None
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"腾讯数据请求失败（已重试 3 次）：{url}") from last_error


def collect_raw(config: dict) -> dict:
    raw = {
        "version_config": {
            "赛季名称": f"{config['season']}-{config['title']}",
            "版本信息": config["version"],
            "爬取日期": config["restored_at"],
            "归档说明": "从腾讯官方历史版本接口恢复",
            "数据路径": config["archive_path"],
        },
        "chess": [],
        "race": [],
        "job": [],
        "equip": [],
        "hex": [],
    }
    for kind in ("chess", "race", "job", "equip"):
        url = config["urls"][kind]
        raw["version_config"][f"url_{kind}_data"] = url
        payload = fetch_json(url)
        raw[kind] = payload["data"]
    hex_url = config["urls"].get("hex")
    if hex_url:
        raw["version_config"]["url_hex_data"] = hex_url
        payload = fetch_json(hex_url)
        raw["hex"] = list(payload.values()) if isinstance(payload, dict) else payload
    else:
        raw["version_config"]["url_hex_data"] = None
        raw["version_config"]["强化符文说明"] = config.get(
            "hex_note", "该赛季没有强化符文系统"
        )
    write_json(DATA_DIR / "tft_raw_data.json", raw)
    return raw


def split_values(value) -> set[str]:
    if value is None:
        return set()
    return {item.strip() for item in str(value).split(",") if item.strip()}


def match_traits(raw: dict, trait_kind: str, id_key: str, names_key: str) -> dict:
    result = {}
    for trait in raw[trait_kind]:
        name = trait.get("name", "")
        trait_id = str(trait.get(id_key, ""))
        members = []
        for chess in raw["chess"]:
            ids = split_values(chess.get(f"{trait_kind}Ids"))
            names = split_values(chess.get(names_key))
            if trait_id in ids or name in names:
                members.append(chess.get("displayName", ""))
        result[name] = members
    return result


def process_raw(raw: dict) -> dict:
    race_chess = match_traits(raw, "race", "raceId", "races")
    job_chess = match_traits(raw, "job", "jobId", "jobs")
    prices = {}
    for chess in raw["chess"]:
        prices.setdefault(str(chess.get("price", "")), []).append(
            chess.get("displayName", "")
        )
    processed = {
        "all_chess_name": "-".join(x.get("displayName", "") for x in raw["chess"]),
        "all_race_name": "-".join(x.get("name", "") for x in raw["race"]),
        "all_job_name": "-".join(x.get("name", "") for x in raw["job"]),
        "job_chess": job_chess,
        "race_chess": race_chess,
        "price_chess": dict(sorted(prices.items())),
        "chess_name_info": {
            x.get("displayName", ""): x for x in raw["chess"] if x.get("displayName")
        },
    }
    write_json(DATA_DIR / "tft_processed_data.json", processed)
    write_tft_class(raw, processed)
    return processed


def write_tft_class(raw: dict, processed: dict) -> None:
    simplified = {}
    for name, info in processed["chess_name_info"].items():
        simplified[name] = {
            "name": name,
            "jobs": [k for k, values in processed["job_chess"].items() if name in values],
            "races": [k for k, values in processed["race_chess"].items() if name in values],
            "price": info.get("price"),
            "gui_name": f"{info.get('price')}-{name}",
            "gui_checkbox_key": f"checkbox_{name}",
            "gui_combo_num_key": f"combo_num_{name}",
        }
    attrs = {
        "version_config": raw["version_config"],
        "all_chess_name_str": processed["all_chess_name"],
        "all_race_name_str": processed["all_race_name"],
        "all_job_name_str": processed["all_job_name"],
        "race_chess": processed["race_chess"],
        "job_chess": processed["job_chess"],
        "price_chess": processed["price_chess"],
        "chess_name_info": simplified,
    }
    lines = [
        '"""Generated, immutable convenience view of this season archive."""',
        "",
        "class TFTData:",
        "    _instance = None",
        "",
        "    def __new__(cls):",
        "        if cls._instance is None:",
        "            cls._instance = super().__new__(cls)",
        "        return cls._instance",
        "",
    ]
    for key, value in attrs.items():
        lines.append(f"    {key} = {pprint.pformat(value, width=100, sort_dicts=False)}")
        lines.append("")
    (DATA_DIR / "TFTData.py").write_text("\n".join(lines), encoding="utf-8")


def safe_name(value) -> str:
    text = str(value or "unnamed").strip()
    text = re.sub(r"[\\/:*?\"<>|\r\n]+", "_", text)
    return text[:120] or "unnamed"


def image_jobs(raw: dict):
    for chess in raw["chess"]:
        tft_id = chess.get("TFTID") or chess.get("chessId")
        title = safe_name(chess.get("title"))
        name = safe_name(chess.get("displayName"))
        yield (
            "chess",
            IMAGE_DIR / "chess" / f"{tft_id}-{title}-{name}.jpg",
            # Many old originalImage values point to 64x64 skill icons.  The
            # cham-icons endpoint is the official 624x318 champion card art.
            f"https://game.gtimg.cn/images/lol/tft/cham-icons/624x318/{tft_id}.jpg",
        )
        if chess.get("skillImage"):
            skill = safe_name(chess.get("skillName"))
            yield (
                "skill",
                IMAGE_DIR / "skill" / f"{tft_id}-{title}-{name}-{skill}.jpg",
                chess["skillImage"],
            )
    for equip in raw["equip"]:
        if equip.get("imagePath"):
            tft_id = equip.get("TFTID") or equip.get("equipId")
            yield (
                "equip",
                IMAGE_DIR / "equip" / f"{tft_id}-{safe_name(equip.get('name'))}.png",
                equip["imagePath"],
            )
    for item in raw["hex"]:
        if item.get("imgUrl"):
            hex_id = item.get("hexId") or item.get("id")
            yield (
                "hex",
                IMAGE_DIR / "hex" / f"{hex_id}-{safe_name(item.get('name'))}.png",
                item["imgUrl"],
            )


def valid_image(content: bytes) -> None:
    with Image.open(io.BytesIO(content)) as image:
        image.verify()


def download_one(job: tuple[str, Path, str]):
    kind, path, url = job
    try:
        if path.exists():
            valid_image(path.read_bytes())
            return None
        response = requests.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 TFT_Spider historical archive"},
        )
        response.raise_for_status()
        valid_image(response.content)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".part")
        temp.write_bytes(response.content)
        os.replace(temp, path)
        return None
    except Exception as exc:  # keep a complete audit instead of fake image files
        return {
            "kind": kind,
            "path": str(path.relative_to(ROOT)),
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def download_images(raw: dict, workers: int) -> list[dict]:
    jobs = list(image_jobs(raw))
    errors = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_one, job) for job in jobs]
        for index, future in enumerate(as_completed(futures), 1):
            error = future.result()
            if error:
                errors.append(error)
            if index % 250 == 0 or index == len(futures):
                print(f"images {index}/{len(futures)}; errors {len(errors)}", flush=True)
    errors.sort(key=lambda item: (item["kind"], item["path"]))
    write_json(DATA_DIR / "image_download_errors.json", errors)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="Use the archived JSON and only download missing images",
    )
    args = parser.parse_args()
    if args.images_only:
        raw = read_json(DATA_DIR / "tft_raw_data.json")
        errors = download_images(raw, max(1, args.workers))
        print(f"image errors: {len(errors)}")
        return
    config = read_json(CONFIG_FILE)
    print(f"rebuilding {config['season']} {config['title']} ({config['version']})")
    raw = collect_raw(config)
    process_raw(raw)
    if not args.skip_images:
        errors = download_images(raw, max(1, args.workers))
        print(f"image errors: {len(errors)}")
    print("done")


if __name__ == "__main__":
    main()
