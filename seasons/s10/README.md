# TFT_Spider — S10 强音争霸

仓库历史赛季快照。数据版本 `13.23`，快照日期 `2023-11-23`。

<img src="tft_web.png" width="70%" alt="S10 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 62 |
| 种族羁绊 | 15 |
| 职业羁绊 | 14 |
| 装备 | 405 |
| 强化符文 | 237 |
| 已归档图片 | 762 |
| 官方失效图片链接 | 1 |

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
python scripts/generate_readme_images.py --season s10
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
