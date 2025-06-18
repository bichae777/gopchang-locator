#!/opt/homebrew/Caskroom/miniconda/base/envs/gopchang-locator/bin/python
# -*- coding: utf-8 -*-

"""
Build a master GeoPackage by merging boundary, resident, facility, flow, and income datasets.
Usage:
    ./build_master.py --out data/processed/master.gpkg --crs 5186
"""

import sys
from pathlib import Path
import argparse

# Ensure we can import geopandas and its dependencies
try:
    import geopandas as gpd
except ImportError:
    sys.stderr.write(
        "[ERROR] geopandas not found. Make sure you're using the correct Python interpreter.\n"
    )
    sys.exit(1)

import pandas as pd


def load_boundary(boundary_dir: Path):
    shp_path = next(boundary_dir.glob("*.shp"), None)
    if shp_path is None:
        raise RuntimeError(f"{boundary_dir}에 .shp 파일이 없습니다.")

    gdf = gpd.read_file(shp_path)
    # find appropriate code column
    if "상권_코드" in gdf.columns:
        code_col = "상권_코드"
    elif "TRDAR_CD" in gdf.columns:
        code_col = "TRDAR_CD"
    else:
        raise ValueError(
            f"boundary shapefile에 식별용 컬럼이 없습니다. (컬럼: {list(gdf.columns)})"
        )
    gdf = gdf.rename(columns={code_col: "상권_코드"})
    return gdf


def load_points(csv_path: Path):
    df = pd.read_csv(csv_path)
    x_col, y_col = "엑스좌표_값", "와이좌표_값"
    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError(
            f"좌표 컬럼을 찾을 수 없습니다: {x_col}, {y_col} (CSV 컬럼: {list(df.columns)})"
        )
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[x_col], df[y_col]), crs=None
    )
    return gdf


def load_table(csv_path: Path, name: str):
    df = pd.read_csv(csv_path)
    if "상권_코드" not in df.columns:
        raise KeyError(f"{csv_path.name}에 '상권_코드' 컬럼이 없습니다.")
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="output GeoPackage path")
    parser.add_argument("--crs", required=True, type=int, help="target CRS EPSG code")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_path = Path(args.out)
    crs_target = f"EPSG:{args.crs}"

    # 1) boundary
    boundary = load_boundary(root / "data" / "boundary")
    boundary = boundary.to_crs(crs_target)
    boundary[["상권_코드", "geometry"]].to_file(
        out_path, layer="boundary", driver="GPKG"
    )

    # 2) resident
    resident = load_points(root / "data" / "raw" / "resident" / "resident_all.csv")
    resident = resident.set_crs(crs_target)
    resident.to_file(out_path, layer="resident", driver="GPKG")

    # 3) facility, flow, income - tabular joins
    facility = load_table(
        root / "data" / "raw" / "facility" / "facility_all.csv", "facility"
    )
    flow = load_table(root / "data" / "raw" / "flow" / "flow_all.csv", "flow")
    income = load_table(root / "data" / "raw" / "income" / "income_all.csv", "income")

    # merge all tabular into boundary
    merged = boundary.merge(facility, on="상권_코드", how="left")
    merged = merged.merge(flow, on="상권_코드", how="left")
    merged = merged.merge(income, on="상권_코드", how="left")

    # write master layer
    merged.to_file(out_path, layer="master", driver="GPKG")

    print(f"✅ Created master GeoPackage at {out_path}")


if __name__ == "__main__":
    main()
