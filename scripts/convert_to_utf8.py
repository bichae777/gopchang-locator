#!/usr/bin/env python3
import argparse
import glob
import pathlib
import chardet
import pandas as pd


def convert_file(path, bom=False):
    # 감지
    raw = pathlib.Path(path).read_bytes()
    enc = chardet.detect(raw)["encoding"] or "utf-8"
    print(f"Converting: {path} (detected encoding: {enc})")
    # 읽기
    try:
        df = pd.read_csv(path, encoding=enc)
    except Exception as e:
        print(f"  [Error] Failed to read {path}: {e}")
        return
    # 저장
    out_path = pathlib.Path(path)
    try:
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  [OK] Wrote UTF-8 to {out_path}")
    except Exception as e:
        print(f"  [Error] Failed to write {out_path}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV files to UTF-8")
    parser.add_argument("patterns", nargs="+", help="파일 패턴 (예: data/raw/*/*.csv)")
    args = parser.parse_args()

    files = []
    for pat in args.patterns:
        files.extend(glob.glob(pat, recursive=True))
    files = sorted(set(files))

    if not files:
        print("No files matched the given patterns.")
        exit(1)

    for f in files:
        convert_file(f)
