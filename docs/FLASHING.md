# Heltec Wireless Paper 地圖韌體刷機教學

以下流程以 macOS 為例，目標是建立含指定地區離線地圖的 Meshtastic InkHUD 韌體。範例使用宜蘭與台北，但同一套流程可以套用到任何 `regions/*.json`。

## 1. 準備目錄

建議工作目錄：

```bash
cd ~/Documents/ESP32
```

Clone E-ink Map Tiles 工具：

```bash
git clone https://github.com/HarukiToreda/E-ink-Map-Tiles.git
```

Clone Meshtastic firmware：

```bash
git clone https://github.com/meshtastic/firmware.git meshtastic-firmware-yilan
cd meshtastic-firmware-yilan
git checkout develop
```

Clone 本 repo：

```bash
git clone https://github.com/MAXXTANG/heltec-wireless-paper-meshtastic-map.git
```

## 2. 安裝 E-ink Map Tiles 依賴

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 3. 放入地區設定與匯出腳本

```bash
cp -R ~/Documents/ESP32/heltec-wireless-paper-meshtastic-map/regions \
  ~/Documents/ESP32/E-ink-Map-Tiles/

cp ~/Documents/ESP32/heltec-wireless-paper-meshtastic-map/scripts/export_region_inkhud.py \
  ~/Documents/ESP32/E-ink-Map-Tiles/scripts/export_region_inkhud.py
```

## 4. 產生 MapTile.h

宜蘭版：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_region_inkhud.py regions/yilan.json
```

台北版：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_region_inkhud.py regions/taipei.json
```

輸出位置：

```text
yilan_exports/yilan/MapTile.h
yilan_exports/taipei/MapTile.h
```

目前地區配置：

| 地區 | 內容 |
|---|---|
| 宜蘭 | 台灣概覽 z7-z9、全宜蘭 z12、宜蘭活動帶 z13、礁溪/宜蘭市/羅東 z14-z15 |
| 台北 | 台灣概覽 z7-z9、台北盆地 z12、台北市中心 z13、台北車站/信義/士林北投 z14-z15 |

台北版為了控制容量，移除文字標籤與捷運線，且 z15 重點區使用 `3x3` grid。

## 5. 複製 MapTile.h 到 Meshtastic firmware

選擇要刷入的地區。以宜蘭為例：

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/yilan/MapTile.h \
  ~/Documents/ESP32/meshtastic-firmware-yilan/src/graphics/niche/InkHUD/Applets/Bases/Map/MapTile.h
```

以台北為例：

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/taipei/MapTile.h \
  ~/Documents/ESP32/meshtastic-firmware-yilan/src/graphics/niche/InkHUD/Applets/Bases/Map/MapTile.h
```

## 6. 編譯韌體

```bash
cd ~/Documents/ESP32/meshtastic-firmware-yilan
pio run -e heltec-wireless-paper-inkhud
```

如果你使用 VS Code PlatformIO 或遇到 cache 衝突，可以指定獨立 core dir：

```bash
PLATFORMIO_CORE_DIR=./.platformio-core-yilan pio run -e heltec-wireless-paper-inkhud
```

成功時會看到：

```text
Environment                   Status
heltec-wireless-paper-inkhud  SUCCESS
```

目前實測容量：

| 地區 | Firmware Flash |
|---|---:|
| 宜蘭 | 約 `98.5%` |
| 台北 | 約 `97.5%` |

若 Flash 超過 `100%`，請縮小 z15 範圍、移除文字標籤、移除 transit，或減少 focus region。

## 7. 找到 USB serial port

接上 Heltec Wireless Paper 後：

```bash
ls /dev/cu.*
```

常見 port：

```text
/dev/cu.usbserial-0001
```

如果沒有出現，請重新插拔 USB，或按住 BOOT 再插 USB 進下載模式。

## 8. 刷入韌體

```bash
cd ~/Documents/ESP32/meshtastic-firmware-yilan
pio run -e heltec-wireless-paper-inkhud -t upload --upload-port /dev/cu.usbserial-0001
```

成功時會看到：

```text
Hash of data verified.
Hard resetting via RTS pin...
SUCCESS
```

## 9. 手機位置與 GPS

Heltec Wireless Paper 沒有內建 GPS。你可以：

- 用 Meshtastic App 經藍牙分享手機位置
- 設定固定座標
- 外接 GNSS/GPS 模組

如果沒有位置，裝置仍可收發訊息，但地圖上的自己位置、距離與方向可能不正確。

## 10. 新增地區

新增一個 `regions/<slug>.json`，建議沿用這個策略：

- 台灣概覽：z7-z9
- 全縣市或都會區：z12
- 主要活動帶：z13
- 重點區：z14-z15

不要把全縣市都做到 z14/z15。Heltec Wireless Paper 的 app partition 放不下，而且 2.13 吋電子紙螢幕也不適合塞太多細節。

## 11. 宜蘭等高線版本

宜蘭的實驗腳本仍保留在 `scripts/export_yilan_contour_inkhud.py` 與 `scripts/export_yilan_road_contour_inkhud.py`。這兩個版本使用國土測繪中心 `MOI_CONTOUR_2` 圖資，適合之後做登山、溪流、水域活動版本。
