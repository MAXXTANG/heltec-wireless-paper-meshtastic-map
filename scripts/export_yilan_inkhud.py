#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import lz4.block
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from eink_map_tiles import core as cli  # noqa: E402


DEFAULT_CENTER_LAT = 24.70
DEFAULT_CENTER_LON = 121.76
DEFAULT_STYLE = "osm-eink-white-water"
DEFAULT_ELEMENTS = ["land", "water", "roads", "highways", "paths", "boundaries", "labels", "transit"]
DEFAULT_REGIONS = [
    {
        "name": "Taiwan overview",
        "lat": 23.70,
        "lon": 120.95,
        "specs": [
            (7, 2),
            (8, 4),
            (9, 6),
        ],
    },
    {
        "name": "Yilan county",
        "bbox": (121.25, 24.30, 122.10, 25.05),
        "zooms": [12],
    },
    {
        "name": "Yilan activity plain",
        "lat": DEFAULT_CENTER_LAT,
        "lon": DEFAULT_CENTER_LON,
        "specs": [(13, 8)],
    },
    {
        "name": "Jiaoxi focus",
        "lat": 24.82703,
        "lon": 121.77535,
        "specs": [(14, 4), (15, 4)],
    },
    {
        "name": "Yilan City focus",
        "lat": 24.75911,
        "lon": 121.75374,
        "specs": [(14, 4), (15, 4)],
    },
    {
        "name": "Luodong focus",
        "lat": 24.67695,
        "lon": 121.77083,
        "specs": [(14, 4), (15, 4)],
    },
]


def grid_origin(lon: float, lat: float, zoom: int, grid: int) -> tuple[int, int]:
    n = 2**zoom
    cx = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    cy = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n
    return int(math.floor(cx - grid / 2.0 + 0.5)), int(math.floor(cy - grid / 2.0 + 0.5))


def tile_bbox(tx: int, ty: int, zoom: int, grid: int) -> tuple[float, float, float, float]:
    n = 2**zoom
    west = tx / n * 360.0 - 180.0
    east = (tx + grid) / n * 360.0 - 180.0
    north = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * ty / n))))
    south = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * (ty + grid) / n))))
    return west, south, east, north


def single_tile_bbox(tx: int, ty: int, zoom: int) -> tuple[float, float, float, float]:
    return tile_bbox(tx, ty, zoom, 1)


def parse_specs(value: str) -> list[tuple[int, int]]:
    specs: list[tuple[int, int]] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        zoom_text, grid_text = item.split(":", 1)
        zoom = int(zoom_text)
        grid = int(grid_text.lower().replace("x", ""))
        if zoom < 0 or zoom > 20:
            raise ValueError(f"invalid zoom: {zoom}")
        if grid < 1:
            raise ValueError(f"invalid grid for z{zoom}: {grid}")
        specs.append((zoom, grid))
    if not specs:
        raise ValueError("at least one zoom:grid spec is required")
    return specs


def pack_inkhud_tile(rgb_image, contrast: float, brightness: float, protect_land: bool) -> list[int]:
    bw = cli.inkhud_process(rgb_image, contrast, brightness, protect_land=protect_land)
    arr = np.array(bw, dtype=np.uint8)
    bits = (arr == 0).astype(np.uint8)
    bits_col = bits.T.reshape(32, 8, 256)
    shifts = np.array([1 << bit for bit in range(8)], dtype=np.uint8)
    packed = (bits_col * shifts[:, np.newaxis]).sum(axis=1).astype(np.uint8)
    return packed.flatten().tolist()


def render_tile(tile: cli.Tile, style: str, elements: list[str], contrast: float, brightness: float) -> tuple[int, int, int, list[int]]:
    rgb = cli.render_openfreemap_image(tile, cli.DEFAULT_USER_AGENT, 30.0, 3, elements, style)
    raw = pack_inkhud_tile(rgb, contrast, brightness, protect_land="land" in set(elements))
    return tile.z, tile.x, tile.y, raw


def build_tile_header(
    tile_data: list[tuple[int, int, int, list[int]]],
    style: str,
    region_comments: list[str],
) -> tuple[str, int]:
    zoom_set = sorted({tile[0] for tile in tile_data})
    compressed = [lz4.block.compress(bytes(raw), store_size=False) for _, _, _, raw in tile_data]
    total_bytes = sum(len(item) for item in compressed)

    lines = [
        "#pragma once",
        "#include <stdint.h>",
        "",
        f"// Taiwan + Yilan InkHUD offline map: {len(tile_data)} tiles, zooms [{', '.join(str(z) for z in zoom_set)}]",
        f"// style: {style}",
        "// Each tile is 256x256px = 8192 bytes uncompressed, stored as raw LZ4 blocks.",
        "// Byte layout is COLUMN-MAJOR: byte = tile[(px/8)*256 + py], bit = px%8.",
    ]
    lines.extend(f"// {comment}" for comment in region_comments)
    lines.extend([
        "",
        f"static const int map_tile_count = {len(tile_data)};",
        "static const int map_tile_zooms[] = { " + ", ".join(str(z) for z, _, _, _ in tile_data) + " };",
        "static const int map_tile_tx[]    = { " + ", ".join(str(tx) for _, tx, _, _ in tile_data) + " };",
        "static const int map_tile_ty[]    = { " + ", ".join(str(ty) for _, _, ty, _ in tile_data) + " };",
        "static const int map_tile_sizes[] = { " + ", ".join(str(len(item)) for item in compressed) + " };",
        "",
    ])

    for index, ((zoom, tx, ty, _), data) in enumerate(zip(tile_data, compressed)):
        lines.append(f"static const uint8_t map_tile_data_{index}[] = {{  // z{zoom}/{tx}/{ty}, {len(data)} bytes")
        for offset in range(0, len(data), 16):
            lines.append("    " + ", ".join(f"0x{byte:02X}" for byte in data[offset : offset + 16]) + ",")
        lines.append("};")
        lines.append("")

    lines.append("static const uint8_t* const map_tile_data[] = { " + ", ".join(f"map_tile_data_{i}" for i in range(len(tile_data))) + " };")
    lines.append("")
    return "\n".join(lines), total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Taiwan overview + Yilan detailed InkHUD MapTile.h.")
    parser.add_argument("--style", default=DEFAULT_STYLE)
    parser.add_argument("--brightness", type=float, default=0.96)
    parser.add_argument("--contrast", type=float, default=0.96)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "yilan_exports" / "MapTile.h")
    args = parser.parse_args()

    tiles: list[cli.Tile] = []
    region_comments: list[str] = []
    seen: set[tuple[int, int, int]] = set()
    print("Taiwan + Yilan InkHUD export")
    for region in DEFAULT_REGIONS:
        name = str(region["name"])
        if "bbox" in region:
            west, south, east, north = tuple(float(v) for v in region["bbox"])
            zooms = [int(z) for z in region["zooms"]]
            bbox = cli.BBox(west=west, south=south, east=east, north=north)
            region_tiles = cli.tiles_for_bbox(bbox, zooms)
            region_comments.append(
                f"{name}: bbox west={west:.6f} south={south:.6f} east={east:.6f} north={north:.6f}; zooms {', '.join(f'z{z}' for z in zooms)}"
            )
            print(f"\n{name}: {west:.6f},{south:.6f} -> {east:.6f},{north:.6f}")
            print(f"  zooms {', '.join(str(z) for z in zooms)}: {len(region_tiles)} tiles")
            for tile in region_tiles:
                key = (tile.z, tile.x, tile.y)
                if key in seen:
                    continue
                seen.add(key)
                tiles.append(tile)
            continue

        lat = float(region["lat"])
        lon = float(region["lon"])
        specs = list(region["specs"])
        spec_text = ", ".join(f"z{z}:{g}x{g}" for z, g in specs)
        region_comments.append(f"{name}: center lat={lat:.6f} lon={lon:.6f}; specs {spec_text}")
        print(f"\n{name}: {lat:.6f}, {lon:.6f}")
        for zoom, grid in specs:
            tx0, ty0 = grid_origin(lon, lat, zoom, grid)
            west, south, east, north = tile_bbox(tx0, ty0, zoom, grid)
            print(f"  z{zoom} {grid}x{grid}: {west:.3f},{south:.3f} -> {east:.3f},{north:.3f} ({grid * grid} tiles)")
            for dy in range(grid):
                for dx in range(grid):
                    tile = cli.Tile(z=zoom, x=tx0 + dx, y=ty0 + dy)
                    key = (tile.z, tile.x, tile.y)
                    if key in seen:
                        continue
                    seen.add(key)
                    tiles.append(tile)

    tile_data: list[tuple[int, int, int, list[int]]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(render_tile, tile, args.style, DEFAULT_ELEMENTS, args.contrast, args.brightness): tile
            for tile in tiles
        }
        for index, future in enumerate(as_completed(futures), 1):
            tile = futures[future]
            tile_data.append(future.result())
            print(f"  rendered {index:3d}/{len(tiles)} z{tile.z}/{tile.x}/{tile.y}")

    tile_data.sort(key=lambda item: (item[0], item[1], item[2]))
    header, total_bytes = build_tile_header(tile_data, args.style, region_comments)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header, encoding="utf-8")

    raw_bytes = len(tile_data) * 8192
    print(f"Saved: {args.out}")
    print(f"Compressed tiles: {total_bytes:,} bytes ({total_bytes / raw_bytes * 100:.1f}% of {raw_bytes:,} raw bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
