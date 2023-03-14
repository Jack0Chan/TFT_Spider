"""
爬虫工具，爬取官网的各种信息，包括图片：https://lol.qq.com/tft/
目前包含以下内容：
棋子 chess
海克斯 hex
装备 equipment
种族 race
职业 job
"""

import requests
from multiprocessing.dummy import Process
from multiprocessing import cpu_count
import threading
import datetime
import random
import os
from rich.progress import track
import json


def load_json(filename: str):
    with open(filename, 'r', encoding='utf-8') as load_f:
        return json.load(load_f)


def save_json(data: dict, filename: str):
    with open(filename, 'w', encoding='utf8') as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=4)


class DataCollector:
    def __init__(self, multi_process=True):
        self.multi_process = multi_process
        self.max_num_process = cpu_count()
        self.version_info_dict = {
            "赛季名称": "双城之战",
            "版本信息": "",
            "赛季信息": "",
            "软件更新日期": f"{datetime.date.today().year}年{datetime.date.today().month}月{datetime.date.today().day}日"
        }
        self.data_dict = {"chess": [], "hex": [], "equipment": [], "race": [], "job": []}

        self.__headers = {
            'authority': 'game.gtimg.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        }
        self.__url_dir = {"chess": 'https://game.gtimg.cn/images/lol/act/img/tft/js/chess.js',
                          "hex": 'https://game.gtimg.cn/images/lol/act/img/tft/js/hex.js',
                          "equipment": 'https://game.gtimg.cn/images/lol/act/img/tft/js/equip.js',
                          "race": 'https://game.gtimg.cn/images/lol/act/img/tft/js/race.js',
                          "job": 'https://game.gtimg.cn/images/lol/act/img/tft/js/job.js'}
        requests.packages.urllib3.disable_warnings()

    def use_multi_process(self, option: bool):
        self.multi_process = option

    def __collect_one_list(self, data_kind: str):
        """
        爬取某一种信息，并保存到self.data_dict或self.version_info_dict中
        在self.collect_all_list()调用
        """
        # 如果已经请求过，直接返回
        if self.data_dict[data_kind]:
            return self.data_dict[data_kind]
        # 没有请求过的话，就去请求
        params = {'v': f'{random.randint(10000, 50000)}'}
        response = requests.get(self.__url_dir[data_kind], headers=self.__headers, params=params)
        res = response.json()
        if data_kind == "hex":
            res = [res[key] for key in res]
            self.data_dict[data_kind] = res
            return res
        else:
            self.version_info_dict["版本信息"] = res['version']
            self.version_info_dict["赛季信息"] = res['season']
            res = res['data']
            self.data_dict[data_kind] = res
            return res

    def collect_all_lists(self):
        """
        下载所有的信息，并保存到json和csv文件
        """
        for key in self.data_dict:
            self.data_dict[key] = self.__collect_one_list(data_kind=key)
            save_json(self.data_dict[key], f'{key}.json')
        save_json(self.version_info_dict, 'version_info.json')
        return True

    def __download_one_image_thread(self, img_name: str, img_url: str):
        if os.path.exists(img_name):
            print(f"file_exists: {img_name}")
            pass
        else:
            img_resp = requests.get(img_url, headers=self.__headers)
            if "was not found" in str(img_resp.content):
                # img_resp = requests.get(img_url, verify=False)
                img_resp = requests.get(img_url, headers=self.__headers, verify=False)
            if "was not found" in str(img_resp.content):
                print(img_url)
                print(img_resp.content)
            with open(img_name, mode="wb") as f:
                f.write(img_resp.content)

    def __download_image(self, img_name: str, img_url: str):
        if self.multi_process:
            while threading.active_count() > self.max_num_process:
                pass
            p = Process(target=self.__download_one_image_thread, args=(img_name, img_url))
            p.start()
        else:
            self.__download_one_image_thread(img_name, img_url)

    def download_chess_imgs(self):
        chess_list = load_json('Database/chess.json')
        for champion in track(chess_list, description="正在爬取棋子图片"):
            img_name = f"images/chess{champion['chessId']}.jpg"
            img_url = f"https://game.gtimg.cn/images/lol/tft/cham-icons/624x318/{champion['TFTID']}.jpg"
            self.__download_image(img_name, img_url)

    def download_hex_imgs(self):
        hex_list = load_json('Database/hex.json')
        for hex_info in track(hex_list, description="正在爬取海克斯图片"):
            img_name = f"images/hex{hex_info['hexId']}.png"
            self.__download_image(img_name, hex_info['imgUrl'])

    def download_equipment_imgs(self):
        equip_list = load_json('Database/equipment.json')
        for equip in track(equip_list, description="正在爬取装备图片"):
            img_name = f"images/equipment{equip['equipId']}.png"
            self.__download_image(img_name, equip['imagePath'])


def match_race_chess():
    """
    将race与chess匹配起来,并保存到race_chess.json文件
    """
    race_chess_filename = 'race_chess.json'
    # race_dict = {'全部种族': []}
    race_dict = {}
    race_data = load_json('race.json')
    chess_data = load_json('chess.json')
    for race in race_data:
        # 'raceIds': '9'
        race_id = race['raceId']
        race_name = f"{race_id}-{race['name']}"
        race_dict[race_name] = []
        for chess in chess_data:
            race_ids = chess['raceIds'].split(',')
            if race_id in race_ids:
                race_dict[race_name].append(f"{chess['chessId']}-{chess['displayName']}")
                # race_dict['全部种族'].append(f"{chess['chessId']}-{chess['displayName']}")
    save_json(race_dict, race_chess_filename)


def match_job_chess():
    """
    将job与chess匹配起来,并保存到job_chess.json文件
    """
    job_chess_filename = 'job_chess.json'
    job_dict = {}
    job_data = load_json('job.json')
    chess_data = load_json('chess.json')
    for job in job_data:
        job_id = job['jobId']
        job_name = f"{job['jobId']}-{job['name']}"
        job_dict[job_name] = []
        for chess in chess_data:
            job_ids = chess['jobIds'].split(',')
            if job_id in job_ids:
                job_dict[job_name].append(f"{chess['chessId']}-{chess['displayName']}")
                # job_dict['全部职业'].append(f"{chess['chessId']}-{chess['displayName']}")
    save_json(job_dict, job_chess_filename)


def get_chess_strings():
    """
    获得所有的棋子名字,职业,以及种族.
    组成字符串,方便ocr以后匹配.
    """
    chess_name = [f'{chess["displayName"]}' for chess in load_json('chess.json')]
    race_name = [f'{race["name"]}' for race in load_json('race.json')]
    job_name = [f'{job["name"]}' for job in load_json('job.json')]

    res = {"chess_name": '-'.join(chess_name),
           "race_name": '-'.join(race_name),
           "job_name": '-'.join(job_name)}
    save_json(res, 'chess_strings.json')
    return res


def get_chess_info():
    chess = load_json('chess.json')
    chess_name_info = {}
    for info in chess:
        name = info['displayName']
        chess_name_info[name] = info
    save_json(chess_name_info, 'chess_name_info.json')


def create_database():
    dc = DataCollector()
    dc.collect_all_lists()
    match_race_chess()
    match_job_chess()
    get_chess_strings()
    get_chess_info()
    res = {'version_info': load_json('version_info.json'),
           'race_chess': load_json('race_chess.json'),
           'job_chess': load_json('job_chess.json'),
           'chess_name_info': load_json('chess_name_info.json'),
           'chess_strings': load_json('chess_strings.json')}
    save_json(res, 'Database.json')


def create_py_class():
    js = load_json('Database.json')
    new_chess_name_info = {}
    for key in js['chess_name_info']:
        new_chess_name_info[key] = {
            "price": js['chess_name_info'][key]["price"],
            "chessId": js['chess_name_info'][key]["chessId"],
            "TFTID": js['chess_name_info'][key]["TFTID"]
        }
    js['chess_name_info'] = new_chess_name_info
    res = f"""
class TFTData:
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
        self.version_info = {js['version_info']}
        self.race_chess = {js['race_chess']}
        self.job_chess = {js['job_chess']}
        self.chess_name_info = {js['chess_name_info']}
        self.all_chess_name_str = "{js['chess_strings']['chess_name']}"
        self.all_race_name_str = "{js['chess_strings']['race_name']}"
        self.all_job_name_str = "{js['chess_strings']['job_name']}"
"""
    with open('TFTData.py', 'w', encoding='utf-8') as f:
        f.writelines(res)


if __name__ == '__main__':
    dc = DataCollector()
    
    
    dc.collect_all_lists()
    create_database()
    create_py_class()
    # # 这里我们只下载chess_imgs就可以,其他的目前不需要
    # # 如果下载失败,多跑几次就下载下来了
    dc.download_chess_imgs()
