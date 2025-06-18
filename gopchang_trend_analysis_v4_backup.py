"""
Gopchang Trend Analysis – v4.0 (multi‑module)
---------------------------------------------
새 기능 (요청 2·3·4·5 반영)
2️⃣  네이버플레이스 경쟁 매장 리뷰 스크래퍼 (placeholder)
3️⃣  메뉴·가격 트렌드 추출기 (₩·원 패턴 파싱)
4️⃣  인스타그램 해시태그 분석 (Instaloader 기반, 최근 N건 워드클라우드)
5️⃣  Streamlit 대시보드 (`streamlit run dashboard.py`)

※ 일부 기능은 API·로그인 세션이 필요하므로, 실제 실행 전 쿠키·세션 설정이 필요합니다.
"""

from __future__ import annotations
import os, re, time, textwrap, json, argparse, subprocess, tempfile
from collections import Counter
from datetime import datetime
from typing import Dict, List

import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from wordcloud import WordCloud

plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["figure.autolayout"] = True
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------------------------
# 0. 공통 유틸
# ------------------------------------------------------------------
PRICE_PATTERN = re.compile(r"(\d{1,3}(?:,\d{3})*)(?:\s?원|₩)")


# ------------------------------------------------------------------
# 1. 네이버 API 래퍼 (동일)
# ------------------------------------------------------------------
class NaverAPIClient:
    BASE_URL = "https://openapi.naver.com/v1/search"

    def __init__(self, cid: str, sec: str, rate: float = 0.2):
        self.headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}
        self.rate = rate

    def _get(self, ep, params):
        r = requests.get(
            f"{self.BASE_URL}/{ep}.json",
            headers=self.headers,
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        time.sleep(self.rate)
        return r.json()["items"]

    def search(self, q, ep, disp=100, pages=1):
        out = []
        for p in range(pages):
            out += self._get(
                ep, {"query": q, "display": disp, "start": p * disp + 1, "sort": "date"}
            )
            if len(out) < (p + 1) * disp:
                break
        return out

    news = lambda s, q, **k: s.search(q, "news", **k)
    blog = lambda s, q, **k: s.search(q, "blog", **k)
    cafe = lambda s, q, **k: s.search(q, "cafearticle", **k)


# ------------------------------------------------------------------
# 2. 경쟁 매장 리뷰 스크래퍼 (placeholder)
# ------------------------------------------------------------------
class CompetitorReviewScraper:
    """네이버플레이스 리뷰 스크래퍼 (비공식 모바일 endpoint 사용).

    Parameters
    ----------
    place_id : str
        네이버플레이스 식별자(숫자).
    cookies : str, optional
        로그인 쿠키 문자열. 로그인하지 않아도 최대 20개까지는 조회 가능하지만,
        더 많은 리뷰·‘사장님 댓글’ 등을 보려면 세션 쿠키가 필요합니다.
    headers : Dict[str, str], optional
        추가 User‑Agent 등 커스텀 헤더.
    """

    MOBILE_API = (
        "https://m.place.naver.com/restaurant/{pid}/review/visitor.json"
        "?display={display}&page={page}&orderby=recent"
    )

    def __init__(
        self,
        place_id: str,
        *,
        cookies: str | None = None,
        headers: Dict[str, str] | None = None,
    ):
        self.place_id = place_id
        self.session = requests.Session()
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1"
            ),
            "Referer": f"https://m.place.naver.com/restaurant/{place_id}/review/visitor",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        if cookies:
            self.session.headers.update({"Cookie": cookies})

    def fetch_reviews(self, max_pages: int = 10, display: int = 20) -> List[Dict]:
        """리뷰 JSON 목록 반환 (page당 최대 20개).

        Returns
        -------
        List[Dict]
            각 Dict에는 `content`, `rating`, `date`, `author` 등이 포함됩니다.
        """
        reviews: List[Dict] = []
        for page in range(1, max_pages + 1):
            url = self.MOBILE_API.format(pid=self.place_id, display=display, page=page)
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"❌ 요청 실패(page={page}): {e}")
                break

            items = data.get("items", [])
            if not items:
                break  # 더 이상 페이지 없음

            for it in items:
                reviews.append(
                    {
                        "content": it.get("reviewContent", "").strip(),
                        "rating": it.get("rating", 0),
                        "date": it.get("regTime", ""),
                        "author": it.get("userName", ""),
                    }
                )

            # 모바일 API는 마지막 페이지에 `items` 길이가 `display`보다 작음
            if len(items) < display:
                break

            time.sleep(0.2)  # 우회 트래픽 완화
        return reviews


# ------------------------------------------------------------------
# 3. 트렌드 분석기 (기존 + 가격/메뉴 추출)
# ------------------------------------------------------------------
class GopchangTrendAnalyzer:
    KW = ["곱창", "막창", "대창", "양곱창", "곱창전골", "곱창구이"]
    DIST = [
        "강남역",
        "종로",
        "명동",
        "신촌",
        "홍대",
        "노량진",
        "노원",
        "잠실",
        "여의도",
        "연남동",
    ]
    POS = ["맛있", "좋", "추천", "대박", "부드러", "쫄깃", "고소", "감동"]
    NEG = ["맛없", "별로", "실망", "최악", "비싸", "불친절", "더러"]

    def __init__(self, cli):
        self.cli = cli

    # collect(), preprocess(), sent(), summary() 동일 → (생략: 이전 코드 그대로)
    def collect(self, days=30):
        cutoff = (datetime.now() - pd.Timedelta(days=days)).timestamp()
        data = {s: [] for s in ("news", "blog", "cafe")}
        for kw in self.KW[:3]:
            data["news"] += self.cli.news(kw)
            data["blog"] += self.cli.blog(kw)
            data["cafe"] += self.cli.cafe(kw)
        for kw in [f"{d} {k}" for d in self.DIST[:5] for k in self.KW[:2]]:
            data["blog"] += self.cli.blog(kw, disp=50)

        def recent(i):
            try:
                ts = datetime.strptime(
                    i["pubDate"], "%a, %d %b %Y %H:%M:%S %z"
                ).timestamp()
                return ts >= cutoff
            except:
                return True

        for k in data:
            data[k] = [i for i in data[k] if recent(i)]
        return data

    def preprocess(self, raw):
        rows = []
        for src, items in raw.items():
            for it in items:
                txt = f"{it.get('title','')} {it.get('description','')}"
                rows.append(
                    {
                        "source": src,
                        "title": it.get("title", ""),
                        "description": it.get("description", ""),
                        "pub_date": it.get("pubDate", ""),
                        "sentiment": self.sent(txt),
                        "districts": [d for d in self.DIST if d in txt],
                        "prices": PRICE_PATTERN.findall(txt),
                    }
                )
        return pd.DataFrame(rows)

    def sent(self, txt):
        c = re.sub(r"<[^>]+>", "", txt)
        p = sum(w in c for w in self.POS)
        n = sum(w in c for w in self.NEG)
        return "positive" if p > n else "negative" if n > p else "neutral"


# ------------------------------------------------------------------
# 4. 인스타그램 해시태그 수집 (Instaloader)
# ------------------------------------------------------------------
class InstagramHashtagAnalyzer:
    def __init__(self, hashtag: str):
        self.hashtag = hashtag.lstrip("#")

    def fetch_captions(self, max_posts: int = 200) -> List[str]:
        try:
            import instaloader
        except ImportError:
            print("❌ instaloader 미설치. `pip install instaloader` 후 재시도하세요.")
            return []
        L = instaloader.Instaloader(download_pictures=False, quiet=True)
        posts = instaloader.Hashtag.from_name(L.context, self.hashtag).get_posts()
        captions = []
        for _, post in zip(range(max_posts), posts):
            captions.append(post.caption or "")
        return captions

    def wordcloud(self, captions: List[str]):
        txt = " ".join(captions)
        if not txt.strip():
            return
        wc = WordCloud(
            font_path="/System/Library/Fonts/AppleGothic.ttf",
            background_color="white",
            width=800,
            height=400,
        ).generate(txt)
        wc.to_file(f"ig_wc_{self.hashtag}.png")
        print(f"✅ 인스타 해시태그 워드클라우드 → ig_wc_{self.hashtag}.png")


# ------------------------------------------------------------------
# 5. Streamlit 대시보드 (별도 파일 생성)
# ------------------------------------------------------------------
DASHBOARD_CODE = """
import streamlit as st, pandas as pd, matplotlib.pyplot as plt, os, json
st.set_page_config(page_title="Gopchang Dashboard", layout="wide")

st.title("곱창 상권 트렌드 대시보드")

if not os.path.exists('gopchang_report.txt'):
    st.warning('Run the analysis script first.')
    st.stop()

report=open('gopchang_report.txt').read()
segments=report.split('='*60)[:-1]
for seg in segments:
    st.markdown(f"```\n{seg}\n```")

cols=st.columns(3)
for i,p in enumerate(['daily_trend.png','wc_pos.png','wc_neg.png']):
    if os.path.exists(p): cols[i].image(p, use_column_width=True)
"""


def ensure_dashboard():
    with open("dashboard.py", "w", encoding="utf-8") as fp:
        fp.write(DASHBOARD_CODE)
    print("✅ dashboard.py 생성 → `streamlit run dashboard.py` 로 실행")


# ------------------------------------------------------------------
# 6. 메인
# ------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Gopchang Trend System")
    parser.add_argument(
        "--mode", choices=["trend", "reviews", "insta", "dashboard"], default="trend"
    )
    parser.add_argument("--place_id", help="네이버플레이스 식별자", default="")
    parser.add_argument(
        "--cookies",
        help="세션 쿠키 문자열 (예: 'NID_AUT=...; NID_SES=...')",
        default="",
    )
    parser.add_argument("--hashtag", help="#해시태그", default="곱창")
    args = parser.parse_args()

    if args.mode == "reviews":
        if not args.place_id:
            print("--place_id 필요")
            return
        scraper = CompetitorReviewScraper(
            args.place_id, cookies=args.cookies if args.cookies else None
        )
        reviews = scraper.fetch_reviews()
        print("\n".join(reviews))
    elif args.mode == "insta":
        iga = InstagramHashtagAnalyzer(args.hashtag)
        caps = iga.fetch_captions(300)
        iga.wordcloud(caps)
    elif args.mode == "dashboard":
        ensure_dashboard()
    else:  # trend (default)
        from dotenv import load_dotenv

        load_dotenv()
        cid = os.getenv("NAVER_CLIENT_ID", "QjzwUZBwBgZijbaadyKV")
        sec = os.getenv("NAVER_CLIENT_SECRET", "fIqgUfyng8")
        cli = NaverAPIClient(cid, sec)
        analyzer = GopchangTrendAnalyzer(cli)
        df = analyzer.preprocess(analyzer.collect())
        make_visuals(df)
        # 간단 리포트
        dists = [
            ("강남역", "프리미엄 비즈니스"),
            ("명동", "관광/전통상권"),
            ("홍대", "대학가"),
            ("신촌", "대학가"),
            ("종로", "관광/전통상권"),
        ]
        lines = []
