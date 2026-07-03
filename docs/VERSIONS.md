# 地圖版本

目前 repo 的主流程版本都使用 `scripts/export_region_inkhud.py` 搭配 `regions/*.json` 產生 `MapTile.h`。

| 版本 | 設定檔 | 用途 | 圖磚數 | 壓縮圖資 | Firmware Flash |
|---|---|---|---:|---:|---:|
| 宜蘭道路版 | `regions/yilan.json` | 一般宜蘭活動、防災、節點分布 | `323` | `1,056,198 bytes` | 約 `98.5%` |
| 宜蘭道路 + 等高線版 | `regions/yilan-road-contour.json` | 登山、溪流、水域或地形感較重要的活動 | `323` | `1,047,385 bytes` | 約 `98.3%` |
| 台北道路版 | `regions/taipei.json` | 台北市區與盆地概覽 | `210` | `1,023,177 bytes` | 約 `97.5%` |
| 高雄道路版 | `regions/kaohsiung.json` | 高雄都會區與沿海平原 | `229` | `975,984 bytes` | 約 `96.1%` |
| 台中道路版 | `regions/taichung.json` | 台中都會盆地 | `222` | `1,028,674 bytes` | 約 `97.7%` |
| 台南道路版 | `regions/tainan.json` | 台南平原與市區 | `229` | `985,784 bytes` | 約 `96.4%` |

## 宜蘭道路版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan.json
```

內容：

- 台灣概覽：z7-z9
- 全宜蘭：z12
- 宜蘭活動帶：z13
- 礁溪、宜蘭市、羅東：z14-z15
- 保留道路、步道、水域、邊界、標籤與 transit

## 宜蘭道路 + 等高線版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan-road-contour.json
```

內容：

- 與宜蘭道路版相同範圍
- 道路圖移除 labels、transit、boundaries
- 只在 z14-z15 重點區疊 `MOI_CONTOUR_2` 等高線

不要把等高線套到全宜蘭 z12-z15，會超過 Heltec Wireless Paper app partition。

## 台北道路版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/taipei.json
```

內容：

- 台灣概覽：z7-z9
- 台北盆地：z12
- 台北市中心活動區：z13
- 台北車站、信義、士林北投：z14-z15
- 移除 labels 與 transit
- z15 重點區使用 `3x3` grid

## 高雄道路版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/kaohsiung.json
```

內容：

- 台灣概覽：z7-z9
- 高雄都會區與沿海平原：z12
- 高雄活動區：z13
- 高雄車站、左營、鳳山：z14-z15
- 移除 labels 與 transit
- z15 重點區使用 `3x3` grid

## 台中道路版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/taichung.json
```

內容：

- 台灣概覽：z7-z9
- 台中都會盆地：z12
- 台中活動區：z13
- 台中車站、西屯市政、豐原：z14-z15
- 移除 labels、transit、boundaries
- z15 重點區使用 `2x2` grid

台中道路密度較高，原本 z15 `3x3` 版本壓縮後約 `1.10 MB`，太接近 Heltec Wireless Paper app partition 上限；目前版本改為 z15 `2x2`，build 實測可過。

## 台南道路版

```bash
.venv/bin/python -u scripts/export_region_inkhud.py regions/tainan.json
```

內容：

- 台灣概覽：z7-z9
- 台南平原：z12
- 台南活動區：z13
- 台南車站、安平、新營：z14-z15
- 移除 labels 與 transit
- z15 重點區使用 `3x3` grid

## 實驗腳本

repo 也保留兩個宜蘭實驗腳本：

- `scripts/export_yilan_contour_inkhud.py`：純等高線版
- `scripts/export_yilan_road_contour_inkhud.py`：舊版道路 + 等高線疊圖腳本

新版本建議優先使用 `regions/*.json` 搭配通用 exporter，後續新增台中、台南、高雄也沿用同一套格式。
