# TFT_Spider — S15 天下无双格斗大赛

仓库历史赛季快照。数据版本 `15.16`，快照日期 `2025-08-17`。

<img src="tft_web.png" width="70%" alt="S15 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 71 |
| 种族羁绊 | 15 |
| 职业羁绊 | 12 |
| 装备 | 265 |
| 强化符文 | 349 |
| 已归档图片 | 885 |
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
python scripts/generate_readme_images.py --season s15
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
