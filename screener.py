import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
import json
import sys
import os
from datetime import datetime

# 주요 러셀 1000 종목 한글 기업명 매핑
KOR_NAMES = {
    "AAPL": "애플", "MSFT": "마이크로소프트", "NVDA": "엔비디아", "GOOGL": "알파벳 A", "GOOG": "알파벳 C",
    "AMZN": "아마존", "META": "메타", "BRK-B": "버크셔 해서웨이", "LLY": "일라이 릴리", "AVGO": "브로드컴",
    "TSLA": "테슬라", "JPM": "JP모건 체이스", "WMT": "월마트", "UNH": "유나이티드헬스", "V": "비자",
    "XOM": "엑슨모빌", "MA": "마스터카드", "PG": "프록터 앤 갬블", "JNJ": "존슨앤드존슨", "COST": "코스트코",
    "HD": "홈디포", "ORCL": "오라클", "ABBV": "애브비", "MRK": "머크", "BAC": "뱅크오브아메리카",
    "KO": "코카콜라", "NFLX": "넷플릭스", "AMD": "AMD", "CRM": "세일즈포스", "CVX": "셰브론",
    "PEP": "펩시코", "TMO": "써모피셔", "LIN": "린데", "ADBE": "어도비", "WFC": "웰스파고",
    "MCD": "맥도날드", "CSCO": "시스코", "ABT": "애보트", "DIS": "월트 디즈니", "INTC": "인텔",
    "QCOM": "퀄컴", "IBM": "IBM", "CAT": "캐터필러", "GE": "GE 에어로스페이스", "VZ": "버라이즌",
    "NOW": "서비스나우", "UBER": "우버", "PFE": "화이자", "NKE": "나이키", "PLTR": "팔란티어",
    "SNOW": "스노우플레이크", "COIN": "코인베이스", "ARM": "ARM 홀딩스", "SMCI": "슈퍼마이크로컴퓨터",
    "MSTR": "마이크로스트래티지", "IONQ": "아이온큐", "RIVN": "리비안", "LCID": "루시드", "SOFI": "소파이",
    "U": "유니티", "RBLX": "로블록스", "HOOD": "로빈후드", "CPNG": "쿠팡", "DPZ": "도미노피자",
    "A": "애질런트 테크놀로지스", "SCHW": "찰스 슈왑", "APD": "에어프로덕츠", "CDW": "CDW 코퍼레이션", "LDOS": "라이도스 홀딩스",
    "AMAT": "어플라이드 머티어리얼즈", "INTU": "인투이트", "ISRG": "인튜이티브 서지컬", "BKNG": "부킹 홀딩스",
    "GEHC": "GE헬스케어", "LMT": "록히드 마틴", "ETN": "이턴", "PLD": "프로롤지스", "AXP": "아메리칸 익스프레스"
}

def get_russell1000_tickers():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    ticker_dict = {}

    # 1순위: iShares Russell 1000 ETF (IWB) 공식 보유종목 CSV
    try:
        iwb_url = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/1467271812596.ajax?fileType=csv&fileName=IWB_holdings&dataType=fund"
        res = requests.get(iwb_url, headers=headers, timeout=15)
        if res.status_code == 200:
            lines = res.text.splitlines()
            start_idx = 0
            for i, line in enumerate(lines[:30]):
                if line.startswith("Ticker,") or '"Ticker"' in line:
                    start_idx = i
                    break
            df = pd.read_csv(io.StringIO("\n".join(lines[start_idx:])))
            if "Ticker" in df.columns and "Name" in df.columns:
                if "Asset Class" in df.columns:
                    df = df[df["Asset Class"] == "Equity"]
                for _, row in df.iterrows():
                    t = str(row["Ticker"]).strip().replace(".", "-").replace("/", "-")
                    if not t or t == "nan" or len(t) > 6 or " " in t:
                        continue
                    eng_name = str(row["Name"]).strip()
                    ticker_dict[t] = KOR_NAMES.get(t, eng_name)
                if len(ticker_dict) > 500:
                    return list(ticker_dict.keys()), ticker_dict
    except Exception:
        pass

    # 2순위: Wikipedia 백업
    urls = [
        "https://en.wikipedia.org/wiki/Russell_1000_Index",
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            tables = pd.read_html(io.StringIO(res.text))
            for t in tables:
                if isinstance(t.columns, pd.MultiIndex):
                    t.columns = [' '.join(map(str, col)).strip() for col in t.columns.values]
                cols_lower = [str(c).lower() for c in t.columns]
                if len(t) >= 300 and any('symbol' in c or 'ticker' in c for c in cols_lower):
                    t_col = next(c for c in t.columns if 'symbol' in str(c).lower() or 'ticker' in str(c).lower())
                    n_col = next((c for c in t.columns if any(k in str(c).lower() for k in ['company', 'security', 'name'])), t_col)
                    for _, row in t.iterrows():
                        sym = str(row[t_col]).strip().replace(".", "-")
                        if not sym or sym == "nan" or len(sym) > 6 or " " in sym:
                            continue
                        name = str(row[n_col]).strip()
                        ticker_dict[sym] = KOR_NAMES.get(sym, name)
            if len(ticker_dict) >= 850:
                break
        except Exception:
            continue

    if not ticker_dict:
        raise ValueError("종목 테이블을 가져올 수 없습니다.")

    return list(ticker_dict.keys()), ticker_dict

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_screener():
    print("1. 러셀 1000(Russell 1000) 종목 리스트 수집 중...")
    tickers, name_map = get_russell1000_tickers()
    total_count = len(tickers)
    print(f"-> 총 {total_count}개 종목 확인 완료.")

    results_sma20 = []
    results_sma200 = []
    
    batch_size = 100
    for i in range(0, total_count, batch_size):
        batch = tickers[i:i+batch_size]
        print(f"2. 데이터 분석 중... ({i+1} ~ {min(i+batch_size, total_count)} / {total_count})")
        
        try:
            # yfinance 내부 표준 출력/에러(상폐 경고 등) 일시 차단
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            
            data = yf.download(batch, period="2y", group_by="ticker", threads=True, progress=False)
            
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        except Exception:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            continue
            
        for ticker in batch:
            try:
                df = data[ticker] if len(batch) > 1 else data
                if df is None or df.empty:
                    continue
                df = df.dropna(subset=['Close'])
                if len(df) < 200:
                    continue
                
                close = df['Close']
                volume = df['Volume']
                high = df['High']
                low = df['Low']
                
                curr_price = float(close.iloc[-1])
                sma20 = float(close.rolling(20).mean().iloc[-1])
                sma200 = float(close.rolling(200).mean().iloc[-1])
                rsi = float(calculate_rsi(close).iloc[-1])
                
                vol_20_avg = float(volume.rolling(20).mean().iloc[-1])
                curr_vol = float(volume.iloc[-1])
                vol_ratio = round((curr_vol / vol_20_avg) * 100, 1) if vol_20_avg > 0 else 0.0
                
                high_52w = float(high.iloc[-252:].max()) if len(high) >= 252 else float(high.max())
                low_52w = float(low.iloc[-252:].min()) if len(low) >= 252 else float(low.min())
                pct_from_high = round(((curr_price - high_52w) / high_52w) * 100, 2)
                pct_from_low = round(((curr_price - low_52w) / low_52w) * 100, 2)
                
                diff_sma20 = round(((curr_price - sma20) / sma20) * 100, 2)
                diff_sma200 = round(((curr_price - sma200) / sma200) * 100, 2)
                
                stock_info = {
                    "ticker": ticker,
                    "name": name_map.get(ticker, ticker),
                    "price": round(curr_price, 2),
                    "sma20": round(sma20, 2),
                    "diff_sma20": diff_sma20,
                    "sma200": round(sma200, 2),
                    "diff_sma200": diff_sma200,
                    "rsi": round(rsi, 1),
                    "vol_ratio": vol_ratio,
                    "high_52w": round(high_52w, 2),
                    "low_52w": round(low_52w, 2),
                    "pct_from_high": pct_from_high,
                    "pct_from_low": pct_from_low
                }
                
                if abs(diff_sma20) <= 2.0:
                    results_sma20.append(stock_info)
                if abs(diff_sma200) <= 2.0:
                    results_sma200.append(stock_info)
                    
            except Exception:
                continue

    results_sma20 = sorted(results_sma20, key=lambda x: abs(x['diff_sma20']))
    results_sma200 = sorted(results_sma200, key=lambda x: abs(x['diff_sma200']))

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "universe": "Russell 1000",
        "total_analyzed": total_count,
        "sma20_near": results_sma20,
        "sma200_near": results_sma200
    }

    with open("screened_stocks.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"완료! 20일선 근접: {len(results_sma20)}개, 200일선 근접: {len(results_sma200)}개 저장됨.")

if __name__ == "__main__":
    run_screener()