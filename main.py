# -*- coding: utf-8 -*-
"""Download and process Teamfight Tactics data published by Tencent."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from rich.progress import track

ROOT_DIR = Path(__file__).resolve().parent
TFT_DATA_DIR = ROOT_DIR / "tft_data"
TFT_RAW_DATA_FILE = TFT_DATA_DIR / "tft_raw_data.json"
TFT_PROCESSED_DATA_FILE = TFT_DATA_DIR / "tft_processed_data.json"
TFT_PY_CLASS_FILE = TFT_DATA_DIR / "TFTData.py"
TFT_IMG_FILE = ROOT_DIR / "tft_images"
VERSION_CONFIG_URL = "https://game.gtimg.cn/images/lol/tfth5lib/v1/versionconfig.json"

CORE_URLS = {
    "chess": "urlChessData", "race": "urlRaceData", "job": "urlJobData",
    "equip": "urlEquipData", "hex": "urlBuffData",
}
EXTRA_URLS = {
    "powerup": "urlPowerupData", "task": "urlTaskData",
    "bless": "urlBlessData", "elf": "urlElfData",
}
IMAGE_EXT = {"s16": "jpg", "s17": "png", "s18": "png"}
CURRENT_CORE_URLS = {
    "chess": "https://game.gtimg.cn/images/lol/act/img/tft/js/chess.js",
    "race": "https://game.gtimg.cn/images/lol/act/img/tft/js/race.js",
    "job": "https://game.gtimg.cn/images/lol/act/img/tft/js/job.js",
    "equip": "https://game.gtimg.cn/images/lol/act/img/tft/js/equip.js",
    "hex": "https://game.gtimg.cn/images/lol/act/img/tft/js/hex.js",
}
CHESS_PREFIXES = {
    "s16": ("TFT16_",), "s17": ("TFT17_",),
    "s18": ("DA_18_", "TFT18_"),
}


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def save_json(data, filename, indent=4):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=indent)


def safe_name(value):
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", str(value or ""))
    return re.sub(r"\s+", " ", text).strip(" .-") or "unnamed"


def price_key(value):
    try:
        return 0, int(value)
    except (TypeError, ValueError):
        return 1, value


def select_season_chess(raw_data, season):
    chess = raw_data.get("chess", [])
    prefixes = CHESS_PREFIXES.get(season, ())
    selected = [
        item for item in chess
        if str(item.get("hero_EN_name", "")).startswith(prefixes)
    ]
    return selected or chess


class RawDataCollector:
    """Collect one explicitly selected TFT set from the official data feed."""

    def __init__(self, season="s18", timeout=20):
        self.season = "s18" if season.lower() == "current" else season.lower()
        self.timeout = timeout
        self._cache = {}
        self.data_urls = {}
        self.fallback_data_urls = {}
        self.image_errors = []
        self.version_config = self._get_version_info()
        self.raw_data = {"version_config": self.version_config}
        self._collect_raw_data()

    def _request_json(self, url):
        url = url.strip()
        if url not in self._cache:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            self._cache[url] = response.json()
        return self._cache[url]

    def _get_version_info(self):
        response = requests.get(VERSION_CONFIG_URL, timeout=self.timeout)
        response.raise_for_status()
        configs = response.json()
        selected = next(
            (x for x in configs if str(x.get("idSeason", "")).lower() == self.season),
            None,
        )
        if selected is None:
            available = ", ".join(str(x.get("idSeason")) for x in configs)
            raise ValueError(f"找不到赛季 {self.season}；官方提供：{available}")

        for kind, key in {**CORE_URLS, **EXTRA_URLS}.items():
            if selected.get(key):
                self.data_urls[kind] = str(selected[key]).strip()
        self.fallback_data_urls = dict(self.data_urls)

        # The catalogue retains the S18 launch snapshot for stable historical
        # URLs, while the unversioned official endpoints receive live patches.
        # Prefer them only after confirming that they still identify as S18.
        if self.season == "s18":
            current_race = self._request_json(CURRENT_CORE_URLS["race"])
            if str(current_race.get("season", "")).upper().endswith(".S18"):
                self.data_urls.update(CURRENT_CORE_URLS)
        race_payload = self._request_json(self.data_urls["race"])
        version = race_payload.get("version") or selected["arrVersionLimit"][0]
        return {
            "赛季名称": f"{self.season}-{selected['stringName']}",
            "版本信息": version,
            "爬取日期": f"{datetime.date.today()}",
            "数据赛季": race_payload.get("season", ""),
            "版本配置来源": VERSION_CONFIG_URL,
            **{f"url_{kind}_data": url for kind, url in self.data_urls.items()},
        }

    def _collect_raw_data(self):
        for kind in ("chess", "race", "job", "equip"):
            payload = self._request_json(self.data_urls[kind])
            if not isinstance(payload, dict) or "data" not in payload:
                raise ValueError(f"{kind} 官方数据结构异常")
            self.raw_data[kind] = payload["data"]

        payload = self._request_json(self.data_urls["hex"])
        if not isinstance(payload, dict):
            raise ValueError("hex 官方数据结构异常")
        # Preserve the raw schema used by previous branches: metadata fields
        # followed by the augment dictionary as the fifth list member.
        self.raw_data["hex"] = list(payload.values())

        for kind in EXTRA_URLS:
            if kind not in self.data_urls:
                continue
            payload = self._request_json(self.data_urls[kind])
            if kind in {"powerup", "bless"} and isinstance(payload, dict):
                payload = payload.get("data", payload)
            self.raw_data[kind] = payload
        self.save_tft_raw_data()

    def save_tft_raw_data(self):
        save_json(self.raw_data, TFT_RAW_DATA_FILE)

    @staticmethod
    def _hex_items(raw_hex):
        if isinstance(raw_hex, list):
            if len(raw_hex) >= 5 and isinstance(raw_hex[4], dict):
                return list(raw_hex[4].values())
            if all(isinstance(item, dict) for item in raw_hex):
                return raw_hex
        return list(raw_hex.values()) if isinstance(raw_hex, dict) else []

    @staticmethod
    def _urls(*values):
        result = []
        for value in values:
            if not value:
                continue
            url = str(value).strip()
            if url.startswith("//"):
                url = "https:" + url
            if url.startswith(("https://", "http://")) and url not in result:
                result.append(url)
        return result

    def _download_image(self, path, urls):
        if path.exists():
            return
        headers = {"user-agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/124 Safari/537.36"}
        last_error = None
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                if not response.content or response.content.lstrip().startswith(b"<html"):
                    raise ValueError("返回内容不是图片")
                path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = path.with_suffix(path.suffix + ".part")
                with open(temp_path, "wb") as file_obj:
                    file_obj.write(response.content)
                os.replace(temp_path, path)
                return
            except (requests.RequestException, OSError, ValueError) as exc:
                last_error = exc
        raise RuntimeError(f"{path.name}: {last_error}")

    def _download_tasks(self, tasks, description, workers):
        tasks = [(path, urls) for path, urls in tasks if urls]
        errors = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._download_image, path, urls): path
                for path, urls in tasks
            }
            for future in track(as_completed(futures), total=len(futures), description=description):
                try:
                    future.result()
                except Exception as exc:
                    errors.append(str(exc))
        if errors:
            self.image_errors.extend(
                {"category": description, "error": error} for error in errors
            )
            print(f"警告：{description}有 {len(errors)} 个官方图片 URL 不可用")

    def download_chess_imgs(self, workers=12):
        ext = IMAGE_EXT.get(self.season, "jpg")
        tasks = []
        for chess in select_season_chess(self.raw_data, self.season):
            tft_id = chess.get("TFTID")
            if not tft_id:
                continue
            # Some summoned placeholders (for example TFT16_MalzaharVoidling)
            # are present in the data feed but Tencent publishes no image for
            # them in either the store or the record itself.
            if (
                str(chess.get("price")) == "11"
                and not chess.get("originalImage")
                and not chess.get("skillImage")
            ):
                continue
            title = safe_name(chess.get("title"))
            title = "" if title == "unnamed" else title
            filename = f"{tft_id}-{title}-{safe_name(chess.get('displayName'))}.{ext}"
            splash = (
                f"https://game.gtimg.cn/images/lol/tftstore/{self.season}/"
                f"624x318/{tft_id}.{ext}"
            )
            tasks.append((
                TFT_IMG_FILE / "chess" / filename,
                self._urls(splash, chess.get("originalImage"), chess.get("skillImage")),
            ))
        self._download_tasks(tasks, "正在下载棋子图片", workers)

    def download_skill_imgs(self, workers=12):
        tasks = []
        fallback = {}
        old_url = self.fallback_data_urls.get("chess")
        if old_url and old_url != self.data_urls.get("chess"):
            old_payload = self._request_json(old_url)
            fallback = {
                str(item.get("hero_EN_name")): item
                for item in old_payload.get("data", [])
            }
        for chess in select_season_chess(self.raw_data, self.season):
            if not chess.get("skillImage"):
                continue
            parts = (
                chess.get("TFTID", "unknown"), chess.get("title"),
                chess.get("displayName"), chess.get("skillName"),
            )
            filename = "-".join(safe_name(part) for part in parts) + ".jpg"
            old = fallback.get(str(chess.get("hero_EN_name")), {})
            urls = self._urls(
                chess["skillImage"], old.get("skillImage"), old.get("originalImage")
            )
            tasks.append((TFT_IMG_FILE / "skill" / filename, urls))
        self._download_tasks(tasks, "正在下载技能图片", workers)

    def download_hex_imgs(self, workers=12):
        tasks = []
        for item in self._hex_items(self.raw_data.get("hex")):
            filename = (
                f"{safe_name(item.get('hexId') or item.get('id'))}-"
                f"{safe_name(item.get('name'))}.jpg"
            )
            tasks.append((TFT_IMG_FILE / "hex" / filename, self._urls(item.get("imgUrl"), item.get("icon"))))
        self._download_tasks(tasks, "正在下载强化符文图片", workers)

    def download_equipment_imgs(self, workers=12):
        tasks = []
        fallback = {}
        old_url = self.fallback_data_urls.get("equip")
        if old_url and old_url != self.data_urls.get("equip"):
            old_payload = self._request_json(old_url)
            fallback = {
                str(item.get("TFTID") or item.get("equipId")): item
                for item in old_payload.get("data", [])
            }
        for item in self.raw_data.get("equip", []):
            item_id = str(item.get("TFTID") or item.get("equipId"))
            filename = (
                f"{safe_name(item_id)}-"
                f"{safe_name(item.get('name'))}.jpg"
            )
            old = fallback.get(item_id, {})
            tasks.append((
                TFT_IMG_FILE / "equip" / filename,
                self._urls(item.get("imagePath"), old.get("imagePath")),
            ))
        self._download_tasks(tasks, "正在下载装备图片", workers)

    def download_extra_imgs(self, workers=12):
        specs = []
        powerup = self.raw_data.get("powerup")
        if isinstance(powerup, dict):
            specs.append(("powerup", list(powerup.values()), "id", "title", "imageUrl"))
        elif isinstance(powerup, list):
            specs.append(("powerup", powerup, "id", "title", "imageUrl"))
        if isinstance(self.raw_data.get("task"), list):
            specs.append(("task", self.raw_data["task"], "apiname", "Name", "img"))
        if isinstance(self.raw_data.get("bless"), list):
            specs.append(("bless", self.raw_data["bless"], "id", "blessingName", "blessingIconDetail"))
        elf = self.raw_data.get("elf")
        if isinstance(elf, dict) and isinstance(elf.get("wisps"), list):
            specs.append(("elf", elf["wisps"], "adventureId", "name_cn", "icon_url"))

        for dirname, items, id_key, name_key, url_key in specs:
            tasks = []
            for item in items:
                filename = f"{safe_name(item.get(id_key))}-{safe_name(item.get(name_key))}.jpg"
                urls = self._urls(item.get(url_key), item.get("blessingIcon"), item.get("imageUrl"))
                tasks.append((TFT_IMG_FILE / dirname / filename, urls))
            self._download_tasks(tasks, f"正在下载 {dirname} 图片", workers)

    def download_all_imgs(self, workers=12):
        self.download_chess_imgs(workers)
        self.download_skill_imgs(workers)
        self.download_hex_imgs(workers)
        self.download_equipment_imgs(workers)
        self.download_extra_imgs(workers)
        save_json(self.image_errors, TFT_DATA_DIR / "image_download_errors.json")


class TFTDataProcessor:
    def __init__(self):
        self.raw_data = load_json(TFT_RAW_DATA_FILE)
        name = self.raw_data.get("version_config", {}).get("赛季名称", "")
        self.season = str(name).split("-", 1)[0].lower()
        self.processed_data = {
            "all_chess_name": "", "all_race_name": "", "all_job_name": "",
            "job_chess": {}, "race_chess": {}, "price_chess": {},
            "chess_name_info": {},
        }
        self._process_data()

    def _chess(self):
        return select_season_chess(self.raw_data, self.season)

    def _match_traits(self, kind, id_key, chess_id_key, output_key):
        chess_data = self._chess()
        result = {}
        for trait in self.raw_data[kind]:
            trait_id = str(trait[id_key])
            result[trait["name"]] = [
                chess["displayName"] for chess in chess_data
                if trait_id in str(chess.get(chess_id_key, "")).split(",")
            ]
        self.processed_data[output_key] = result

    def _process_data(self):
        self._match_traits("job", "jobId", "jobIds", "job_chess")
        self._match_traits("race", "raceId", "raceIds", "race_chess")
        prices = {}
        for chess in self._chess():
            prices.setdefault(str(chess.get("price", "")), []).append(chess["displayName"])
        self.processed_data["price_chess"] = dict(
            sorted(prices.items(), key=lambda item: price_key(item[0]))
        )
        self.processed_data["all_chess_name"] = "-".join(x["displayName"] for x in self._chess())
        self.processed_data["all_race_name"] = "-".join(x["name"] for x in self.raw_data["race"])
        self.processed_data["all_job_name"] = "-".join(x["name"] for x in self.raw_data["job"])
        self.processed_data["chess_name_info"] = {x["displayName"]: x for x in self._chess()}
        self.save_tft_processed_data()

    def save_tft_processed_data(self):
        save_json(self.processed_data, TFT_PROCESSED_DATA_FILE)

    def save_py_class(self):
        simple = {}
        for key, value in self.processed_data["chess_name_info"].items():
            jobs = [k for k, names in self.processed_data["job_chess"].items() if key in names]
            races = [k for k, names in self.processed_data["race_chess"].items() if key in names]
            price = value.get("price", "")
            simple[key] = {
                "name": key, "jobs": jobs, "races": races, "price": price,
                "gui_name": f"{price}-{value['displayName']}",
                "gui_checkbox_key": f"checkbox_{key}",
                "gui_combo_num_key": f"combo_num_{key}",
            }
        result = f'''class TFTData:
    _instance = None
    _is_first_init = True

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_first_init:
            return
        self._is_first_init = False
        self.version_config = {self.raw_data['version_config']!r}
        self.all_chess_name_str = {self.processed_data['all_chess_name']!r}
        self.all_race_name_str = {self.processed_data['all_race_name']!r}
        self.all_job_name_str = {self.processed_data['all_job_name']!r}
        self.race_chess = {self.processed_data['race_chess']!r}
        self.job_chess = {self.processed_data['job_chess']!r}
        self.price_chess = {self.processed_data['price_chess']!r}
        self.chess_name_info = {simple!r}
'''
        TFT_PY_CLASS_FILE.write_text(result.replace("菈", "拉"), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="下载腾讯官方云顶之弈赛季数据")
    parser.add_argument("--season", default="s18", choices=("s16", "s17", "s18", "current"))
    parser.add_argument("--workers", type=int, default=12, help="并行图片下载线程数")
    parser.add_argument("--skip-images", action="store_true", help="只刷新数据文件")
    return parser.parse_args()


def main():
    args = parse_args()
    collector = RawDataCollector(args.season)
    print(f"原始数据已保存：{TFT_RAW_DATA_FILE}")
    if not args.skip_images:
        collector.download_all_imgs(max(1, args.workers))
        print(f"图片已保存：{TFT_IMG_FILE}")
    processor = TFTDataProcessor()
    processor.save_py_class()
    print(f"处理后数据已保存：{TFT_PROCESSED_DATA_FILE}")
    print(f"Singleton 已保存：{TFT_PY_CLASS_FILE}")


if __name__ == "__main__":
    main()
