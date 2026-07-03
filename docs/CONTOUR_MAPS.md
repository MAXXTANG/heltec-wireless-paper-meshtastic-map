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

注意：加入等高線會增加地圖細節與壓縮容量。現在這版韌體 Flash 約 `98.5%`，要加入等高線前，必須先刪減部分 z14/z15 圖磚。
