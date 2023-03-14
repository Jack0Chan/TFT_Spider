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
import requests
from rich.progress import track


def load_json(filename: str) -> None:
    with open(filename, 'r', encoding='utf-8') as load_f:
        return json.load(load_f)


def save_json(data: dict, filename: str, indent: int=4) -> None:
    with open(filename, 'w', encoding='utf8') as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=indent)

class DataCollector:
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
        response = requests.get('https://lol.qq.com/zmtftzone/public-lib/versionconfig.json')
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
        self.version_config["urlChessData"] = res['urlChessData']
        self.version_config["urlRaceData"] = res['urlRaceData']
        self.version_config["urlJobData"] = res['urlJobData']
        self.version_config["urlEquipData"] = res['urlEquipData']
        self.version_config["urlBuffData"] = res['urlBuffData']
        # 通过job获取版本信息
        response = requests.get(self.version_config["urlRaceData"], timeout=self.__time_out)
        # 13.5
        self.version_config["版本信息"] = response.json()["version"]
        # self.version_config 更新后结果：
        # {'赛季名称': 's8-怪兽来袭', '版本信息': '13.5', '爬取日期': '2023-03-14', xxxx(各种url)}

    def __collect_raw_data(self) -> None:
        data_list = ['chess', 'race', 'job', 'equip']
        for data_kind in data_list:
            url = self.version_config[f'url_{data_kind}_data']
            response = requests.get(url, timeout=self.__time_out)
            self.raw_data[data_kind] = response.json()['data']
        # 'hex'特殊处理
        response = requests.get(self.version_config['url_hex_data'], timeout=self.__time_out)
        hex_res = response.json()
        self.raw_data['hex'] = [hex_res[key] for key in hex_res]

    def __download_image(self, img_name: str, img_url: str):
        headers = {
            'authority': 'game.gtimg.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
        }
        if os.path.exists(img_name):
            print(f"file_exists: {img_name}")
        else:
            img_resp = requests.get(img_url, headers=headers, timeout=self.__time_out)
            if "was not found" in str(img_resp.content):
                img_resp = requests.get(img_url, headers=headers,
                                        timeout=self.__time_out, verify=False)
            # if "was not found" in str(img_resp.content):
            #     print(img_url)
            #     print(img_resp.content)
            with open(img_name, mode="wb") as f:
                f.write(img_resp.content)

    def download_chess_imgs(self) -> None:
        print("如果图片有错误，比如版本不对，请将所有图片删除重新下载。")
        chess_list = self.raw_data['chess']
        for chess in track(chess_list, description="正在爬取棋子图片"):
            img_name = f"images/chess/{chess['TFTID']}-{chess['title']}-{chess['displayName']}.jpg"
            img_url = f"https://game.gtimg.cn/images/lol/tft/cham-icons/624x318/{chess['TFTID']}.jpg"
            self.__download_image(img_name, img_url)

    def download_skill_imgs(self) -> None:
        print("如果图片有错误，比如版本不对，请将所有图片删除重新下载。")
        chess_list = self.raw_data['chess']
        for chess in track(chess_list, description="正在爬取技能图片"):
            img_name = f"images/skill/{chess['TFTID']}-{chess['title']}-{chess['displayName']}-{chess['skillName']}.jpg"
            img_url = chess['skillImage']
            self.__download_image(img_name, img_url)

    def download_hex_imgs(self) -> None:
        print("如果图片有错误，比如版本不对，请将所有图片删除重新下载。")
        hex_list = self.raw_data['hex']
        for hex_info in track(hex_list, description="正在爬取海克斯图片"):
            img_name = f"images/hex/{hex_info['hexId']}-{hex_info['name']}.png"
            self.__download_image(img_name, hex_info['imgUrl'])

    def download_equipment_imgs(self) -> None:
        print("如果图片有错误，比如版本不对，请将所有图片删除重新下载。")
        equip_list = self.raw_data['equip']
        for equip in track(equip_list, description="正在爬取装备图片"):
            img_name = f"images/equip/{equip['TFTID']}-{equip['name']}.png"
            img_name = img_name.replace(" ", "").replace("//", "")
            self.__download_image(img_name, equip['imagePath'])

    def download_all_imgs(self) -> None:
        self.download_chess_imgs()
        self.download_skill_imgs()
        self.download_hex_imgs()
        self.download_equipment_imgs()

if __name__ == '__main__':
    dc = DataCollector()
    # print(dc.version_config)
    # print(dc.raw_data)
    dc.download_all_imgs()
    
