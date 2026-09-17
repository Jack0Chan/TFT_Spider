# TFT_Spider — S3 银河战争

腾讯官方历史版本 `10.6-2020.S3` 的自包含恢复快照，数据版本
`10.6`，于 `2026-09-17` 恢复并校验。

> 强化符文：该赛季尚未引入强化符文系统

<img src="readme_images/tft_web.png" width="70%">

## 内容

| 类型 | 数量 |
| --- | ---: |
| 棋子 | 51 |
| 种族羁绊 | 10 |
| 职业羁绊 | 13 |
| 装备 | 66 |
| 强化符文 | 0 |
| 官方失效图片链接 | 1 |

- 原始数据：`tft_data/tft_raw_data.json`
- 处理数据：`tft_data/tft_processed_data.json`
- Python 数据类：`tft_data/TFTData.py`
- 图片错误审计：`tft_data/image_download_errors.json`
- 图片目录：`tft_images/`

## 重新构建

```bash
pip install -r requirements.txt
python main.py --workers 24
python scripts/generate_readme_images.py --season s3
```

数据来源：[腾讯官方云顶之弈历史静态资源](https://game.gtimg.cn/)

<img src="readme_images/terminal.png" width="60%">
