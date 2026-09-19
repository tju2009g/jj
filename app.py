import json
import datetime
from pathlib import Path

import streamlit as st
import feedparser

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(
    page_title="지현이의 스마트 데일리 허브",
    page_icon="📚",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"
TODAY = datetime.date.today()
DAY_OF_YEAR = TODAY.timetuple().tm_yday

# 뉴스 검색 키워드 (필요하면 자유롭게 수정하세요)
NEWS_KEYWORDS = ["고2 입시", "미디어 트렌드", "영어 독학", "미디어커뮤니케이션학과"]
NEWS_PER_KEYWORD = 3
NEWS_TOTAL = 5


# ------------------------------------------------------------------
# 데이터 로딩
# ------------------------------------------------------------------
def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=24 * 60 * 60)  # 하루에 한 번만 새로 계산/조회
def get_words_of_day():
    words = load_json("words.json")
    n = len(words)
    start = (DAY_OF_YEAR * 3) % n
    picked = [words[(start + i) % n] for i in range(3)]
    return picked


@st.cache_data(ttl=24 * 60 * 60)
def get_quote_of_day():
    quotes = load_json("quotes.json")
    return quotes[DAY_OF_YEAR % len(quotes)]


def get_dday_list():
    items = load_json("dday_config.json")
    result = []
    for item in items:
        target = datetime.date.fromisoformat(item["date"])
        d = (target - TODAY).days
        result.append({**item, "d_value": d})
    # 지나지 않은 일정만, 가까운 순으로
    upcoming = [x for x in result if x["d_value"] >= 0]
    upcoming.sort(key=lambda x: x["d_value"])
    return upcoming


@st.cache_data(ttl=24 * 60 * 60)
def fetch_news():
    """구글 뉴스 RSS에서 키워드별 최신 기사를 모아 최대 NEWS_TOTAL개 반환."""
    collected = []
    seen_links = set()
    for kw in NEWS_KEYWORDS:
        url = f"https://news.google.com/rss/search?q={kw}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for entry in feed.entries[:NEWS_PER_KEYWORD]:
            link = getattr(entry, "link", None)
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            source = ""
            if hasattr(entry, "source") and hasattr(entry.source, "title"):
                source = entry.source.title
            collected.append(
                {
                    "keyword": kw,
                    "title": getattr(entry, "title", "제목 없음"),
                    "link": link,
                    "source": source,
                    "published": getattr(entry, "published", ""),
                }
            )
    return collected[:NEWS_TOTAL]


# ------------------------------------------------------------------
# 스타일
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    .day-header {font-size: 1.05rem; color: #6b7280; margin-bottom: 0.5rem;}
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .quote-box {
        background: linear-gradient(135deg, #eef2ff, #fdf4ff);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.2rem;
    }
    .word-badge {
        display: inline-block;
        background: #eef2ff;
        color: #4338ca;
        border-radius: 999px;
        padding: 0.1rem 0.7rem;
        font-size: 0.75rem;
        margin-left: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 헤더 & D-Day
# ------------------------------------------------------------------
st.title("📚 지현이의 스마트 데일리 허브")
st.markdown(
    f"<div class='day-header'>{TODAY.strftime('%Y년 %m월 %d일')} · 오늘도 화이팅!</div>",
    unsafe_allow_html=True,
)

dday_list = get_dday_list()
if dday_list:
    cols = st.columns(len(dday_list[:4]))
    for col, item in zip(cols, dday_list[:4]):
        with col:
            st.metric(label=item["label"], value=f"D-{item['d_value']}")
    with st.expander("D-Day 일정에 대한 참고사항"):
        for item in dday_list[:4]:
            st.caption(f"• {item['label']}: {item['note']}")
else:
    st.info("표시할 예정된 D-Day가 없습니다. data/dday_config.json을 확인해주세요.")

st.divider()

# ------------------------------------------------------------------
# 본문: 2단 레이아웃
# ------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    st.subheader("📰 오늘의 입시 · 미디어 트렌드 뉴스")
    news_items = fetch_news()
    if not news_items:
        st.warning("뉴스를 불러오지 못했어요. 네트워크 상태 또는 키워드를 확인해주세요.")
    else:
        for n in news_items:
            st.markdown(
                f"""
                <div class="card">
                    <span class="word-badge">{n['keyword']}</span><br>
                    <a href="{n['link']}" target="_blank"><b>{n['title']}</b></a><br>
                    <span style="color:#9ca3af; font-size:0.8rem;">{n['source']} · {n['published']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

with right:
    st.subheader("🧠 오늘의 단어 3개")
    for w in get_words_of_day():
        st.markdown(
            f"""
            <div class="card">
                <b>{w['word']}</b> <span class="word-badge">{w['category']}</span><br>
                <span style="color:#374151;">{w['meaning']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("✨ 오늘의 한마디")
    q = get_quote_of_day()
    st.markdown(
        f"""
        <div class="quote-box">
            <p style="font-size:1.05rem; font-style:italic; margin-bottom:0.4rem;">"{q['en']}"</p>
            <p style="color:#4b5563; margin-bottom:0.4rem;">{q['ko']}</p>
            <p style="text-align:right; color:#9ca3af; font-size:0.85rem;">— {q['author']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.caption(
    "이 페이지는 매일 접속 시 하루 단위로 새 단어·명언이 자동 계산되고, "
    "뉴스는 24시간 캐시 후 다시 수집됩니다. 새로고침해도 하루에 한 번만 실제로 갱신됩니다."
)
