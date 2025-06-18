# scripts/preprocess_csvs.py

import pandas as pd
from pathlib import Path

# ——————————————————————————————————————————————
# 1) 여기에 필요한 한글→영어 매핑을 추가하세요.
#    예) '상권_코드':'market_code'
COLUMN_MAP = {
    # 공통 키
    "상권_코드": "market_code",
    "상권_코드_명": "market_name",
    "기준_년분기_코드": "period_quarter",
    # resident_all.csv
    "총_상주인구_수": "resident_total",
    "남성_상주인구_수": "resident_male",
    "여성_상주인구_수": "resident_female",
    # facility_all.csv
    "집객시설_수": "facility_count",
    "관공서_수": "public_office_count",
    # income_all.csv
    "총_가구당_소득_평균": "avg_income_per_household",
    # flow_all.csv
    "유동인구_수": "flow_population",
    # 필요에 따라 계속 추가…
}
# ——————————————————————————————————————————————

RAW_DIR = Path("data/raw")

for subdir in ["resident", "facility", "income", "flow"]:
    csv_path = RAW_DIR / subdir / f"{subdir}_all.csv"
    df = pd.read_csv(csv_path, encoding="utf-8")
    # 2) 컬럼명 변경
    df = df.rename(columns=COLUMN_MAP)
    # 3) 변경된 CSV로 덮어쓰기
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(
        f"✔ {csv_path} processed, {len([c for c in df.columns if c in COLUMN_MAP])} columns renamed"
    )
