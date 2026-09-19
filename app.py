import json
import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

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
KST = ZoneInfo("Asia/Seoul")
TODAY = datetime.datetime.now(KST).date()  # 서버 시간대와 무관하게 항상 한국시간 기준 날짜
DAY_OF_YEAR = TODAY.timetuple().tm_yday
TODAY_STR = TODAY.isoformat()

# 뉴스 검색 키워드 (필요하면 자유롭게 수정하세요)
# 뉴스는 아래 두 섹션으로 분리되어 표시됨:
#   1) ADMISSION_KEYWORDS: 2028학년도 대입 제도 변경 관련 뉴스
#   2) MAJOR_KEYWORDS: 서울·수도권 영문학과 / 미디어커뮤니케이션 전공 관련 소식
ADMISSION_KEYWORDS = [
    "2028 대입 제도 개편",
    "2028학년도 대학입시",
    "대학입시제도 개편 발표",
]
MAJOR_KEYWORDS = [
    "서울 영문학과",
    "수도권 영문학과",
    "서울 미디어커뮤니케이션학과",
    "수도권 미디어커뮤니케이션학과 -호남대",
]
NEWS_PER_KEYWORD = 3
NEWS_PER_SECTION = 4


# ------------------------------------------------------------------
# 데이터 로딩
# ------------------------------------------------------------------
def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data  # day_of_year가 바뀌면(=한국시간 자정이 지나면) 자동으로 새로 계산됨
def get_words_of_day(day_of_year):
    """매일 두 카테고리(수능 필수 / 미디어·시사)가 반드시 섞여 나오도록 선택.
    (하루 3개 중 2:1 또는 1:2 비율로 날짜에 따라 주도 카테고리가 바뀜)"""
    words = load_json("words.json")
    exam = [w for w in words if w["category"] == "수능 필수"]
    media = [w for w in words if w["category"] != "수능 필수"]
    e_n, m_n = len(exam), len(media)

    e_start = (day_of_year * 2) % e_n
    m_start = (day_of_year * 2) % m_n

    if day_of_year % 2 == 0:
        picked = [exam[(e_start + i) % e_n] for i in range(2)]
        picked.append(media[m_start % m_n])
    else:
        picked = [media[(m_start + i) % m_n] for i in range(2)]
        picked.append(exam[e_start % e_n])
    return picked


@st.cache_data
def get_quote_of_day(day_of_year):
    quotes = load_json("quotes.json")
    return quotes[day_of_year % len(quotes)]


@st.cache_data
def get_idiom_of_day(day_of_year):
    idioms = load_json("idioms.json")
    return idioms[day_of_year % len(idioms)]


@st.cache_data
def get_science_fact_of_day(day_of_year):
    facts = load_json("science_facts.json")
    return facts[day_of_year % len(facts)]


@st.cache_data  # today_str이 바뀌면(=한국시간 자정이 지나면) 자동으로 새로 수집됨
def fetch_news_section(keywords, limit, today_str):
    """주어진 키워드 목록으로 구글 뉴스 RSS를 검색해 최대 limit개 반환."""
    collected = []
    seen_links = set()
    for query in keywords:
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
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
                    "title": getattr(entry, "title", "제목 없음"),
                    "link": link,
                    "source": source,
                    "published": getattr(entry, "published", ""),
                }
            )
            if len(collected) >= limit:
                return collected
    return collected


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
    .subject-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 0.15rem 0.7rem;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subject-kor { background: #fef3c7; color: #92400e; }
    .subject-eng { background: #eef2ff; color: #4338ca; }
    .subject-sci { background: #dcfce7; color: #166534; }
    .subject-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #0f172a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 헤더
# ------------------------------------------------------------------
st.title("📚 지현이의 스마트 데일리 허브")
st.markdown(
    f"<div class='day-header'>{TODAY.strftime('%Y년 %m월 %d일')} · 오늘도 화이팅!</div>",
    unsafe_allow_html=True,
)

st.divider()

# ------------------------------------------------------------------
# 오늘의 학습 카드 (영어 · 국어 · 과학)
# ------------------------------------------------------------------
st.subheader("📖 오늘의 학습 카드 (영어 · 국어 · 과학)")

word_preview = get_words_of_day(DAY_OF_YEAR)[0]
idiom = get_idiom_of_day(DAY_OF_YEAR)
fact = get_science_fact_of_day(DAY_OF_YEAR)

kor_col, eng_col, sci_col = st.columns(3)

with kor_col:
    idiom_html = (
        '<div class="card"><div class="subject-badge subject-kor">국어</div>'
        f'<div class="subject-title">{idiom["hangul"]} <span style="font-weight:400; color:#9ca3af; font-size:0.85rem;">({idiom["idiom"]})</span></div>'
        f'<div style="color:#374151; margin-top:0.3rem;">{idiom["meaning"]}</div>'
        f'<div style="margin-top:0.5rem; padding:0.5rem 0.7rem; background:#f9fafb; border-left:3px solid #b45309; border-radius:6px; color:#4b5563; font-size:0.9rem;">{idiom["example"]}</div>'
        "</div>"
    )
    st.markdown(idiom_html, unsafe_allow_html=True)

with eng_col:
    example_en = word_preview.get("example_en", "")
    example_ko = word_preview.get("example_ko", "")
    eng_example = (
        f'<div style="margin-top:0.5rem; padding:0.5rem 0.7rem; background:#f9fafb; border-left:3px solid #4338ca; border-radius:6px; color:#4b5563; font-size:0.9rem;">{example_en}<br><span style="color:#9ca3af; font-size:0.8rem;">{example_ko}</span></div>'
        if example_en
        else ""
    )
    word_html = (
        '<div class="card"><div class="subject-badge subject-eng">영어</div>'
        f'<div class="subject-title">{word_preview["word"]}</div>'
        f'<div style="color:#374151; margin-top:0.3rem;">{word_preview["meaning"]}</div>'
        f"{eng_example}"
        "</div>"
    )
    st.markdown(word_html, unsafe_allow_html=True)

with sci_col:
    fact_html = (
        '<div class="card"><div class="subject-badge subject-sci">과학</div>'
        f'<div class="subject-title">{fact["title"]} <span style="font-weight:400; color:#9ca3af; font-size:0.85rem;">({fact["category"]})</span></div>'
        f'<div style="color:#374151; margin-top:0.3rem;">{fact["fact"]}</div>'
        "</div>"
    )
    st.markdown(fact_html, unsafe_allow_html=True)

st.divider()

# ------------------------------------------------------------------
# 본문: 2단 레이아웃
# ------------------------------------------------------------------
left, right = st.columns([3, 2])

def render_news_cards(news_items, empty_message):
    if not news_items:
        st.warning(empty_message)
        return
    for n in news_items:
        card_html = (
            '<div class="card">'
            f'<span class="word-badge">{n["keyword"]}</span><br>'
            f'<a href="{n["link"]}" target="_blank"><b>{n["title"]}</b></a><br>'
            f'<span style="color:#9ca3af; font-size:0.8rem;">{n["source"]} · {n["published"]}</span>'
            "</div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)


with left:
    st.subheader("🏛️ 2028학년도 대입 제도 뉴스")
    admission_news = fetch_news_section(ADMISSION_KEYWORDS, NEWS_PER_SECTION, TODAY_STR)
    render_news_cards(admission_news, "대입 제도 관련 뉴스를 불러오지 못했어요.")

    st.subheader("🎓 수도권·서울 영문학과 · 미디어커뮤니케이션 전공 소식")
    major_news = fetch_news_section(MAJOR_KEYWORDS, NEWS_PER_SECTION, TODAY_STR)
    render_news_cards(major_news, "학과 관련 뉴스를 불러오지 못했어요.")

with right:
    st.subheader("🧠 오늘의 단어 더 보기")
    st.caption("위 학습 카드의 영단어 외에 오늘 함께 익히면 좋은 단어들이에요.")
    for w in get_words_of_day(DAY_OF_YEAR)[1:]:
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
    q = get_quote_of_day(DAY_OF_YEAR)
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
