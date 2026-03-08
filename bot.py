
import requests
import pandas as pd
from telegram import Bot
from datetime import datetime, timedelta
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
TD_API_KEY = "454cf9eb0d8d4fa7a8b033b256eeb6ab"
TELEGRAM_TOKEN = "8663731149:AAHw8gZzbTt42FvzOO7Qr8YMCnnS96s9xIA"
CHAT_ID = "8255900012"
bot = Bot(token=TELEGRAM_TOKEN)

PAIRS = ["GBP/USD", "EUR/USD", "USD/JPY", "USD/CHF"]
TRADE_AMOUNT = 50  # Demo amount
EXPIRATION = 2     # minutes
TARGET_PIPS = "5–7 pips"

MORNING_SESSION = (10, 12)
EVENING_SESSION = (17, 19)
MAX_SIGNALS_PER_SESSION = 4
HEARTBEAT_INTERVAL = 6 * 60 * 60  # 6 hours

# -----------------------------
# STATE TRACKING
# -----------------------------
signals_sent = {"morning": 0, "evening": 0}
last_heartbeat = datetime.now() - timedelta(seconds=HEARTBEAT_INTERVAL)
start_time = datetime.now()

# -----------------------------
# FUNCTIONS
# -----------------------------
def get_candles(pair):
    symbol = pair.replace("/","")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=10&apikey={TD_API_KEY}"
    resp = requests.get(url).json()
    if "values" not in resp:
        print(f"No data for {pair}: {resp}")
        return None
    df = pd.DataFrame(resp["values"])
    df = df.sort_values("datetime")
    df["close"] = df["close"].astype(float)
    return df

def detect_signal(df):
    if df is None or len(df) < 3:
        return None
    df["EMA9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["EMA21"] = df["close"].ewm(span=21, adjust=False).mean()
    last = df.iloc[-3:]
    ema9 = last["EMA9"].values
    ema21 = last["EMA21"].values
    close = last["close"].values

    if ema9[-2] > ema21[-2] and ema9[-1] < ema21[-1]:
        if close[-1] < close[-2] < close[-3]:
            return "SELL"
    if ema9[-2] < ema21[-2] and ema9[-1] > ema21[-1]:
        if close[-1] > close[-2] > close[-3]:
            return "BUY"
    return None

def send_signal(pair, direction):
    message = f"""👑👑👑👑👑👑 
SIGNAL

💱 Pair: {pair}
⏱ Expiration: {EXPIRATION} min
💰 Trade Amount: ${TRADE_AMOUNT}
{'⬇️' if direction=='SELL' else '⬆️'} Direction: {direction} ({'Down' if direction=='SELL' else 'Up'})

🔍 Analysis: {"Lower highs" if direction=="SELL" else "Higher lows"} forming, EMA 9 crossed EMA 21 {'downward' if direction=='SELL' else 'upward'}
🏹 Target: {TARGET_PIPS}"""
    bot.send_message(chat_id=CHAT_ID, text=message)

def send_heartbeat():
    uptime = int((datetime.now() - start_time).total_seconds() / 60)
    trades_today = signals_sent["morning"] + signals_sent["evening"]
    message = f"""☘️ CRUXIFEED HEARTBEAT

⏱ Uptime: {uptime} minutes
📊 Trades Today: {trades_today}/{MAX_SIGNALS_PER_SESSION*2}
📡 Status: ONLINE"""
    bot.send_message(chat_id=CHAT_ID, text=message)

def in_session():
    now = datetime.now()
    hour = now.hour
    if MORNING_SESSION[0] <= hour < MORNING_SESSION[1]:
        return "morning"
    elif EVENING_SESSION[0] <= hour < EVENING_SESSION[1]:
        return "evening"
    return None

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    session = in_session()
    now = datetime.now()

    # Heartbeat every 6 hours
    if (now - last_heartbeat).total_seconds() >= HEARTBEAT_INTERVAL:
        send_heartbeat()
        last_heartbeat = now

    # Check signals only during sessions
    if session and signals_sent[session] < MAX_SIGNALS_PER_SESSION:
        for pair in PAIRS:
            df = get_candles(pair)
            signal = detect_signal(df)
            if signal:
                send_signal(pair, signal)
                signals_sent[session] += 1
                print(f"Signal sent for {pair}: {signal}")
                time.sleep(60)  # Wait 1 min before checking next pair

    time.sleep(30)  # main loop wait