# -*- coding: utf-8 -*-

"""
爬虫工具，爬取官网的各种信息，包括图片：https://lol.qq.com/tft/
目前包含以下内容：
棋子 chess
海克斯 hex
装备 equipment
种族 race
职业 job
"""
import os
import json
import datetime
from PIL import Image
import io
# 第三方库
import requests
from rich.progress import track

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TFT_RAW_DATA_FILE = os.path.join(ROOT_DIR, 'tft_data')
TFT_RAW_DATA_FILE = os.path.join(TFT_RAW_DATA_FILE, 'tft_raw_data.json')

TFT_PROCESSED_DATA_FILE = os.path.join(ROOT_DIR, 'tft_data')
TFT_PROCESSED_DATA_FILE = os.path.join(TFT_PROCESSED_DATA_FILE, 'tft_processed_data.json')

TFT_PY_CLASS_FILE = os.path.join(ROOT_DIR, 'tft_data')
TFT_PY_CLASS_FILE = os.path.join(TFT_PY_CLASS_FILE, 'TFTData.py')
TFT_IMG_FILE = os.path.join(ROOT_DIR, 'tft_images')


def load_json(filename: str) -> None:
    with open(filename, 'r', encoding='utf-8') as load_f:
        return json.load(load_f)


def save_json(data: dict, filename: str, indent: int = 4) -> None:
    with open(filename, 'w', encoding='utf8') as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=indent)


class RawDataCollector:
    """_summary_
    """

    def __init__(self) -> None:
        # 每个requests请求超时时间(秒)
        self.__time_out: int = 5

        # self.version_info_dict 里的所有信息，包括url
        # 都会通过代码__get_version_info()更新
        self.version_config: dict = {
            "赛季名称": "s8-怪兽来袭",
            "版本信息": "13.5",
            "爬取日期": f"{datetime.date.today()}",
            'url_chess_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/chess.js',
            'url_race_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/race.js',
            'url_job_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/job.js',
            'url_equip_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/equip.js',
            'url_hex_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/hex.js'
        }
        self.__get_version_info()
        self.raw_data: dict = {
            "version_config": self.version_config,
            # 每一个chess例子（list里套的是字典）
            # {"chessId":"1", "title":"黑暗之女", "name":"788.png", "displayName":"安妮", "raceIds":"8108,8105", "jobIds":"8014", "price":"2", "skillName":"爆裂护盾", "skillType":"主动", "skillImage":"https://game.gtimg.cn/images/lol/act/img/tft/champions/annie-burst-shield.png", "skillIntroduce":"【安妮】用火焰引爆一个锥形区域，对她前方的敌人造成140/210/325魔法伤害，然后给自己生成300/350/425护盾值，持续4秒。", "skillDetail":"【安妮】用火焰引爆一个锥形区域，对她前方的敌人造成140/210/325魔法伤害，然后给自己生成300/350/425护盾值，持续4秒。", "life":"750", "magic":"90", "startMagic":"30", "armor":"40", "spellBlock":"40", "attackMag":"1.5", "attack":"40", "attackSpeed":"0.6", "attackRange":"2", "crit":"25", "originalImage":"upload/img/champions/annie-burst-shield.png", "lifeMag":"1.8", "TFTID":"788", "synergies":"", "illustrate":"", "recEquip":"559,581,597", "proStatus":"最新", "hero_EN_name":"Annie", "races":"福牛守护者,小天才", "jobs":"灵能使", "attackData":"40/60/90", "lifeData":"750/1350/2430"}
            "chess": [],
            # 每一个race例子
            # {"raceId":"8101", "name":"AI程序", "traitId":"8101", "introduce":"【AI程序】在每局游戏中对每个玩家的配置都不同。", "alias":"8101.png", "level":{"2":"初始化【AI程序】的条件和结果]", "4":"[对程序添加另一个结果]", "6":"前几个层级的加成提升200%"},"TFTID":"8101", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/origins/8101.png", "race_color_list":"2:1,4:2,6:3"}
            "race": [],
            # 每一个job例子
            # {"jobId":"8001", "name":"精英战士", "traitId":"8001", "introduce":"这个羁绊仅会在你恰好拥有1个或4个独特的【精英战士】弈子时激活。", "alias":"8001.png", "level":{"1":"处决低于15%生命值的敌人", "4":"处决低于30%生命值的敌人"},"TFTID":"8001", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/classes/8001.png", "job_color_list":"1:1,4:3"}
            "job": [],
            # 每一个equip例子
            # {"equipId":"201", "type":"2", "name":"幽梦之灵", "effect":"携带者也是一名刺客", "keywords":"攻击力，转职，暴击", "formula":"301,308", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/equip/201.png", "TFTID":"2001", "jobId":"3", "raceId":"0", "proStatus":"无", "isShow":"0"}
            "equip": [],
            # 每一个hex例子
            # {"id":"7351", "hexId":"2415", "type":"1", "name":"开摆", "imgUrl":"https://game.gtimg.cn/images/lol/act/img/tft/hex/20220531155500HEX6295c9d41fbf3.PNG", "fetterId":"0", "fetterType":"0", "augments":"TFT7_Augment_AFK", "hero_EN_name":"", "isShow":"1", "hero_enhancement_type":"0", "description":"你在接下来的3回合里无法采取任何行动。在此之后，获得18金币。", "createTime":"2023-03-0815:55:40"}
            "hex": [],
        }
        self.__collect_raw_data()

    def __get_version_info(self) -> None:
        """
        """
        # 获取赛季信息
        url = 'https://lol.qq.com/zmtftzone/public-lib/versionconfig.json'
        response = requests.get(url, timeout=self.__time_out)
        res = response.json()[0]
        # 返回案例，供参考，不使用
        res_example = {
            'booleanPreVersion': False,
            'arrVersionLimit': ['12.23'],
            'stringName': '怪兽来袭',
            'idSeason': 's8',
            'url_chess_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/chess.js',
            'url_race_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/race.js',
            'url_job_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/job.js',
            'url_equip_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/equip.js',
            'url_hex_data': 'https://game.gtimg.cn/images/lol/act/img/tft/js/hex.js'
        }
        # s8-怪兽来袭
        self.version_config["赛季名称"] = f"{res['idSeason']}-{res['stringName']}"
        # 更新url
        self.version_config["url_chess_data"] = res['urlChessData']
        self.version_config["url_race_data"] = res['urlRaceData']
        self.version_config["url_job_data"] = res['urlJobData']
        self.version_config["url_equip_data"] = res['urlEquipData']
        self.version_config["url_hex_data"] = res['urlBuffData']
        # 通过job获取版本信息
        response = requests.get(self.version_config["url_race_data"], timeout=self.__time_out)
        # 13.5
        self.version_config["版本信息"] = response.json()["version"]
        # self.version_config 更新后结果：
        # {'赛季名称': 's8-怪兽来袭', '版本信息': '13.5', '爬取日期': '2023-03-14', xxxx(各种url)}

    def __collect_raw_data(self) -> None:
        """收集raw_data，并保存到 TFT_RAW_DATA_FILE 。
        """
        data_list = ['chess', 'race', 'job', 'equip']
        for data_kind in data_list:
            url = self.version_config[f'url_{data_kind}_data']
            response = requests.get(url, timeout=self.__time_out)
            self.raw_data[data_kind] = response.json()['data']
        # 'hex'特殊处理
        response = requests.get(self.version_config['url_hex_data'], timeout=self.__time_out)
        hex_res = response.json()
        self.raw_data['hex'] = [hex_res[key] for key in hex_res]
        # 保存文件
        save_json(self.raw_data, TFT_RAW_DATA_FILE)

    def save_tft_raw_data(self) -> None:
        save_json(self.raw_data, TFT_RAW_DATA_FILE)

    def __download_image(self, img_name: str, img_url: str):
        headers = {
            'authority': 'game.gtimg.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        }
        if os.path.exists(img_name):
            # print(f"file_exists: {img_name}")
            pass
        else:
            img_resp = requests.get(img_url, headers=headers, timeout=self.__time_out)
            if "was not found" in str(img_resp.content):
                img_resp = requests.get(img_url, headers=headers,
                                        timeout=self.__time_out, verify=False)
            # img = Image.open(io.BytesIO(img_resp.content))
            # img.save(img_name, 'JPEG')
            with open(img_name, mode="wb") as f:
                f.write(img_resp.content)

    def download_chess_imgs(self) -> None:
        chess_list = self.raw_data['chess']
        for chess in track(chess_list, description="正在爬取棋子图片"):
            img_name = f"{TFT_IMG_FILE}/chess/{chess['TFTID']}-{chess['title']}-{chess['displayName']}.jpg"
            img_name = os.path.join(ROOT_DIR, img_name)
            img_url = f"https://game.gtimg.cn/images/lol/tft/cham-icons/624x318/{chess['TFTID']}.jpg"
            try:
                self.__download_image(img_name, img_url)
            except:
                print(f"{chess['TFTID']}-{chess['title']}-{chess['displayName']} 图片下载失败。")
                print(f"chess - url: {img_url}")

    def download_skill_imgs(self) -> None:
        chess_list = self.raw_data['chess']
        for chess in track(chess_list, description="正在爬取技能图片"):
            skill_name = chess['skillName'].replace("/", "-").replace("：", "-")
            img_name = f"{chess['TFTID']}-{chess['title']}-{chess['displayName']}-{skill_name}.jpg"
            img_name = f"{TFT_IMG_FILE}/skill/{img_name}"
            img_name = os.path.join(ROOT_DIR, img_name)
            img_url = chess['skillImage']
            try:
                self.__download_image(img_name, img_url)
            except Exception as e:
                # print(f"{chess['TFTID']}-{chess['title']}-{chess['displayName']}-{chess['skillName']} 图片下载失败。详细信息：{chess}, {e}")
                print(f"{chess['TFTID']}-{chess['title']}-{chess['displayName']}-{chess['skillName']} 图片下载失败。")
                print(f"skill - url: {img_url}")

    def download_hex_imgs(self) -> None:
        hex_list = self.raw_data['hex'][4]
        for hex_info in track(hex_list, description="正在爬取海克斯图片"):
            # print(hex_info)
            hex_info = hex_list[hex_info]
            img_name = f"{TFT_IMG_FILE}/hex/{hex_info['hexId']}-{hex_info['name']}.jpg"
            img_name = os.path.join(ROOT_DIR, img_name)
            try:
                self.__download_image(img_name, hex_info['imgUrl'])
            except Exception as e:
                # print(f"{hex_info['hexId']}-{hex_info['name']} 图片下载失败。详细信息：{hex_info}, {e}")
                print(f"{hex_info['hexId']}-{hex_info['name']} 图片下载失败。")
                print(f"hex - url: {hex_info['imgUrl']}")

    def download_equipment_imgs(self) -> None:
        equip_list = self.raw_data['equip']
        for equip in track(equip_list, description="正在爬取装备图片"):
            img_name = f"{TFT_IMG_FILE}/equip/{equip['TFTID']}-{equip['name'].replace('/', '')}.jpg"
            img_name = img_name.replace(" ", "").replace("//", "")
            img_name = os.path.join(ROOT_DIR, img_name)
            try:
                self.__download_image(img_name, equip['imagePath'])
            except Exception as e:
                print(f"{equip['TFTID']}-{equip['name'].replace('/', '')} 图片下载失败。")
                print(f"url: {equip['imagePath']}")

    def download_all_imgs(self) -> None:
        self.download_chess_imgs()
        self.download_skill_imgs()
        self.download_hex_imgs()
        self.download_equipment_imgs()


class TFTDataProcessor:
    def __init__(self) -> None:
        self.raw_data: dict = load_json(TFT_RAW_DATA_FILE)
        # example of self.raw_data
        self.__raw_data_example: dict = {
            "version_config": {},
            # 每一个chess例子（list里套的是字典）
            # {"chessId":"1", "title":"黑暗之女", "name":"788.png", "displayName":"安妮", "raceIds":"8108,8105", "jobIds":"8014", "price":"2", "skillName":"爆裂护盾", "skillType":"主动", "skillImage":"https://game.gtimg.cn/images/lol/act/img/tft/champions/annie-burst-shield.png", "skillIntroduce":"【安妮】用火焰引爆一个锥形区域，对她前方的敌人造成140/210/325魔法伤害，然后给自己生成300/350/425护盾值，持续4秒。", "skillDetail":"【安妮】用火焰引爆一个锥形区域，对她前方的敌人造成140/210/325魔法伤害，然后给自己生成300/350/425护盾值，持续4秒。", "life":"750", "magic":"90", "startMagic":"30", "armor":"40", "spellBlock":"40", "attackMag":"1.5", "attack":"40", "attackSpeed":"0.6", "attackRange":"2", "crit":"25", "originalImage":"upload/img/champions/annie-burst-shield.png", "lifeMag":"1.8", "TFTID":"788", "synergies":"", "illustrate":"", "recEquip":"559,581,597", "proStatus":"最新", "hero_EN_name":"Annie", "races":"福牛守护者,小天才", "jobs":"灵能使", "attackData":"40/60/90", "lifeData":"750/1350/2430"}
            "chess": [],
            # 每一个race例子
            # {"raceId":"8101", "name":"AI程序", "traitId":"8101", "introduce":"【AI程序】在每局游戏中对每个玩家的配置都不同。", "alias":"8101.png", "level":{"2":"初始化【AI程序】的条件和结果]", "4":"[对程序添加另一个结果]", "6":"前几个层级的加成提升200%"},"TFTID":"8101", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/origins/8101.png", "race_color_list":"2:1,4:2,6:3"}
            "race": [],
            # 每一个job例子
            # {"jobId":"8001", "name":"精英战士", "traitId":"8001", "introduce":"这个羁绊仅会在你恰好拥有1个或4个独特的【精英战士】弈子时激活。", "alias":"8001.png", "level":{"1":"处决低于15%生命值的敌人", "4":"处决低于30%生命值的敌人"},"TFTID":"8001", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/classes/8001.png", "job_color_list":"1:1,4:3"}
            "job": [],
            # 每一个equip例子
            # {"equipId":"201", "type":"2", "name":"幽梦之灵", "effect":"携带者也是一名刺客", "keywords":"攻击力，转职，暴击", "formula":"301,308", "imagePath":"https://game.gtimg.cn/images/lol/act/img/tft/equip/201.png", "TFTID":"2001", "jobId":"3", "raceId":"0", "proStatus":"无", "isShow":"0"}
            "equip": [],
            # 每一个hex例子
            # {"id":"7351", "hexId":"2415", "type":"1", "name":"开摆", "imgUrl":"https://game.gtimg.cn/images/lol/act/img/tft/hex/20220531155500HEX6295c9d41fbf3.PNG", "fetterId":"0", "fetterType":"0", "augments":"TFT7_Augment_AFK", "hero_EN_name":"", "isShow":"1", "hero_enhancement_type":"0", "description":"你在接下来的3回合里无法采取任何行动。在此之后，获得18金币。", "createTime":"2023-03-0815:55:40"}
            "hex": [],
        }
        self.processed_data: dict = {
            "all_chess_name": "",
            "all_race_name": "",
            "all_job_name": "",
            "job_chess": {},
            "race_chess": {},
            "price_chess": {},
            "chess_name_info": {}
        }

        self.__process_data()

    def __match_job_chess(self) -> None:
        res = {}
        job_data = self.raw_data['job']
        chess_data = self.raw_data['chess']
        for job in job_data:
            job_id = job['jobId']
            job_name = job['name']
            res[job_name] = []
            for chess in chess_data:
                job_ids = chess['jobIds'].split(',')
                if job_id in job_ids:
                    res[job_name].append(chess['displayName'])
        self.processed_data["job_chess"] = res

    def __match_race_chess(self) -> None:
        res = {}
        race_data = self.raw_data['race']
        chess_data = self.raw_data['chess']
        for race in race_data:
            race_id = race['raceId']
            race_name = race['name']
            res[race_name] = []
            for chess in chess_data:
                race_ids = chess['raceIds'].split(',')
                if race_id in race_ids:
                    res[race_name].append(chess['displayName'])
        self.processed_data["race_chess"] = res

    def __match_price_chess(self) -> None:
        res = {'1': [], '2': [], '3': [], '4': [], '5': []}
        chess_data = self.raw_data['chess']
        for price in res:
            for chess in chess_data:
                if chess['price'] == price:
                    res[price].append(chess['displayName'])
        self.processed_data["price_chess"] = res

    def __parse_all_strings(self) -> None:
        """
        获得所有的棋子名字,职业,以及种族.
        组成字符串,方便ocr以后匹配.
        """
        chess_name = [f'{chess["displayName"]}' for chess in self.raw_data['chess']]
        race_name = [f'{race["name"]}' for race in self.raw_data['race']]
        job_name = [f'{job["name"]}' for job in self.raw_data['job']]

        self.processed_data["all_chess_name"] = '-'.join(chess_name)
        self.processed_data["all_race_name"] = '-'.join(race_name)
        self.processed_data["all_job_name"] = '-'.join(job_name)

    def __parse_chess_name_info(self) -> None:
        chess = self.raw_data['chess']
        res = {}
        for info in chess:
            name = info['displayName']
            res[name] = info
        self.processed_data["chess_name_info"] = res

    def __process_data(self) -> None:
        self.__match_job_chess()
        self.__match_race_chess()
        self.__match_price_chess()
        self.__parse_all_strings()
        self.__parse_chess_name_info()
        save_json(self.processed_data, TFT_PROCESSED_DATA_FILE)

    def save_tft_processed_data(self) -> None:
        save_json(self.processed_data, TFT_PROCESSED_DATA_FILE)

    def save_py_class(self) -> None:
        # {name: {"name": str, "gui_name": str, "jobs": list[str], "races": list[str], "price": int}}
        simplified_chess_name_info = {}
        for key, val in self.processed_data['chess_name_info'].items():
            gui_name = f"{val['price']}-{val['displayName']}"

            jobs = []
            for job, chess_names in self.processed_data['job_chess'].items():
                if key in chess_names:
                    jobs.append(job)

            races = []
            for race, chess_names in self.processed_data['race_chess'].items():
                if key in chess_names:
                    races.append(race)

            tmp = {
                "name": key,
                "jobs": jobs,
                "races": races,
                "price": val['price'],
                "gui_name": gui_name,
                "gui_checkbox_key": f"checkbox_{key}",
                "gui_combo_num_key": f"combo_num_{key}"}
            simplified_chess_name_info[key] = tmp
        res = f"""class TFTData:
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
        self.version_config = {self.raw_data['version_config']}
        self.all_chess_name_str = "{self.processed_data['all_chess_name']}"
        self.all_race_name_str = "{self.processed_data['all_race_name']}"
        self.all_job_name_str = "{self.processed_data['all_job_name']}"
        self.race_chess = {self.processed_data['race_chess']}
        self.job_chess = {self.processed_data['job_chess']}
        self.price_chess = {self.processed_data['price_chess']}
        self.chess_name_info = {simplified_chess_name_info}
"""

        # 有些英雄名字字符ocr不支持，比如：chars in candidates are not in the vocab, ignoring them: {'菈'}
        # 因此在测试后将其替换成识别出来的文字
        replace_dict = {
            '菈': '拉',
        }

        for key in replace_dict:
            res = res.replace(key, replace_dict[key])

        with open(TFT_PY_CLASS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(res)


if __name__ == '__main__':
    # 下载官方的raw数据
    rdc = RawDataCollector()
    # 保存爬取的信息到 TFT_RAW_DATA_FILE = 'tft_raw_data.json'
    print()
    print("================ 下载所有原始数据 ================")
    rdc.save_tft_raw_data()
    print(f'\033[32m原始数据爬取完成，保存到：{TFT_RAW_DATA_FILE}\033[0m')
    print()

    # 下载图片
    print("================ 下载棋子、技能、海克斯、装备图片 ================")
    print("\033[31m如果图片有错，比如版本不对，请将所有图片删除重新下载（只删除图片，别删除文件夹）。\033[0m")
    rdc.download_all_imgs()
    print(f"\033[32m图片下载完成，保存到：{TFT_IMG_FILE}\033[0m")
    print()

    # 作者根据自己的需求对数据进行了处理和汇总
    tdp = TFTDataProcessor()
    # 处理好的数据保存到 TFT_PROCESSED_DATA_FILE = 'tft_processed_data.json'
    print("================ 处理数据，导出json ================")
    tdp.save_tft_processed_data()
    print(f"\033[32m数据处理完成，保存到：{TFT_PROCESSED_DATA_FILE}\033[0m")
    print()

    # 保存一份TFTData.py的Singleton，方便作者自己调用。
    print("================ 处理数据，导出py Singleton ================")
    tdp.save_py_class()
    print(f"\033[32mSingleton构建完成，保存到：{TFT_PY_CLASS_FILE}\033[0m")
    print()
