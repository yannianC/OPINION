#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rsi_top200_sqlite.py
Full version (Scheme B confirmation):
- Monitor Binance USDT Top N (default 200)
- 15m aligned to UTC+8 (0/15/30/45)
- Signal: RSI-step crosses ±50 from inside->outside + candle close + multi-TF confirmation
- TP1/TP2/TP3, initial SL (ATR), trailing SL on TP hits
- FVG simple detection, support/resistance, AI scoring
- Persistence: SQLite (trade_record.db)
- Push: Telegram (image + text) if TG token provided
"""

import os
import sys
import time
import math
import json
import ccxt
import sqlite3
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
from PIL import Image
from dateutil import tz

# -------------------------
# CONFIG -- modify as needed
# -------------------------
TG_BOT_TOKEN = "6343055800:AAEEhBUrIg0qkI2CG8mTHtZT0qRjHc1i2JI"   # <- fill your bot token
TG_CHAT_ID = "6387103286"     # <- fill your chat id (e.g. -100...)
SEND_PHOTO = True    # B mode uses image push

# 代理配置
PROXIES = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}

SYMBOL_BASE = "USDT"
TOP_N = 200
MAIN_TF = "15m"
MULTI_TF = ["1h", "4h"]   # higher timeframes to confirm
LIMIT = 300
COOLDOWN_SECONDS = 60 * 60  # per-symbol state cooldown after triggered (1 hour)
RSI_LEN = 14
SMOOTH_LEN = 3
THRESH = 50.0
ATR_LEN = 14
OUT_DIR = "charts"
DB_FILE = "trade_record.db"
SMALL_SLEEP = 0.12   # small pause between requests to reduce rate limit
MAX_RETRIES = 2

os.makedirs(OUT_DIR, exist_ok=True)

# -------------------------
# Time helpers
# -------------------------
def utc_now():
    return datetime.now(timezone.utc)

def utc8_now():
    return utc_now() + timedelta(hours=8)

def utc8_str():
    return utc8_now().strftime("%Y-%m-%d %H:%M:%S")

def ts_now():
    return utc_now().strftime("%Y%m%dT%H%M%SZ")

# -------------------------
# SQLite init
# -------------------------
def init_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
      id TEXT PRIMARY KEY,
      symbol TEXT,
      direction TEXT,
      entry REAL,
      exit REAL,
      result TEXT,
      tp_level INTEGER,
      created_at TEXT,
      closed_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
      symbol TEXT PRIMARY KEY,
      total INTEGER DEFAULT 0,
      wins INTEGER DEFAULT 0,
      losses INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    return conn, cur

db_conn, db_cur = init_db(DB_FILE)

# -------------------------
# Telegram helpers
# -------------------------
TG_API_BASE = f"https://api.telegram.org/bot{TG_BOT_TOKEN}" if TG_BOT_TOKEN else None

def send_tg_text(text):
    """
    发送Telegram文本消息（使用代理）
    """
    if not TG_API_BASE or not TG_CHAT_ID:
        print("[TG] not configured. Message would be:\n", text)
        return None
    try:
        payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
        r = requests.post(f"{TG_API_BASE}/sendMessage", data=payload, timeout=20, proxies=PROXIES)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("[TG] send text error:", e)
        return None

def send_tg_photo(pfile, caption=""):
    """
    发送Telegram图片消息（使用代理）
    """
    if not TG_API_BASE or not TG_CHAT_ID:
        print("[TG] not configured. Photo would be:", pfile)
        return None
    if not pfile or not os.path.exists(pfile):
        print("[TG] photo not found:", pfile)
        return None
    try:
        with open(pfile, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(f"{TG_API_BASE}/sendPhoto", files=files, data=data, timeout=40, proxies=PROXIES)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print("[TG] send photo error:", e)
        return None

# -------------------------
# Indicator helpers
# -------------------------
def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def rsi_series(close, length=RSI_LEN):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(length, min_periods=length).mean()
    avg_loss = loss.rolling(length, min_periods=length).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def atr_series(high, low, close, length=ATR_LEN):
    prev = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev).abs()
    tr3 = (low - prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(length, min_periods=1).mean()

def bollinger(close, length=20, mult=2.0):
    ma = close.rolling(length).mean()
    sd = close.rolling(length).std()
    return ma, ma + mult * sd, ma - mult * sd

def stepline_from_smoothed(smoothed: pd.Series):
    s = smoothed.ffill().fillna(0)
    step = s.copy()
    for i in range(1, len(s)):
        step.iat[i] = s.iat[i-1]
    return step

# -------------------------
# FVG simple finder
# -------------------------
def find_fvg_zones(df):
    zones = []
    n = len(df)
    for i in range(2, n):
        try:
            if df['low'].iat[i-2] > df['high'].iat[i]:
                zones.append({"type": "up", "top": float(df['high'].iat[i]), "bottom": float(df['low'].iat[i-2]), "i": i})
            if df['high'].iat[i-2] < df['low'].iat[i]:
                zones.append({"type": "down", "top": float(df['high'].iat[i-2]), "bottom": float(df['low'].iat[i]), "i": i})
        except Exception:
            continue
    return zones

# -------------------------
# Swing / divergence
# -------------------------
def find_swings_idx(series: pd.Series, left=2, right=2):
    highs, lows = [], []
    n = len(series)
    for i in range(left, n-right):
        v = series.iat[i]
        if v > series.iloc[i-left:i].max() and v > series.iloc[i+1:i+1+right].max():
            highs.append(i)
        if v < series.iloc[i-left:i].min() and v < series.iloc[i+1:i+1+right].min():
            lows.append(i)
    return highs, lows

def detect_rsi_divergence(closes: pd.Series, rsi: pd.Series, window=120):
    recent_close = closes.tail(window)
    highs, lows = find_swings_idx(recent_close, left=2, right=2)
    base = len(closes) - len(recent_close)
    top_div = bottom_div = False
    if len(highs) >= 2:
        i1, i2 = base + highs[-2], base + highs[-1]
        try:
            if closes.iat[i2] > closes.iat[i1] and rsi.iat[i2] < rsi.iat[i1]:
                top_div = True
        except Exception:
            pass
    if len(lows) >= 2:
        i1, i2 = base + lows[-2], base + lows[-1]
        try:
            if closes.iat[i2] < closes.iat[i1] and rsi.iat[i2] > rsi.iat[i1]:
                bottom_div = True
        except Exception:
            pass
    return top_div, bottom_div

# -------------------------
# Multi TF trend
# -------------------------
def tf_trend_name(df: pd.DataFrame):
    c = df['close']
    try:
        e21 = ema(c, 21).iat[-1]
        e50 = ema(c, 50).iat[-1]
        e100 = ema(c, 100).iat[-1]
        e200 = ema(c, 200).iat[-1]
    except Exception:
        return "NEUTRAL"
    if e21 > e50 > e100 > e200:
        return "UP"
    if e21 < e50 < e100 < e200:
        return "DOWN"
    return "NEUTRAL"

# -------------------------
# AI signal scoring (simple)
# -------------------------
def ai_signal_level(ema_vals, rsi_val, vol_ok, multi_tf_trend):
    score = 0
    if ema_vals.get("aligned_up"):
        score += 35
    if ema_vals.get("aligned_down"):
        score -= 35
    if rsi_val is not None:
        if rsi_val < 30:
            score += 20
        if rsi_val > 70:
            score -= 20
    if vol_ok:
        score += 10
    ups = list(multi_tf_trend.values()).count("UP")
    downs = list(multi_tf_trend.values()).count("DOWN")
    if ups >= 2:
        score += 20
    if downs >= 2:
        score -= 20
    score = max(-100, min(100, score))
    if score >= 60:
        label = "强烈做多"
    elif score >= 15:
        label = "做多"
    elif score > -15:
        label = "中性"
    elif score > -60:
        label = "做空"
    else:
        label = "强烈做空"
    return label, score

# -------------------------
# Support / Resistance (simple)
# -------------------------
def detect_support_resistance(df, window=30):
    highs, lows = [], []
    h = df['high']; l = df['low']; n = len(df)
    for i in range(window, n-window):
        if h.iat[i] == h.iloc[i-window:i+window].max():
            highs.append(float(h.iat[i]))
        if l.iat[i] == l.iloc[i-window:i+window].min():
            lows.append(float(l.iat[i]))
    highs = sorted(list(set(highs)))
    lows = sorted(list(set(lows)))
    return highs[-3:], lows[:3]

# -------------------------
# TP/SL calculation
# -------------------------
def compute_tp_sl(entry_price, direction, atr):
    if atr is None or atr <= 0:
        atr = max(0.0001, entry_price * 0.001)
    if direction == "LONG":
        tp1 = entry_price + atr * 1.0
        tp2 = entry_price + atr * 1.8
        tp3 = entry_price + atr * 3.0
        sl = entry_price - atr * 1.2
    elif direction == "SHORT":
        tp1 = entry_price - atr * 1.0
        tp2 = entry_price - atr * 1.8
        tp3 = entry_price - atr * 3.0
        sl = entry_price + atr * 1.2
    else:
        return None
    def r(v):
        return round(v, 6) if v >= 1 else round(v, 8)
    return {"tp1": r(tp1), "tp2": r(tp2), "tp3": r(tp3), "sl": r(sl), "atr": atr}

# -------------------------
# Trailing SL update on TP hits
# -------------------------
def update_trailing_sl(trade, current_price):
    moved = False
    dirc = trade.get("direction")
    if dirc == "LONG":
        if (not trade.get("tp1_hit", False)) and trade.get("tp1") and current_price >= trade.get("tp1"):
            trade["tp1_hit"] = True; trade["sl"] = trade["entry"]; moved = True
        if (not trade.get("tp2_hit", False)) and trade.get("tp2") and current_price >= trade.get("tp2"):
            trade["tp2_hit"] = True; trade["sl"] = trade.get("tp1", trade["entry"]); moved = True
        if (not trade.get("tp3_hit", False)) and trade.get("tp3") and current_price >= trade.get("tp3"):
            trade["tp3_hit"] = True; trade["sl"] = trade.get("tp2", trade.get("tp1", trade["entry"])); moved = True
    elif dirc == "SHORT":
        if (not trade.get("tp1_hit", False)) and trade.get("tp1") and current_price <= trade.get("tp1"):
            trade["tp1_hit"] = True; trade["sl"] = trade["entry"]; moved = True
        if (not trade.get("tp2_hit", False)) and trade.get("tp2") and current_price <= trade.get("tp2"):
            trade["tp2_hit"] = True; trade["sl"] = trade.get("tp1", trade["entry"]); moved = True
        if (not trade.get("tp3_hit", False)) and trade.get("tp3") and current_price <= trade.get("tp3"):
            trade["tp3_hit"] = True; trade["sl"] = trade.get("tp2", trade.get("tp1", trade["entry"])); moved = True
    return moved

# -------------------------
# Plotting (price + EMA + step + TP/SL)
# -------------------------
def plot_signal_chart(symbol, df, step_series, signals, tpsl, outpath):
    plt.close("all")
    fig = plt.figure(figsize=(12,7))
    ax1 = fig.add_axes([0.05,0.35,0.9,0.6])
    ax2 = fig.add_axes([0.05,0.05,0.9,0.25])
    times = pd.to_datetime(df['timestamp'], unit='ms') if 'timestamp' in df.columns else pd.to_datetime(df['ts'], unit='ms')
    o = df['open'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
    width = pd.Timedelta(minutes=10)
    for i in range(len(c)):
        color = 'green' if c[i] >= o[i] else 'red'
        ax1.plot([times[i], times[i]], [l[i], h[i]], color=color, linewidth=0.8)
        ax1.add_patch(plt.Rectangle((times[i] - width/2, min(o[i], c[i])), width, abs(c[i]-o[i]), color=color, alpha=0.8))
    ax1.set_title(f"{symbol} {MAIN_TF} {utc8_str()}")
    for span in (21,50,100,200):
        try:
            ax1.plot(times, ema(pd.Series(c), span), label=f"EMA{span}")
        except Exception:
            pass
    ax1.legend(loc='upper left')
    ax2.plot(times, step_series, drawstyle='steps-post', linewidth=2)
    ax2.axhline(THRESH, color='red', linestyle='--'); ax2.axhline(-THRESH, color='green', linestyle='--')
    ax2.set_ylim(-100,100); ax2.grid(True)
    for idx, val in signals.get('squares', []):
        if 0 <= idx < len(times):
            ax2.scatter(times.iloc[idx], step_series.iloc[idx], marker='s', color='red' if val=='top' else 'green', s=60)
    if tpsl:
        if tpsl.get('tp3') is not None: ax1.axhline(tpsl['tp3'], linestyle='-.', linewidth=1, label='TP3')
        if tpsl.get('tp2') is not None: ax1.axhline(tpsl['tp2'], linestyle=':', linewidth=1, label='TP2')
        if tpsl.get('tp1') is not None: ax1.axhline(tpsl['tp1'], linestyle='--', linewidth=1, label='TP1')
        if tpsl.get('sl') is not None: ax1.axhline(tpsl['sl'], linestyle='-', linewidth=1, label='SL')
        ax1.legend()
    plt.savefig(outpath, dpi=140, bbox_inches='tight')
    plt.close(fig)

# -------------------------
# Fetch top N symbols robustly
# -------------------------
def fetch_top_n_binance(n=TOP_N, exchange=None):
    """
    获取币安交易量前N的交易对（使用代理）
    """
    ex = exchange or ccxt.binance({
        "enableRateLimit": True,
        "proxies": PROXIES
    })
    try:
        tickers = ex.fetch_tickers()
    except Exception as e:
        print("[fetch_top_n_binance] fetch_tickers error:", e)
        try:
            mk = ex.load_markets()
            cand = [m for m in mk.keys() if m.endswith(f"/{SYMBOL_BASE}")]
            return [c.split("/")[0] for c in cand][:n]
        except Exception as e2:
            print("[fetch_top_n_binance] fallback load_markets failed:", e2)
            return []
    markets = []
    for sym, info in tickers.items():
        try:
            if f"/{SYMBOL_BASE}" not in sym:
                continue
            last = info.get("last") or info.get("close")
            baseVol = info.get("baseVolume") or 0
            if last is None:
                continue
            est = float(last) * float(baseVol)
            markets.append((sym.split("/")[0], est))
        except Exception:
            continue
    if not markets:
        try:
            mk = ex.load_markets()
            cand = [m for m in mk.keys() if m.endswith(f"/{SYMBOL_BASE}")]
            return [c.split("/")[0] for c in cand][:n]
        except Exception:
            return []
    markets_sorted = sorted(markets, key=lambda x: x[1] if x[1] else 0.0, reverse=True)
    return [m[0] for m in markets_sorted[:n]]

# -------------------------
# analyze_symbol: returns analysis dict
# -------------------------
def analyze_symbol(ex, symbol):
    pair = f"{symbol}/{SYMBOL_BASE}"
    # fetch main TF candles
    for attempt in range(MAX_RETRIES):
        try:
            ohlcv = ex.fetch_ohlcv(pair, timeframe=MAIN_TF, limit=LIMIT)
            break
        except Exception as e:
            print(f"[{symbol}] fetch_ohlcv error (attempt {attempt+1}):", e)
            time.sleep(0.5 + attempt)
            if attempt == MAX_RETRIES - 1:
                return None
    try:
        df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
        if df.empty or len(df) < 30:
            return None

        # compute indicators
        rsi = rsi_series(df['close'], RSI_LEN)
        smoothed = ema(rsi.fillna(0), SMOOTH_LEN)
        step = stepline_from_smoothed(smoothed)
        last_step = float(step.iat[-1])
        prev_step = float(step.iat[-2]) if len(step) >= 2 else 0.0
        last_price = float(df['close'].iat[-1])

        # squares detection (for plotting)
        squares = []
        for i in range(1, len(step)):
            prev = step.iat[i-1]; cur = step.iat[i]
            if prev > THRESH and cur <= THRESH:
                squares.append((i, 'top'))
            if prev < -THRESH and cur >= -THRESH:
                squares.append((i, 'bottom'))

        # divergence
        top_div, bottom_div = detect_rsi_divergence(df['close'], rsi, window=120)

        # EMAs
        ema21 = float(ema(df['close'],21).iat[-1])
        ema50 = float(ema(df['close'],50).iat[-1])
        ema100 = float(ema(df['close'],100).iat[-1])
        ema200 = float(ema(df['close'],200).iat[-1])
        aligned_up = ema21 > ema50 > ema100 > ema200
        aligned_down = ema21 < ema50 < ema100 < ema200

        # volume filter
        vol_ma = df['volume'].rolling(20).mean().iat[-1] if len(df) >= 20 else df['volume'].mean()
        vol_ok = df['volume'].iat[-1] > vol_ma

        # atr / boll
        atr_v = float(atr_series(df['high'], df['low'], df['close']).iat[-1])
        ma20, bb_up, bb_low = bollinger(df['close'])
        bb_u = float(bb_up.iat[-1]) if not math.isnan(bb_up.iat[-1]) else None
        bb_l = float(bb_low.iat[-1]) if not math.isnan(bb_low.iat[-1]) else None

        # fvg / sr
        fvg = find_fvg_zones(df)
        res_levels, sup_levels = detect_support_resistance(df)

        # multi-tf trends
        multi_tf = {}
        for tf in MULTI_TF:
            try:
                o2 = ex.fetch_ohlcv(pair, timeframe=tf, limit=200)
                df2 = pd.DataFrame(o2, columns=['timestamp','open','high','low','close','volume'])
                multi_tf[tf] = tf_trend_name(df2)
                time.sleep(SMALL_SLEEP)
            except Exception:
                multi_tf[tf] = "NEUTRAL"

        # AI
        ai_label, ai_score = ai_signal_level({"aligned_up": aligned_up, "aligned_down": aligned_down},
                                             float(rsi.iat[-1]) if not math.isnan(rsi.iat[-1]) else None,
                                             vol_ok, multi_tf)

        # detect whether step crossed threshold from inside to outside (scheme B)
        # CROSS TO OVERBOUGHT: prev_step <= THRESH and last_step > THRESH
        cross_to_overb = (prev_step <= THRESH and last_step > THRESH)
        # CROSS TO OVERSOLD: prev_step >= -THRESH and last_step < -THRESH
        cross_to_overs = (prev_step >= -THRESH and last_step < -THRESH)

        # decide triggered flag (but final requirement: candle must be closed and multi-TF confirm)
        # For our fetched candles, the "last" row is assumed closed (fetch_ohlcv returns closed candles)
        triggered = None
        direction = None
        if cross_to_overb:
            triggered = "OVERBOUGHT"; direction = "SHORT"
        elif cross_to_overs:
            triggered = "OVERSOLD"; direction = "LONG"

        # confirm multi-TF: require either (15m + at least one higher TF same) OR majority of all TFs agree
        def multi_tf_confirm(direction_hint):
            # map direction_hint LONG->UP, SHORT->DOWN
            need = "UP" if direction_hint == "LONG" else "DOWN"
            votes = [v for v in multi_tf.values()]
            count_need = votes.count(need)
            # requirement: either 15m equals need AND (1 higher TF also equals), or majority of TFs equals need
            tf15 = tf_trend_name(pd.DataFrame(df)) if MAIN_TF in MULTI_TF else None
            # simpler: majority of (15m + provided multi_tf) => include 15m trend via EMA
            # compute 15m trend:
            try:
                trend15 = "UP" if aligned_up else ("DOWN" if aligned_down else "NEUTRAL")
            except Exception:
                trend15 = "NEUTRAL"
            votes_all = [trend15] + votes
            if votes_all.count(need) >= math.ceil(len(votes_all)/2):
                return True
            # or (trend15 == need and any higher tf == need)
            if trend15 == need and any(v == need for v in votes):
                return True
            return False

        multi_confirm = False
        if triggered and direction:
            multi_confirm = multi_tf_confirm(direction)

        # prepare tpsl if suggestion exists
        tpsl = compute_tp_sl(last_price, direction, atr_v) if direction else None

        # prepare chart file
        ts = ts_now()
        chart_p = os.path.join(OUT_DIR, f"{symbol}_{ts}.png")
        try:
            plot_signal_chart(symbol, df, pd.Series(step.values, index=df.index), {"squares":[], "top_div":top_div, "bottom_div":bottom_div}, tpsl or {}, chart_p)
        except Exception:
            chart_p = None

        return {
            "symbol": symbol,
            "pair": pair,
            "price": last_price,
            "prev_step": prev_step,
            "last_step": last_step,
            "cross_to_overb": cross_to_overb,
            "cross_to_overs": cross_to_overs,
            "triggered": triggered,
            "direction": direction,
            "multi_confirm": multi_confirm,
            "ai_label": ai_label, "ai_score": ai_score,
            "ema21": ema21, "ema50": ema50, "ema100": ema100, "ema200": ema200,
            "rsi": float(rsi.iat[-1]) if not math.isnan(rsi.iat[-1]) else None,
            "tpsl": tpsl,
            "atr": atr_v,
            "vol_ok": vol_ok,
            "res": res_levels, "sup": sup_levels,
            "fvg": fvg,
            "chart": chart_p,
            "top_div": top_div, "bottom_div": bottom_div,
            "step_series": pd.Series(step.values, index=df.index)
        }

    except Exception as e:
        print(f"[{symbol}] analyze error:", e)
        return None

# -------------------------
# DB helpers
# -------------------------
def db_insert_trade_open(trade_id, trade):
    try:
        db_cur.execute("INSERT OR REPLACE INTO trades (id, symbol, direction, entry, created_at) VALUES (?, ?, ?, ?, ?)",
                       (trade_id, trade['symbol'], trade['direction'], trade['entry'], trade['created_at']))
        db_conn.commit()
    except Exception as e:
        print("db_insert_trade_open error:", e)

def db_close_trade(trade_id, exit_price, result, tp_level=None):
    try:
        db_cur.execute("UPDATE trades SET exit=?, result=?, tp_level=?, closed_at=? WHERE id=?",
                       (exit_price, result, tp_level, utc8_str(), trade_id))
        db_conn.commit()
        # update stats
        db_cur.execute("SELECT symbol FROM trades WHERE id=?", (trade_id,))
        row = db_cur.fetchone()
        if row:
            sym = row[0]
            db_cur.execute("INSERT OR IGNORE INTO stats (symbol, total, wins, losses) VALUES (?, 0, 0, 0)", (sym,))
            if result == "WIN":
                db_cur.execute("UPDATE stats SET total=total+1, wins=wins+1 WHERE symbol=?", (sym,))
            else:
                db_cur.execute("UPDATE stats SET total=total+1, losses=losses+1 WHERE symbol=?", (sym,))
            db_conn.commit()
    except Exception as e:
        print("db_close_trade error:", e)

def db_get_top_winrate(n=10):
    try:
        db_cur.execute("SELECT symbol, total, wins, losses, (1.0*wins/total) as winrate FROM stats WHERE total>0 ORDER BY winrate DESC LIMIT ?", (n,))
        return db_cur.fetchall()
    except Exception:
        return []

# -------------------------
# Signal state memory (avoid duplicates) - persisted to file
# -------------------------
STATE_FILE = "signal_state.json"
def load_signal_state():
    try:
        if os.path.exists(STATE_FILE):
            return json.load(open(STATE_FILE, 'r', encoding='utf8'))
    except Exception:
        pass
    return {}

def save_signal_state(state):
    try:
        json.dump(state, open(STATE_FILE, 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    except Exception as e:
        print("save_signal_state error:", e)

signal_state = load_signal_state()  # mapping symbol -> {state: "NORMAL"/"OVERBOUGHT"/"OVERSOLD", last_trigger_ts:..., last_price:...}

# -------------------------
# Manage open trades (in-memory)
# -------------------------
OPEN_TRADES = {}  # trade_id -> trade dict

def create_trade_from_analysis(analysis):
    tid = f"{analysis['symbol']}_{ts_now()}"
    tps = analysis.get('tpsl') or {}
    trade = {
        "id": tid,
        "symbol": analysis['symbol'],
        "pair": analysis['pair'],
        "direction": analysis['direction'],
        "entry": analysis['price'],
        "tp1": tps.get('tp1'),
        "tp2": tps.get('tp2'),
        "tp3": tps.get('tp3'),
        "sl": tps.get('sl'),
        "atr": analysis.get('atr'),
        "tp1_hit": False, "tp2_hit": False, "tp3_hit": False,
        "created_at": utc8_str()
    }
    return tid, trade

def manage_open_trades(exchange):
    to_remove = []
    for tid, trade in list(OPEN_TRADES.items()):
        pair = trade.get("pair")
        try:
            ticker = exchange.fetch_ticker(pair)
            last = ticker.get("last") or ticker.get("close")
            if last is None:
                continue
            last = float(last)
        except Exception as e:
            print("[manage_open_trades] fetch_ticker error:", e)
            continue

        moved = update_trailing_sl(trade, last)
        if moved:
            send_tg_text(f"🔁 移动止损：{trade['symbol']} 新SL={trade['sl']} 价格={last} (UTC+8 {utc8_str()})")

        # close checks
        dirc = trade.get("direction")
        if dirc == "LONG":
            if trade.get("tp3") and last >= trade["tp3"]:
                db_close_trade(trade['id'], last, "WIN", tp_level=3)
                send_tg_text(f"✅ TP3 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue
            if trade.get("tp2") and last >= trade["tp2"]:
                db_close_trade(trade['id'], last, "WIN", tp_level=2)
                send_tg_text(f"✅ TP2 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue
            if trade.get("tp1") and last >= trade["tp1"]:
                if not trade.get("tp1_hit"):
                    trade["tp1_hit"] = True; trade["sl"] = trade["entry"]
                    send_tg_text(f"🔔 TP1 触及，止损移至入场价：{trade['symbol']}")
                continue
            if trade.get("sl") is not None and last <= trade["sl"]:
                db_close_trade(trade['id'], last, "LOSS", tp_level=None)
                send_tg_text(f"❌ SL 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue
        elif dirc == "SHORT":
            if trade.get("tp3") and last <= trade["tp3"]:
                db_close_trade(trade['id'], last, "WIN", tp_level=3)
                send_tg_text(f"✅ TP3 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue
            if trade.get("tp2") and last <= trade["tp2"]:
                db_close_trade(trade['id'], last, "WIN", tp_level=2)
                send_tg_text(f"✅ TP2 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue
            if trade.get("tp1") and last <= trade["tp1"]:
                if not trade.get("tp1_hit"):
                    trade["tp1_hit"] = True; trade["sl"] = trade["entry"]
                    send_tg_text(f"🔔 TP1 触及(short)，止损移至入场价：{trade['symbol']}")
                continue
            if trade.get("sl") is not None and last >= trade["sl"]:
                db_close_trade(trade['id'], last, "LOSS", tp_level=None)
                send_tg_text(f"❌ SL 命中 {trade['symbol']}: Entry {trade['entry']} Exit {last}")
                to_remove.append(tid); continue

        OPEN_TRADES[tid] = trade

    for tid in to_remove:
        if tid in OPEN_TRADES:
            del OPEN_TRADES[tid]

# -------------------------
# Build message text
# -------------------------
def build_signal_text(analysis):
    sym = analysis['symbol']; price = analysis['price']; dirc = analysis.get('direction')
    tpsl = analysis.get('tpsl') or {}; ai = f"{analysis.get('ai_label')} ({analysis.get('ai_score')})"
    div = "顶部背离" if analysis.get('top_div') else ("底部背离" if analysis.get('bottom_div') else "无")
    res = analysis.get('res', []); sup = analysis.get('sup', [])
    txt = (f"🔔 新信号 — {sym}/{SYMBOL_BASE}\n"
           f"价格：{price}\n"
           f"建议：{ '做多' if dirc=='LONG' else ('做空' if dirc=='SHORT' else '无') }\n"
           f"TP1/TP2/TP3：{tpsl.get('tp1')} / {tpsl.get('tp2')} / {tpsl.get('tp3')}\n"
           f"初始止损：{tpsl.get('sl')}\n"
           f"ATR：{analysis.get('atr'):.8f}\n"
           f"AI：{ai}\n"
           f"RSI：{analysis.get('rsi')} 背离：{div}\n"
           f"阻力：{res}\n支撑：{sup}\n"
           f"时间 (UTC+8)：{utc8_str()}")
    return txt

# -------------------------
# Wait until next aligned 15m in UTC+8
# -------------------------
def wait_until_next_15m_utc8():
    now = utc_now() + timedelta(hours=8)
    minute = now.minute
    next_q = ((minute // 15) + 1) * 15
    if next_q >= 60:
        target = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    else:
        target = now.replace(minute=next_q, second=0, microsecond=0)
    wait = (target - now).total_seconds()
    if wait < 1:
        wait = 1
    print(f"[sleep] Next run at (UTC+8): {target.strftime('%Y-%m-%d %H:%M:%S')}  sleep {wait:.1f}s")
    time.sleep(wait)

# -------------------------
# Main runner
# -------------------------
def main():
    """
    主函数：监控币安USDT交易对的RSI信号（使用代理）
    """
    exchange = ccxt.binance({
        "enableRateLimit": True,
        "proxies": PROXIES
    })
    # startup: fetch top N and run full scan immediately
    try:
        symbols = fetch_top_n_binance(TOP_N, exchange=exchange)
    except Exception as e:
        print("fetch_top_n_binance failed:", e); return

    print(f"Monitoring {len(symbols)} symbols (Top {TOP_N}). Start (UTC+8): {utc8_str()}")
    if TG_API_BASE:
        send_tg_text(f"🚀 Bot 启动，监控 Top {len(symbols)} USDT（{MAIN_TF}） 时间(UTC+8): {utc8_str()}")

    # initial full scan on startup
    for symbol in symbols:
        try:
            analysis = analyze_symbol(exchange, symbol)
            if not analysis:
                time.sleep(SMALL_SLEEP)
                continue
            # only send if crosses & multi_confirm (scheme B)
            if analysis.get('triggered') and analysis.get('multi_confirm'):
                # only send if previous state isn't same
                prev = signal_state.get(symbol, {}).get('state', 'NORMAL')
                # mapping triggered -> state
                new_state = "OVERBOUGHT" if analysis.get('direction') == "SHORT" else ("OVERSOLD" if analysis.get('direction') == "LONG" else 'NORMAL')
                if prev != new_state:
                    # create trade + persist + notify
                    tid, trade = create_trade_from_analysis(analysis)
                    OPEN_TRADES[tid] = trade
                    db_insert_trade_open(tid, trade)
                    text = build_signal_text(analysis)
                    send_tg_text(text)
                    if SEND_PHOTO and analysis.get('chart'):
                        send_tg_photo(analysis.get('chart'), caption=f"{symbol} 信号图 ({utc8_str()})")
                    # update state
                    signal_state[symbol] = {"state": new_state, "last_trigger_ts": utc8_str(), "last_price": analysis.get('price')}
                    save_signal_state(signal_state)
                    time.sleep(SMALL_SLEEP)
            time.sleep(SMALL_SLEEP)
        except Exception as e:
            print("[startup scan] error for", symbol, e)
            time.sleep(SMALL_SLEEP)

    # main loop aligned to 15m UTC+8
    while True:
        cycle_start = time.time()
        print("[cycle] start", utc8_str())
        for symbol in symbols:
            try:
                # analyze
                analysis = analyze_symbol(exchange, symbol)
                if not analysis:
                    time.sleep(SMALL_SLEEP); continue

                # apply Scheme B:
                # - must cross from inside to outside (cross flags computed)
                # - must have multi_confirm True
                # - must have previous state different (i.e., only on change)
                prev_state = signal_state.get(symbol, {}).get('state', 'NORMAL')
                new_state = prev_state
                if analysis.get('cross_to_overb') and analysis.get('multi_confirm'):
                    new_state = "OVERBOUGHT"
                elif analysis.get('cross_to_overs') and analysis.get('multi_confirm'):
                    new_state = "OVERSOLD"
                else:
                    # if step returned to neutral zone, set to NORMAL
                    lp = analysis.get('last_step')
                    if lp is not None and -THRESH < lp < THRESH:
                        new_state = "NORMAL"

                # if state changed to a signal state, send once
                if new_state in ("OVERBOUGHT", "OVERSOLD") and prev_state != new_state:
                    # create trade and persist
                    tid, trade = create_trade_from_analysis(analysis)
                    OPEN_TRADES[tid] = trade
                    db_insert_trade_open(tid, trade)
                    txt = build_signal_text(analysis)
                    send_tg_text(txt)
                    if SEND_PHOTO and analysis.get('chart'):
                        send_tg_photo(analysis.get('chart'), caption=f"{symbol} 信号图 ({utc8_str()})")
                    # update state
                    signal_state[symbol] = {"state": new_state, "last_trigger_ts": utc8_str(), "last_price": analysis.get('price')}
                    save_signal_state(signal_state)
                # if returned to normal, update state
                elif new_state == "NORMAL" and prev_state != "NORMAL":
                    signal_state[symbol] = {"state": "NORMAL", "last_trigger_ts": None, "last_price": None}
                    save_signal_state(signal_state)

                # cooldown is enforced implicitly by state transitions; but also avoid rapid re-evaluation
                time.sleep(SMALL_SLEEP)
            except Exception as e:
                print("[main loop] error for", symbol, e)
                time.sleep(SMALL_SLEEP)

        # manage open trades (trailing + TP/SL)
        manage_open_trades(exchange)

        # optional: report top winrates occasionally (not every cycle)
        # to reduce noise, report once every N cycles - here we skip by default

        # wait until next aligned 15m tick
        wait_until_next_15m_utc8()

# -------------------------
# Entry
# -------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Fatal error:", e)
        time.sleep(10)
        os.execv(sys.executable, [sys.executable] + sys.argv)
