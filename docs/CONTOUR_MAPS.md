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
