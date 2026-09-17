# TFT_Spider — S12 魔法大乱斗

仓库历史赛季快照。数据版本 `14.15`，快照日期 `2024-08-07`。

<img src="tft_web.png" width="70%" alt="S12 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 71 |
| 种族羁绊 | 16 |
| 职业羁绊 | 12 |
| 装备 | 201 |
| 强化符文 | 275 |
| 已归档图片 | 599 |
| 官方失效图片链接 | 11 |

## 目录

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
- 图片错误审计：`tft_data/image_download_errors.json`
- 图片目录：`tft_images/`
- README 图片生成器：`scripts/generate_readme_images.py`

## 使用

```bash
pip install -r requirements.txt
python main.py
python scripts/generate_readme_images.py --season s12
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
