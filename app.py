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
# 입시/학교 소식 관련 키워드는 수도권·서울 중심으로 한정하고,
# "입시제도" 카테고리는 화면에서 항상 "트렌드" 카테고리보다 위에 오도록 우선 배치됨
NEWS_KEYWORDS = [
    {"query": "서울 고2 입시", "category": "입시제도"},
    {"query": "수도권 대입", "category": "입시제도"},
    {"query": "서울 전국연합학력평가", "category": "입시제도"},
    {"query": "미디어 트렌드", "category": "트렌드"},
    {"query": "영어 독학", "category": "트렌드"},
    {"query": "미디어커뮤니케이션학과", "category": "트렌드"},
]
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
    """매일 두 카테고리(수능 필수 / 미디어·시사)가 반드시 섞여 나오도록 선택.
    (하루 3개 중 2:1 또는 1:2 비율로 날짜에 따라 주도 카테고리가 바뀜)"""
    words = load_json("words.json")
    exam = [w for w in words if w["category"] == "수능 필수"]
    media = [w for w in words if w["category"] != "수능 필수"]
    e_n, m_n = len(exam), len(media)

    e_start = (DAY_OF_YEAR * 2) % e_n
    m_start = (DAY_OF_YEAR * 2) % m_n

    if DAY_OF_YEAR % 2 == 0:
        picked = [exam[(e_start + i) % e_n] for i in range(2)]
        picked.append(media[m_start % m_n])
    else:
        picked = [media[(m_start + i) % m_n] for i in range(2)]
        picked.append(exam[e_start % e_n])
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
    """구글 뉴스 RSS에서 키워드별 최신 기사를 모아 최대 NEWS_TOTAL개 반환.
    '입시제도' 카테고리 기사가 '트렌드' 카테고리보다 항상 먼저 오도록 정렬."""
    collected = []
    seen_links = set()
    for kw in NEWS_KEYWORDS:
        query, category = kw["query"], kw["category"]
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
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
                    "keyword": query,
                    "category": category,
                    "title": getattr(entry, "title", "제목 없음"),
                    "link": link,
                    "source": source,
                    "published": getattr(entry, "published", ""),
                }
            )

    # 입시제도 카테고리를 항상 먼저 (같은 카테고리 내에서는 수집 순서 유지)
    category_priority = {"입시제도": 0, "트렌드": 1}
    collected.sort(key=lambda x: category_priority.get(x["category"], 99))
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
    .word-en {
        color: #0f172a;
        font-weight: 800;
        font-size: 1.15rem;
    }
    details summary {
        cursor: pointer;
    }
    details summary::marker {
        color: #4338ca;
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
        example_en = w.get("example_en", "")
        example_ko = w.get("example_ko", "")
        example_block = (
            f'<div style="margin-top:0.5rem; padding:0.6rem 0.8rem; background:#f9fafb; '
            f'border-left:3px solid #4338ca; border-radius:6px;">'
            f'<span style="color:#1f2937;">{example_en}</span><br>'
            f'<span style="color:#6b7280; font-size:0.85rem;">{example_ko}</span></div>'
            if example_en
            else ""
        )
        card_html = (
            '<div class="card"><details><summary>'
            f'<span class="word-en">{w["word"]}</span> '
            f'<span class="word-badge">{w["category"]}</span>'
            '</summary>'
            '<div style="margin-top:0.5rem;">'
            f'<span style="color:#374151;">{w["meaning"]}</span>'
            f'{example_block}'
            '</div></details></div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.subheader("✨ 오늘의 한마디")
    q = get_quote_of_day()
    st.markdown(
        f"""
        <div class="quote-box">
            <p style="font-size:1.05rem; font-style:italic; font-weight:800; color:#0f172a; margin-bottom:0.4rem;">"{q['en']}"</p>
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
