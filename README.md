# 지현이의 스마트 데일리 허브

고2 학생을 위한 매일 자동 업데이트 웹페이지입니다.
- 📰 오늘의 입시/미디어 트렌드 뉴스 (구글 뉴스 RSS 기반, 24시간마다 자동 갱신)
- 🧠 오늘의 단어 3개 (수능 필수 + 미디어/시사 어휘, 날짜 기준 자동 순환)
- ✨ 오늘의 영문 명언 + 번역 (날짜 기준 자동 순환)
- ⏳ D-Day 카운트다운 (모의고사, 진급일 등)

Python/Streamlit만으로 만들어져 있어 서버 관리 없이 무료로 배포할 수 있습니다.

---

## 1. 로컬에서 미리 확인하기 (선택)

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속하면 바로 확인할 수 있습니다.

---

## 2. 무료 배포하기 (Streamlit Community Cloud) — 초보자 추천 경로

1. **GitHub 계정 만들기** (이미 있다면 생략)
2. **새 저장소(repository) 만들기**
   - GitHub 우측 상단 `+` → `New repository`
   - 이름 예: `jihyun-daily-hub`
   - Public으로 설정 (무료 배포는 Public 저장소가 가장 간단합니다)
3. **이 폴더의 파일을 그대로 저장소에 업로드**
   - GitHub 웹에서 `Add file` → `Upload files`로 `app.py`, `requirements.txt`, `README.md`, `data/` 폴더를 통째로 올리면 됩니다.
   - (Git에 익숙하다면 `git init` → `git add .` → `git commit` → `git push`로 올려도 됩니다.)
4. **Streamlit Community Cloud 가입/접속**
   - https://share.streamlit.io 접속 → GitHub 계정으로 로그인
5. **앱 배포**
   - `New app` 클릭
   - 방금 만든 저장소, 브랜치(`main`), 메인 파일(`app.py`) 지정
   - `Deploy` 클릭 → 1~2분 후 `https://xxxx.streamlit.app` 형태의 주소가 생성됩니다.
6. 이 주소를 지현이의 즐겨찾기/홈 화면에 등록하면 끝입니다.

배포 후에는 **매일 접속할 때마다 자동으로**:
- 뉴스는 24시간에 한 번씩 새로 수집되고,
- 단어와 명언은 날짜가 바뀌면 자동으로 다음 항목으로 넘어갑니다.

별도의 서버나 크론(cron) 설정 없이도 "매일 갱신"이 되도록 캐시(ttl=24시간) 방식으로 구현했기 때문입니다.

---

## 3. 자주 수정하게 될 부분

| 무엇을 바꾸고 싶을 때 | 어디를 수정하나요 |
|---|---|
| 단어 목록 추가/변경 | `data/words.json` |
| 명언 추가/변경 | `data/quotes.json` |
| D-Day 일정 추가/수정 | `data/dday_config.json` (날짜는 `YYYY-MM-DD` 형식) |
| 뉴스 검색 키워드 변경 | `app.py` 상단의 `NEWS_KEYWORDS` 리스트 |
| 화면 색/디자인 | `app.py`의 `<style>` 부분 (CSS) |

파일을 수정한 뒤 GitHub 저장소에 다시 업로드(커밋)하면, Streamlit Community Cloud가 자동으로 재배포합니다.

> ⚠️ `data/dday_config.json`에 들어있는 날짜는 **예상치**입니다. 시/도교육청 및 교육부의 공식 발표(전국연합학력평가 일정, 수능 시행일 등)가 나오면 정확한 날짜로 꼭 교체해주세요.

---

## 4. (선택) 더 안정적으로 만들고 싶다면 — GitHub Actions

지금 구조는 Streamlit 앱이 접속 시점에 직접 뉴스를 가져오는 방식이라 별도 설정 없이 바로 동작합니다.
나중에 "매일 새벽 정해진 시간에 미리 뉴스를 수집해 저장해두고 싶다" 정도의 요구가 생기면, GitHub Actions로 `scripts/crawl_news.py`를 만들어 cron 스케줄로 실행하고 결과를 `data/news_cache.json`에 커밋한 뒤, `app.py`가 그 파일을 읽도록 확장할 수 있습니다. 이 확장이 필요해지면 언제든 요청해주세요.
