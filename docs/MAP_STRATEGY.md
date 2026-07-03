# 宜蘭圖資切分策略

InkHUD 離線地圖不是 SD 卡地圖，也不是線上地圖。圖磚會被壓縮後編進韌體，所以 Flash 空間是最大限制。

## 目前採用策略

```text
Taiwan overview: z7-z9
Yilan county: z12
Yilan activity plain: z13
Jiaoxi focus: z14-z15
Yilan City focus: z14-z15
Luodong focus: z14-z15
```

## 實測容量

目前版本：

- 圖磚數：`323`
- `MapTile.h` 文字檔：約 `6.6 MB`
- 壓縮圖磚資料：約 `1.05 MB`
- 韌體 app bin：約 `3.29 MB`
- Flash 使用率：約 `98.5%`

## 全宜蘭高縮放不可行

用粗略宜蘭範圍：

```text
west=121.25
south=24.30
east=122.10
north=25.05
```

估算：

| Zoom | 約略圖磚數 | 估計壓縮容量 |
|---:|---:|---:|
| z12 | 110 | 約 0.3 MB |
| z13 | 400 | 約 1.4 MB |
| z14 | 1,521 | 約 7.8 MB |
| z15 | 5,928 | 約 23 MB |

因此全宜蘭做到 z14 或 z15 都不適合 Heltec Wireless Paper。

## 建議修改方式

如果你要換活動地點，優先改三個 focus regions：

```python
{
    "name": "Jiaoxi focus",
    "lat": 24.82703,
    "lon": 121.77535,
    "specs": [(14, 4), (15, 4)],
}
```

`4x4` 大約覆蓋：

- z14：約 8-9 km 寬
- z15：約 4-5 km 寬

如果 Flash 爆掉，先把 z15 從 `4x4` 改成 `3x3`。
