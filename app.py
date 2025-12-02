
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="정보통TV AI 마스터", layout="wide")

st.markdown("""
<style>
    .news-title { font-size:18px; font-weight: bold; color: #4FA5FF; text-decoration: none; }
    .news-box { border: 1px solid #333; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #0E1117; }
    .news-title:hover { text-decoration: underline; color: #82CFFF; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📺 방송용 컨트롤러")
    ticker = st.text_input("종목 코드 입력", value="NVDA").upper()
    st.caption("※ 엔터(Enter)를 치면 분석이 갱신됩니다.")
    st.markdown("---")
    st.write("1. 주가 & 등급 공개")
    st.write("2. 차트(추세) 해설")
    st.write("3. 최신 뉴스 체크")
    st.write("4. 최종 결론")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")

        if df.empty:
            st.error("데이터를 찾을 수 없습니다. 코드를 확인해주세요.")
        else:
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
            rsi = df['RSI'].iloc[-1]
            if rsi < 30: score += 30
            elif rsi > 70: score -= 10
            score = max(0, min(100, score))
            
            if score >= 80: grade = "SSS (강력 매수)"
            elif score >= 60: grade = "S (매수)"
            elif score >= 40: grade = "A (관망)"
            else: grade = "B (주의)"

            currency = "₩" if "KRW" in stock.info.get('currency', 'USD') else "$"
            
            st.title(f"📊 {ticker} 종합 분석 대시보드")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("현재 주가", f"{currency}{current_price:,.2f}")
            c2.metric("전일 대비", f"{df['Close'].diff().iloc[-1]:,.2f}")
            c3.metric("AI 종합 점수", f"{score}점")
            c4.metric("최종 등급", grade.split()[0])
            st.divider()

            col_chart, col_news = st.columns([2, 1])

            with col_chart:
                st.subheader("📈 기술적 분석 (Chart)")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_width=[0.2, 0.7])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='캔들'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='20일선'), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], showlegend=False, marker_color='teal'), row=2, col=1)
                fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with col_news:
                st.subheader("📰 실시간 관련 뉴스")
                try:
                    news_list = stock.news
                    if not news_list: st.info("관련 뉴스가 없습니다.")
                    else:
                        for item in news_list[:5]:
                            title = item.get('title', '제목 없음')
                            link = item.get('link', '#')
                            publisher = item.get('publisher', '언론사')
                            ts = item.get('providerPublishTime', 0)
                            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                            st.markdown(f"<div class='news-box'><a href='{link}' target='_blank' class='news-title'>{title}</a><br><span style='color:#888;font-size:0.8em;'>🏢 {publisher} | 🕒 {date_str}</span></div>", unsafe_allow_html=True)
                except: st.write("뉴스 로딩 실패")

            st.divider()
            with st.expander("🎙️ 방송용 큐시트 (AI 요약)"):
                st.markdown(f"1. **오프닝:** {ticker} 분석 시작합니다. 점수 **{score}점**, 등급 **{grade}**입니다.")
                st.markdown(f"2. **차트:** 현재 주가가 20일선 {'위에' if current_price > df['MA20'].iloc[-1] else '아래에'} 있습니다.")
                st.markdown("3. **뉴스:** 우측 최신 기사를 참고하세요.")
                st.markdown(f"4. **결론:** 종합적으로 {'매수 관점' if score >= 60 else '관망/주의'} 의견입니다.")

    except Exception as e:
        st.error(f"오류: {e}")
