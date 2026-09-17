# TFT_Spider — S8 怪兽来袭

仓库历史赛季快照。数据版本 `13.5`，快照日期 `2023-03-18`。

<img src="readme_images/tft_web.png" width="70%" alt="S8 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 62 |
| 种族羁绊 | 12 |
| 职业羁绊 | 15 |
| 装备 | 331 |
| 强化符文 | 298 |
| 已归档图片 | 762 |
| 官方失效图片链接 | 未单独审计 |

## 目录

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
- 图片目录：`tft_images/`
- README 图片生成器：`scripts/generate_readme_images.py`

## 使用

```bash
pip install -r requirements.txt
python main.py
python scripts/generate_readme_images.py --season s8
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
