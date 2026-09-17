# TFT_Spider — S6 双城之战

腾讯官方历史静态接口恢复。数据版本 `11.22`，快照日期 `2026-09-17`。

> 强化符文说明：S1-S5.5 尚未引入强化符文；S6 的腾讯历史强化符文文件未公开保留

<img src="readme_images/tft_web.png" width="70%" alt="S6 数据概览">

## 数据概览

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 59 |
| 种族羁绊 | 15 |
| 职业羁绊 | 13 |
| 装备 | 267 |
| 强化符文 | 0 |
| 已归档图片 | 385 |
| 官方失效图片链接 | 0 |

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
python scripts/generate_readme_images.py --season s6
```

数据来源：[腾讯官方云顶之弈静态资源](https://game.gtimg.cn/)
