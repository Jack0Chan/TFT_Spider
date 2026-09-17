# TFT_Spider — S7 巨龙之境

腾讯官方历史静态接口恢复。数据版本 `12.11`，快照日期 `2026-09-17`。

<img src="readme_images/tft_web.png" width="70%" alt="S7 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 60 |
| 种族羁绊 | 11 |
| 职业羁绊 | 18 |
| 装备 | 304 |
| 强化符文 | 213 |
| 已归档图片 | 635 |
| 官方失效图片链接 | 2 |

## 目录

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
- 图片错误审计：`tft_data/image_download_errors.json`
- 历史接口配置：`season_config.json`
- 图片目录：`tft_images/`
- README 图片生成器：`scripts/generate_readme_images.py`

## 使用

```bash
pip install -r requirements.txt
python main.py --workers 24
python scripts/generate_readme_images.py --season s7
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
