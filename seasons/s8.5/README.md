# TFT_Spider — S8.5 怪兽来袭：铲铲市危机！

仓库历史赛季快照。数据版本 `13.10`，快照日期 `2023-05-19`。

<img src="tft_web.png" width="70%" alt="S8.5 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 61 |
| 种族羁绊 | 14 |
| 职业羁绊 | 15 |
| 装备 | 331 |
| 强化符文 | 297 |
| 已归档图片 | 835 |
| 官方失效图片链接 | 4 |

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
python scripts/generate_readme_images.py --season s8.5
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
