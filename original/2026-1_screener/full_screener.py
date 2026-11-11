import yfinance as yf
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Data parsed from Wikipedia table
raw_data = """
Amorepacific | 090430
Amorepacific Holdings | 002790
APR | 278470
Asia Holdings | 002030
BGF Retail | 282330
BNK Financial | 138930
Celltrion | 068270
Cheil Worldwide | 030000
Chong Kun Dang | 185750
CJ | 001040
CJ CheilJedang | 097950
CJ Logistics | 000120
Cosmax | 192820
Cosmo Chemical | 005420
Coway | 021240
CS Wind | 112610
Daesang | 001680
Daewoo E&C | 047040
Daewoong | 003090
Daewoong Pharmaceutical | 069620
DB Insurance | 005830
DL | 000210
DL E&C | 375500
DN Automotive | 007340
Dongsuh | 026960
Dongwon Industries | 006040
Dongwon Systems | 014820
Doosan | 000150
Doosan Bobcat | 241560
Doosan Enerbility | 034020
Doosan Robotics | 454910
DoubleU Games | 192080
Ecopro Materials | 450080
Emart | 139480
F&F | 383220
Foosung | 093370
Grand Korea Leisure | 114090
Green Cross | 006280
Green Cross Holdings | 005250
GS | 078930
GS E&C | 006360
GS Retail | 007070
Hana Financial | 086790
Hanall Biopharma | 009420
Hanil Cement | 300720
Hanjin KAL | 180640
Hankook | 161390
Hankook & Company | 000240
Hanmi Pharm | 128940
Hanmi Science | 008930
Hanmi Semiconductor | 042700
Hanon Systems | 018880
Hansol Chemical | 014680
Hanssem | 009240
Hanwha | 000880
Hanwha Aerospace | 012450
Hanwha Engine | 082740
Hanwha Life | 088350
Hanwha Ocean | 042660
Hanwha Solutions | 009830
Hanwha Systems | 272210
HD Hyundai | 267250
HD Hyundai Electric | 267260
HD Hyundai Heavy Industries | 329180
HD Hyundai Marine Engine | 071970
HD Hyundai Marine Solution | 443060
HD KSOE | 009540
Hankuk Carbon | 017960
HiteJinro | 000080
HL Mando | 204320
HMM | 011200
Hotel Shilla | 008770
HS Hyosung Advanced Materials | 298050
Hybe | 352820
Hyosung Heavy Industries | 298040
Hyosung TNC | 298020
Hyundai AutoEver | 307950
Hyundai Department Store | 069960
Hyundai E&C | 000720
Hyundai Elevator | 017800
Hyundai Glovis | 086280
Hyundai Marine & Fire | 001450
Hyundai Mobis | 012330
Hyundai Motor | 005380
Hyundai Rotem | 064350
Hyundai Steel | 004020
Hyundai WIA | 011210
IM Financial | 139130
Industrial Bank of Korea | 024110
Isu Petasys | 007660
Isu Specialty Chemical | 457190
JB Financial | 175330
Kakao | 035720
KakaoBank | 323410
KakaoPay | 377300
Kangwon Land | 035250
KB Financial | 105560
KCC | 002380
KEPCO | 015760
KEPCO E&C | 052690
KEPCO KPS | 051600
Kia | 000270
Kiwoom Securities | 039490
Kolmar Korea | 161890
Kolon Industries | 120110
Korea Aerospace | 047810
Korea District Heating | 071320
Korea Gas | 036460
Korea Investment | 071050
Korea Petrochemical | 006650
Korea Zinc | 010130
Korean Air | 003490
Krafton | 259960
KT | 030200
KT&G | 033780
Kumho Petrochemical | 011780
Kumho Tire | 073240
L&F | 066970
LG | 003550
LG Chem | 051910
LG CNS | 064400
LG Display | 034220
LG Electronics | 066570
LG Energy Solution | 373220
LG H&H | 051900
LG Innotek | 011070
LG Uplus | 032640
LIG Nex1 | 079550
Lotte | 004990
Lotte Chemical | 011170
Lotte Chilsung | 005300
Lotte Fine Chemical | 004000
Lotte Shopping | 023530
Lotte Wellfood | 280360
LS | 006260
LS Electric | 010120
Meritz Financial | 138040
Mirae Asset Securities | 006800
Misto | 081660
Miwon Commercial | 002840
Miwon Specialty Chemical | 268280
Naver | 035420
NCSoft | 036570
Netmarble | 251270
NH Investment & Securities | 005940
Nongshim | 004370
OCI Holdings | 010060
Orion | 271560
Orion Holdings | 001800
Ottogi | 007310
Pan Ocean | 028670
Paradise | 034230
Poongsan | 103140
POSCO | 005490
POSCO DX | 022100
POSCO Future M | 003670
POSCO International | 047050
S-1 | 012750
Sanil Electric | 062040
Samsung Biologics | 207940
Samsung C&T | 028260
Samsung Card | 029780
Samsung E&A | 028050
Samsung Electro-Mechanics | 009150
Samsung Electronics | 005930
Samsung Epis | 0126Z0
Samsung Fire & Marine | 000810
Samsung Heavy Industries | 010140
Samsung Life | 032830
Samsung SDI | 006400
Samsung SDS | 018260
Samsung Securities | 016360
Samyang Foods | 003230
SD Biosensor | 137310
Seah Besteel | 001430
Seah Steel Holdings | 003030
Sebang Global Battery | 004490
Shinhan Financial | 055550
Shinsegae | 004170
SK | 034730
SK Biopharm | 326030
SK Bioscience | 302440
SK Chemicals | 285130
SK Hynix | 000660
SK IE Technology | 361610
SK Innovation | 096770
SK Square | 402340
SK Telecom | 017670
SKC | 011790
SL | 005850
S-Oil | 010950
Taekwang Industrial | 003240
Taihan Cable & Solution | 001440
TKG Huchems | 069260
Woori Financial | 316140
Youlchon Chemical | 008730
Young Poong | 000670
Youngone | 111770
Youngone Holdings | 009970
Yuhan | 000100
"""

stocks = []
for line in raw_data.strip().split('\n'):
    if '|' in line:
        name, symbol = line.split('|')
        stocks.append((symbol.strip() + ".KS", name.strip()))

def screen_stocks(stock_list):
    breakouts = []
    period = 20
    multiplier = 2.0
    
    print(f"Screening {len(stock_list)} KOSPI 200 stocks...")
    
    # Process in batches for better performance
    for ticker_code, name in stock_list:
        try:
            df = yf.download(ticker_code, period='2mo', interval='1d', progress=False)
            if len(df) < period: continue
            
            # Keltner calculation
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - df['Close'].shift()).abs()
            low_close = (df['Low'] - df['Close'].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            ema = df['Close'].ewm(span=period, adjust=False).mean()
            upper_band = ema + (multiplier * atr)
            lower_band = ema - (multiplier * atr)
            
            current_close = df['Close'].iloc[-1].item()
            current_upper = upper_band.iloc[-1].item()
            current_lower = lower_band.iloc[-1].item()
            
            if (current_upper - current_lower) != 0:
                k_pos = (current_close - current_lower) / (current_upper - current_lower)
            else:
                k_pos = 0

            # Condition: Upper < Close AND Position >= 0.8
            if current_close > current_upper and k_pos >= 0.8:
                prev_close = df['Close'].iloc[-2].item()
                change = ((current_close - prev_close) / prev_close) * 100
                breakouts.append({
                    'Ticker': ticker_code.replace('.KS', ''),
                    'Name': name,
                    'Close': int(current_close),
                    'Upper': round(current_upper, 2),
                    'Position': round(k_pos, 3),
                    'Change(%)': round(change, 2)
                })
        except:
            continue
            
    return pd.DataFrame(breakouts)

results = screen_stocks(stocks)
if not results.empty:
    print(results.to_markdown(index=False))
else:
    print("No KOSPI 200 stocks found matching the criteria.")
