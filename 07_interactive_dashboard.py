# 🚀 곱창집 입지 분석 인터랙티브 대시보드
# 07_interactive_dashboard.py
#
# 목적: 전체 분석 결과를 통합한 실시간 인터랙티브 웹 대시보드
# 기능: 상권 비교, 필터링, 지도 연동, 투자 시뮬레이터
# 실행: python 07_interactive_dashboard.py
# ================================================================================

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import json


# 📂 데이터 로드 함수
def load_data():
    """모든 분석 결과 데이터 로드"""
    try:
        OUTPUT_PATH = Path("docs")

        # TOP 30 결과
        top30_df = pd.read_csv(
            OUTPUT_PATH / "gopchang_top30_locations_v2.csv", encoding="utf-8-sig"
        )

        # 좌표 정보
        coords_df = pd.read_csv(
            OUTPUT_PATH / "gopchang_top30_coordinates.csv", encoding="utf-8-sig"
        )

        # 투자 계획
        investment_df = pd.read_csv(
            OUTPUT_PATH / "gopchang_investment_plan.csv", encoding="utf-8-sig"
        )

        print("✅ 모든 데이터 로드 완료")
        return top30_df, coords_df, investment_df

    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        # 샘플 데이터 생성
        return create_sample_data()


def create_sample_data():
    """샘플 데이터 생성 (테스트용)"""
    sample_data = {
        "상권_코드_명": ["강남역", "홍대입구역", "명동", "신촌역", "종로3가역"],
        "곱창집_적합도_v2": [46.8, 35.5, 38.8, 38.1, 36.6],
        "T1_야간유동인구": [2521295, 1624245, 1657878, 2150525, 1775563],
        "한식_월매출": [
            56439136006,
            27852500000,
            105631000000,
            20004622800,
            35012517932,
        ],
        "T1_점수_v2": [100, 64, 65, 85, 70],
        "T2_점수_v2": [8, 6, 23, 3, 7],
        "C1_점수_v2": [27, 27, 27, 27, 27],
        "C2_점수_v2": [40, 14, 43, 9, 31],
        "E1_점수_v2": [34, 74, 18, 51, 39],
    }
    return (
        pd.DataFrame(sample_data),
        pd.DataFrame(sample_data),
        pd.DataFrame(sample_data),
    )


def classify_district_type(name):
    """상권 유형 분류"""
    if any(keyword in name for keyword in ["강남", "역삼", "선릉", "신논현"]):
        return "프리미엄 비즈니스"
    elif any(keyword in name for keyword in ["홍대", "연남", "망리단"]):
        return "젊은층 문화"
    elif any(keyword in name for keyword in ["신촌", "대학로", "신림", "건대"]):
        return "대학가"
    elif any(keyword in name for keyword in ["명동", "종로", "북창동", "관광특구"]):
        return "관광/전통상권"
    elif any(
        keyword in name for keyword in ["노원", "수유", "불광", "영등포", "노량진"]
    ):
        return "지역 거점"
    else:
        return "복합상권"


# 📊 데이터 로드 및 전처리
top30_df, coords_df, investment_df = load_data()

# 상권 유형 추가
top30_df["상권유형"] = top30_df["상권_코드_명"].apply(classify_district_type)


# 투자 규모 분류
def classify_investment_level(korean_sales):
    if korean_sales >= 50000000000:
        return "고투자"
    elif korean_sales >= 20000000000:
        return "중투자"
    else:
        return "저투자"


top30_df["투자규모"] = top30_df["한식_월매출"].apply(classify_investment_level)

# 🎨 Dash 앱 초기화
app = dash.Dash(__name__)
app.title = "🍖 곱창집 입지 분석 대시보드"

# 🎨 CSS 스타일
colors = {
    "background": "#f8f9fa",
    "text": "#2c3e50",
    "primary": "#e74c3c",
    "secondary": "#3498db",
    "success": "#27ae60",
    "warning": "#f39c12",
}

# 📱 레이아웃 정의
app.layout = html.Div(
    [
        # 헤더
        html.Div(
            [
                html.H1(
                    "🍖 곱창집 입지 분석 대시보드",
                    style={
                        "textAlign": "center",
                        "color": colors["primary"],
                        "marginBottom": "10px",
                    },
                ),
                html.P(
                    "데이터 기반 최적 상권 선정 및 투자 시뮬레이션",
                    style={
                        "textAlign": "center",
                        "color": colors["text"],
                        "fontSize": "18px",
                    },
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "marginBottom": "20px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
        ),
        # 필터 패널
        html.Div(
            [
                html.H3("🔍 필터 옵션", style={"color": colors["text"]}),
                html.Div(
                    [
                        # 상권 유형 필터
                        html.Div(
                            [
                                html.Label("상권 유형:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="district-type-filter",
                                    options=[{"label": "전체", "value": "all"}]
                                    + [
                                        {"label": dtype, "value": dtype}
                                        for dtype in top30_df["상권유형"].unique()
                                    ],
                                    value="all",
                                    style={"marginBottom": "10px"},
                                ),
                            ],
                            style={"width": "48%", "display": "inline-block"},
                        ),
                        # 투자 규모 필터
                        html.Div(
                            [
                                html.Label("투자 규모:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="investment-level-filter",
                                    options=[{"label": "전체", "value": "all"}]
                                    + [
                                        {"label": level, "value": level}
                                        for level in top30_df["투자규모"].unique()
                                    ],
                                    value="all",
                                    style={"marginBottom": "10px"},
                                ),
                            ],
                            style={
                                "width": "48%",
                                "float": "right",
                                "display": "inline-block",
                            },
                        ),
                    ]
                ),
                # 점수 범위 슬라이더
                html.Div(
                    [
                        html.Label("적합도 점수 범위:", style={"fontWeight": "bold"}),
                        dcc.RangeSlider(
                            id="score-range-slider",
                            min=top30_df["곱창집_적합도_v2"].min(),
                            max=top30_df["곱창집_적합도_v2"].max(),
                            value=[
                                top30_df["곱창집_적합도_v2"].min(),
                                top30_df["곱창집_적합도_v2"].max(),
                            ],
                            marks={
                                i: f"{i}점"
                                for i in range(
                                    int(top30_df["곱창집_적합도_v2"].min()),
                                    int(top30_df["곱창집_적합도_v2"].max()) + 1,
                                    5,
                                )
                            },
                            step=0.5,
                        ),
                    ],
                    style={"marginTop": "20px"},
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "marginBottom": "20px",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            },
        ),
        # 메인 대시보드
        html.Div(
            [
                # 첫 번째 행: KPI 카드들
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4(
                                    "📊 총 분석 상권",
                                    style={
                                        "color": colors["text"],
                                        "marginBottom": "5px",
                                    },
                                ),
                                html.H2(
                                    id="total-districts",
                                    style={"color": colors["primary"], "margin": "0"},
                                ),
                            ],
                            className="kpi-card",
                            style={
                                "width": "23%",
                                "display": "inline-block",
                                "margin": "1%",
                                "backgroundColor": "white",
                                "padding": "20px",
                                "textAlign": "center",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                "borderRadius": "5px",
                            },
                        ),
                        html.Div(
                            [
                                html.H4(
                                    "🏆 평균 적합도",
                                    style={
                                        "color": colors["text"],
                                        "marginBottom": "5px",
                                    },
                                ),
                                html.H2(
                                    id="avg-score",
                                    style={"color": colors["success"], "margin": "0"},
                                ),
                            ],
                            className="kpi-card",
                            style={
                                "width": "23%",
                                "display": "inline-block",
                                "margin": "1%",
                                "backgroundColor": "white",
                                "padding": "20px",
                                "textAlign": "center",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                "borderRadius": "5px",
                            },
                        ),
                        html.Div(
                            [
                                html.H4(
                                    "👥 평균 야간유동",
                                    style={
                                        "color": colors["text"],
                                        "marginBottom": "5px",
                                    },
                                ),
                                html.H2(
                                    id="avg-flow",
                                    style={"color": colors["secondary"], "margin": "0"},
                                ),
                            ],
                            className="kpi-card",
                            style={
                                "width": "23%",
                                "display": "inline-block",
                                "margin": "1%",
                                "backgroundColor": "white",
                                "padding": "20px",
                                "textAlign": "center",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                "borderRadius": "5px",
                            },
                        ),
                        html.Div(
                            [
                                html.H4(
                                    "💰 평균 한식매출",
                                    style={
                                        "color": colors["text"],
                                        "marginBottom": "5px",
                                    },
                                ),
                                html.H2(
                                    id="avg-sales",
                                    style={"color": colors["warning"], "margin": "0"},
                                ),
                            ],
                            className="kpi-card",
                            style={
                                "width": "23%",
                                "display": "inline-block",
                                "margin": "1%",
                                "backgroundColor": "white",
                                "padding": "20px",
                                "textAlign": "center",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                                "borderRadius": "5px",
                            },
                        ),
                    ],
                    style={"marginBottom": "20px"},
                ),
                # 두 번째 행: 메인 차트들
                html.Div(
                    [
                        # 적합도 순위 차트
                        html.Div(
                            [dcc.Graph(id="ranking-chart")],
                            style={
                                "width": "48%",
                                "display": "inline-block",
                                "margin": "1%",
                            },
                        ),
                        # 레이더 차트
                        html.Div(
                            [dcc.Graph(id="radar-chart")],
                            style={
                                "width": "48%",
                                "display": "inline-block",
                                "margin": "1%",
                            },
                        ),
                    ]
                ),
                # 세 번째 행: 상세 분석
                html.Div(
                    [
                        # 산점도 차트
                        html.Div(
                            [dcc.Graph(id="scatter-chart")],
                            style={
                                "width": "48%",
                                "display": "inline-block",
                                "margin": "1%",
                            },
                        ),
                        # 투자 분석 차트
                        html.Div(
                            [dcc.Graph(id="investment-chart")],
                            style={
                                "width": "48%",
                                "display": "inline-block",
                                "margin": "1%",
                            },
                        ),
                    ]
                ),
                # 네 번째 행: 데이터 테이블
                html.Div(
                    [
                        html.H3("📋 상권별 상세 정보", style={"color": colors["text"]}),
                        dash_table.DataTable(
                            id="districts-table",
                            columns=[
                                {"name": "순위", "id": "rank"},
                                {"name": "상권명", "id": "상권_코드_명"},
                                {
                                    "name": "적합도",
                                    "id": "곱창집_적합도_v2",
                                    "type": "numeric",
                                    "format": {"specifier": ".1f"},
                                },
                                {"name": "상권유형", "id": "상권유형"},
                                {"name": "투자규모", "id": "투자규모"},
                                {
                                    "name": "야간유동인구",
                                    "id": "T1_야간유동인구",
                                    "type": "numeric",
                                    "format": {"specifier": ",.0f"},
                                },
                                {
                                    "name": "한식매출(억원)",
                                    "id": "한식매출_억",
                                    "type": "numeric",
                                    "format": {"specifier": ".1f"},
                                },
                            ],
                            style_cell={"textAlign": "center", "fontSize": "12px"},
                            style_header={
                                "backgroundColor": colors["primary"],
                                "color": "white",
                                "fontWeight": "bold",
                            },
                            style_data_conditional=[
                                {
                                    "if": {"filter_query": "{곱창집_적합도_v2} >= 40"},
                                    "backgroundColor": "#ffe6e6",
                                    "color": "black",
                                },
                                {
                                    "if": {
                                        "filter_query": "{곱창집_적합도_v2} >= 35 && {곱창집_적합도_v2} < 40"
                                    },
                                    "backgroundColor": "#fff2e6",
                                    "color": "black",
                                },
                            ],
                            sort_action="native",
                            page_size=15,
                        ),
                    ],
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "marginTop": "20px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    },
                ),
            ]
        ),
    ],
    style={
        "backgroundColor": colors["background"],
        "minHeight": "100vh",
        "padding": "20px",
    },
)


# 📊 콜백 함수들
@app.callback(
    [
        Output("total-districts", "children"),
        Output("avg-score", "children"),
        Output("avg-flow", "children"),
        Output("avg-sales", "children"),
        Output("ranking-chart", "figure"),
        Output("radar-chart", "figure"),
        Output("scatter-chart", "figure"),
        Output("investment-chart", "figure"),
        Output("districts-table", "data"),
    ],
    [
        Input("district-type-filter", "value"),
        Input("investment-level-filter", "value"),
        Input("score-range-slider", "value"),
    ],
)
def update_dashboard(district_type, investment_level, score_range):
    # 필터링
    filtered_df = top30_df.copy()

    if district_type != "all":
        filtered_df = filtered_df[filtered_df["상권유형"] == district_type]

    if investment_level != "all":
        filtered_df = filtered_df[filtered_df["투자규모"] == investment_level]

    filtered_df = filtered_df[
        (filtered_df["곱창집_적합도_v2"] >= score_range[0])
        & (filtered_df["곱창집_적합도_v2"] <= score_range[1])
    ]

    # KPI 계산
    total_districts = len(filtered_df)
    avg_score = (
        f"{filtered_df['곱창집_적합도_v2'].mean():.1f}점"
        if len(filtered_df) > 0
        else "0점"
    )
    avg_flow = (
        f"{filtered_df['T1_야간유동인구'].mean()/10000:.0f}만명"
        if len(filtered_df) > 0
        else "0명"
    )
    avg_sales = (
        f"{filtered_df['한식_월매출'].mean()/100000000:.0f}억원"
        if len(filtered_df) > 0
        else "0억원"
    )

    # 1. 순위 차트
    ranking_fig = px.bar(
        filtered_df.head(10),
        x="상권_코드_명",
        y="곱창집_적합도_v2",
        color="곱창집_적합도_v2",
        color_continuous_scale="Reds",
        title="🏆 상권별 적합도 점수 순위",
    )
    ranking_fig.update_layout(xaxis={"tickangle": 45}, height=400)

    # 2. 레이더 차트
    if len(filtered_df) > 0:
        top5_avg = filtered_df.head(5)[
            ["T1_점수_v2", "T2_점수_v2", "C1_점수_v2", "C2_점수_v2", "E1_점수_v2"]
        ].mean()

        radar_fig = go.Figure()
        categories = [
            "야간유동인구",
            "매출밀도",
            "경쟁우위",
            "상권활성도",
            "주류친화도",
        ]

        radar_fig.add_trace(
            go.Scatterpolar(
                r=list(top5_avg) + [top5_avg.iloc[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name="선택된 상권 평균",
                line_color="red",
            )
        )

        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="📊 선택된 상권 KPI 분석",
            height=400,
        )
    else:
        radar_fig = go.Figure().add_annotation(
            text="데이터 없음", xref="paper", yref="paper", x=0.5, y=0.5
        )

    # 3. 산점도 차트
    scatter_fig = px.scatter(
        filtered_df,
        x="T1_야간유동인구",
        y="곱창집_적합도_v2",
        size="한식_월매출",
        color="상권유형",
        hover_name="상권_코드_명",
        title="🎯 야간유동인구 vs 적합도 점수",
        labels={
            "T1_야간유동인구": "야간 유동인구 (명)",
            "곱창집_적합도_v2": "적합도 점수",
        },
    )
    scatter_fig.update_layout(height=400)

    # 4. 투자 분석 차트
    investment_summary = (
        filtered_df.groupby("투자규모")["곱창집_적합도_v2"]
        .agg(["count", "mean"])
        .reset_index()
    )
    investment_summary.columns = ["투자규모", "상권수", "평균점수"]

    investment_fig = px.bar(
        investment_summary,
        x="투자규모",
        y="상권수",
        color="평균점수",
        color_continuous_scale="Blues",
        title="💰 투자 규모별 상권 분포",
        text="상권수",
    )
    investment_fig.update_layout(height=400)

    # 5. 테이블 데이터
    table_data = filtered_df.copy()
    table_data["rank"] = range(1, len(table_data) + 1)
    table_data["한식매출_억"] = table_data["한식_월매출"] / 100000000

    table_dict = table_data[
        [
            "rank",
            "상권_코드_명",
            "곱창집_적합도_v2",
            "상권유형",
            "투자규모",
            "T1_야간유동인구",
            "한식매출_억",
        ]
    ].to_dict("records")

    return (
        total_districts,
        avg_score,
        avg_flow,
        avg_sales,
        ranking_fig,
        radar_fig,
        scatter_fig,
        investment_fig,
        table_dict,
    )


# 🚀 앱 실행
if __name__ == "__main__":
    print("🚀 곱창집 입지 분석 대시보드 시작!")
    print("📱 브라우저에서 http://127.0.0.1:8050 접속")
    print("⏹️ 종료하려면 Ctrl+C 누르세요")

    app.run_server(debug=True, host="127.0.0.1", port=8050)
