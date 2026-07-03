# 道路版疊等高線

道路版疊等高線使用同一份 InkHUD `MapTile.h` 同時放入道路底圖與等高線，不需要在裝置端切換圖層。建議從宜蘭版開始，因為它已經針對 Heltec Wireless Paper 的 app partition 做過容量取捨。

## 設定檔

```text
regions/yilan-road-contour.json
```

這份設定檔使用：

- 道路底圖：OpenFreeMap / OpenStreetMap
- 等高線圖層：國土測繪中心 WMTS `MOI_CONTOUR_2`
- 台灣概覽：z7-z9
- 全宜蘭：z12
- 宜蘭活動帶：z13
- 礁溪、宜蘭市、羅東：z14-z15
- 等高線只疊：z14-z15

道路元素只保留：

```json
["land", "water", "roads", "highways", "paths"]
```

為了塞進 Heltec Wireless Paper，這個版本移除：

- `labels`
- `transit`
- `boundaries`

## 產生 MapTile.h

先把本 repo 的 `regions/` 與 `scripts/export_region_inkhud.py` 複製到 E-ink Map Tiles 專案，然後執行：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan-road-contour.json
```

輸出位置：

```text
yilan_exports/yilan-road-contour/MapTile.h
```

## 刷入 firmware

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/yilan-road-contour/MapTile.h \
  ~/Documents/ESP32/meshtastic-firmware-yilan/src/graphics/niche/InkHUD/Applets/Bases/Map/MapTile.h

cd ~/Documents/ESP32/meshtastic-firmware-yilan
pio run -e heltec-wireless-paper-inkhud
pio run -e heltec-wireless-paper-inkhud -t upload --upload-port /dev/cu.usbserial-0001
```

## 容量限制

實測可用版本：

| 項目 | 數值 |
|---|---:|
| 圖磚數 | `323` |
| 等高線 zoom | `z14-z15` |
| 壓縮圖資 | `1,047,385 bytes` |
| Firmware Flash | 約 `98.3%` |

曾測試把等高線疊到更大範圍：

| 等高線範圍 | 結果 |
|---|---|
| z12-z15 | 韌體超過 app partition |
| z13-z15 | 仍然太貼近上限 |
| z14-z15 | 可刷入 |

所以目前建議只在重點區 z14/z15 疊等高線。z12/z13 保留道路與水系即可，避免容量爆掉。

## 調整等高線

設定檔中的這段控制等高線：

```json
"contour": {
  "layer": "MOI_CONTOUR_2",
  "zooms": [14, 15],
  "threshold": 80
}
```

- `layer`：國土測繪中心 WMTS 圖層
- `zooms`：要疊等高線的 zoom level
- `threshold`：把 NLSC 圖磚中的亮色線條轉成黑色 ink pixels 的門檻

`threshold` 調低會保留更多線條與雜訊，圖資也可能變大；調高會讓線條變少、容量下降，但細節可能消失。

## 100m 等高線

目前 `MOI_CONTOUR_2` 是 raster 圖磚，不能像向量圖層一樣指定「每 100m 一條」。如果要真正控制 100m 間距，需要改用 DEM 或向量等高線資料重新產生線條，再 rasterize 成 InkHUD 圖磚。
