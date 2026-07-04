# Heltec Wireless Paper Meshtastic 安裝說明

這份文件說明如何先把 Heltec Wireless Paper 安裝成可用的 Meshtastic 裝置。完成後，再依照 [FLASHING.md](FLASHING.md) 製作含離線地圖的 InkHUD 韌體。

官方入口：

- Meshtastic Flashing Firmware 文件：https://meshtastic.org/docs/getting-started/flashing-firmware/
- Meshtastic Web Flasher：https://flasher.meshtastic.org/
- Meshtastic Downloads：https://meshtastic.org/downloads/

## 安裝前檢查

- 確認板子是 Heltec Wireless Paper。
- 確認 LoRa 頻段符合你的所在地與天線，例如台灣常見為 AS923/TW 類型設定；實際選項以 Meshtastic App 顯示為準。
- 接上 LoRa 天線後再長時間開機或測試發射。
- 使用可傳輸資料的 USB-C 線，不要只用充電線。
- macOS / Windows 若看不到 serial port，先安裝對應 USB serial driver。

## 方法一：官方 Web Flasher

這個方法適合先確認硬體正常、先跑官方 Meshtastic，不含自訂離線地圖。

1. 使用 Chrome 或 Edge 開啟 https://flasher.meshtastic.org/。
2. 用 USB-C 接上 Heltec Wireless Paper。
3. 選擇 ESP32 類裝置，連接 serial port。
4. 裝置型號選 Heltec Wireless Paper 對應韌體。
5. 如果有 InkHUD 版本可選，選 `heltec-wireless-paper-inkhud`。
6. 選擇 Stable、Beta 或 Alpha。若要使用最新 InkHUD 地圖功能，可能需要較新的 Alpha/Beta 或自行編譯。
7. 執行 flash。
8. 完成後重新開機，使用 Meshtastic App 連線設定。

如果 Web Flasher 找不到裝置，可以按住 BOOT 再插 USB，讓 ESP32-S3 進入下載模式。

## 方法二：自行編譯 InkHUD 韌體

這個方法適合要加入本 repo 的離線地圖 `MapTile.h`。

```bash
cd ~/Documents/ESP32
git clone https://github.com/meshtastic/firmware.git meshtastic-firmware-yilan
cd meshtastic-firmware-yilan
git checkout develop
```

編譯 Heltec Wireless Paper InkHUD：

```bash
pio run -e heltec-wireless-paper-inkhud
```

若使用獨立 PlatformIO core dir：

```bash
PLATFORMIO_CORE_DIR=./.platformio-core-yilan pio run -e heltec-wireless-paper-inkhud
```

刷入：

```bash
pio run -e heltec-wireless-paper-inkhud -t upload --upload-port /dev/cu.usbserial-0001
```

macOS 常見 serial port：

```text
/dev/cu.usbserial-0001
/dev/cu.usbmodem*
```

## 加入離線地圖

先依 [FLASHING.md](FLASHING.md) 產生指定版本的 `MapTile.h`，再複製到 Meshtastic firmware：

```bash
cp ~/Documents/ESP32/E-ink-Map-Tiles/yilan_exports/yilan/MapTile.h \
  ~/Documents/ESP32/meshtastic-firmware-yilan/src/graphics/niche/InkHUD/Applets/Bases/Map/MapTile.h
```

再重新編譯與刷入：

```bash
cd ~/Documents/ESP32/meshtastic-firmware-yilan
pio run -e heltec-wireless-paper-inkhud
pio run -e heltec-wireless-paper-inkhud -t upload --upload-port /dev/cu.usbserial-0001
```

## 初始設定

刷完後使用 Meshtastic App：

1. 透過 Bluetooth 連線 Heltec Wireless Paper。
2. 設定 LoRa region，需符合所在地法規與硬體頻段。
3. 設定裝置名稱。
4. 設定 channel。
5. 若裝置沒有外接 GPS，可用手機分享位置或設定固定位置。
6. 到 InkHUD / Positions / Favorites map 頁面確認節點與地圖顯示。

## 外殼資源

可參考這個 3D 列印外殼：

- Heltec Wireless Paper Case for Meshtastic：<https://www.printables.com/model/956383-hp-heltec-wireless-paper-case-for-meshtastic/>

列印外殼前請確認你的板子版本、電池尺寸、天線接頭與按鍵位置是否相容。
