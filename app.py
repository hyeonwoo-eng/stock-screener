import streamlit as st
import pandas as pd
import json
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(
    page_title="US Equity Technical Screener Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 다크모드 스타일링
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .metric-title { color: #8b949e; font-size: 0.85rem; margin-bottom: 6px; }
    .metric-value { color: #f0f6fc; font-size: 1.6rem; font-weight: 700; }
    .info-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_screened_data():
    if not os.path.exists("screened_stocks.json"):
        return None
    with open("screened_stocks.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(ttl=3600)
def fetch_chart_data(ticker, timeframe):
    """200일 이동평균선이 끊기지 않도록 넉넉한 기간의 데이터를 받아옵니다."""
    if timeframe == "일봉":
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
    elif timeframe == "주봉":
        df = yf.download(ticker, period="10y", interval="1wk", progress=False)
    else:  # 월봉
        df = yf.download(ticker, period="max", interval="1mo", progress=False)
        
    if df.empty:
        return df
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.dropna(subset=['Close'])
    
    # 전체 데이터로 이동평균선 먼저 계산 (앞부분 끊김 현상 해결)
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA200'] = df['Close'].rolling(200).mean()
    df['Vol_MA20'] = df['Volume'].rolling(20).mean()
    
    # 화면에 보여줄 최근 캔들 개수로 슬라이싱
    if timeframe == "일봉":
        df = df.iloc[-150:]
    elif timeframe == "주봉":
        df = df.iloc[-120:]
    else:
        df = df.iloc[-80:]
        
    return df

data = load_screened_data()

# 상단 타이틀 영역
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("### US Equity Technical Screener Pro")
    st.caption("Russell 1000 이동평균선(±2.0%) 지지·저항 및 거래량·RSI 입체 분석 터미널")

if data is None:
    st.warning("`screened_stocks.json` 파일을 찾을 수 없습니다. 먼저 `python screener.py`를 실행해 데이터를 생성해 주세요.")
    st.stop()

sma20_list = data.get("sma20_near", [])
sma200_list = data.get("sma200_near", [])
sma20_oversold = sum(1 for x in sma20_list if x.get("rsi", 50) <= 30)
sma200_oversold = sum(1 for x in sma200_list if x.get("rsi", 50) <= 30)

# 상단 요약 지표 카드 4개
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">분석 대상 종목 (Russell 1000)</div><div class="metric-value">{data.get("total_analyzed", 0)}개</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">20일선 근접 (과매도)</div><div class="metric-value">{len(sma20_list)}개 ({sma20_oversold})</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">200일선 근접 (과매도)</div><div class="metric-value">{len(sma200_list)}개 ({sma200_oversold})</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">데이터 기준</div><div class="metric-value">{data.get("updated_at", "-")}</div></div>', unsafe_allow_html=True)

st.write("")

# 필터 및 검색 컨트롤 바
f1, f2, f3, f4 = st.columns([1.3, 1.3, 1.2, 2.2])
with f1:
    ma_choice = st.radio("기준 이동평균선", ["20일 이동평균선 (SMA 20)", "200일 이동평균선 (SMA 200)"])
with f2:
    pos_filter = st.selectbox("위치 필터", ["전체 보기", "이동평균선 위 (지지 테스트)", "이동평균선 아래 (저항 돌파 시도)"])
with f3:
    st.write("")
    st.write("")
    rsi_only = st.checkbox("RSI 과매도(30 이하)만")
with f4:
    search_query = st.text_input("종목 빠른 검색 (티커 또는 기업명)", placeholder="예: AAPL, 애플, 도미노피자, NVDA")

is_sma20 = "20일" in ma_choice
raw_list = sma20_list if is_sma20 else sma200_list
diff_key = "diff_sma20" if is_sma20 else "diff_sma200"
sma_key = "sma20" if is_sma20 else "sma200"
ma_label = "20일선(이격)" if is_sma20 else "200일선(이격)"

# 조건별 필터링 적용
filtered = []
for item in raw_list:
    if pos_filter == "이동평균선 위 (지지 테스트)" and item[diff_key] < 0:
        continue
    if pos_filter == "이동평균선 아래 (저항 돌파 시도)" and item[diff_key] >= 0:
        continue
    if rsi_only and item["rsi"] > 30:
        continue
    if search_query:
        q = search_query.strip().lower()
        if q not in item["ticker"].lower() and q not in item["name"].lower():
            continue
    filtered.append(item)

st.divider()

# 메인 화면: 좌측 테이블 / 우측 차트
left_col, right_col = st.columns([1.15, 1.85])

with left_col:
    sub_col1, sub_col2 = st.columns([2, 1])
    with sub_col1:
        st.markdown(f"**검출 종목 ({len(filtered)})** <span style='color:#8b949e; font-size:0.8rem;'>행 클릭 시 우측 차트 연동</span>", unsafe_allow_html=True)
    
    if not filtered:
        st.info("조건에 맞는 종목이 없습니다.")
        selected_stock = None
    else:
        df_display = pd.DataFrame(filtered)
        
        # CSV 다운로드 버튼
        with sub_col2:
            csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_data,
                file_name=f"russell1000_screened_{'sma20' if is_sma20 else 'sma200'}.csv",
                mime="text/csv",
                use_container_width=True
            )

        df_table = pd.DataFrame({
            "티커": df_display["ticker"],
            "기업명": df_display["name"],
            "현재가": df_display["price"].apply(lambda x: f"${x:,.2f}"),
            ma_label: df_display.apply(lambda r: f"${r[sma_key]:,.2f} ({r[diff_key]:+.2f}%)", axis=1),
            "RSI(14)": df_display["rsi"],
            "거래량(20일비)": df_display["vol_ratio"].apply(lambda x: f"{x:.0f}%")
        })

        event = st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            height=520,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        sel_rows = event.selection.rows if event and hasattr(event, "selection") else []
        sel_idx = sel_rows[0] if sel_rows else 0
        selected_stock = filtered[sel_idx]

with right_col:
    if selected_stock:
        c_head1, c_head2 = st.columns([1.8, 1.2])
        with c_head1:
            st.markdown(f"#### {selected_stock['name']} ({selected_stock['ticker']})")
        with c_head2:
            timeframe = st.radio("차트 주기", ["일봉", "주봉", "월봉"], horizontal=True, label_visibility="collapsed")

        vol_r = selected_stock['vol_ratio']
        vol_status = "🔥 거래량 급증" if vol_r >= 150 else ("💧 거래량 침체" if vol_r <= 60 else "평소 수준")
        
        st.markdown(f"""
        <div class="info-box">
            <b>현재가:</b> ${selected_stock['price']:,.2f} &nbsp;|&nbsp;
            <b>52주 최고가:</b> ${selected_stock['high_52w']:,.2f} (<span style="color:#f85149;">{selected_stock['pct_from_high']:+.1f}%</span>) &nbsp;|&nbsp;
            <b>52주 최저가:</b> ${selected_stock['low_52w']:,.2f} (<span style="color:#3fb950;">{selected_stock['pct_from_low']:+.1f}%</span>) &nbsp;|&nbsp;
            <b>당일 거래량(20일비):</b> {vol_r:.0f}% ({vol_status})
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("차트 데이터를 불러오는 중..."):
            chart_df = fetch_chart_data(selected_stock['ticker'], timeframe)

        if not chart_df.empty:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_heights=[0.75, 0.25]
            )

            # 1단: 캔들스틱 및 이동평균선
            fig.add_trace(go.Candlestick(
                x=chart_df.index,
                open=chart_df['Open'], high=chart_df['High'],
                low=chart_df['Low'], close=chart_df['Close'],
                name=timeframe,
                increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['SMA20'],
                mode='lines', name='20선',
                line=dict(color='#f59e0b', width=1.6)
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['SMA200'],
                mode='lines', name='200선',
                line=dict(color='#3b82f6', width=2.0)
            ), row=1, col=1)

            # 2단: 거래량 바 차트 및 거래량 20일 이동평균선
            vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(chart_df['Close'], chart_df['Open'])]
            fig.add_trace(go.Bar(
                x=chart_df.index, y=chart_df['Volume'],
                name='거래량', marker_color=vol_colors, opacity=0.75
            ), row=2, col=1)

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['Vol_MA20'],
                mode='lines', name='거래량 20선',
                line=dict(color='#a855f7', width=1.2, dash='dot')
            ), row=2, col=1)

            fig.update_layout(
                template="plotly_dark",
                height=520,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117"
            )
            
            if timeframe == "일봉":
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("차트 데이터를 불러오지 못했습니다.")