#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

import lz4.block
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from eink_map_tiles import core as cli  # noqa: E402


DEFAULT_CENTER_LAT = 24.70
DEFAULT_CENTER_LON = 121.76
DEFAULT_STYLE = "osm-eink-white-water"
DEFAULT_ELEMENTS = ["land", "water", "roads", "highways", "paths", "boundaries"]
DEFAULT_CONTOUR_LAYER = "MOI_CONTOUR_2"
DEFAULT_CONTOUR_ZOOMS = {12, 13, 14, 15}
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


def parse_zoom_set(value: str) -> set[int]:
    zooms: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        zoom = int(item)
        if zoom < 0 or zoom > 20:
            raise ValueError(f"invalid zoom: {zoom}")
        zooms.add(zoom)
    return zooms


def collect_tiles() -> tuple[list[cli.Tile], list[str]]:
    tiles: list[cli.Tile] = []
    region_comments: list[str] = []
    seen: set[tuple[int, int, int]] = set()

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
                if key not in seen:
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
                    if key not in seen:
                        seen.add(key)
                        tiles.append(tile)

    return tiles, region_comments


def pack_bits(bits: np.ndarray) -> list[int]:
    bits_col = bits.astype(np.uint8).T.reshape(32, 8, 256)
    shifts = np.array([1 << bit for bit in range(8)], dtype=np.uint8)
    packed = (bits_col * shifts[:, np.newaxis]).sum(axis=1).astype(np.uint8)
    return packed.flatten().tolist()


def road_bits(rgb_image: Image.Image, contrast: float, brightness: float) -> np.ndarray:
    bw = cli.inkhud_process(rgb_image, contrast, brightness, protect_land=True)
    return (np.array(bw, dtype=np.uint8) == 0)


def fetch_nlsc_tile(tile: cli.Tile, layer: str, timeout: float, retries: int) -> Image.Image:
    url = f"https://wmts.nlsc.gov.tw/wmts/{layer}/default/GoogleMapsCompatible/{tile.z}/{tile.y}/{tile.x}"
    context = ssl._create_unverified_context()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": cli.DEFAULT_USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                data = response.read()
            return Image.open(BytesIO(data)).convert("RGBA")
        except Exception as exc:  # noqa: BLE001 - retry all transient WMTS/image errors.
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def contour_bits(image: Image.Image, threshold: int) -> np.ndarray:
    rgba = np.array(image.convert("RGBA"), dtype=np.uint8)
    alpha = rgba[:, :, 3]
    rgb = rgba[:, :, :3].astype(np.int16)
    brightness = rgb.mean(axis=2)

    # NLSC contour tiles use a black transparent-looking canvas with bright strokes.
    # Treat only bright non-transparent pixels as InkHUD black pixels.
    return (alpha > 0) & (brightness >= threshold)


def render_tile(
    tile: cli.Tile,
    style: str,
    elements: list[str],
    contrast: float,
    brightness: float,
    contour_layer: str,
    contour_zooms: set[int],
    contour_threshold: int,
) -> tuple[int, int, int, list[int]]:
    rgb = cli.render_openfreemap_image(tile, cli.DEFAULT_USER_AGENT, 30.0, 3, elements, style)
    bits = road_bits(rgb, contrast, brightness)
    if tile.z in contour_zooms:
        contour = fetch_nlsc_tile(tile, contour_layer, 30.0, 3)
        bits = bits | contour_bits(contour, contour_threshold)
    raw = pack_bits(bits)
    return tile.z, tile.x, tile.y, raw


def build_tile_header(
    tile_data: list[tuple[int, int, int, list[int]]],
    style: str,
    contour_layer: str,
    contour_zooms: set[int],
    region_comments: list[str],
) -> tuple[str, int]:
    zoom_set = sorted({tile[0] for tile in tile_data})
    compressed = [lz4.block.compress(bytes(raw), store_size=False) for _, _, _, raw in tile_data]
    total_bytes = sum(len(item) for item in compressed)
    contour_text = ", ".join(f"z{z}" for z in sorted(contour_zooms))

    lines = [
        "#pragma once",
        "#include <stdint.h>",
        "",
        f"// Taiwan + Yilan InkHUD road + contour map: {len(tile_data)} tiles, zooms [{', '.join(str(z) for z in zoom_set)}]",
        f"// road style: {style}",
        f"// contour layer: {contour_layer}; applied on {contour_text if contour_text else 'none'}",
        "// Road tiles: OpenFreeMap / OpenStreetMap. Contours: National Land Surveying and Mapping Center WMTS.",
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
    parser = argparse.ArgumentParser(description="Export Taiwan + Yilan road+contour InkHUD MapTile.h.")
    parser.add_argument("--style", default=DEFAULT_STYLE)
    parser.add_argument("--brightness", type=float, default=0.96)
    parser.add_argument("--contrast", type=float, default=0.96)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--contour-layer", default=DEFAULT_CONTOUR_LAYER)
    parser.add_argument("--contour-threshold", type=int, default=80)
    parser.add_argument("--contour-zooms", default=",".join(str(z) for z in sorted(DEFAULT_CONTOUR_ZOOMS)))
    parser.add_argument(
        "--elements",
        default=",".join(DEFAULT_ELEMENTS),
        help="Comma-separated OpenFreeMap element list. Default removes labels to save firmware space.",
    )
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "yilan_exports" / "MapTile_road_contour.h")
    args = parser.parse_args()

    elements = [item.strip() for item in args.elements.split(",") if item.strip()]
    contour_zooms = parse_zoom_set(args.contour_zooms)

    print("Taiwan + Yilan InkHUD road + contour export")
    print(f"Road elements: {', '.join(elements)}")
    print(f"Contour layer: {args.contour_layer}")
    print(f"Contour zooms: {', '.join(str(z) for z in sorted(contour_zooms))}")
    tiles, region_comments = collect_tiles()

    tile_data: list[tuple[int, int, int, list[int]]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(
                render_tile,
                tile,
                args.style,
                elements,
                args.contrast,
                args.brightness,
                args.contour_layer,
                contour_zooms,
                args.contour_threshold,
            ): tile
            for tile in tiles
        }
        for index, future in enumerate(as_completed(futures), 1):
            tile = futures[future]
            tile_data.append(future.result())
            print(f"  rendered {index:3d}/{len(tiles)} z{tile.z}/{tile.x}/{tile.y}")

    tile_data.sort(key=lambda item: (item[0], item[1], item[2]))
    header, total_bytes = build_tile_header(tile_data, args.style, args.contour_layer, contour_zooms, region_comments)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header, encoding="utf-8")

    raw_bytes = len(tile_data) * 8192
    print(f"Saved: {args.out}")
    print(f"Compressed tiles: {total_bytes:,} bytes ({total_bytes / raw_bytes * 100:.1f}% of {raw_bytes:,} raw bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
