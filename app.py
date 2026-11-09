import streamlit as st
import pandas as pd
import json
import urllib.request
import urllib.parse
import os
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from screener import run_screener, get_logo_url

st.set_page_config(
    page_title="US Equity Technical Screener Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    .stock-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .stock-header img {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: contain;
        background-color: #ffffff;
        padding: 2px;
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
    """DLL 차단 없이 야후 파이낸스 API에서 직접 차트 데이터를 받아옵니다."""
    if timeframe == "일봉":
        rng, interval = "2y", "1d"
    elif timeframe == "주봉":
        rng, interval = "10y", "1wk"
    else:
        rng, interval = "max", "1mo"

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range={rng}&interval={interval}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8", errors="ignore"))
            
        res = raw.get("chart", {}).get("result", [None])[0]
        if not res:
            return pd.DataFrame()
            
        timestamps = res.get("timestamp", [])
        quote = res.get("indicators", {}).get("quote", [{}])[0]
        
        rows = []
        for ts, o, h, l, c, v in zip(
            timestamps,
            quote.get("open", []),
            quote.get("high", []),
            quote.get("low", []),
            quote.get("close", []),
            quote.get("volume", [])
        ):
            if c is not None and o is not None and h is not None and l is not None:
                dt = datetime.fromtimestamp(ts)
                rows.append({
                    "Date": dt,
                    "Open": float(o),
                    "High": float(h),
                    "Low": float(l),
                    "Close": float(c),
                    "Volume": float(v) if v is not None else 0.0
                })
                
        df = pd.DataFrame(rows)
        if df.empty:
            return df
            
        df.set_index("Date", inplace=True)
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()
        df["Vol_MA20"] = df["Volume"].rolling(20).mean()
        
        if timeframe == "일봉":
            df = df.iloc[-150:]
        elif timeframe == "주봉":
            df = df.iloc[-120:]
        else:
            df = df.iloc[-80:]
            
        return df
    except Exception:
        return pd.DataFrame()

# 상단 타이틀 및 데이터 업데이트 버튼
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("### US Equity Technical Screener Pro")
    st.caption("Russell 1000 이동평균선(±2.0%) 지지·저항 및 전체 분석 대상 종목 통합 터미널")
with col_btn:
    st.write("")
    if st.button("🔄 데이터 업데이트", use_container_width=True):
        with st.spinner("Russell 1000 정상 상장 종목 수집 및 한글화 분석 중... (약 1~2분 소요)"):
            run_screener()
            st.cache_data.clear()
        st.rerun()

data = load_screened_data()

if data is None:
    st.warning("데이터 파일이 없습니다. 우측 상단의 '🔄 데이터 업데이트' 버튼을 눌러주세요.")
    st.stop()

sma20_list = data.get("sma20_near", [])
sma200_list = data.get("sma200_near", [])
all_stocks_list = data.get("all_stocks", [])

# 만약 구버전 JSON이라 all_stocks가 비어있다면 기존 리스트들을 병합해 생성
if not all_stocks_list and (sma20_list or sma200_list):
    merged_map = {item["ticker"]: item for item in (sma20_list + sma200_list)}
    all_stocks_list = sorted(list(merged_map.values()), key=lambda x: x["ticker"])

total_cnt = len(all_stocks_list) if all_stocks_list else data.get("total_analyzed", 0)
sma20_oversold = sum(1 for x in sma20_list if x.get("rsi", 50) <= 30)
sma200_oversold = sum(1 for x in sma200_list if x.get("rsi", 50) <= 30)
all_oversold = sum(1 for x in all_stocks_list if x.get("rsi", 50) <= 30)

# 상단 요약 지표 카드 4개
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">분석 대상 전체 종목 (상폐 제외)</div><div class="metric-value">{total_cnt}개 (과매도 {all_oversold})</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">20일선 근접 (과매도)</div><div class="metric-value">{len(sma20_list)}개 ({sma20_oversold})</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">200일선 근접 (과매도)</div><div class="metric-value">{len(sma200_list)}개 ({sma200_oversold})</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">데이터 기준</div><div class="metric-value">{data.get("updated_at", "-")}</div></div>', unsafe_allow_html=True)

st.write("")

# 필터 및 조회 모드 컨트롤 바 (기준 이동평균선에서 '전체 종목 보기' 직접 선택 가능!)
f1, f2, f3, f4 = st.columns([1.5, 1.3, 1.1, 2.1])

with f1:
    view_mode = st.radio(
        "조회 기준 선택",
        [
            "20일 이동평균선 근접 (SMA 20)",
            "200일 이동평균선 근접 (SMA 200)",
            f"📋 분석 대상 전체 종목 ({total_cnt}개)"
        ]
    )

is_all_mode = "전체 종목" in view_mode
is_sma20 = "20일" in view_mode

with f2:
    if is_all_mode:
        sort_opt = st.selectbox(
            "전체 종목 정렬 기준",
            ["티커순 (A-Z)", "한글 기업명순 (가-하)", "현재가 높은순", "RSI 낮은순 (과매도순)", "거래량 급증순 (20일비)", "20일선 밀착순", "200일선 밀착순"]
        )
        pos_filter = st.selectbox(
            "이평선 위치 필터",
            ["전체 보기 (이평선 무관)", "20일선 위", "20일선 아래", "200일선 위", "200일선 아래"]
        )
    else:
        pos_filter = st.selectbox(
            "위치 필터",
            ["전체 보기", "이동평균선 위 (지지 테스트)", "이동평균선 아래 (저항 돌파 시도)"]
        )
        sort_opt = "이평선 밀착순"

with f3:
    st.write("")
    st.write("")
    rsi_only = st.checkbox("RSI 과매도(30 이하)만")

with f4:
    search_query = st.text_input(
        "종목 빠른 검색 (티커 또는 한글 기업명)",
        placeholder="예: AAPL, 애플, 테슬라, 엔비디아, 도미노피자"
    )

# 선택된 모드에 따른 원본 리스트 지정
if is_all_mode:
    raw_list = all_stocks_list
else:
    raw_list = sma20_list if is_sma20 else sma200_list

# 필터링 적용
filtered = []
for item in raw_list:
    rsi_val = item.get("rsi", 50.0)
    d20 = item.get("diff_sma20", 0.0)
    d200 = item.get("diff_sma200", 0.0)

    if is_all_mode:
        if pos_filter == "20일선 위" and d20 < 0:
            continue
        elif pos_filter == "20일선 아래" and d20 >= 0:
            continue
        elif pos_filter == "200일선 위" and d200 < 0:
            continue
        elif pos_filter == "200일선 아래" and d200 >= 0:
            continue
    else:
        diff_val = d20 if is_sma20 else d200
        if pos_filter == "이동평균선 위 (지지 테스트)" and diff_val < 0:
            continue
        if pos_filter == "이동평균선 아래 (저항 돌파 시도)" and diff_val >= 0:
            continue

    if rsi_only and rsi_val > 30:
        continue

    if search_query:
        q = search_query.strip().lower()
        if q not in item.get("ticker", "").lower() and q not in item.get("name", "").lower():
            continue

    filtered.append(item)

# 전체 종목 모드일 때 정렬 적용
if is_all_mode:
    if sort_opt == "한글 기업명순 (가-하)":
        filtered.sort(key=lambda x: x.get("name", ""))
    elif sort_opt == "현재가 높은순":
        filtered.sort(key=lambda x: x.get("price", 0), reverse=True)
    elif sort_opt == "RSI 낮은순 (과매도순)":
        filtered.sort(key=lambda x: x.get("rsi", 50))
    elif sort_opt == "거래량 급증순 (20일비)":
        filtered.sort(key=lambda x: x.get("vol_ratio", 0), reverse=True)
    elif sort_opt == "20일선 밀착순":
        filtered.sort(key=lambda x: abs(x.get("diff_sma20", 999)))
    elif sort_opt == "200일선 밀착순":
        filtered.sort(key=lambda x: abs(x.get("diff_sma200", 999)))
    else:
        filtered.sort(key=lambda x: x.get("ticker", ""))

st.divider()

# 좌측 종목 목록 테이블 / 우측 캔들스틱 차트
left_col, right_col = st.columns([1.22, 1.78])

with left_col:
    sub_col1, sub_col2 = st.columns([2, 1])
    with sub_col1:
        title_prefix = "전체 분석 대상 종목" if is_all_mode else "이평선 근접 검출 종목"
        st.markdown(f"**{title_prefix} ({len(filtered)}개)** <span style='color:#8b949e; font-size:0.8rem;'>행 클릭 시 우측 차트 연동</span>", unsafe_allow_html=True)

    if not filtered:
        st.info("조건에 맞는 종목이 없습니다. 필터를 변경하거나 우측 상단 '🔄 데이터 업데이트' 버튼을 눌러주세요.")
        selected_stock = None
    else:
        df_display = pd.DataFrame(filtered)
        with sub_col2:
            csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
            file_tag = "all" if is_all_mode else ("sma20" if is_sma20 else "sma200")
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_data,
                file_name=f"russell1000_{file_tag}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if is_all_mode:
            # 전체 종목 모드에서는 20일선과 200일선 이격도를 동시에 모두 표시!
            df_table = pd.DataFrame({
                "로고": df_display.apply(lambda r: r.get("logo") or get_logo_url(r["ticker"]), axis=1),
                "티커": df_display["ticker"],
                "기업명": df_display["name"],
                "현재가": df_display["price"].apply(lambda x: f"${x:,.2f}"),
                "20일선(이격)": df_display.apply(lambda r: f"${r.get('sma20', 0):,.2f} ({r.get('diff_sma20', 0):+.2f}%)", axis=1),
                "200일선(이격)": df_display.apply(lambda r: f"${r.get('sma200', 0):,.2f} ({r.get('diff_sma200', 0):+.2f}%)", axis=1),
                "RSI(14)": df_display["rsi"],
                "거래량(20일비)": df_display["vol_ratio"].apply(lambda x: f"{x:.0f}%")
            })
        else:
            sma_key = "sma20" if is_sma20 else "sma200"
            diff_key = "diff_sma20" if is_sma20 else "diff_sma200"
            ma_label = "20일선(이격)" if is_sma20 else "200일선(이격)"
            df_table = pd.DataFrame({
                "로고": df_display.apply(lambda r: r.get("logo") or get_logo_url(r["ticker"]), axis=1),
                "티커": df_display["ticker"],
                "기업명": df_display["name"],
                "현재가": df_display["price"].apply(lambda x: f"${x:,.2f}"),
                ma_label: df_display.apply(lambda r: f"${r.get(sma_key, 0):,.2f} ({r.get(diff_key, 0):+.2f}%)", axis=1),
                "RSI(14)": df_display["rsi"],
                "거래량(20일비)": df_display["vol_ratio"].apply(lambda x: f"{x:.0f}%")
            })

        event = st.dataframe(
            df_table,
            column_config={
                "로고": st.column_config.ImageColumn("", width="small")
            },
            use_container_width=True,
            hide_index=True,
            height=540,
            on_select="rerun",
            selection_mode="single-row"
        )
        sel_rows = event.selection.rows if event and hasattr(event, "selection") else []
        sel_idx = sel_rows[0] if sel_rows else 0
        selected_stock = filtered[sel_idx]

with right_col:
    if selected_stock:
        logo_url = selected_stock.get("logo") or get_logo_url(selected_stock["ticker"])
        c_head1, c_head2 = st.columns([1.8, 1.2])
        with c_head1:
            st.markdown(f"""
            <div class="stock-header">
                <img src="{logo_url}" onerror="this.style.display='none'">
                <h4 style="margin:0;">{selected_stock['name']} ({selected_stock['ticker']})</h4>
            </div>
            """, unsafe_allow_html=True)
        with c_head2:
            timeframe = st.radio(
                "차트 주기", ["일봉", "주봉", "월봉"],
                horizontal=True, label_visibility="collapsed"
            )

        vol_r = selected_stock.get("vol_ratio", 100.0)
        vol_status = "🔥 거래량 급증" if vol_r >= 150 else ("💧 거래량 침체" if vol_r <= 60 else "평소 수준")
        
        st.markdown(f"""
        <div class="info-box">
            <b>현재가:</b> ${selected_stock['price']:,.2f} &nbsp;|&nbsp;
            <b>20일선 이격:</b> {selected_stock.get('diff_sma20', 0):+.2f}% &nbsp;|&nbsp;
            <b>200일선 이격:</b> {selected_stock.get('diff_sma200', 0):+.2f}%<br>
            <b>52주 최고가:</b> ${selected_stock.get('high_52w', 0):,.2f} (<span style="color:#f85149;">{selected_stock.get('pct_from_high', 0):+.1f}%</span>) &nbsp;|&nbsp;
            <b>52주 최저가:</b> ${selected_stock.get('low_52w', 0):,.2f} (<span style="color:#3fb950;">{selected_stock.get('pct_from_low', 0):+.1f}%</span>) &nbsp;|&nbsp;
            <b>거래량(20일비):</b> {vol_r:.0f}% ({vol_status})
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("차트 데이터를 불러오는 중..."):
            chart_df = fetch_chart_data(selected_stock["ticker"], timeframe)

        if not chart_df.empty:
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.04, row_heights=[0.75, 0.25]
            )
            fig.add_trace(go.Candlestick(
                x=chart_df.index, open=chart_df["Open"], high=chart_df["High"],
                low=chart_df["Low"], close=chart_df["Close"], name=timeframe,
                increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df["SMA20"], mode="lines",
                name="20일선", line=dict(color="#f59e0b", width=1.6)
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df["SMA200"], mode="lines",
                name="200일선", line=dict(color="#3b82f6", width=2.0)
            ), row=1, col=1)

            vol_colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(chart_df["Close"], chart_df["Open"])]
            fig.add_trace(go.Bar(
                x=chart_df.index, y=chart_df["Volume"], name="거래량",
                marker_color=vol_colors, opacity=0.75
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df["Vol_MA20"], mode="lines",
                name="거래량 20선", line=dict(color="#a855f7", width=1.2, dash="dot")
            ), row=2, col=1)

            fig.update_layout(
                template="plotly_dark", height=520, margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
            )
            if timeframe == "일봉":
                fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("차트 데이터를 불러오지 못했습니다.")