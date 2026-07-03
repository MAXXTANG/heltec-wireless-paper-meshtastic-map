# 台灣等高線圖資

國土測繪中心的免申請服務有可用的等高線與地形圖 WMTS 圖層。

官方 capabilities：

```text
https://wmts.nlsc.gov.tw/wmts?SERVICE=WMTS&REQUEST=GetCapabilities
```

可用圖層包含：

| Layer | 說明 |
|---|---|
| `EMAP5_OPENDATA` | 臺灣通用電子地圖，套疊等高線，OpenData |
| `EMAP5` | 臺灣通用電子地圖，等高線 + 門牌 |
| `MOI_CONTOUR_2` | 等高線圖，2010-2015 |
| `MOI_CONTOUR` | 等高線圖，2003-2005 |
| `MOI_HILLSHADE` | 陰影圖 |
| `MOI_SHADERMAP` | 渲染圖 |
| `B25000` | 1/25000 地形圖 |
| `TOPO25K_114` | 114 年 1/25000 地形圖 |

## WMTS URL 格式

```text
https://wmts.nlsc.gov.tw/wmts/{Layer}/default/GoogleMapsCompatible/{z}/{y}/{x}
```

例如礁溪附近 z14：

```text
https://wmts.nlsc.gov.tw/wmts/EMAP5_OPENDATA/default/GoogleMapsCompatible/14/7024/13734
```

## InkHUD 建議

目前建議優先測試 `EMAP5_OPENDATA`，因為它已經包含道路、溪流與等高線。

`MOI_CONTOUR_2` 是純等高線圖層，但原始圖磚偏黑底，直接轉成電子紙會太重，需要額外反相與去背景處理。

本 repo 的 `scripts/export_yilan_contour_inkhud.py` 會把 `MOI_CONTOUR_2` 轉成白底黑線：

- 原始黑底會被移除
- 亮色等高線與標記會轉成黑色 ink pixels
- 範圍與道路版相同：台灣 z7-z9、全宜蘭 z12、活動帶 z13、礁溪/宜蘭市/羅東 z14-z15

實測純等高線版：

- 圖磚數：`323`
- 壓縮圖磚資料：約 `441 KB`
- Heltec Wireless Paper InkHUD Flash：約 `80.1%`

注意：這是「獨立純等高線版」，不是疊加在道路版上。道路版目前 Flash 約 `98.5%`，已經沒有足夠空間再追加等高線。

## 道路 + 等高線疊圖版

`scripts/export_yilan_road_contour_inkhud.py` 會先產生白底道路圖，再把 `MOI_CONTOUR_2` 的等高線轉成黑線並疊到同一張 InkHUD tile。

為了讓 Heltec Wireless Paper 放得下，實測可刷版本使用以下取捨：

- 道路圖保留：`land`, `water`, `roads`, `highways`, `paths`
- 道路圖移除：`labels`, `transit`, `boundaries`
- 等高線只疊：`z14`, `z15`
- 圖磚數：`323`
- 壓縮圖磚資料：約 `1.05 MB`
- Heltec Wireless Paper InkHUD Flash：約 `98.3%`

曾測試把等高線疊到 `z12-z15`，壓縮圖資約 `1.26 MB`，韌體會超過 app partition。疊到 `z13-z15` 約 `1.13 MB`，仍然太貼近容量上限。

## 100m 等高線限制

截至本次測試，國土測繪中心 WMTS capabilities 只列出 `MOI_CONTOUR` 與 `MOI_CONTOUR_2` 兩個純等高線 raster 圖層，沒有獨立的「100m 等高線」圖層可以切換。

目前能做到的是使用官方 raster 圖磚中已經畫出的等高線；若圖上只標示 `500`，那通常是標高文字，不代表可以從 raster 直接篩出每 100m 的等高線。要真正控制 100m 間距，需要改用 DEM 或向量等高線資料重新產生等高線，再 rasterize 成 InkHUD 圖磚。
