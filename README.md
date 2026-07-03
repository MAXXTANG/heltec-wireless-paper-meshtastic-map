# Heltec Wireless Paper 宜蘭離線地圖韌體教學

這個 repo 記錄如何替 Heltec Wireless Paper 建立 Meshtastic InkHUD 離線地圖韌體，範例圖資以台灣概覽與宜蘭縣為主。

目前實測配置：

- 裝置：Heltec Wireless Paper
- 韌體目標：`heltec-wireless-paper-inkhud`
- Meshtastic firmware：`develop` 分支，實測版本 `2.8.0.3778fb0`
- 地圖功能：InkHUD offline map tiles
- 授權：本 repo 的教學與輔助腳本使用 MIT License

## 圖資配置

目前可用版本採用分層策略，避免 ESP32-S3 app partition 爆掉：

| 範圍 | Zoom | 用途 |
|---|---:|---|
| 台灣概覽 | z7-z9 | 大尺度 overview，避免縮遠時整片空白 |
| 全宜蘭 | z12 | 縣域級定位 |
| 宜蘭活動帶 | z13 | 宜蘭平原與主要活動區 |
| 礁溪 | z14-z15 | 重點活動區細節 |
| 宜蘭市 | z14-z15 | 重點活動區細節 |
| 羅東 | z14-z15 | 重點活動區細節 |

這版約 `323` 張圖磚，地圖壓縮資料約 `1.05 MB`。在 Heltec Wireless Paper 上編譯後 Flash 使用率約 `98.5%`，已經非常接近上限。

## 為什麼不做全宜蘭 z14/z15

粗估全宜蘭：

- z14 約 `1,521` 張圖磚，約 `7.8 MB`
- z15 約 `5,928` 張圖磚，約 `23 MB`

Heltec Wireless Paper 的 app partition 放不下，所以 z14/z15 必須只放重點區域。

## 快速流程

1. Clone E-ink Map Tiles 工具。
2. Clone Meshtastic firmware。
3. 用本 repo 的 `scripts/export_yilan_inkhud.py` 產生 `MapTile.h`。
4. 把 `MapTile.h` 複製到 Meshtastic firmware 的 InkHUD map applet。
5. 編譯 `heltec-wireless-paper-inkhud`。
6. 透過 USB serial 刷入 Heltec Wireless Paper。

詳細步驟請看 [docs/FLASHING.md](docs/FLASHING.md)。

## 目錄

- [docs/FLASHING.md](docs/FLASHING.md)：完整刷機教學
- [docs/MAP_STRATEGY.md](docs/MAP_STRATEGY.md)：圖資切分策略與容量評估
- [docs/CONTOUR_MAPS.md](docs/CONTOUR_MAPS.md)：台灣等高線圖資可行性
- [scripts/export_yilan_inkhud.py](scripts/export_yilan_inkhud.py)：產生宜蘭 InkHUD `MapTile.h` 的腳本
- [NOTICE.md](NOTICE.md)：上游專案與圖資來源說明

## 授權

本 repo 的文件與輔助腳本採 MIT License。

注意：Meshtastic firmware、OpenStreetMap/OpenFreeMap 圖資、國土測繪中心圖資各有自己的授權與使用規範。本 repo 不重新授權那些上游資料或韌體。
