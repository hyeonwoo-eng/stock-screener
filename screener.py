import pandas as pd
import yfinance as yf
import requests
import io
import json
from datetime import datetime

def get_russell1000_tickers():
    """위키피디아에서 Russell 1000 구성 종목 티커와 기업명을 가져옵니다."""
    url = "https://en.wikipedia.org/wiki/Russell_1000_Index"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    tables = pd.read_html(io.StringIO(response.text))
    df = None
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any('symbol' in c or 'ticker' in c for c in cols):
            df = t
            break
            
    if df is None:
        raise ValueError("Russell 1000 테이블을 찾을 수 없습니다.")
        
    # 컬럼명 표준화
    col_map = {}
    for c in df.columns:
        cl = str(c).lower()
        if 'symbol' in cl or 'ticker' in cl:
            col_map[c] = 'ticker'
        elif 'company' in cl or 'name' in cl:
            col_map[c] = 'name'
    df = df.rename(columns=col_map)
    
    # yfinance 포맷에 맞게 점(.)을 하이픈(-)으로 변환 (예: BRK.B -> BRK-B)
    df['ticker'] = df['ticker'].astype(str).str.strip().str.replace('.', '-', regex=False)
    
    # 티커-기업명 딕셔너리 및 리스트 반환
    ticker_dict = dict(zip(df['ticker'], df.get('name', df['ticker'])))
    return list(ticker_dict.keys()), ticker_dict