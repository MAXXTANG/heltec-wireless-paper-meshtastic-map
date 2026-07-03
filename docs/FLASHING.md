# Heltec Wireless Paper 刷機教學

以下流程以 macOS 為例，目標是建立含宜蘭離線地圖的 Meshtastic InkHUD 韌體。

## 1. 準備目錄

建議工作目錄：

```bash
cd ~/Documents/ESP32
```

Clone 地圖工具：

```bash
git clone https://github.com/HarukiToreda/E-ink-Map-Tiles.git
```

Clone Meshtastic firmware：

```bash
git clone https://github.com/meshtastic/firmware.git meshtastic-firmware-yilan
cd meshtastic-firmware-yilan
git checkout develop
```

## 2. 安裝 E-ink Map Tiles 依賴

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 3. 放入本 repo 的匯出腳本

把本 repo 的：

```text
scripts/export_yilan_inkhud.py
```

複製到：

```text
~/Documents/ESP32/E-ink-Map-Tiles/scripts/export_yilan_inkhud.py
```

## 4. 產生 MapTile.h

道路版：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_yilan_inkhud.py
```

輸出位置：

```text
yilan_exports/MapTile.h
```

純等高線版：

```bash
cd ~/Documents/ESP32/E-ink-Map-Tiles
.venv/bin/python -u scripts/export_yilan_contour_inkhud.py
cp yilan_exports/MapTile_contour.h yilan_exports/MapTile.h
```

目前腳本會產生：

- 台灣概覽：`z7-z9`
- 全宜蘭：`z12`
- 宜蘭活動帶：`z13`
- 礁溪、宜蘭市、羅東：`z14-z15`

## 5. 複製 MapTile.h 到 Meshtastic firmware

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/MapTile.h \
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

成功時會看到類似：

```text
Environment                   Status
heltec-wireless-paper-inkhud  SUCCESS
```

目前這版接近上限，Flash 約 `98.5%`。如果再增加圖磚，可能會超過 app partition。

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

## 10. 疑難排解

如果地圖縮到 z14/z15 變白：

- 表示目前位置不在高縮放圖磚覆蓋範圍內
- 請把實際座標加入 `scripts/export_yilan_inkhud.py` 的 focus region
- 重新產生 `MapTile.h`、編譯、刷入

如果編譯顯示 Flash 超過上限：

- 減少 z15 區域
- 把 `4x4` 改成 `3x3`
- 移除一個 focus region
- 不要做全宜蘭 z14/z15
