import json
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf
from screener import run_screener

# 페이지 기본 설정
st.set_page_config(
    page_title="US Equity Technical Screener Pro",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 상단 헤더, 야간모드 토글, 데이터 갱신 버튼 배치
header_col1, header_col2, header_col3 = st.columns([6.4, 1.6, 2.0])

with header_col2:
  st.write("")
  dark_mode = st.toggle("🌙 야간 모드", value=True)

# 테마별 컬러셋 정의
if dark_mode:
  bg_color = "#0E1117"
  card_bg = "#161B22"
  border_color = "#30363D"
  text_primary = "#F0F6FC"
  text_secondary = "#8B949E"
  grid_color = "#21262D"
  btn_bg = "#21262D"
  btn_border = "#30363D"
  plotly_template = "plotly_dark"
  table_filter = "invert(0.92) hue-rotate(180deg)"
  img_revert = "invert(1) hue-rotate(180deg)"
else:
  bg_color = "#FFFFFF"
  card_bg = "#F9FAFB"
  border_color = "#E5E7EB"
  text_primary = "#111827"
  text_secondary = "#6B7280"
  grid_color = "#F3F4F6"
  btn_bg = "#FFFFFF"
  btn_border = "#D1D5DB"
  plotly_template = "plotly_white"
  table_filter = "none"
  img_revert = "none"

# CSS 스타일링 주입
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_primary};
    }}
    header[data-testid="stHeader"] {{
        background-color: {bg_color} !important;
    }}
    .block-container {{
        padding-top: 1.6rem;
        padding-bottom: 2rem;
        max-width: 97%;
    }}
    .main-header {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {text_primary};
        letter-spacing: -0.02em;
        margin-bottom: 0.1rem;
    }}
    .sub-header {{
        font-size: 0.88rem;
        color: {text_secondary};
        margin-bottom: 1.2rem;
    }}
    div[data-testid="stMetric"] {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        padding: 12px 16px;
        border-radius: 8px;
    }}
    div[data-testid="stMetricLabel"] {{
        font-size: 0.8rem !important;
        color: {text_secondary} !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: {text_primary} !important;
    }}
    div.stButton > button, div.stDownloadButton > button {{
        background-color: {btn_bg};
        color: {text_primary};
        border: 1px solid {btn_border};
        border-radius: 6px;
        font-weight: 500;
    }}
    div.stButton > button:hover, div.stDownloadButton > button:hover {{
        border-color: #3B82F6;
        color: #3B82F6;
    }}
    div[data-testid="stWidgetLabel"] p, label p {{
        color: {text_primary} !important;
    }}
    div[data-testid="stDataFrame"] {{
        filter: {table_filter};
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid {border_color};
    }}
    div[data-testid="stDataFrame"] img {{
        filter: {img_revert};
    }}
    .section-title {{
        font-size: 1.02rem;
        font-weight: 600;
        color: {text_primary};
        margin-top: 0.3rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid {border_color};
    }}
    .stat-bar {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 0.84rem;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
    }}
    hr {{
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
        border-color: {border_color} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

with header_col1:
  st.markdown(
      '<div class="main-header">미국 대형주 기술적 스크리너 Pro</div>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<div class="sub-header">S&P 500 · NASDAQ 100 이동평균선(±2.0%)'
      " 지지·저항 및 거래량·RSI 입체 분석 터미널</div>",
      unsafe_allow_html=True,
  )

with header_col3:
  st.write("")
  if st.button("데이터 업데이트", use_container_width=True):
    with st.spinner("미국 전 종목 시세 및 거래량 데이터를 동기화하는 중입니다..."):
      run_screener(threshold_pct=2.0)
    st.rerun()

JSON_FILE = "screened_stocks.json"

if not os.path.exists(JSON_FILE):
  st.info(
      "스크리닝 데이터가 없습니다. 우측 상단의 '데이터 업데이트' 버튼을"
      " 눌러주세요."
  )
  st.stop()

with open(JSON_FILE, "r", encoding="utf-8") as f:
  data = json.load(f)

oversold_20 = sum(1 for s in data["results"]["20"] if s["rsi"] <= 30)
oversold_200 = sum(1 for s in data["results"]["200"] if s["rsi"] <= 30)

# 상단 요약 지표 바
m1, m2, m3, m4 = st.columns(4)
m1.metric("분석 대상 종목", f"{data['total_screened']}개")
m2.metric(
    "20일선 근접 (과매도)", f"{len(data['results']['20'])}개 ({oversold_20})"
)
m3.metric(
    "200일선 근접 (과매도)", f"{len(data['results']['200'])}개 ({oversold_200})"
)
m4.metric("데이터 기준", data["updated_at"][:16])

st.markdown("<hr>", unsafe_allow_html=True)

# 컨트롤 바 (필터 및 검색 영역)
c1, c2, c3, c4 = st.columns([2.6, 2.0, 2.2, 3.2])

with c1:
  selected_period = st.radio(
      "기준 이동평균선",
      options=["20", "200"],
      format_func=lambda x: f"{x}일 이동평균선 (SMA {x})",
      horizontal=True,
  )

with c2:
  trend_filter = st.selectbox(
      "위치 필터",
      options=["전체 보기", "지지 종목만", "저항 종목만"],
  )

with c3:
  st.write("")
  only_oversold = st.toggle("RSI 과매도(30 이하)만", value=False)

with c4:
  search_query = st.text_input(
      "종목 빠른 검색 (티커 또는 한국어 기업명)",
      placeholder="예: AAPL, 애플, 도미노피자, NVDA",
  )

# 데이터 필터링 적용
stocks_list = data["results"][selected_period]

if trend_filter == "지지 종목만":
  stocks_list = [s for s in stocks_list if s["diff_pct"] >= 0]
elif trend_filter == "저항 종목만":
  stocks_list = [s for s in stocks_list if s["diff_pct"] < 0]

if only_oversold:
  stocks_list = [s for s in stocks_list if s["rsi"] <= 30]

if search_query:
  q = search_query.strip().lower()
  stocks_list = [
      s
      for s in stocks_list
      if q in s["ticker"].lower() or q in s["company_name"].lower()
  ]

# 메인 2단 분할 레이아웃
left_col, right_col = st.columns([5.3, 4.7], gap="large")

with left_col:
  st.markdown(
      f'<div class="section-title">검출 종목 ({len(stocks_list)}) <span'
      f' style="font-size:0.78rem; font-weight:400; color:{text_secondary};'
      ' margin-left:6px;">행 클릭 시 우측 차트 연동</span></div>',
      unsafe_allow_html=True,
  )

  if not stocks_list:
    st.info("조건에 부합하는 종목이 없습니다.")
    selected_stock = None
  else:
    df = pd.DataFrame(stocks_list)

    # 이평선 가격 + 이격률 통합 표기
    sma_col_name = f"{selected_period}일선(이격)"
    df[sma_col_name] = df.apply(
        lambda r: f"${r['sma']:,.2f} ({r['diff_pct']:+.2f}%)", axis=1
    )

    # 위치 텍스트 정돈 ('지지' / '저항')
    df["clean_trend"] = df["diff_pct"].apply(
        lambda x: "지지" if x >= 0 else "저항"
    )

    # 거래량 비율 컬럼 처리 (기존 JSON 파일 호환성 보장)
    if "vol_ratio" in df.columns:
      df["vol_display"] = df["vol_ratio"].apply(
          lambda v: f"🔥 {v:.0f}%" if v >= 150 else f"{v:.0f}%"
      )
    else:
      df["vol_display"] = "-"

    display_df = df[[
        "logo",
        "ticker",
        "company_name",
        "current_price",
        sma_col_name,
        "clean_trend",
        "rsi",
        "vol_display",
    ]].copy()

    display_df.columns = [
        "로고",
        "티커",
        "기업명",
        "현재가",
        sma_col_name,
        "위치",
        "RSI(14)",
        "거래량(20일비)",
    ]

    # 가로 잘림 없이 한눈에 들어오도록 폭 최적화
    event = st.dataframe(
        display_df,
        column_config={
            "로고": st.column_config.ImageColumn("", width="small"),
            "티커": st.column_config.TextColumn("티커", width="small"),
            "기업명": st.column_config.TextColumn("기업명", width="small"),
            "현재가": st.column_config.NumberColumn(
                "현재가", format="$%.2f", width="small"
            ),
            sma_col_name: st.column_config.TextColumn(
                sma_col_name, width="medium"
            ),
            "위치": st.column_config.TextColumn("위치", width="small"),
            "RSI(14)": st.column_config.ProgressColumn(
                "RSI(14)",
                format="%.1f",
                min_value=0,
                max_value=100,
                width="small",
            ),
            "거래량(20일비)": st.column_config.TextColumn(
                "수급(거래량)", width="small"
            ),
        },
        use_container_width=True,
        hide_index=True,
        height=510,
        on_select="rerun",
        selection_mode="single-row",
    )

    selected_rows = event.selection.rows
    selected_idx = selected_rows[0] if selected_rows else 0
    selected_stock = stocks_list[selected_idx]

    # 워치리스트 CSV 다운로드 버튼
    csv_export = df[[
        "ticker",
        "company_name",
        "current_price",
        "sma",
        "diff_pct",
        "clean_trend",
        "rsi",
    ]].copy()
    csv_export.columns = [
        "티커",
        "기업명",
        "현재가($)",
        f"{selected_period}일선($)",
        "이격률(%)",
        "위치",
        "RSI(14)",
    ]
    csv_bytes = csv_export.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label=f"📥 현재 검출된 {len(stocks_list)}개 종목 엑셀(CSV) 다운로드",
        data=csv_bytes,
        file_name=f"us_stocks_sma{selected_period}_list.csv",
        mime="text/csv",
        use_container_width=True,
    )

with right_col:
  if selected_stock:
    t_ticker = selected_stock["ticker"]
    t_name = selected_stock["company_name"]

    c_head1, c_head2 = st.columns([6.2, 3.8])
    with c_head1:
      st.markdown(
          f'<div class="section-title">{t_name} <span'
          f' style="color:{text_secondary};'
          f' font-weight:400;">({t_ticker})</span></div>',
          unsafe_allow_html=True,
      )
    with c_head2:
      timeframe = st.radio(
          "주기 선택",
          options=["일봉", "주봉", "월봉"],
          horizontal=True,
          label_visibility="collapsed",
      )

    # 200일선이 끊기지 않도록 일봉 조회 시 2년치(2y)를 받아와 계산
    tf_map = {
        "일봉": {"period": "2y", "interval": "1d", "unit": "일"},
        "주봉": {"period": "5y", "interval": "1wk", "unit": "주"},
        "월봉": {"period": "max", "interval": "1mo", "unit": "개월"},
    }
    params = tf_map[timeframe]

    hist = yf.download(
        t_ticker,
        period=params["period"],
        interval=params["interval"],
        auto_adjust=True,
        progress=False,
    )

    if not hist.empty:
      if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)

      # 1. 전체 기간에 대해 20선, 200선, 20거래량 평균선 먼저 계산 (끊김 방지)
      hist["SMA20"] = hist["Close"].rolling(window=20).mean()
      hist["SMA200"] = hist["Close"].rolling(window=200).mean()
      hist["VOL_MA20"] = hist["Volume"].rolling(window=20).mean()

      # 2.52주(252거래일) 최고가 및 당일 거래량 수급 계산
      recent_1y = hist.tail(252)
      max_52w = float(recent_1y["High"].max())
      current_p = float(hist["Close"].iloc[-1])
      drop_from_high = ((current_p - max_52w) / max_52w) * 100

      cur_vol = float(hist["Volume"].iloc[-1])
      avg_vol = (
          float(hist["VOL_MA20"].iloc[-1])
          if not pd.isna(hist["VOL_MA20"].iloc[-1])
          else cur_vol
      )
      vol_pct = (cur_vol / avg_vol * 100) if avg_vol > 0 else 100.0
      vol_badge = f"🔥 {vol_pct:.0f}% (수급 유입)" if vol_pct >= 150 else f"{vol_pct:.0f}% (평소 수준)"

      # 3. 일봉일 경우 화면에는 최근 1년(252거래일)만 쾌적하게 슬라이싱
      if timeframe == "일봉":
        plot_df = hist.tail(252)
      else:
        plot_df = hist

      # 차트 상단 요약 바 (52주 고점 대비 낙폭 & 거래량 수급)
      st.markdown(
          f"""
          <div class="stat-bar">
              <span>현재가: <b>${current_p:,.2f}</b></span>
              <span>52주 최고가: <b>${max_52w:,.2f}</b> (<span style="color:#EF4444; font-weight:600;">{drop_from_high:+.1f}%</span>)</span>
              <span>당일 거래량(20일비): <b>{vol_badge}</b></span>
          </div>
          """,
          unsafe_allow_html=True,
      )

      # 4. 캔들(상단 73%) + 거래량(하단 27%) 2단 서브플롯 차트 구성
      fig = make_subplots(
          rows=2,
          cols=1,
          shared_xaxes=True,
          vertical_spacing=0.03,
          row_heights=[0.73, 0.27],
      )

      # (1) 캔들스틱
      fig.add_trace(
          go.Candlestick(
              x=plot_df.index,
              open=plot_df["Open"],
              high=plot_df["High"],
              low=plot_df["Low"],
              close=plot_df["Close"],
              name=timeframe,
              increasing_line_color="#10B981",
              decreasing_line_color="#EF4444",
          ),
          row=1,
          col=1,
      )

      # (2) 20 이동평균선
      fig.add_trace(
          go.Scatter(
              x=plot_df.index,
              y=plot_df["SMA20"],
              mode="lines",
              line=dict(color="#F59E0B", width=1.6),
              name=f"20{params['unit']}선",
          ),
          row=1,
          col=1,
      )

      # (3) 200 이동평균선 (2년치로 미리 계산했으므로 처음부터 끝까지 연결됨)
      if plot_df["SMA200"].notna().any():
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["SMA200"],
                mode="lines",
                line=dict(color="#3B82F6", width=1.8),
                name=f"200{params['unit']}선",
            ),
            row=1,
            col=1,
        )

      # (4) 하단 거래량 바 (양봉: 초록, 음봉: 빨강)
      vol_colors = [
          "#10B981" if c >= o else "#EF4444"
          for c, o in zip(plot_df["Close"], plot_df["Open"])
      ]
      fig.add_trace(
          go.Bar(
              x=plot_df.index,
              y=plot_df["Volume"],
              marker_color=vol_colors,
              name="거래량",
              showlegend=False,
          ),
          row=2,
          col=1,
      )

      # (5) 거래량 20일 평균선
      fig.add_trace(
          go.Scatter(
              x=plot_df.index,
              y=plot_df["VOL_MA20"],
              mode="lines",
              line=dict(color="#A855F7", width=1.2, dash="dot"),
              name="거래량 20선",
          ),
          row=2,
          col=1,
      )

      fig.update_layout(
          template=plotly_template,
          margin=dict(l=10, r=10, t=10, b=10),
          yaxis=dict(
              title="",
              side="right",
              gridcolor=grid_color,
              zeroline=False,
              tickfont=dict(color=text_secondary),
          ),
          yaxis2=dict(
              title="",
              side="right",
              showticklabels=False,
              gridcolor=grid_color,
          ),
          xaxis=dict(
              gridcolor=grid_color,
              rangeslider=dict(visible=False),
          ),
          xaxis2=dict(
              gridcolor=grid_color,
              tickfont=dict(color=text_secondary),
          ),
          plot_bgcolor=card_bg if dark_mode else "#FFFFFF",
          paper_bgcolor=bg_color,
          font=dict(color=text_primary),
          hovermode="x unified",
          legend=dict(
              orientation="h",
              yanchor="bottom",
              y=1.02,
              xanchor="left",
              x=0,
              font=dict(size=11, color=text_primary),
          ),
          height=510,
      )

      st.plotly_chart(fig, use_container_width=True)
    else:
      st.warning("차트 데이터를 불러올 수 없습니다.")