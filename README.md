# 🍖 곱창집 입지 분석 프로젝트 (Gopchang Locator)

서울시 공개 데이터와 민간 데이터를 활용한 곱창집 최적 입지 분석 프로젝트

## 📋 프로젝트 개요

### 목표
- 서울시 상권별 곱창집 입지 경쟁력 분석
- 야간 유동인구, 상주인구, 추정매출 등 다차원 지표 기반 스코어링
- 최적 입지 Top 10 추출 및 투자 의사결정 지원

### 핵심 분석 지표
- **T1**: 검색·리뷰 인지도 지수 (네이버 API)
- **T2**: 야간 체류인구 (18-01시 기준)
- **C1**: ㎡당 임대비율
- **C2**: 재료비 비중
- **E1**: 경쟁밀도 지수
- **F1**: 5년 IRR

## 🗂️ 프로젝트 구조

```
gopchang-locator/
│
├── README.md              # 프로젝트 개요·설치 방법
├── env.yml                # conda 환경 설정
├── .gitignore             # Git 추적 제외 파일
│
├── notebooks/             # 📒 Jupyter 노트북
│   ├── 00_eda_night_window.ipynb    # 야간 시간대 정의 EDA
│   ├── 01_fetch_openapi.ipynb       # 서울 열린데이터 수집
│   └── 02_master_build.ipynb        # 통합 데이터셋 구축
│
├── data/                  # 📂 데이터 저장소
│   ├── boundary/          # 상권 경계 Shapefile (OA-15560)
│   ├── raw/               # 공개 API CSV 원본
│   │   ├── resident/      # 상주인구 (OA-15584)
│   │   ├── flow/          # 유동인구 (OA-15568)
│   │   ├── sales/         # 추정매출 (OA-15572)
│   │   ├── income_exp/    # 소득·소비 (OA-21278)
│   │   └── facility/      # 집객시설 (OA-15581)
│   ├── card/              # 민간 카드매출 CSV
│   ├── rent/              # 직방 임대료 데이터
│   └── processed/         # 통합·파생 데이터 (GPKG)
│
├── scripts/               # 🛠️ 재실행 가능한 스크립트
│   ├── fetch_openapi.py   # 서울 열린데이터 자동 다운로드
│   └── build_master.py    # 마스터 데이터셋 구축
│
└── docs/                  # 📑 보고서 및 산출물
    └── night_window_definition.pdf
```

## 🔧 설치 및 환경 설정

### 1. 레포지토리 클론
```bash
git clone <repository-url>
cd gopchang-locator
```

### 2. Conda 환경 생성
```bash
# 환경 생성
conda env create -f env.yml

# 환경 활성화
conda activate gopchang-locator
```

### 3. Jupyter 설정 (선택사항)
```bash
# 노트북 커밋 시 출력 셀 제거
nbstripout --install --attributes .gitattributes
```

## 📊 데이터 소스

### 서울 열린데이터
| 데이터셋 | 코드 | 설명 | 갱신주기 |
|---------|------|------|----------|
| 상권 경계 | OA-15560 | 서울시 상권 영역 Shapefile | 연 1회 |
| 상주인구 | OA-15584 | 상권별 거주인구 현황 | 분기 |
| 유동인구 | OA-15568 | 길단위 시간대별 유동인구 | 일별 |
| 추정매출 | OA-15572 | 상권별 업종별 추정매출 | 분기 |
| 소득·소비 | OA-21278 | 상권별 소득 및 소비 현황 | 분기 |
| 집객시설 | OA-15581 | 상권 배후지 집객시설 현황 | 연 1회 |

### 민간 데이터
- 카드매출 데이터 (곱창/주류 업종)
- 부동산 임대료 (직방 등)
- 경쟁매장 위치 정보
- 네이버 검색/리뷰 트렌드

## 🚀 실행 순서

### Phase 1: 기초 분석 (W1-A)
```bash
# 1. 야간 시간대 정의
jupyter notebook notebooks/00_eda_night_window.ipynb

# 2. 데이터 수집 현황 확인
jupyter notebook notebooks/01_fetch_openapi.ipynb
```

### Phase 2: 데이터 통합 (W2-A)
```bash
# 3. 마스터 데이터셋 구축
jupyter notebook notebooks/02_master_build.ipynb

# 또는 스크립트 실행
python scripts/build_master.py
```

### Phase 3: 분석 및 시각화 (W3-W4)
- KPI 지표 계산
- 상권별 스코어링
- 입지 추천 결과 도출

## 📈 주요 산출물

1. **야간 시간대 정의서**: `docs/night_window_definition.pdf`
2. **마스터 데이터셋**: `data/processed/seoul_gopchang_master.gpkg`
3. **입지 분석 맵**: `gopchang_map.html`
4. **최종 보고서**: `docs/곱창_입지전략_v1.pdf`

## 🎯 KPI 목표값

| 지표 | 목표 | 설명 |
|------|------|------|
| T1 (인지도) | ≥ 0.55 | 상위 30% 트렌드 상권 |
| T2 (야간인구) | 상위 30% | 18-01시 평균 유동인구 |
| C1 (임대비율) | ≤ 0.20 | 임대료/매출 비율 20% 이하 |
| E1 (경쟁밀도) | ≤ 0.5 | 블루오션 상권 |
| F1 (IRR) | ≥ 18% | 5년 내부수익률 |

## 🔍 문제 해결

### 자주 발생하는 오류
1. **GeoPandas 설치 오류**: conda-forge 채널 우선순위 확인
2. **인코딩 오류**: CSV 파일은 EUC-KR 인코딩 사용
3. **메모리 부족**: 대용량 CSV는 청크 단위 처리

### 연락처
- 프로젝트 리드: [담당자명]
- 데이터 엔지니어: [담당자명]
- 분석 팀: [담당자명]

## 📝 라이선스

This project is for internal analysis purpose only.

---

**마지막 업데이트**: 2024년 12월