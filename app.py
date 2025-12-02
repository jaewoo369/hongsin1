import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import feedparser
import urllib.parse

# === 페이지 설정 ===
st.set_page_config(page_title="정보통TV AI 마스터", layout="wide")

# === 스타일 설정 ===
st.markdown("""
<style>
    .news-box { border: 1px solid #444; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #262730; }
    .news-title { font-size:16px; font-weight: bold; color: #4FA5FF; text-decoration: none; }
    .news-title:hover { text-decoration: underline; }
    .news-meta { font-size: 12px; color: #aaa; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# === 구글 뉴스 가져오기 함수 ===
def get_google_news(ticker, company_name):
    try:
        # 검색어 설정
        query = urllib.parse.quote(company_name)
        # 구글 뉴스 RSS 주소
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        
        feed = feedparser.parse(rss_url)
        return feed.entries[:5] # 최신 뉴스 5개만 가져오기
    except:
        return []

# === 사이드바 ===
with st.sidebar:
    st.header("📺 방송용 컨트롤러")
    ticker = st.text_input("종목 코드 입력", value="NVDA").upper()
    st.caption("※ 엔터(Enter)를 치면 분석이 갱신됩니다.")
    st.markdown("---")
    st.info("📢 실시간 뉴스 & 차트 분석 시스템 가동 중")

# === 메인 로직 ===
if ticker:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")

        if df.empty:
            st.error("데이터를 찾을 수 없습니다.")
        else:
            # 회사 이름 가져오기
            info = stock.info
            company_name = info.get('shortName', ticker)
            if not company_name or company_name == ticker:
                 company_name = ticker

            # === 지표 계산 ===
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['std'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['MA20'] + (df['std'] * 2)
            df['Lower'] = df['MA20'] - (df['std'] * 2)
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            current_price = df['Close'].iloc[-1]
            score = 50
            if current_price > df['MA20'].iloc[-1]: score += 20
            else: score -= 10
            
            # RSI 처리 (데이터 부족 시 예외 처리)
            if len(df) > 14:
                rsi_val = df['RSI'].iloc[-1]
                if rsi_val < 30: score += 30
                elif rsi_val > 70: score -= 10
            
            score = max(0, min(100, score))
            
            if score >= 80: grade = "SSS (강력 매수)"
            elif score >= 60: grade = "S (매수)"
            elif score >= 40: grade = "A (관망)"
            else: grade = "B (주의)"

            currency = "₩" if "KRW" in info.get('currency', 'USD') else "$"

            # === 화면 출력 ===
            st.title(f"📊 {company_name} ({ticker}) 분석")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("현재 주가", f"{currency}{current_price:,.2f}")
            c2.metric("전일 대비", f"{df['Close'].diff().iloc[-1]:,.2f}")
            c3.metric("AI 종합 점수", f"{score}점")
            c4.metric("등급", grade.split()[0])
            st.divider()

            col_chart, col_news = st.columns([2, 1])

            with col_chart:
                st.subheader("📈 기술적 분석 (Chart)")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='캔들'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='20일선'), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], showlegend=False, marker_color='teal'), row=2, col=1)
                
                # 여기가 아까 에러났던 부분 (수정됨)
                fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with col_news:
                st.subheader("📰 실시간 뉴스 (Google News)")
                news_items = get_google_news(ticker, company_name)
                
                if not news_items:
                    st.info("최근 뉴스가 없습니다.")
                else:
                    for item in news_items:
                        title = item.title
                        link = item.link
                        pub_date = item.published if 'published' in item else ""
                        try: pub_date = pub_date.split('+')[0]
                        except: pass
                        
                        st.markdown(f'''
                        <div class="news-box">
                            <a href="{link}" target="_blank" class="news-title">{title}</a>
                            <div class="news-meta">🕒 {pub_date}</div>
                        </div>
                        ''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"오류 발생: {e}")
