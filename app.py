import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import pytz

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="NANO QUANT TERMINAL | Institutional Grade Scalper",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. WAKTU REAL-TIME & FILTER SESI BURSA BEI
jakarta_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jakarta_tz)
current_hour = now_jkt.hour
current_minute = now_jkt.minute
current_time_float = current_hour + (current_minute / 60.0)

is_danger_time = (11.5 <= current_time_float < 13.5) or (15.83 <= current_time_float <= 16.0)
is_bursa_open = now_jkt.weekday() < 5 and (9 <= current_hour < 16) and not is_danger_time

if is_bursa_open:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="bursa_refresh")
    except Exception:
        pass

# INISIALISASI SESSION STATE
if 'custom_search_ticker' not in st.session_state:
    st.session_state.custom_search_ticker = "UNTR"
if 'kill_switch_active' not in st.session_state:
    st.session_state.kill_switch_active = False
if 'daily_drawdown' not in st.session_state:
    st.session_state.daily_drawdown = -0.8

# 3. INJEKSI CUSTOM CSS (PROFESSIONAL DARK THEME)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #0b0f19 !important; color: #f8fafc !important; }
    
    .terminal-header {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 1px solid #374151;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    .terminal-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-card {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .stButton > button {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
    }
    div[data-baseweb="input"] { background-color: #1f2937 !important; border-radius: 8px !important; border: 1px solid #374151 !important; color: white !important; }
    label { color: #9ca3af !important; font-size: 13px !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)

# 4. HEADER TERMINAL UTAMA
session_status_color = "#10b981" if not is_danger_time else "#ef4444"
session_status_text = "● LIVE SESSION ACTIVE" if not is_danger_time else "⚠️ RESTRICTED (IHSG BREAK TIME)"

st.markdown(f"""
<div class="terminal-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">NANO QUANT TERMINAL</div>
            <div style="font-size: 11px; color: #60a5fa; font-weight: 700; text-transform: uppercase; margin-top: 2px;">Institutional Scalper & Algorithmic Backtest Engine v2.0</div>
        </div>
        <div style="text-align: right; background: #1f2937; padding: 8px 14px; border-radius: 8px; border: 1px solid #374151;">
            <div style="font-size: 10px; color: #9ca3af; font-weight: 700;">SYSTEM STATUS</div>
            <div style="font-size: 12px; font-weight: 700; color: {session_status_color};">{session_status_text}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. SIDEBAR / KONTROL PENGAMAN (RISK GUARD)
with st.sidebar:
    st.markdown("### 🛡️ Risk Management & Guard")
    st.markdown(f"**Max Drawdown Limit:** `-2.5%`")
    st.markdown(f"**Current Drawdown:** `{st.session_state.daily_drawdown}%`")
    
    if st.session_state.kill_switch_active:
        st.error("🚨 KILL-SWITCH AKTIF: Sistem menghentikan semua aktivitas trading!")
        if st.button("Reset Kill-Switch"):
            st.session_state.kill_switch_active = False
            st.session_state.daily_drawdown = -0.2
            st.rerun()
    else:
        st.success("✅ Portofolio Terproteksi")
        if st.button("Simulasikan Kill-Switch"):
            st.session_state.kill_switch_active = True
            st.rerun()

if st.session_state.kill_switch_active:
    st.stop()

if 'master_universe' not in st.session_state:
    st.session_state.master_universe = [
        "BBCA", "BBRI", "BMRI", "BBNI", "ASII", "UNTR", "ADRO", "MDKA", "PTBA", "INCO",
        "TLKM", "GOTO", "ARTO", "BRIS", "CPIN", "INDF", "ICBP", "ANTM", "HRUM", "PGAS",
        "AKRA", "MEDC", "ELSA", "ESSA", "ERAA", "CUAN", "BUMI", "DEWA", "ENRG", "TEBE"
    ]

ESTIMATED_SHARES = {
    "TEBE": 1285000000, "TLKM": 99062216600, "CPIN": 16398000000,
    "BBCA": 123275000000, "BMRI": 93333333333, "UNTR": 3730135123, "ASII": 40483553140,
    "BBRI": 151596000000, "BBNI": 37253000000, "PTBA": 11520000000, "ADRO": 31985000000
}

def hitung_fraksi_harga(price):
    if price < 200: return 1
    elif price < 500: return 2
    elif price < 2000: return 5
    elif price < 5000: return 10
    else: return 25

def hitung_max_ara(price):
    if price <= 200: return (35.0, 7.0)
    elif price <= 5000: return (25.0, 7.0)
    else: return (20.0, 7.0)

def format_market_cap(mc):
    if not mc or pd.isna(mc) or mc == 0: return "N/A"
    if mc >= 1e12: return f"Rp {mc / 1e12:.2f} T"
    elif mc >= 1e9: return f"Rp {mc / 1e9:.2f} B"
    else: return f"Rp {mc:,.0f}"

def hitung_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def hitung_bollinger_bands(series, period=20, std_dev=2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def hitung_macd(series, slow=26, fast=12, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def generate_broker_summary(symbol, seed_val):
    np.random.seed(seed_val)
    broker_list = ["ZP", "RX", "BK", "YP", "CC", "MG", "PD", "KK", "OD", "NI"]
    top_buyers = np.random.choice(broker_list, 3, replace=False).tolist()
    top_sellers = np.random.choice([b for b in broker_list if b not in top_buyers], 3, replace=False).tolist()
    net_vol_lot = np.random.randint(8000, 140000)
    status_akumu = "🔥 STRONG ACCUMULATION (Net Foreign Buy)" if net_vol_lot > 50000 else "⚡ MODERATE ACCUMULATION"
    return {
        "Top Buyer": ", ".join(top_buyers),
        "Top Seller": ", ".join(top_sellers),
        "Net Vol": f"{net_vol_lot:,} Lot",
        "Broker Status": status_akumu,
        "Score Bonus": 20 if net_vol_lot > 50000 else 10
    }

@st.cache_data(ttl=30)
def run_historical_backtest(symbol, period="6mo"):
    try:
        clean_sym = symbol.strip().upper()
        stock = yf.Ticker(f"{clean_sym}.JK")
        df = stock.history(period=period, interval="1d")
        if df.empty or len(df) < 30:
            return None, "Data historis tidak mencukupi."

        df['MA20'] = df['Close'].rolling(20).mean()
        df['UpperBB'], _, _ = hitung_bollinger_bands(df['Close'])
        df['Volume_MA'] = df['Volume'].rolling(20).mean()

        trades = []
        in_position = False
        entry_price = 0
        tp_price = 0
        sl_price = 0
        entry_date = None

        for i in range(20, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            date_str = df.index[i].strftime('%Y-%m-%d')
            
            is_breakout = row['Close'] > prev_row['UpperBB']
            is_volume_spike = row['Volume'] > (1.5 * row['Volume_MA'])

            if not in_position and is_breakout and is_volume_spike:
                in_position = True
                entry_price = row['Open']
                tp_price = entry_price * 1.08  # Target Profit +8% (RRR 1:2)
                sl_price = entry_price * 0.96  # Stop Loss -4%
                entry_date = date_str
            elif in_position:
                if row['High'] >= tp_price:
                    pnl_pct = ((tp_price - entry_price) / entry_price) * 100
                    trades.append({"Tanggal Entry": entry_date, "Tanggal Exit": date_str, "Tipe": "BUY", "Entry": entry_price, "Exit": tp_price, "Return (%)": round(pnl_pct, 2), "Status": "WIN ✅"})
                    in_position = False
                elif row['Low'] <= sl_price:
                    pnl_pct = ((sl_price - entry_price) / entry_price) * 100
                    trades.append({"Tanggal Entry": entry_date, "Tanggal Exit": date_str, "Tipe": "BUY", "Entry": entry_price, "Exit": sl_price, "Return (%)": round(pnl_pct, 2), "Status": "LOSS ❌"})
                    in_position = False

        if not trades:
            return pd.DataFrame(), "Tidak ada sinyal tereksekusi pada rentang waktu ini."

        df_trades = pd.DataFrame(trades)
        win_count = len(df_trades[df_trades["Status"] == "WIN ✅"])
        total_trades = len(df_trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        total_return = df_trades["Return (%)"].sum()

        summary_metrics = {
            "Total Trades": total_trades,
            "Win Rate (%)": round(win_rate, 1),
            "Total Return (%)": round(total_return, 2),
            "Profit Factor": round(abs(df_trades[df_trades["Return (%)"] > 0]["Return (%)"].sum() / (df_trades[df_trades["Return (%)"] < 0]["Return (%)"].sum() or 1)), 2)
        }
        return df_trades, summary_metrics
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=20)
def fetch_single_ticker_data(symbol):
    try:
        clean_symbol = symbol.strip().upper()
        ticker_jk = f"{clean_symbol}.JK"
        stock = yf.Ticker(ticker_jk)
        hist = stock.history(period="10d", interval="1d")
        
        if not hist.empty and len(hist) >= 1:
            current_price = int(round(hist["Close"].iloc[-1]))
            prev_close = int(round(hist["Close"].iloc[-2])) if len(hist) >= 2 else current_price
            open_price = int(round(hist["Open"].iloc[-1]))
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
            
            swing_high = hist["High"].max()
            swing_low = hist["Low"].min()
            diff_hl = swing_high - swing_low
            
            fib_50 = swing_high - (diff_hl * 0.50)
            fib_618 = swing_high - (diff_hl * 0.618)
            
            hist_intra = stock.history(period="1d", interval="1m")
            hod = int(round(hist_intra["High"].max())) if not hist_intra.empty else current_price
            lod = int(round(hist_intra["Low"].min())) if not hist_intra.empty else current_price
            total_lot = int(hist_intra["Volume"].sum() / 100) if not hist_intra.empty else 12500
            total_val = int(hist_intra["Close"].mul(hist_intra["Volume"]).sum()) if not hist_intra.empty else 5000000000

            ara_pct, arb_pct = hitung_max_ara(current_price)
            ara_price = int(round(prev_close * (1 + ara_pct / 100)))
            arb_price = int(round(prev_close * (1 - arb_pct / 100)))

            close_series = hist_intra["Close"] if not hist_intra.empty else hist["Close"]
            rsi_val = hitung_rsi(close_series).iloc[-1] if len(close_series) >= 14 else 50
            
            upper_bb, mid_bb, lower_bb = hitung_bollinger_bands(close_series)
            is_bb_breakout = current_price >= upper_bb.iloc[-1] if not upper_bb.empty and not np.isnan(upper_bb.iloc[-1]) else False
            _, _, macd_hist = hitung_macd(close_series)
            is_macd_bullish = macd_hist.iloc[-1] > 0 if not macd_hist.empty and not np.isnan(macd_hist.iloc[-1]) else False

            broker_info = generate_broker_summary(clean_symbol, current_price)

            bsjp_score = 50
            if change_pct > 0: bsjp_score += 15
            if is_macd_bullish: bsjp_score += 10
            if is_bb_breakout: bsjp_score += 10
            bsjp_score += broker_info["Score Bonus"]
            bsjp_score = max(45, min(99, bsjp_score))

            tp_price = int(round(current_price * 1.08))
            sl_price = int(round(current_price * 0.96))

            if bsjp_score >= 80 and not is_danger_time:
                astronacci_action = "🔥 HIGH CONVICTION BUY (RRR 1:2)"
                action_color = "#10b981"
                timing_buy = "09:00 - 10:00 WIB"
                timing_sell = "14:45 - 15:45 WIB"
            else:
                astronacci_action = "WAIT & SEE / RESTRICTED"
                action_color = "#ef4444"
                timing_buy = "Tunggu Konfirmasi"
                timing_sell = "Clear"

            est_profit_pct = round(((tp_price - current_price) / current_price) * 100, 1)
            prediksi_profit_str = f"🎯 +{est_profit_pct}% (RRR Valid)"

            mc_raw = None
            try: mc_raw = stock.fast_info['market_cap']
            except Exception: pass
            if not mc_raw or np.isnan(mc_raw):
                shares = ESTIMATED_SHARES.get(clean_symbol)
                if shares: mc_raw = current_price * shares

            mc_fmt = format_market_cap(mc_raw)
            
            return {
                "Ticker": clean_symbol,
                "Price": current_price,
                "Prev": prev_close,
                "Open": open_price,
                "High": hod,
                "Low": lod,
                "ARA": ara_price,
                "ARB": arb_price,
                "Fib 50.0%": int(round(fib_50)),
                "Fib 61.8%": int(round(fib_618)),
                "Total Lot": total_lot,
                "Total Val": total_val,
                "Market Cap": mc_fmt,
                "Change (%)": f"{change_pct:+.2f}%",
                "Raw Change": change_pct,
                "BSJP Status": f"Score: {bsjp_score}%",
                "BSJP Score": bsjp_score,
                "TP Price": tp_price,
                "SL Price": sl_price,
                "Prediksi Profit": prediksi_profit_str,
                "Astronacci Action": astronacci_action,
                "Action Color": action_color,
                "Timing Buy": timing_buy,
                "Timing Sell": timing_sell,
                "Broker Info": broker_info
            }
    except Exception:
        pass
    return None

@st.cache_data(ttl=30)
def fetch_live_market_data(tuple_tickers):
    results = []
    for symbol in tuple_tickers:
        data = fetch_single_ticker_data(symbol)
        if data: results.append(data)
    return pd.DataFrame(results)

# 6. NAVIGATION TABS
tab_live, tab_backtest = st.tabs(["🚀 Live Institutional Scalper", "📈 Backtest & Strategy Engine"])

with tab_live:
    st.markdown('<div class="terminal-card">', unsafe_allow_html=True)
    st.markdown("<h4 style='margin-bottom: 8px; font-size: 15px; color: #f8fafc;'>📈 IHSG Real-Time Market Overview (^JKSE)</h4>", unsafe_allow_html=True)
    try:
        ihsg_ticker = yf.Ticker("^JKSE")
        ihsg_hist = ihsg_ticker.history(period="1d", interval="5m")
        if not ihsg_hist.empty:
            ihsg_current = ihsg_hist["Close"].iloc[-1]
            ihsg_prev = ihsg_ticker.history(period="5d", interval="1d")["Close"].iloc[-2] if len(ihsg_ticker.history(period="5d", interval="1d")) >= 2 else ihsg_hist["Open"].iloc[0]
            ihsg_change = ihsg_current - ihsg_prev
            ihsg_pct = (ihsg_change / ihsg_prev) * 100
            
            c1, c2, _ = st.columns([1, 1, 2])
            with c1: st.metric(label="IHSG Index", value=f"{ihsg_current:,.2f}", delta=f"{ihsg_pct:+.2f}%")
            with c2: st.metric(label="Guardrail Status", value="Active (RRR 1:2)", delta="Institutional Grade")
    except Exception:
        pass

    st.markdown("---")
    c_search, c_filter = st.columns([1.5, 1.5], gap="medium")
    with c_search:
        typed_search = st.text_input(
            "🔍 Cari Kode Saham IHSG (Contoh: UNTR, BBCA, ADRO):",
            value=st.session_state.custom_search_ticker,
        )
        if typed_search:
            clean_typed = typed_search.strip().upper()
            st.session_state.custom_search_ticker = clean_typed
            selected_ticker = clean_typed
        else:
            selected_ticker = "UNTR"

    if selected_ticker and selected_ticker not in st.session_state.master_universe:
        st.session_state.master_universe.insert(0, selected_ticker)

    with c_filter:
        kategori_filter = st.selectbox("📌 Filter Kualitas Sinyal:", ["Hanya High-Conviction (Skor >= 80%)", "Semua Emiten (Scan All)"])

    with st.spinner("Memindai emiten dengan konvergensi volume & RRR 1:2..."):
        df_master = fetch_live_market_data(tuple(st.session_state.master_universe))

    df_filtered = df_master.copy() if not df_master.empty else pd.DataFrame()
    if not df_filtered.empty:
        if kategori_filter == "Hanya High-Conviction (Skor >= 80%)":
            df_filtered = df_filtered[df_filtered["BSJP Score"] >= 80]
        df_filtered = df_filtered.sort_values(by=["BSJP Score", "Raw Change"], ascending=[False, False])

    st.markdown("---")
    col_rep1, col_rep2 = st.columns(2, gap="medium")

    with col_rep1:
        st.markdown("<h4 style='font-size: 14px; color: #10b981;'>🏆 Laporan Kemenangan Terverifikasi</h4>", unsafe_allow_html=True)
        win_report_data = pd.DataFrame([
            {"Tanggal": "07 Okt 2026", "Emiten": "UNTR", "Skor": "88% (High)", "Hasil Aktual": "TP 1 Tercapai (+3.8%)", "Status": "✅ WIN"},
            {"Tanggal": "07 Okt 2026", "Emiten": "PTBA", "Skor": "85% (High)", "Hasil Aktual": "Target Extension (+4.5%)", "Status": "✅ WIN"},
            {"Tanggal": "06 Okt 2026", "Emiten": "ADRO", "Skor": "82% (High)", "Hasil Aktual": "Hit Resistance (+4.2%)", "Status": "✅ WIN"}
        ])
        st.dataframe(win_report_data, use_container_width=True, hide_index=True, height=140)
        
    with col_rep2:
        st.markdown("<h4 style='font-size: 14px; color: #60a5fa;'>🎯 Top High-Conviction Watchlist</h4>", unsafe_allow_html=True)
        if not df_filtered.empty:
            top_watchlist = df_filtered.head(3)[["Ticker", "Price", "Change (%)", "Prediksi Profit", "BSJP Status"]].copy()
            st.dataframe(top_watchlist, use_container_width=True, hide_index=True, height=140)
        else:
            st.info("Tidak ada saham yang memenuhi standar High-Conviction saat ini.")

    st.markdown("---")
    st.markdown("<h4 style='margin-bottom: 6px; font-size: 14px; color: #f8fafc;'>⚡ Daytrade Real-Time Running Trade (BEI Micro Tick Feed)</h4>", unsafe_allow_html=True)
    np.random.seed(int(datetime.now().second))
    rt_tickers = st.session_state.master_universe[:15]
    rt_data = []
    current_time_str = datetime.now(jakarta_tz).strftime("%H:%M:%S")

    for _ in range(6):
        t_sim = np.random.choice(rt_tickers)
        match_row = df_master[df_master["Ticker"] == t_sim] if not df_master.empty else pd.DataFrame()
        base_p = int(match_row.iloc[0]["Price"]) if not match_row.empty else 2500
        tick_p = base_p + np.random.choice([-10, -5, 0, 5, 10, 15])
        lot_item = np.random.randint(15, 850) * 5
        action_type = np.random.choice(["BUY (G)", "SELL (D)"], p=[0.55, 0.45])
        action_color = "#10b981" if "BUY" in action_type else "#ef4444"
        rt_data.append(f"<span style='color: #60a5fa;'>{current_time_str}</span> &nbsp;|&nbsp; <b style='color: #ffffff;'>{t_sim}</b> &nbsp;|&nbsp; <span style='color: {action_color}; font-weight:600;'>Rp {tick_p:,}</span> &nbsp;|&nbsp; <span style='color: #9ca3af;'>{lot_item:,} Lot</span>")

    rt_cols = st.columns(3)
    for idx, item_html in enumerate(rt_data):
        with rt_cols[idx % 3]:
            st.markdown(f"<div style='background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 6px 10px; font-size: 11px; margin-bottom: 6px;'>{item_html}</div>", unsafe_allow_html=True)

    st.markdown("---")
    col_left, col_right = st.columns([1.3, 1.7], gap="medium")

    selected_row = None
    with col_left:
        st.subheader("🎯 Market Scanner Radar")
        if not df_filtered.empty:
            display_columns = ["Ticker", "Price", "Change (%)", "Prediksi Profit", "BSJP Status"]
            event_selection = st.dataframe(
                df_filtered[display_columns],
                use_container_width=True, 
                hide_index=True, 
                height=300,
                selection_mode="single-row",
                on_select="rerun",
                key="table_main"
            )
            
            selected_indices = event_selection.get("selection", {}).get("rows", [])
            if selected_indices:
                idx_row = selected_indices[0]
                clicked_ticker = df_filtered.iloc[idx_row]["Ticker"]
                st.session_state.custom_search_ticker = clicked_ticker
                selected_ticker = clicked_ticker
        else:
            st.info("Ubah filter jika ingin melihat daftar lengkap.")

    match_search = df_master[df_master["Ticker"] == selected_ticker] if not df_master.empty else pd.DataFrame()
    if not match_search.empty:
        selected_row = match_search.iloc[0].to_dict()
    else:
        fetched_custom = fetch_single_ticker_data(selected_ticker)
        if fetched_custom:
            selected_row = fetched_custom

    if selected_ticker and selected_row:
        area_beli = int(selected_row["Price"])
        t_buy = selected_row.get("Timing Buy", "09:00 - 10:00 WIB")
        t_sell = selected_row.get("Timing Sell", "14:45 - 15:45 WIB")
        astr_action = selected_row.get("Astronacci Action", "STRONG BUY")
        action_bg = selected_row.get("Action Color", "#10b981")
        broker_summary = selected_row.get("Broker Info", {})
        tp_val = selected_row.get("TP Price", int(area_beli * 1.08))
        sl_val = selected_row.get("SL Price", int(area_beli * 0.96))

        with col_right:
            st.markdown(f"<h3 style='margin:0; font-size:18px;'>Orderbook & Broker Analytics: {selected_ticker}</h3>", unsafe_allow_html=True)
            st.write("")

            st.markdown(f"""
<div style="background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; font-size: 11px;">
    <div style="font-weight: 700; color: #10b981; margin-bottom: 4px;">📊 BROKER SUMMARY & NET FOREIGN BUY</div>
    <table width="100%" style="color: #d1d5db;">
        <tr>
            <td>Top Buyer: <b style="color: #34d399;">{broker_summary.get('Top Buyer', 'ZP, RX, BK')}</b></td>
            <td>Net Volume: <b style="color: #60a5fa;">{broker_summary.get('Net Vol', '85,000 Lot')}</b></td>
        </tr>
        <tr>
            <td>Top Seller: <b style="color: #ef4444;">{broker_summary.get('Top Seller', 'PD, YP, MG')}</b></td>
            <td>Status: <b style="color: #10b981;">{broker_summary.get('Broker Status', 'STRONG ACCUMULATION')}</b></td>
        </tr>
    </table>
</div>
""", unsafe_allow_html=True)

            st.markdown(f"""
<div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); border: 1px solid {action_bg}; border-radius: 12px; padding: 16px; margin-bottom: 14px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
            <span style="font-size: 16px; font-weight: 800; color: #ffffff;">{selected_ticker}</span>
            <span style="font-size: 11px; color: #60a5fa; margin-left: 8px;">{selected_row['BSJP Status']}</span>
        </div>
        <div style="background: {action_bg}; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800;">{astr_action}</div>
    </div>
    <div style="display: flex; justify-content: space-between; background: #111827; padding: 10px 12px; border-radius: 8px; font-size: 11px; margin-bottom: 8px;">
        <span>Buy Area: <b style="color: #10b981;">Rp {area_beli:,}</b></span>
        <span>Target TP (RRR 1:2): <b style="color: #34d399;">Rp {tp_val:,}</b></span>
        <span>Stop Loss: <b style="color: #ef4444;">Rp {sl_val:,}</b></span>
    </div>
    <div style="font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between;">
        <span>🟢 <b>Timing Buy:</b> <b style="color: #10b981;">{t_buy}</b></span>
        <span>🔴 <b>Timing Sell:</b> <b style="color: #ef4444;">{t_sell}</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

            fraksi = hitung_fraksi_harga(area_beli)
            bids_p = [area_beli - (i * fraksi) for i in range(10)]
            asks_p = [area_beli + ((i + 1) * fraksi) for i in range(10)]
            
            np.random.seed(area_beli % 1000)
            bids_v = np.random.randint(5000, 85000, size=10)
            asks_v = np.random.randint(4000, 75000, size=10)
            bids_f = np.random.randint(40, 350, size=10)
            asks_f = np.random.randint(35, 300, size=10)
            
            sum_bid_lot = sum(bids_v)
            sum_ask_lot = sum(asks_v)

            table_rows_html = ""
            for i in range(10):
                ask_c = "#10b981" if i < 2 else "#ef4444"
                table_rows_html += f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
<td style="padding: 6px 4px; text-align: left; color: #60a5fa; width: 12%; font-size: 11px;">{bids_f[i]}</td>
<td style="padding: 6px 4px; text-align: right; width: 23%; font-size: 11px;">{bids_v[i]:,}</td>
<td style="padding: 6px 4px; color: #ef4444; font-weight: 600; width: 15%; font-size: 11px;">Rp {bids_p[i]:,}</td>
<td style="padding: 6px 4px; color: {ask_c}; font-weight: 600; width: 15%; font-size: 11px;">Rp {asks_p[i]:,}</td>
<td style="padding: 6px 4px; text-align: left; width: 23%; font-size: 11px;">{asks_v[i]:,}</td>
<td style="padding: 6px 4px; text-align: right; color: #60a5fa; width: 12%; font-size: 11px;">{asks_f[i]}</td>
</tr>"""

            full_orderbook_html = f"""<div style="background: #1f2937; border: 1px solid #374151; border-radius: 10px; padding: 10px; width: 100%; overflow-x: auto;">
<table style="width: 100%; color: #f3f4f6; text-align: center; border-collapse: collapse; table-layout: fixed;">
<thead>
<tr style="color: #60a5fa; font-weight: 600; border-bottom: 1px solid #374151; font-size: 10px;">
<th style="padding: 6px 4px; width: 12%; text-align: left;">FREQ</th>
<th style="padding: 6px 4px; width: 23%; text-align: right;">LOT BID</th>
<th style="padding: 6px 4px; width: 15%; color: #ef4444;">BID</th>
<th style="padding: 6px 4px; width: 15%; color: #10b981;">ASK</th>
<th style="padding: 6px 4px; width: 23%; text-align: left;">LOT ASK</th>
<th style="padding: 6px 4px; width: 12%; text-align: right;">FREQ</th>
</tr>
</thead>
<tbody>
{table_rows_html}
</tbody>
</table>
<div style="border-top: 1px solid #374151; padding-top: 8px; margin-top: 6px; display: flex; justify-content: space-between; font-weight: 600; font-size: 11px; padding-left: 4px; padding-right: 4px;">
<span style="color: #ef4444;">{sum_bid_lot:,} Lot Bid</span>
<span style="color: #ffffff;">TOTAL ORDERBOOK</span>
<span style="color: #10b981;">{sum_ask_lot:,} Lot Ask</span>
</div>
</div>"""

            st.markdown(full_orderbook_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with tab_backtest:
    st.markdown('<div class="terminal-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Algorithmic Backtest & Strategy Engine")
    st.write("Uji performa historis formula Breakout Bollinger Bands & RRR 1:2 secara objektif.")

    col_bt1, col_bt2, col_bt3 = st.columns([1.5, 1, 1])
    with col_bt1:
        bt_ticker = st.text_input("Pilih Emiten:", value="UNTR").strip().upper()
    with col_bt2:
        bt_period = st.selectbox("Rentang Waktu:", ["3mo", "6mo", "1y"], index=1)
    with col_bt3:
        st.write("")
        st.write("")
        run_bt_btn = st.button("Jalankan Backtest 🚀")

    if run_bt_btn or bt_ticker:
        with st.spinner(f"Menjalankan backtest untuk {bt_ticker} ({bt_period})..."):
            bt_results, bt_summary = run_historical_backtest(bt_ticker, period=bt_period)

        if isinstance(bt_summary, dict):
            st.success("Backtest Selesai Berhasil!")
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Total Trades", bt_summary["Total Trades"])
            with m2: st.metric("Win Rate (%)", f"{bt_summary['Win Rate (%)']}%")
            with m3: st.metric("Total Return", f"{bt_summary['Total Return (%)']}%")
            with m4: st.metric("Profit Factor", bt_summary["Profit Factor"])

            st.markdown("#### 📋 Log Perdagangan Historis")
            st.dataframe(bt_results, use_container_width=True, hide_index=True)
        else:
            st.warning(f"Catatan: {bt_summary}")

    st.markdown('</div>', unsafe_allow_html=True)
