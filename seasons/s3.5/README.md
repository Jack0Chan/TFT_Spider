# TFT_Spider — S3.5 再战星海

腾讯官方历史静态接口恢复。数据版本 `10.12`，快照日期 `2026-09-17`。

> 强化符文说明：该赛季尚未引入强化符文系统

<img src="tft_web.png" width="70%" alt="S3.5 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 66 |
| 种族羁绊 | 12 |
| 职业羁绊 | 14 |
| 装备 | 66 |
| 强化符文 | 0 |
| 已归档图片 | 189 |
| 官方失效图片链接 | 11 |

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
python scripts/generate_readme_images.py --season s3.5
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
