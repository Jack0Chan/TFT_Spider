# TFT_Spider

云顶之弈赛季数据归档与爬取工具。仓库按赛季保存完整快照，包括爬虫代码、
JSON 数据、处理后的 Python 数据类以及配套图片。

当前最新赛季：**[S18 · 自然之力](seasons/s18/)**（版本 16.18）

<img src="seasons/s18/readme_images/tft_web.png" width="70%">

## 赛季目录

| 赛季 | 主题 | 数据版本 | 归档日期 | 完整内容 |
| --- | --- | --- | --- | --- |
| S18 | 自然之力 | 16.18 | 2026-09-17 | [seasons/s18](seasons/s18/) |
| S17 | 星神 | 16.17 | 2026-09-17 | [seasons/s17](seasons/s17/) |
| S16 | 英雄联盟传奇 | 16.7 | 2026-09-17 | [seasons/s16](seasons/s16/) |
| S15 | 天下无双格斗大赛 | 15.16 | 2025-08-17 | [seasons/s15](seasons/s15/) |
| S14 | 赛博之城 | 15.8 | 2025-04-25 | [seasons/s14](seasons/s14/) |
| S13 | 双城之战 2 | 14.24 | 2024-12-19 | [seasons/s13](seasons/s13/) |
| S12 | 魔法大乱斗 | 14.15 | 2024-08-07 | [seasons/s12](seasons/s12/) |
| S11 | 画中灵 | 14.9 | 2024-05-04 | [seasons/s11](seasons/s11/) |
| S10 | 强音争霸 | 13.23 | 2023-11-23 | [seasons/s10](seasons/s10/) |
| S8.5 | 怪兽来袭：铲铲市危机！ | 13.10 | 2023-05-19 | [seasons/s8.5](seasons/s8.5/) |

仓库历史中没有 S9 分支，因此当前归档不包含 S9。每个赛季目录都是原赛季分支的
完整文件快照，目录内的 `README.md` 提供该版本的详细数据结构和使用说明。

## 使用最新赛季

```bash
git clone https://github.com/Jack0Chan/TFT_Spider.git
cd TFT_Spider/seasons/s18
pip install -r requirements.txt
python main.py --season s18
```

只使用已归档数据时无需运行爬虫：

- 文本数据：`seasons/<赛季>/tft_data/`
- 图片数据：`seasons/<赛季>/tft_images/`
- 赛季说明：`seasons/<赛季>/README.md`

S16、S17、S18 支持通过 `--season` 显式指定赛季，并可通过 `--workers` 调整
图片下载并发数，或使用 `--skip-images` 只刷新 JSON 和 `TFTData.py`。旧赛季请按
对应目录 README 中的命令运行。

数据来源：[腾讯官方云顶之弈主题站](https://lol.qq.com/tft/#/champion)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Jack0Chan/TFT_Spider&type=Date)](https://www.star-history.com/#Jack0Chan/TFT_Spider&Date)
