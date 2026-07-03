#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import lz4.block
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
EINK_REPO_ROOT = Path.cwd()
sys.path.insert(0, str(EINK_REPO_ROOT / "src"))

from eink_map_tiles import core as cli  # noqa: E402


DEFAULT_STYLE = "osm-eink-white-water"
DEFAULT_ELEMENTS = ["land", "water", "roads", "highways", "paths", "boundaries", "labels", "transit"]


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


def pack_inkhud_tile(rgb_image, contrast: float, brightness: float, protect_land: bool) -> list[int]:
    bw = cli.inkhud_process(rgb_image, contrast, brightness, protect_land=protect_land)
    arr = np.array(bw, dtype=np.uint8)
    bits = (arr == 0).astype(np.uint8)
    bits_col = bits.T.reshape(32, 8, 256)
    shifts = np.array([1 << bit for bit in range(8)], dtype=np.uint8)
    packed = (bits_col * shifts[:, np.newaxis]).sum(axis=1).astype(np.uint8)
    return packed.flatten().tolist()


def render_tile(
    tile: cli.Tile,
    style: str,
    elements: list[str],
    contrast: float,
    brightness: float,
) -> tuple[int, int, int, list[int]]:
    rgb = cli.render_openfreemap_image(tile, cli.DEFAULT_USER_AGENT, 30.0, 3, elements, style)
    raw = pack_inkhud_tile(rgb, contrast, brightness, protect_land="land" in set(elements))
    return tile.z, tile.x, tile.y, raw


def collect_tiles(config: dict[str, Any]) -> tuple[list[cli.Tile], list[str]]:
    tiles: list[cli.Tile] = []
    region_comments: list[str] = []
    seen: set[tuple[int, int, int]] = set()

    for region in config["regions"]:
        name = str(region["name"])
        region_type = str(region["type"])

        if region_type == "bbox":
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
                if key not in seen:
                    seen.add(key)
                    tiles.append(tile)
            continue

        if region_type != "grid":
            raise ValueError(f"unsupported region type for {name}: {region_type}")

        lat = float(region["lat"])
        lon = float(region["lon"])
        specs = [(int(spec["zoom"]), int(spec["grid"])) for spec in region["specs"]]
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
                    if key not in seen:
                        seen.add(key)
                        tiles.append(tile)

    return tiles, region_comments


def build_tile_header(
    tile_data: list[tuple[int, int, int, list[int]]],
    config: dict[str, Any],
    style: str,
    region_comments: list[str],
) -> tuple[str, int]:
    zoom_set = sorted({tile[0] for tile in tile_data})
    compressed = [lz4.block.compress(bytes(raw), store_size=False) for _, _, _, raw in tile_data]
    total_bytes = sum(len(item) for item in compressed)
    display_name = config.get("display_name", config["slug"])

    lines = [
        "#pragma once",
        "#include <stdint.h>",
        "",
        f"// {display_name} InkHUD offline map: {len(tile_data)} tiles, zooms [{', '.join(str(z) for z in zoom_set)}]",
        f"// slug: {config['slug']}",
        f"// style: {style}",
        "// Each tile is 256x256px = 8192 bytes uncompressed, stored as raw LZ4 blocks.",
        "// Byte layout is COLUMN-MAJOR: byte = tile[(px/8)*256 + py], bit = px%8.",
    ]
    if config.get("description"):
        lines.append(f"// {config['description']}")
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


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if "slug" not in config:
        raise ValueError(f"{path} is missing slug")
    if "regions" not in config:
        raise ValueError(f"{path} is missing regions")
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a region InkHUD MapTile.h from a region JSON file.")
    parser.add_argument("region", type=Path, help="Path to a regions/*.json file.")
    parser.add_argument("--brightness", type=float, default=0.96)
    parser.add_argument("--contrast", type=float, default=0.96)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", type=Path, help="Output MapTile.h path. Defaults to yilan_exports/<slug>/MapTile.h.")
    args = parser.parse_args()

    config = load_config(args.region)
    style = str(config.get("style", DEFAULT_STYLE))
    elements = [str(item) for item in config.get("elements", DEFAULT_ELEMENTS)]
    out = args.out or EINK_REPO_ROOT / "yilan_exports" / str(config["slug"]) / "MapTile.h"

    print(f"{config.get('display_name', config['slug'])} InkHUD export")
    print(f"Region config: {args.region}")
    print(f"Style: {style}")
    print(f"Elements: {', '.join(elements)}")

    tiles, region_comments = collect_tiles(config)

    tile_data: list[tuple[int, int, int, list[int]]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(render_tile, tile, style, elements, args.contrast, args.brightness): tile
            for tile in tiles
        }
        for index, future in enumerate(as_completed(futures), 1):
            tile = futures[future]
            tile_data.append(future.result())
            print(f"  rendered {index:3d}/{len(tiles)} z{tile.z}/{tile.x}/{tile.y}")

    tile_data.sort(key=lambda item: (item[0], item[1], item[2]))
    header, total_bytes = build_tile_header(tile_data, config, style, region_comments)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header, encoding="utf-8")

    raw_bytes = len(tile_data) * 8192
    print(f"Saved: {out}")
    print(f"Compressed tiles: {total_bytes:,} bytes ({total_bytes / raw_bytes * 100:.1f}% of {raw_bytes:,} raw bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
