import urllib.request
import urllib.parse
import json
import csv
import os
import re
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1차: 국내 증권사(토스, 나무, 한투 등) 주요 종목 표준 한글명 사전
KOR_NAMES = {
    "AAPL": "애플", "MSFT": "마이크로소프트", "NVDA": "엔비디아", "GOOGL": "알파벳 A", "GOOG": "알파벳 C",
    "AMZN": "아마존닷컴", "META": "메타 플랫폼스", "BRK-B": "버크셔 해서웨이 B", "BRK-A": "버크셔 해서웨이 A",
    "LLY": "일라이 릴리", "AVGO": "브로드컴", "TSLA": "테슬라", "JPM": "JP모건 체이스", "WMT": "월마트",
    "UNH": "유나이티드헬스 그룹", "V": "비자", "XOM": "엑슨모빌", "MA": "마스터카드", "PG": "프록터 앤 갬블",
    "JNJ": "존슨앤드존슨", "COST": "코스트코 홀세일", "HD": "홈디포", "ORCL": "오라클", "ABBV": "애브비",
    "MRK": "머크", "BAC": "뱅크오브아메리카", "KO": "코카콜라", "NFLX": "넷플릭스", "AMD": "AMD",
    "CRM": "세일즈포스", "CVX": "셰브론", "PEP": "펩시코", "TMO": "써모 피셔 사이언티픽", "LIN": "린데",
    "ADBE": "어도비", "WFC": "웰스파고", "MCD": "맥도날드", "CSCO": "시스코 시스템즈", "ABT": "애보트 래버러토리즈",
    "DIS": "월트 디즈니", "INTC": "인텔", "QCOM": "퀄컴", "IBM": "IBM", "CAT": "캐터필러",
    "GE": "GE 에어로스페이스", "VZ": "버라이즌 커뮤니케이션스", "NOW": "서비스나우", "UBER": "우버 테크놀로지스",
    "PFE": "화이자", "NKE": "나이키", "PLTR": "팔란티어 테크놀로지스", "SNOW": "스노우플레이크", "COIN": "코인베이스 글로벌",
    "ARM": "ARM 홀딩스", "SMCI": "슈퍼마이크로 컴퓨터", "MSTR": "마이크로스트래티지", "IONQ": "아이온큐",
    "RIVN": "리비안 오토모티브", "LCID": "루시드 그룹", "SOFI": "소파이 테크놀로지스", "U": "유니티 소프트웨어",
    "RBLX": "로블록스", "HOOD": "로빈후드 마켓츠", "CPNG": "쿠팡", "DPZ": "도미노피자", "A": "애질런트 테크놀로지스",
    "SCHW": "찰스 슈왑", "APD": "에어프로덕츠 앤 케미컬스", "CDW": "CDW", "LDOS": "라이도스 홀딩스",
    "AMAT": "어플라이드 머티어리얼즈", "INTU": "인투이트", "ISRG": "인튜이티브 서지컬", "BKNG": "부킹 홀딩스",
    "GEHC": "GE 헬스케어 테크놀로지스", "LMT": "록히드 마틴", "ETN": "이튼", "PLD": "프로로지스", "AXP": "아메리칸 익스프레스",
    "SBUX": "스타벅스", "PYPL": "페이팔 홀딩스", "BA": "보잉", "TXN": "텍사스 인스트루먼트", "GS": "골드만삭스",
    "MS": "모건스탠리", "BLK": "블랙록", "C": "씨티그룹", "LOW": "로우스", "HON": "하니웰 인터내셔널",
    "UNP": "유니온 퍼시픽", "AMGN": "암젠", "GILD": "길리어드 사이언스", "VRTX": "버텍스 파마슈티컬스",
    "REGN": "리제네론 파마슈티컬스", "BSX": "보스턴 사이언티픽", "SYK": "스트라이커", "MDT": "메드트로닉",
    "ZTS": "조에티스", "CI": "시그나", "CVS": "CVS 헬스", "ELV": "엘레반스 헬스", "HCA": "HCA 헬스케어",
    "MCK": "매케슨", "COR": "센코라", "CAH": "카디널 헬스", "BMY": "브리스톨 마이어스 스큅", "BDX": "벡톤 디킨슨",
    "LRCX": "램리서치", "KLAC": "KLA", "MU": "마이크론 테크놀로지", "ADI": "아날로그 디바이스", "SNPS": "시놉시스",
    "CDNS": "케이던스 디자인 시스템즈", "PANW": "팔로알토 네트웍스", "CRWD": "크라우드스트라이크 홀딩스", "FTNT": "포티넷",
    "ZS": "지스케일러", "NET": "클라우드플레어", "DDOG": "데이터독", "MDB": "몽고DB", "TEAM": "아틀라시안",
    "WDAY": "워크데이", "ADSK": "오토데스크", "ANSS": "앤시스", "ROP": "로퍼 테크놀로지스", "FICO": "페어 아이작",
    "IT": "가트너", "ACN": "액센츄어", "FI": "파이서브", "FIS": "피델리티 내셔널 인포메이션", "PAYX": "페이첵스",
    "ADP": "오토매틱 데이터 프로세싱", "GPN": "글로벌 페이먼츠", "XYZ": "블록", "AFRM": "어펌 홀딩스", "UPST": "업스타트 홀딩스",
    "DE": "디어 앤 컴퍼니", "CMI": "커민스", "PCAR": "파카", "URI": "유나이티드 렌탈스", "PH": "파카 하니핀",
    "EMR": "에머슨 일렉트릭", "ITW": "일리노이 툴 웍스", "GD": "제너럴 다이내믹스", "NOC": "노스롭 그루만",
    "RTX": "RTX", "LHX": "L3해리스 테크놀로지스", "HII": "헌팅턴 잉걸스 인더스트리스", "TDG": "트랜스다임 그룹",
    "HEI": "헤이코", "CARR": "캐리어 글로벌", "OTIS": "오티스 월드와이드", "TT": "트레인 테크놀로지스", "JCI": "존슨콘트롤즈",
    "PWR": "콴타 서비스", "GEV": "GE 버노바", "VST": "비스트라 에너지", "CEG": "컨스텔레이션 에너지", "NRG": "NRG 에너지",
    "NEE": "넥스트에라 에너지", "SO": "서던 컴퍼니", "DUK": "듀크 에너지", "SRE": "셈프라", "AEP": "아메리칸 일렉트릭 파워",
    "D": "도미니언 에너지", "EXC": "엑셀론", "PCG": "PG&E", "ED": "콘솔리데이티드 에디슨", "XEL": "엑셀 에너지",
    "PEG": "퍼블릭 서비스 엔터프라이즈", "WEC": "WEC 에너지 그룹", "AWK": "아메리칸 워터 웍스", "COP": "코노코필립스",
    "EOG": "EOG 리소시스", "SLB": "슐럼버거", "MPC": "마라톤 페트롤리엄", "PSX": "필립스 66", "VLO": "발레로 에너지",
    "OXY": "옥시덴탈 페트롤리엄", "HAL": "할리버튼", "BKR": "베이커 휴즈", "FANG": "다이아몬드백 에너지", "DVN": "데본 에너지",
    "KMI": "킨더 모건", "WMB": "윌리엄스 컴퍼니즈", "OKE": "원오크", "TRGP": "타르가 리소시스", "FCX": "프리포트 맥모란",
    "NEM": "뉴몬트", "NUE": "뉴코", "STLD": "스틸 다이내믹스", "SHW": "셔윈-윌리엄즈", "ECL": "이콜랩",
    "DOW": "다우", "DD": "듀폰", "LYB": "라이온델바젤 인더스트리스", "PPG": "PPG 인더스트리스",
    "AMT": "아메리칸 타워", "CCI": "크라운 캐슬", "EQIX": "에퀴닉스", "DLR": "디지털 리얼티 트러스트", "WELL": "웰타워",
    "SPG": "사이먼 프로퍼티 그룹", "O": "리얼티 인컴", "PSA": "퍼블릭 스토리지", "EXR": "엑스트라 스페이스 스토리지",
    "VICI": "VICI 프로퍼티스", "AVB": "아발론베이 커뮤니티스", "EQR": "에쿼티 레지덴셜", "INVH": "인비테이션 홈즈",
    "CBRE": "CBRE 그룹", "CSGP": "코스타 그룹", "TMUS": "T-모바일 US", "T": "AT&T", "CMCSA": "컴캐스트",
    "CHTR": "차터 커뮤니케이션즈", "WBD": "워너 브라더스 디스커버리", "PARA": "파라마운트 글로벌", "LYV": "라이브 네이션 엔터테인먼트",
    "SPOT": "스포티파이 테크놀로지", "EA": "일렉트로닉 아츠", "TTWO": "테이크투 인터랙티브", "ROKU": "로쿠", "PINS": "핀터레스트",
    "SNAP": "스냅", "MTCH": "매치 그룹", "RDDT": "레딧", "DKNG": "드래프트킹스", "DASH": "도어대시",
    "ABNB": "에어비앤비", "EXPE": "익스피디아 그룹", "MAR": "메리어트 인터내셔널", "HLT": "힐튼 월드와이드", "H": "하얏트 호텔",
    "RCL": "로얄 캐리비안 크루즈", "CCL": "카니발", "NCLH": "노르웨이지안 크루즈 라인", "DAL": "델타항공", "UAL": "유나이티드 항공",
    "AAL": "아메리칸 항공", "LUV": "사우스웨스트 항공", "FDX": "페덱스", "UPS": "UPS", "JBHT": "J.B. 헌트 트랜스포트",
    "ODFL": "올드 도미니언 프레이트 라인", "CSX": "CSX", "NSC": "노퍽 서던", "GM": "제너럴 모터스", "F": "포드 모터",
    "APTV": "앱티브", "ORLY": "오라일리 오토모티브", "AZO": "오토존", "GPC": "제뉴인 파츠", "TSCO": "트랙터 서플라이",
    "TGT": "타겟", "TJX": "TJX", "ROST": "로스 스토어즈", "LULU": "룰루레몬 애슬레티카", "DECK": "데커스 아웃도어",
    "CROX": "크록스", "ONON": "온 홀딩", "DG": "달러 제너럴", "DLTR": "달러 트리", "BBY": "베스트바이",
    "EBAY": "이베이", "ETSY": "엣시", "W": "웨이페어", "CVNA": "카바나", "KMX": "카맥스",
    "CMG": "치폴레 멕시칸 그릴", "YUM": "얌 브랜즈", "QSR": "레스토랑 브랜즈 인터내셔널", "DRI": "다든 레스토랑츠",
    "WING": "윙스탑", "SHAK": "쉐이크쉑", "CAVA": "카바 그룹", "CELH": "셀시어스 홀딩스", "MNST": "몬스터 베버리지",
    "KDP": "큐리그 닥터페퍼", "STZ": "컨스텔레이션 브랜즈", "TAP": "몰슨 쿠어스 베버리지", "BF-B": "브라운-포맨",
    "PM": "필립 모리스 인터내셔널", "MO": "알트리아 그룹", "BTI": "브리티시 아메리칸 토바코", "MDLZ": "몬덜리즈 인터내셔널",
    "HSY": "허쉬", "GIS": "제너럴 밀스", "K": "켈라노바", "KHC": "크래프트 하인즈", "CAG": "콘아그라 브랜즈",
    "TSN": "타이슨 푸드", "HRL": "호멜 푸드", "SJM": "J.M. 스머커", "MKC": "맥코믹", "CPB": "캠벨 수프",
    "KR": "크로거", "SYY": "시스코(식품)", "ADM": "아처 대니얼스 미들랜드", "BG": "번지 글로벌", "CTVA": "코르테바",
    "EL": "에스티 로더", "CL": "콜게이트-파몰리브", "KMB": "킴벌리 클라크", "CHD": "처치 앤 드와이트", "CLX": "클로록스",
    "KVUE": "켄뷰", "ULTA": "울타 뷰티", "ELF": "엘프 뷰티", "SPGI": "S&P 글로벌", "MCO": "무디스",
    "MSCI": "MSCI", "ICE": "인터컨티넨탈 익스체인지", "CME": "CME 그룹", "NDAQ": "나스닥", "CBOE": "CBOE 글로벌 마켓",
    "BX": "블랙스톤", "KKR": "KKR", "APO": "아폴로 글로벌 매니지먼트", "ARES": "아레스 매니지먼트", "CG": "칼라일 그룹",
    "AMP": "아메리프라이즈 파이낸셜", "TROW": "티 로우 프라이스", "BEN": "프랭클린 리소시스", "STT": "스테이트 스트리트",
    "BK": "뉴욕멜론은행", "NTRS": "노던 트러스트", "USB": "US 뱅코프", "PNC": "PNC 파이낸셜 서비스", "TFC": "트루이스트 파이낸셜",
    "COF": "캐피탈 원 파이낸셜", "DFS": "디스커버 파이낸셜 서비스", "SYF": "싱크로니 파이낸셜", "ALLY": "앨리 파이낸셜",
    "FITB": "피프스 서드 뱅코프", "HBAN": "헌팅턴 뱅크셰어스", "RF": "리전스 파이낸셜", "CFG": "시티즌스 파이낸셜 그룹",
    "KEY": "키코프", "MTB": "M&T 뱅크", "FCNCA": "퍼스트 시티즌스 뱅크셰어스", "CB": "처브", "PGR": "프로그레시브",
    "TRV": "트래블러스", "ALL": "올스테이트", "HIG": "하트포드 파이낸셜", "MET": "메트라이프", "PRU": "프루덴셜 파이낸셜",
    "AFL": "애플랙", "AIG": "AIG", "AJG": "아서 J. 갤러거", "MMC": "마시 앤 맥레넌", "AON": "에이온", "WTW": "윌리스 타워스 왓슨"
}

CACHE_FILE = "kor_names_cache.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def http_get_text(url, timeout=12):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8-sig", errors="ignore")

def get_logo_url(ticker):
    clean_t = ticker.replace("-", ".")
    return f"https://assets.parqet.com/logos/symbol/{clean_t}?format=png"

def clean_eng_company_name(name):
    suffixes = [
        r"\bInc\.?", r"\bCorp\.?", r"\bCorporation\b", r"\bCompany\b", r"\bCo\.?",
        r"\bHoldings?\b", r"\bGroup\b", r"\bPLC\b", r"\bLtd\.?", r"\bLimited\b",
        r"\bL\.?P\.?", r"\bLLC\b", r"\bN\.?V\.?", r"\bS\.?A\.?", r"\bClass [A-Z]\b",
        r"\bCommon Stock\b", r"\bThe\b"
    ]
    cleaned = name
    for s in suffixes:
        cleaned = re.sub(s, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
    return cleaned if cleaned else name

def fetch_korean_name_online(args):
    ticker, eng_name = args
    # 1순위: 네이버 증권 해외주식 검색 API (국내 증권사 표준 한글명)
    try:
        url = f"https://ac.stock.naver.com/ac?q={urllib.parse.quote(ticker)}&target=stock"
        txt = http_get_text(url, timeout=5)
        data = json.loads(txt)
        for item in data.get("items", []):
            code = str(item.get("code", "")).upper()
            if code == ticker or code.startswith(ticker + "."):
                kname = item.get("name", "").strip()
                if kname and any('\uac00' <= c <= '\ud7a3' for c in kname):
                    return ticker, kname
    except Exception:
        pass

    # 2순위: 구글 번역 API
    cleaned = clean_eng_company_name(eng_name)
    try:
        g_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ko&dt=t&q={urllib.parse.quote(cleaned)}"
        txt = http_get_text(g_url, timeout=5)
        arr = json.loads(txt)
        translated = "".join([part[0] for part in arr[0] if part[0]])
        if translated:
            return ticker, translated.strip()
    except Exception:
        pass

    return ticker, cleaned

def build_full_korean_names(raw_ticker_dict):
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    final_map = {}
    todo = []
    for t, eng in raw_ticker_dict.items():
        if t in KOR_NAMES:
            final_map[t] = KOR_NAMES[t]
        elif t in cache and any('\uac00' <= c <= '\ud7a3' for c in cache[t]):
            final_map[t] = cache[t]
        else:
            todo.append((t, eng))

    if todo:
        print(f"-> 사전에 없는 {len(todo)}개 종목의 국내 증권사 한글 기업명 자동 매칭 중...")
        with ThreadPoolExecutor(max_workers=15) as ex:
            for t, kname in ex.map(fetch_korean_name_online, todo):
                final_map[t] = kname
                cache[t] = kname
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return final_map

def parse_wiki_table_pure(html_text):
    """외부 라이브러리(pandas/lxml) 없이 순수 파이썬으로 위키피디아 테이블에서 티커와 기업명을 추출합니다."""
    results = {}
    tables = re.findall(r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>', html_text, re.DOTALL | re.IGNORECASE)
    for tbl in tables:
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, re.DOTALL | re.IGNORECASE)
        if len(rows) < 300:
            continue
        headers = [re.sub(r'<[^>]+>', '', h).strip().lower() for h in re.findall(r'<th[^>]*>(.*?)</th>', rows[0], re.DOTALL | re.IGNORECASE)]
        sym_idx, name_idx = -1, -1
        for idx, h in enumerate(headers):
            if 'symbol' in h or 'ticker' in h:
                sym_idx = idx
            elif 'company' in h or 'security' in h or 'name' in h:
                name_idx = idx
        if sym_idx == -1:
            continue
        if name_idx == -1:
            name_idx = 0 if sym_idx != 0 else 1

        for r in rows[1:]:
            cols = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.IGNORECASE)
            if len(cols) > max(sym_idx, name_idx):
                sym = re.sub(r'<[^>]+>', '', cols[sym_idx]).strip().replace(".", "-").replace("/", "-")
                name = re.sub(r'<[^>]+>', '', cols[name_idx]).strip()
                sym = re.sub(r'\[.*?\]', '', sym).strip()
                name = re.sub(r'\[.*?\]', '', name).strip()
                if sym and len(sym) <= 5 and sym.isalpha() or "-" in sym:
                    results[sym] = name
    return results

def get_russell1000_tickers():
    raw_ticker_dict = {}

    # 1순위: iShares Russell 1000 ETF (IWB) 공식 보유종목 CSV 전체 파싱
    try:
        iwb_url = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/1467271812596.ajax?fileType=csv&fileName=IWB_holdings&dataType=fund"
        txt = http_get_text(iwb_url, timeout=20)
        lines = txt.splitlines()
        start_idx = -1
        for i, line in enumerate(lines[:50]):
            clean_line = line.strip().lstrip('\ufeff')
            if clean_line.startswith("Ticker,") or clean_line.startswith('"Ticker"'):
                start_idx = i
                lines[i] = clean_line
                break
        if start_idx != -1:
            reader = csv.DictReader(lines[start_idx:])
            for row in reader:
                asset_cls = str(row.get("Asset Class", "")).strip()
                if asset_cls and asset_cls != "Equity":
                    continue
                t = str(row.get("Ticker", "")).strip().replace(".", "-").replace("/", "-")
                name = str(row.get("Name", "")).strip()
                if not t or t == "nan" or t == "-" or len(t) > 5 or " " in t or not name:
                    continue
                raw_ticker_dict[t] = name
    except Exception as e:
        print(f"IWB CSV 로드 참고: {e}")

    # 2순위: 만약 IWB CSV에서 800개 미만으로 가져왔다면 위키피디아 Russell 1000 / S&P 500 + 400에서 보충
    if len(raw_ticker_dict) < 800:
        wiki_urls = [
            "https://en.wikipedia.org/wiki/Russell_1000_Index",
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
        ]
        for wurl in wiki_urls:
            try:
                html = http_get_text(wurl, timeout=15)
                extracted = parse_wiki_table_pure(html)
                for k, v in extracted.items():
                    if k not in raw_ticker_dict:
                        raw_ticker_dict[k] = v
                if len(raw_ticker_dict) >= 950:
                    break
            except Exception:
                continue

    print(f"-> 수집된 러셀 1000 원본 티커 수: {len(raw_ticker_dict)}개")
    kor_map = build_full_korean_names(raw_ticker_dict)
    return list(kor_map.keys()), kor_map

def calc_rsi_pure(closes, period=14):
    if len(closes) <= period:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(diff if diff > 0 else 0.0)
        losses.append(-diff if diff < 0 else 0.0)

    alpha = 1.0 / period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = alpha * g + (1 - alpha) * avg_gain
        avg_loss = alpha * l + (1 - alpha) * avg_loss

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def fetch_single_stock_yahoo(args):
    """야후 파이낸스 속도 제한(429) 방지를 위해 재시도(Retry) 로직 및 듀얼 엔드포인트(query1/query2) 적용"""
    ticker, kor_name = args
    
    for attempt in range(3):
        host = "query1" if attempt % 2 == 0 else "query2"
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range=2y&interval=1d"
        try:
            txt = http_get_text(url, timeout=10)
            data = json.loads(txt)
            res_list = data.get("chart", {}).get("result")
            if not res_list:
                return None
            res = res_list[0]
            timestamps = res.get("timestamp", [])
            quote = res.get("indicators", {}).get("quote", [{}])[0]
            closes_raw = quote.get("close", [])
            highs_raw = quote.get("high", [])
            lows_raw = quote.get("low", [])
            vols_raw = quote.get("volume", [])

            valid_rows = []
            for ts, c, h, l, v in zip(timestamps, closes_raw, highs_raw, lows_raw, vols_raw):
                if c is not None and h is not None and l is not None:
                    vol_val = float(v) if v is not None else 0.0
                    valid_rows.append((ts, float(c), float(h), float(l), vol_val))

            # 최소 200거래일 미만(신규 상장 등) 또는 최근 15일 이상 거래가 멈춘 상장폐지 종목 제외
            if len(valid_rows) < 200:
                return None
            last_ts, curr_price, _, _, curr_vol = valid_rows[-1]
            if (time.time() - last_ts) > 15 * 86400:
                return None

            closes = [r[1] for r in valid_rows]
            highs = [r[2] for r in valid_rows]
            lows = [r[3] for r in valid_rows]
            vols = [r[4] for r in valid_rows]

            sma20 = sum(closes[-20:]) / 20.0
            sma200 = sum(closes[-200:]) / 200.0
            rsi = calc_rsi_pure(closes, 14)

            vol_20_avg = sum(vols[-20:]) / 20.0
            vol_ratio = round((curr_vol / vol_20_avg) * 100, 1) if vol_20_avg > 0 else 100.0

            high_52w = max(highs[-252:]) if len(highs) >= 252 else max(highs)
            low_52w = min(lows[-252:]) if len(lows) >= 252 else min(lows)
            pct_from_high = round(((curr_price - high_52w) / high_52w) * 100, 2)
            pct_from_low = round(((curr_price - low_52w) / low_52w) * 100, 2)

            diff_sma20 = round(((curr_price - sma20) / sma20) * 100, 2)
            diff_sma200 = round(((curr_price - sma200) / sma200) * 100, 2)

            return {
                "logo": get_logo_url(ticker),
                "ticker": ticker,
                "name": kor_name,
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
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # 404는 실제로 야후에 없는(상장폐지) 심볼이므로 즉시 종료
                return None
            # 429(Too Many Requests) 등은 잠시 대기 후 재시도
            time.sleep(0.6 * (attempt + 1) + random.uniform(0.1, 0.4))
        except Exception:
            time.sleep(0.4 * (attempt + 1))

    return None

def run_screener():
    print("1. 러셀 1000(Russell 1000) 전체 종목 리스트 및 국내 증권사 한글명 매핑 중...")
    tickers, name_map = get_russell1000_tickers()
    total_candidates = len(tickers)
    print(f"-> 총 {total_candidates}개 종목 확인 완료. 누락 방지를 위한 안정적 주가 수집 시작...")

    results_sma20 = []
    results_sma200 = []
    all_stocks = []

    tasks = [(t, name_map.get(t, t)) for t in tickers]
    completed = 0

    # 야후 서버 차단(429)이 걸리지 않는 최적의 병렬 워커 수(10개)로 전 종목 빠짐없이 수집
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single_stock_yahoo, task) for task in tasks]
        for future in as_completed(futures):
            completed += 1
            if completed % 100 == 0 or completed == total_candidates:
                print(f"2. 주가 분석 진행률: {completed} / {total_candidates} (현재 정상 수집: {len(all_stocks)}개)")
            info = future.result()
            if info:
                all_stocks.append(info)
                if abs(info["diff_sma20"]) <= 2.0:
                    results_sma20.append(info)
                if abs(info["diff_sma200"]) <= 2.0:
                    results_sma200.append(info)

    results_sma20.sort(key=lambda x: abs(x["diff_sma20"]))
    results_sma200.sort(key=lambda x: abs(x["diff_sma200"]))
    all_stocks.sort(key=lambda x: x["ticker"])

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "universe": "Russell 1000 (Active)",
        "total_analyzed": len(all_stocks),
        "sma20_near": results_sma20,
        "sma200_near": results_sma200,
        "all_stocks": all_stocks
    }

    with open("screened_stocks.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"완료! 상폐 제외 정상 반영 종목: {len(all_stocks)}개 (20일선 근접: {len(results_sma20)}개, 200일선 근접: {len(results_sma200)}개)")

if __name__ == "__main__":
    run_screener()