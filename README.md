# Heltec Wireless Paper Meshtastic Map

這個 repo 記錄如何替 Heltec Wireless Paper 建立 Meshtastic InkHUD 離線地圖韌體。設計方式是一個主 repo 搭配多個地區設定檔，未來要新增台中、台南、高雄等版本時，只要新增 `regions/<city>.json`，不用為每個地區開一個 repo 或分支。

![Heltec Wireless Paper 顯示宜蘭離線地圖](docs/images/heltec-wireless-paper-yilan-map.jpg)

上圖是 Heltec Wireless Paper 實機顯示宜蘭離線地圖的測試畫面。背景地圖已預先壓縮進 InkHUD 韌體，不需要即時下載線上地圖。

## 目前版本

目前 repo 上有六個主流程版本：

| 地區 | 設定檔 | 圖磚數 | 壓縮圖資 | Firmware Flash |
|---|---|---:|---:|---:|
| 宜蘭 | `regions/yilan.json` | `323` | `1,056,198 bytes` | 約 `98.5%` |
| 宜蘭道路 + 等高線 | `regions/yilan-road-contour.json` | `323` | `1,047,385 bytes` | 約 `98.3%` |
| 台北 | `regions/taipei.json` | `210` | `1,023,177 bytes` | 約 `97.5%` |
| 高雄 | `regions/kaohsiung.json` | `229` | `975,984 bytes` | 約 `96.1%` |
| 台中 | `regions/taichung.json` | `222` | `1,028,674 bytes` | 約 `97.7%` |
| 台南 | `regions/tainan.json` | `229` | `985,784 bytes` | 約 `96.4%` |

另外保留兩個宜蘭實驗腳本：

- `scripts/export_yilan_contour_inkhud.py`：純等高線版
- `scripts/export_yilan_road_contour_inkhud.py`：舊版宜蘭道路 + 等高線疊圖腳本

目前實測配置：

- 裝置：Heltec Wireless Paper
- 韌體目標：`heltec-wireless-paper-inkhud`
- Meshtastic firmware：`develop` 分支，實測版本 `2.8.0.3778fb0`
- 地圖功能：InkHUD offline map tiles
- 授權：本 repo 的教學與輔助腳本使用 MIT License

## Repo 結構

- `regions/`：各地區圖資切分設定，例如 `yilan.json`、`yilan-road-contour.json`、`taipei.json`、`kaohsiung.json`、`taichung.json`、`tainan.json`
- `scripts/export_region_inkhud.py`：通用地區匯出腳本，讀取 `regions/*.json` 產生 `MapTile.h`
- `scripts/export_yilan_*.py`：宜蘭進階版本腳本，包含純等高線與道路疊等高線實驗版
- `docs/VERSIONS.md`：目前地圖版本總表
- `docs/MESHTASTIC_INSTALL.md`：Heltec Wireless Paper 安裝 Meshtastic 的基礎流程
- `docs/FLASHING.md`：完整產生圖資、編譯、刷機流程
- `docs/MAP_STRATEGY.md`：宜蘭圖資切分策略與容量評估
- `docs/CONTOUR_MAPS.md`：台灣等高線圖資可行性
- `docs/ROAD_CONTOUR.md`：道路版疊等高線版本說明
- `NOTICE.md`：上游專案與圖資來源說明

## 地區策略

Heltec Wireless Paper 的 app partition 很有限，不能把整個城市或縣市都做到 z14/z15。建議使用分層策略：

| 範圍 | Zoom | 用途 |
|---|---:|---|
| 台灣概覽 | z7-z9 | 大尺度 overview，避免縮遠時整片空白 |
| 全縣市或都會區 | z12 | 區域級定位 |
| 主要活動帶 | z13 | 平原、都會核心、活動範圍 |
| 重點區 | z14-z15 | 實際活動熱點與道路細節 |

宜蘭版包含全宜蘭 z12、宜蘭活動帶 z13、礁溪/宜蘭市/羅東 z14-z15。宜蘭道路 + 等高線版沿用相同範圍，但移除道路文字標籤、捷運線與行政邊界，只在 z14-z15 重點區疊國土測繪中心 `MOI_CONTOUR_2` 等高線。台北、高雄、台中、台南版都採道路版策略，移除文字標籤與 transit；台中因道路密度較高，額外移除 boundaries，且 z15 重點區使用 `2x2` grid。

## 快速產生地圖

把本 repo 的 `regions/` 與 `scripts/export_region_inkhud.py` 放到 E-ink Map Tiles 專案後：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan.json
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan-road-contour.json
.venv/bin/python -u scripts/export_region_inkhud.py regions/taipei.json
.venv/bin/python -u scripts/export_region_inkhud.py regions/kaohsiung.json
.venv/bin/python -u scripts/export_region_inkhud.py regions/taichung.json
.venv/bin/python -u scripts/export_region_inkhud.py regions/tainan.json
```

輸出位置：

```text
yilan_exports/yilan/MapTile.h
yilan_exports/yilan-road-contour/MapTile.h
yilan_exports/taipei/MapTile.h
yilan_exports/kaohsiung/MapTile.h
yilan_exports/taichung/MapTile.h
yilan_exports/tainan/MapTile.h
```

再把想刷入的 `MapTile.h` 複製到 Meshtastic firmware：

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/yilan/MapTile.h \
  ~/Documents/ESP32/meshtastic-firmware-yilan/src/graphics/niche/InkHUD/Applets/Bases/Map/MapTile.h
```

詳細步驟請看 [docs/FLASHING.md](docs/FLASHING.md)。

## Meshtastic 安裝

如果你的 Heltec Wireless Paper 還沒有安裝 Meshtastic，請先看：

- [docs/MESHTASTIC_INSTALL.md](docs/MESHTASTIC_INSTALL.md)

這份文件包含官方 Web Flasher、手動編譯 `heltec-wireless-paper-inkhud`、App 初始設定與外殼資源。

## 外殼資源

- [HP - Heltec Wireless Paper Case for Meshtastic](https://www.printables.com/model/956383-hp-heltec-wireless-paper-case-for-meshtastic)

## 為什麼不用分支放不同地區

不建議用 `taipei-map`、`taichung-map` 這類分支管理各地圖，因為分支很容易讓文件、腳本與修正分散。比較好的方式是：

- repo 名稱：`heltec-wireless-paper-meshtastic-map`
- 地區設定：`regions/yilan.json`、`regions/yilan-road-contour.json`、`regions/taipei.json`、`regions/kaohsiung.json`、`regions/taichung.json`、`regions/tainan.json`
- 產出檔案：`yilan_exports/<slug>/MapTile.h`

若未來需要發布可直接刷的 binary，可以用 GitHub Releases 附加 `firmware-*.bin`，不要把大型 binary 直接 commit 進 git。

## 授權

本 repo 的文件與輔助腳本採 MIT License。

注意：Meshtastic firmware、OpenStreetMap/OpenFreeMap 圖資、國土測繪中心圖資各有自己的授權與使用規範。本 repo 不重新授權那些上游資料或韌體。
