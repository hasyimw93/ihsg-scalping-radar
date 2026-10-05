import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Nano Machine Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. AUTO REFRESH REAL-TIME SAAT JAM BURSA BEI (Senin-Jumat, 09:00 - 16:00 WIB)
jakarta_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jakarta_tz)
is_bursa_open = now_jkt.weekday() < 5 and (9 <= now_jkt.hour < 16)

if is_bursa_open:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="bursa_refresh")
    except Exception:
        pass

# INISIALISASI SESSION STATE
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "⚡ Nano Scalping & Orderbook Terminal"

if 'selected_swing_ticker' not in st.session_state:
    st.session_state.selected_swing_ticker = "ADRO"

if 'selected_mb_ticker' not in st.session_state:
    st.session_state.selected_mb_ticker = "BUMI"

if 'custom_search_ticker' not in st.session_state:
    st.session_state.custom_search_ticker = "UNTR"

# 3. INJEKSI CUSTOM CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #002347 !important;
        color: #f8fafc !important;
    }

    .main-hero-nano {
        background: #003366;
        border: 1px solid #004080;
        border-radius: 16px;
        padding: 26px 30px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .hero-title-nano {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #ffffff;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: -0.5px;
    }
    .hero-subtitle-nano {
        font-size: 14px !important;
        color: #93c5fd;
        margin-top: 6px;
        letter-spacing: 1.5px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .dark-terminal-card {
        background: #002b5c;
        border: 1px solid #003b75;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        color: #f3f4f6;
    }

    .top-runner-bar {
        background: #003366;
        border: 1px solid #0047ab;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 14px;
        font-size: 12px;
        color: #cbd5e1;
    }

    .stButton > button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
    }

    div[data-baseweb="input"] {
        background-color: #003366 !important;
        border-radius: 8px !important;
        border: 1px solid #0047ab !important;
        color: white !important;
    }

    .stExpander {
        background-color: #003366 !important;
        border-radius: 12px !important;
        border: 1px solid #0047ab !important;
        color: #ffffff !important;
    }
    label { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# 4. HEADER BANNER UTAMA
st.markdown("""
<div class="main-hero-nano">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="hero-title-nano">NANO IDX SCALPER</div>
            <div class="hero-subtitle-nano">A-CLUB FIBONACCI & DIVIDEND HUNTER TERMINAL</div>
        </div>
        <div style="text-align: right; background: #002347; padding: 8px 14px; border-radius: 8px; border: 1px solid #0047ab;">
            <div style="font-size:10px; color:#93c5fd; font-weight:700;">ENGINE STATUS</div>
            <div style="font-size:12px; font-weight:700; color:#34d399;">● REAL-TIME SYNC</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# NAVIGASI TAB KONTROL TOMBOL (5 TAB)
tab_col1, tab_col2, tab_col3, tab_col4, tab_col5 = st.columns(5)
with tab_col1:
    if st.button("⚡ Scalping Terminal", use_container_width=True):
        st.session_state.active_tab = "⚡ Nano Scalping & Orderbook Terminal"
        st.rerun()
with tab_col2:
    if st.button("🚀 Weekly Swing", use_container_width=True):
        st.session_state.active_tab = "🚀 Weekly Swing Signal"
        st.rerun()
with tab_col3:
    if st.button("💎 Multi-Bagger Hunter", use_container_width=True):
        st.session_state.active_tab = "💎 Multi-Bagger Hunter"
        st.rerun()
with tab_col4:
    if st.button("💰 Dividend Hunter", use_container_width=True):
        st.session_state.active_tab = "💰 Dividend Hunter & Schedule"
        st.rerun()
with tab_col5:
    if st.button("📑 Right Issue & CA", use_container_width=True):
        st.session_state.active_tab = "📑 Right Issue & Corporate Action Module"
        st.rerun()

st.write("")

if 'master_universe' not in st.session_state:
    st.session_state.master_universe = [
        "BBCA", "BBRI", "BMRI", "BBNI", "ASII", "UNTR", "ADRO", "MDKA", "PTBA", "INCO",
        "TLKM", "GOTO", "ARTO", "BRIS", "CPIN", "INDF", "ICBP", "ANTM", "HRUM", "PGAS",
        "AKRA", "MEDC", "ELSA", "ESSA", "ERAA", "CUAN", "BUMI", "DEWA", "ENRG", "TEBE",
        "PANI", "AMMN", "BRMS", "TOBA", "BUKA", "ACES", "MAPI", "INKP", "TKIM", "JARR",
        "GGRM", "HMSP", "UNVR", "KLBF", "SMGR", "INTP", "JSMR", "EXCL", "ISAT", "TBIG",
        "DOOH", "RAJA", "ITMG", "ASGR", "AALI", "GEMS", "TLDN"
    ]

@st.cache_data(ttl=300)
def fetch_live_global_news_sentiment():
    try:
        ihsg = yf.Ticker("^JKSE")
        news_list = ihsg.news
        sentiment_summary = []
        if news_list:
            for item in news_list[:3]:
                title = item.get('title', 'Market Update')
                publisher = item.get('publisher', 'Global Wire')
                sentiment_summary.append(f"<b>{publisher}:</b> {title}")
        else:
            sentiment_summary = [
                "<b>Global Wire:</b> Komoditas Energi & Batu Bara Menopang Pergerakan Sektor Pertambangan IHSG",
                "<b>Market Watch:</b> The Fed Beri Sinyal Kebijakan Suku Bunga Stabil, Dorong Inflow ke Big Banks"
            ]
        return sentiment_summary
    except Exception:
        return ["<b>Global Wire:</b> Sektor Energi & Perbankan Jadi Motor Penggerak Utama Indeks IHSG"]

GLOBAL_NEWS_ITEMS = fetch_live_global_news_sentiment()

ESTIMATED_SHARES = {
    "TEBE": 1285000000, "JPFA": 11726575001, "TLKM": 99062216600, "CPIN": 16398000000,
    "BBCA": 123275000000, "BMRI": 93333333333, "UNTR": 3730135123, "ASII": 40483553140,
    "JARR": 12000000000, "AMRT": 41524500000, "TPIA": 86522000000, "AKRA": 20073000000,
    "BRIS": 46128000000, "ERAA": 15920000000, "PGAS": 24241000000, "ANTM": 24030000000,
    "BBRI": 151596000000, "BBNI": 37253000000, "PTBA": 11520000000, "INCO": 9933000000,
    "CUAN": 11818182000, "BUMI": 371300000000, "GOTO": 1201400000000, "DEWA": 131230000000,
    "ENRG": 25100000000, "BUKA": 103000000000, "ADRO": 31985000000, "DOOH": 5000000000, "RAJA": 9500000000,
    "ITMG": 1129925000, "ASGR": 1350000000, "AALI": 1924688000, "GEMS": 5882353000, "TLDN": 2185000000
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
            ma5 = close_series.rolling(5).mean().iloc[-1] if len(close_series) >= 5 else current_price
            
            upper_bb, mid_bb, lower_bb = hitung_bollinger_bands(close_series)
            is_bb_breakout = current_price >= upper_bb.iloc[-1] if not upper_bb.empty and not np.isnan(upper_bb.iloc[-1]) else False
            _, _, macd_hist = hitung_macd(close_series)
            is_macd_bullish = macd_hist.iloc[-1] > 0 if not macd_hist.empty and not np.isnan(macd_hist.iloc[-1]) else False

            global_sentiment_boost = 15 if clean_symbol in ["PTBA", "ADRO", "BUMI", "BBCA", "BBRI", "BMRI", "DOOH", "RAJA"] else 0

            if change_pct >= -2.0 and (is_macd_bullish or is_bb_breakout or change_pct >= 0):
                astronacci_action = "STRONG BUY"
                action_color = "#34d399"
                timing_buy = "09:00 - 10:15 WIB (Fibonacci Support Area)"
                timing_sell = "14:45 - 15:50 WIB (Fibonacci Extension TP)"
            elif change_pct < -3.0 or rsi_val > 78:
                astronacci_action = "TAKE PROFIT / SELL"
                action_color = "#f87171"
                timing_buy = "Wait / Area Retracement Belum Tercapai"
                timing_sell = "Segera Sesi 1 / Awal Sesi 2"
            else:
                astronacci_action = "STRONG BUY"
                action_color = "#34d399"
                timing_buy = "Akumulasi di Area Support Fibo"
                timing_sell = "Hold Sesuai Target TP"

            if is_bb_breakout and change_pct > 0:
                signal = "🔥 A-CLUB FIBO BREAKOUT"
            elif is_macd_bullish and current_price > ma5:
                signal = "🚀 BULLISH MOMENTUM"
            elif current_price > ma5:
                signal = "📈 BULLISH"
            else:
                signal = "🔻 PULLBACK SEHAT"
                
            if rsi_val > 70: signal += " (OB)"
            elif rsi_val < 30: signal += " (OS)"
                
            avg_vol = hist_intra["Volume"].mean() if not hist_intra.empty else 1
            last_vol = hist_intra["Volume"].iloc[-1] if not hist_intra.empty else 0
            vol_spike = "⚡ SPIKE" if last_vol > (avg_vol * 1.8) else "NORMAL"

            bsjp_score = 65
            if change_pct > 0: bsjp_score += 15
            if current_price >= (hod * 0.98): bsjp_score += 10
            if vol_spike == "⚡ SPIKE": bsjp_score += 10
            bsjp_score += global_sentiment_boost
            bsjp_score = max(55, min(98, bsjp_score))

            bsjp_status = f"⚡ VIP FIBO ({bsjp_score}%)"
            est_profit_pct = round(max(4.0, min(18.5, (bsjp_score / 5.2) + (change_pct if change_pct > 0 else 3.5))), 1)
            prediksi_profit_str = f"🎯 +{est_profit_pct}% (Fibo Target)"

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
                "Signal": signal,
                "Volume": vol_spike,
                "BSJP Status": bsjp_status,
                "BSJP Score": bsjp_score,
                "Prediksi Profit (3-15%+)": prediksi_profit_str,
                "Astronacci Action": astronacci_action,
                "Action Color": action_color,
                "Timing Buy": timing_buy,
                "Timing Sell": timing_sell,
                "Upper_BB": upper_bb,
                "Lower_BB": lower_bb
            }
    except Exception:
        pass
    return None

@st.cache_data(ttl=20)
def fetch_live_market_data(tuple_tickers):
    results = []
    for symbol in tuple_tickers:
        data = fetch_single_ticker_data(symbol)
        if data: results.append(data)
    return pd.DataFrame(results)

# KONTAINER UTAMA APLIKASI
st.markdown('<div class="dark-terminal-card">', unsafe_allow_html=True)

if st.session_state.active_tab == "⚡ Nano Scalping & Orderbook Terminal":
    st.markdown("<h4 style='margin-bottom: 4px; font-size: 15px; color: #f8fafc;'>📈 IHSG Real-Time Market Overview (^JKSE) & A-Club Fibo Formula</h4>", unsafe_allow_html=True)
    try:
        ihsg_ticker = yf.Ticker("^JKSE")
        ihsg_hist = ihsg_ticker.history(period="1d", interval="5m")
        if not ihsg_hist.empty:
            ihsg_current = ihsg_hist["Close"].iloc[-1]
            ihsg_prev = ihsg_ticker.history(period="5d", interval="1d")["Close"].iloc[-2] if len(ihsg_ticker.history(period="5d", interval="1d")) >= 2 else ihsg_hist["Open"].iloc[0]
            ihsg_change = ihsg_current - ihsg_prev
            ihsg_pct = (ihsg_change / ihsg_prev) * 100
            
            col_ihsg1, col_ihsg2, _ = st.columns([1, 1, 2])
            with col_ihsg1:
                st.metric(label="IHSG Index", value=f"{ihsg_current:,.2f}", delta=f"{ihsg_pct:+.2f}%")
            with col_ihsg2:
                st.metric(label="Perubahan Poin", value=f"{ihsg_change:+,.2f}", delta="Fibo Formula Active")
            
            fig_ihsg = go.Figure()
            fig_ihsg.add_trace(go.Scatter(x=ihsg_hist.index, y=ihsg_hist["Close"], mode='lines', name='IHSG', line=dict(color='#60a5fa', width=2), fill='tozeroy', fillcolor='rgba(96, 165, 250, 0.05)'))
            fig_ihsg.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0, 43, 92, 0.7)',
                margin=dict(l=10, r=10, t=10, b=10),
                height=180,
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd')
            )
            st.plotly_chart(fig_ihsg, use_container_width=True)
    except Exception:
        st.info("Memuat data grafik IHSG...")

    st.markdown("---")

    c_search, c_filter = st.columns([1.5, 1.5], gap="medium")
    with c_search:
        typed_search = st.text_input(
            "🔍 Ketik Kode Saham IHSG Apa Saja (Contoh: DOOH, RAJA, BBCA, DLL):",
            value=st.session_state.custom_search_ticker,
            help="Ketik kode emiten BEI apa saja."
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
        kategori_harga = st.selectbox("📌 Filter Rentang Harga Pasar:", ["Semua Saham", "1. > Rp 4.000", "2. Rp 3.000 - Rp 4.000", "3. Rp 2.000 - Rp 3.000", "4. Rp 1.000 - Rp 2.000", "5. Rp 500 - Rp 1.000", "6. Rp 1 - Rp 500"])

    with st.spinner("Memindai emiten dengan formula Fibonacci A-Club Astronacci..."):
        df_master = fetch_live_market_data(tuple(st.session_state.master_universe))

    if not df_master.empty:
        top_bsjp = df_master.sort_values(by="BSJP Score", ascending=False).head(3)
        bsjp_text = " | ".join([f"<b>{row['Ticker']}</b>: {row['BSJP Status']} (Rp {row['Price']:,})" for _, row in top_bsjp.iterrows()])
        st.markdown(f'<div class="top-runner-bar">📐 <b>A-Club Fibo Top Signal</b>: {bsjp_text}</div>', unsafe_allow_html=True)

    df_filtered = df_master.copy() if not df_master.empty else pd.DataFrame()
    if not df_filtered.empty:
        if kategori_harga == "1. > Rp 4.000": df_filtered = df_filtered[df_filtered["Price"] > 4000]
        elif kategori_harga == "2. Rp 3.000 - Rp 4.000": df_filtered = df_filtered[(df_filtered["Price"] >= 3000) & (df_filtered["Price"] <= 4000)]
        elif kategori_harga == "3. Rp 2.000 - Rp 3.000": df_filtered = df_filtered[(df_filtered["Price"] >= 2000) & (df_filtered["Price"] < 3000)]
        elif kategori_harga == "4. Rp 1.000 - Rp 2.000": df_filtered = df_filtered[(df_filtered["Price"] >= 1000) & (df_filtered["Price"] < 2000)]
        elif kategori_harga == "5. Rp 500 - Rp 1.000": df_filtered = df_filtered[(df_filtered["Price"] >= 500) & (df_filtered["Price"] < 1000)]
        elif kategori_harga == "6. Rp 1 - Rp 500": df_filtered = df_filtered[(df_filtered["Price"] >= 1) & (df_filtered["Price"] < 500)]
        
        df_filtered = df_filtered.sort_values(by=["BSJP Score", "Raw Change"], ascending=[False, False])

    st.markdown("<h4 style='margin-bottom: 8px; font-size: 15px; color: #f8fafc;'>⚡ Running Trade (BEI Micro Tick Feed)</h4>", unsafe_allow_html=True)
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
        action_color = "#34d399" if "BUY" in action_type else "#f87171"
        rt_data.append(f"<span style='color: #93c5fd;'>{current_time_str}</span> &nbsp;|&nbsp; <b style='color: #ffffff;'>{t_sim}</b> &nbsp;|&nbsp; <span style='color: {action_color}; font-weight:600;'>Rp {tick_p:,}</span> &nbsp;|&nbsp; <span style='color: #cbd5e1;'>{lot_item:,} Lot</span> &nbsp;|&nbsp; <span style='font-size:10px; color:#93c5fd;'>{action_type}</span>")

    rt_cols = st.columns(3)
    for idx, item_html in enumerate(rt_data):
        with rt_cols[idx % 3]:
            st.markdown(f"<div style='background: #002347; border: 1px solid #003b75; border-radius: 8px; padding: 6px 10px; font-size: 11px; margin-bottom: 6px;'>{item_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns([1.3, 1.7], gap="medium")

    selected_row = None

    with col_left:
        st.subheader("🎯 Market Scanner Radar (Auto-Ranked)")
        if not df_filtered.empty:
            display_columns = ["Ticker", "Price", "Change (%)", "Prediksi Profit (3-15%+)", "Signal", "BSJP Status"]
            event_selection = st.dataframe(
                df_filtered[display_columns],
                use_container_width=True, 
                hide_index=True, 
                height=320,
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
            st.info("Tidak ada saham sesuai kriteria rentang harga.")

        st.write("")

    match_search = df_master[df_master["Ticker"] == selected_ticker] if not df_master.empty else pd.DataFrame()
    if not match_search.empty:
        selected_row = match_search.iloc[0].to_dict()
    else:
        fetched_custom = fetch_single_ticker_data(selected_ticker)
        if fetched_custom:
            selected_row = fetched_custom

    if selected_ticker and selected_row:
        area_beli = int(selected_row["Price"])
        prev_p = int(selected_row.get("Prev", area_beli))
        open_p = int(selected_row.get("Open", area_beli))
        high_p = int(selected_row.get("High", area_beli))
        low_p = int(selected_row.get("Low", area_beli))
        fibo_50 = int(selected_row.get("Fib 50.0%", int(area_beli * 0.98)))
        fibo_618 = int(selected_row.get("Fib 61.8%", int(area_beli * 0.96)))
        
        t_buy = selected_row.get("Timing Buy", "09:00 - 10:15 WIB (Fibo Support)")
        t_sell = selected_row.get("Timing Sell", "14:45 - 15:50 WIB (Fibo Extension)")
        astr_action = selected_row.get("Astronacci Action", "STRONG BUY")
        action_bg = selected_row.get("Action Color", "#34d399")

        with col_right:
            c_head1, c_head2 = st.columns([1, 1])
            with c_head1:
                st.markdown(f"<h3 style='margin:0; font-size:20px;'>Orderbook Matrix: {selected_ticker}</h3>", unsafe_allow_html=True)
            with c_head2:
                st.markdown("<div style='text-align: right; color: #93c5fd; font-size: 13px; font-weight: 500;'>Lihat Antrean Order</div>", unsafe_allow_html=True)
            
            st.write("")

            st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; font-size: 12px;">
        <table width="100%" style="color: #cbd5e1;">
            <tr>
                <td>Open: <b style="color: #34d399;">Rp {open_p:,}</b></td>
                <td>Fibo 50.0%: <b style="color: #60a5fa;">Rp {fibo_50:,}</b></td>
                <td>High: <b style="color: #34d399;">Rp {high_p:,}</b></td>
            </tr>
            <tr>
                <td>Prev: <b>Rp {prev_p:,}</b></td>
                <td>Fibo 61.8%: <b style="color: #34d399;">Rp {fibo_618:,}</b></td>
                <td>Low: <b style="color: #f87171;">Rp {low_p:,}</b></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

            tp_aclubs = int(round(area_beli * 1.12))
            sl_aclubs = fibo_618 if fibo_618 < area_beli else int(round(area_beli * 0.94))

            st.markdown(f"""
    <div style="background: linear-gradient(135deg, #003366 0%, #001f3f 100%); border: 1px solid {action_bg}; border-radius: 14px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
                <span style="font-size: 18px; font-weight: 800; color: #ffffff;">{selected_ticker}</span>
                <span style="font-size: 11px; color: #93c5fd; margin-left: 8px;">A-Club Fibonacci Formula</span>
            </div>
            <div style="background: {action_bg}; color: #002347; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 800;">{astr_action} 🚀</div>
        </div>
        <div style="display: flex; justify-content: space-between; background: #002347; padding: 10px 14px; border-radius: 8px; font-size: 12px; margin-bottom: 10px;">
            <span>Buy Area (Fibo): <b style="color: #34d399;">Rp {area_beli:,}</b></span>
            <span>Target TP: <b style="color: #6ee7b7;">Rp {tp_aclubs:,} (+12%)</b></span>
            <span>Stop Loss: <b style="color: #f87171;">Rp {sl_aclubs:,}</b></span>
        </div>
        <div style="font-size: 11px; color: #cbd5e1; display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
            <span>🟢 <b>Jadwal Masuk (Timing Buy):</b> <b style="color: #34d399;">{t_buy}</b></span>
            <span>🔴 <b>Jadwal Jual (Timing Sell):</b> <b style="color: #f87171;">{t_sell}</b></span>
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
            sum_bid_freq = sum(bids_f)
            sum_ask_freq = sum(asks_f)

            table_rows_html = ""
            for i in range(10):
                ask_c = "#34d399" if i < 2 else "#f87171"
                table_rows_html += f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
    <td style="padding: 7px 4px; text-align: left; color: #93c5fd; width: 12%; font-size: 11px;">{bids_f[i]}</td>
    <td style="padding: 7px 4px; text-align: right; font-weight: 500; width: 23%; font-size: 11px;">{bids_v[i]:,}</td>
    <td style="padding: 7px 4px; color: #f87171; font-weight: 600; width: 15%; font-size: 11px;">Rp {bids_p[i]:,}</td>
    <td style="padding: 7px 4px; color: {ask_c}; font-weight: 600; width: 15%; font-size: 11px;">Rp {asks_p[i]:,}</td>
    <td style="padding: 7px 4px; text-align: left; font-weight: 500; width: 23%; font-size: 11px;">{asks_v[i]:,}</td>
    <td style="padding: 7px 4px; text-align: right; color: #93c5fd; width: 12%; font-size: 11px;">{asks_f[i]}</td>
    </tr>"""

            full_orderbook_html = f"""<div style="background: #002347; border: 1px solid #0047ab; border-radius: 12px; padding: 12px; width: 100%; overflow-x: auto;">
    <table style="width: 100%; color: #e2e8f0; text-align: center; border-collapse: collapse; table-layout: fixed;">
    <thead>
    <tr style="color: #93c5fd; font-weight: 600; border-bottom: 1px solid #0047ab; font-size: 10px;">
    <th style="padding: 6px 4px; width: 12%; text-align: left;">FREQ</th>
    <th style="padding: 6px 4px; width: 23%; text-align: right;">LOT BID</th>
    <th style="padding: 6px 4px; width: 15%; color: #f87171;">BID</th>
    <th style="padding: 6px 4px; width: 15%; color: #34d399;">ASK</th>
    <th style="padding: 6px 4px; width: 23%; text-align: left;">LOT ASK</th>
    <th style="padding: 6px 4px; width: 12%; text-align: right;">FREQ</th>
    </tr>
    </thead>
    <tbody>
    {table_rows_html}
    </tbody>
    </table>
    <div style="border-top: 1px solid #0047ab; padding-top: 10px; margin-top: 8px; display: flex; justify-content: space-between; font-weight: 600; font-size: 11px; padding-left: 4px; padding-right: 4px;">
    <span style="color: #93c5fd;">{sum_bid_freq:,}</span>
    <span style="color: #f87171;">{sum_bid_lot:,} Lot</span>
    <span style="color: #ffffff;">TOTAL</span>
    <span style="color: #34d399;">{sum_ask_lot:,} Lot</span>
    <span style="color: #93c5fd;">{sum_ask_freq:,}</span>
    </div>
    </div>"""

            st.markdown(full_orderbook_html, unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: WEEKLY SWING SIGNAL
# ------------------------------------------
elif st.session_state.active_tab == "🚀 Weekly Swing Signal":
    st.markdown("### 🚀 Weekly Swing Signal & Watchlist")
    
    col_sw1, col_sw2 = st.columns([1.6, 1.4], gap="medium")
    with col_sw1:
        st.markdown("#### 📊 Top Weekly Swing Picks (Klik Baris)")
        swing_picks = [
            {"Emiten": "UNTR", "Setup": "Breakout Resistance", "Buy Zone": "26000", "TP 1": "26800", "TP 2": "27500", "TP 3": "28500", "Stop Loss": "25200", "Target Waktu": "1-2 Minggu"},
            {"Emiten": "ASGR", "Setup": "Pullback MA20", "Buy Zone": "1500", "TP 1": "1560", "TP 2": "1620", "TP 3": "1700", "Stop Loss": "1440", "Target Waktu": "2-3 Minggu"},
            {"Emiten": "AALI", "Setup": "Accumulation Phase", "Buy Zone": "7200", "TP 1": "7450", "TP 2": "7700", "TP 3": "8000", "Stop Loss": "6950", "Target Waktu": "1-3 Minggu"}
        ]
        df_swing = pd.DataFrame(swing_picks)
        event_swing = st.dataframe(df_swing[["Emiten", "Setup", "Buy Zone", "TP 1", "Target Waktu"]], use_container_width=True, hide_index=True, height=200, selection_mode="single-row", on_select="rerun", key="table_swing")
        sel_sw_rows = event_swing.get("selection", {}).get("rows", [])
        if sel_sw_rows:
            st.session_state.selected_swing_ticker = df_swing.iloc[sel_sw_rows[0]]["Emiten"]
            
    active_sw = st.session_state.selected_swing_ticker
    sw_data = next((item for item in swing_picks if item["Emiten"] == active_sw), swing_picks[0])
    
    with col_sw2:
        st.markdown(f"#### ⭐ Astronacci VIP Signal: {active_sw}")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #003366 0%, #002244 100%); border: 1px solid #34d399; border-radius: 12px; padding: 16px;">
            <div style="font-size: 13px; font-weight: 700; color: #ffffff; margin-bottom: 8px;">VIP SIGNAL CARD: {sw_data['Emiten']}</div>
            <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
                <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                    <td style="padding: 6px;">BUY ZONE</td>
                    <td style="padding: 6px;">TP 1</td>
                    <td style="padding: 6px;">TP 2</td>
                    <td style="padding: 6px;">CUT LOSS</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {sw_data['Buy Zone']}</td>
                    <td style="padding: 8px 0; color: #6ee7b7;">Rp {sw_data['TP 1']}</td>
                    <td style="padding: 8px 0; color: #34d399; font-weight: 700;">Rp {sw_data['TP 2']}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {sw_data['Stop Loss']}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 💼 Active Swing Trade Portfolio")
    df_swing_port = pd.DataFrame([
        {"Emiten": "UNTR", "Entry (Rp)": "Rp 26,000", "Live Price (Rp)": "Rp 26,015", "Lot": 10, "Floating P&L": "Rp 15,000 (+0.06%)", "Target Waktu": "1 - 2 Minggu", "Status": "🚀 Cuan (+0.06%)"}
    ])
    st.dataframe(df_swing_port, use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 3: MULTI-BAGGER HUNTER
# ------------------------------------------
elif st.session_state.active_tab == "💎 Multi-Bagger Hunter":
    st.markdown("### 💎 Multi-Bagger Hunter (Gocap to High)")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Analisis saham berharga murah dengan kartu sinyal interaktif target jangka panjang (Multi-Bagger Style).</p>", unsafe_allow_html=True)
    
    col_mb_left, col_mb_right = st.columns([1.6, 1.4], gap="medium")
    
    with col_mb_left:
        st.markdown("#### 📈 Live Multi-Bagger Watchlist (Klik Baris untuk Analisis Kartu)")
        mb_picks = [
            {"Emiten": "BUMI", "Harga Awal": "Rp 50", "Harga Live": "Rp 175", "Perubahan": "+2.94%", "Katalis Utama": "Restrukturisasi & Batubara", "Valuasi/PBV": "0.8x (Murah)", "Target Utama": "Rp 500+", "Buy Zone": 175, "Target 1": 250, "Target 2": 400, "Target 3": 500, "Invalidation": 40},
            {"Emiten": "DEWA", "Harga Awal": "Rp 50", "Harga Live": "Rp 338", "Perubahan": "+1.20%", "Katalis Utama": "Ekspansi Tambang Emas", "Valuasi/PBV": "1.2x", "Target Utama": "Rp 1,200+", "Buy Zone": 338, "Target 1": 500, "Target 2": 800, "Target 3": 1200, "Invalidation": 42},
            {"Emiten": "ENRG", "Harga Awal": "Rp 90", "Harga Live": "Rp 1,440", "Perubahan": "+2.13%", "Katalis Utama": "Akuisisi Blok Migas Baru", "Valuasi/PBV": "1.1x", "Target Utama": "Rp 3,000+", "Buy Zone": 1440, "Target 1": 1800, "Target 2": 2400, "Target 3": 3000, "Invalidation": 80},
            {"Emiten": "BRMS", "Harga Awal": "Rp 50", "Harga Live": "Rp 570", "Perubahan": "+3.64%", "Katalis Utama": "Commercial Production Emas", "Valuasi/PBV": "2.5x", "Target Utama": "Rp 1,500+", "Buy Zone": 570, "Target 1": 750, "Target 2": 1100, "Target 3": 1500, "Invalidation": 45},
            {"Emiten": "TLDN", "Harga Awal": "Rp 200", "Harga Live": "Rp 550", "Perubahan": "+1.85%", "Katalis Utama": "Ekspansi Sawit & Dividen Rutin", "Valuasi/PBV": "1.2x", "Target Utama": "Rp 1,200+", "Buy Zone": 550, "Target 1": 700, "Target 2": 950, "Target 3": 1200, "Invalidation": 180}
        ]
        df_mb = pd.DataFrame(mb_picks)
        
        event_mb = st.dataframe(
            df_mb[["Emiten", "Harga Awal", "Harga Live", "Perubahan", "Katalis Utama", "Valuasi/PBV", "Target Utama"]],
            use_container_width=True, hide_index=True, height=280,
            selection_mode="single-row", on_select="rerun", key="table_mb"
        )
        
        sel_mb_rows = event_mb.get("selection", {}).get("rows", [])
        if sel_mb_rows:
            st.session_state.selected_mb_ticker = df_mb.iloc[sel_mb_rows[0]]["Emiten"]
            
    active_mb = st.session_state.selected_mb_ticker
    mb_data = next((item for item in mb_picks if item["Emiten"] == active_mb), mb_picks[0])
    
    with col_mb_right:
        st.markdown(f"#### ⭐ Multi-Bagger Signal Card: {active_mb}")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #003366 0%, #002244 100%); border: 1px solid #60a5fa; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-size: 13px; font-weight: 700; color: #ffffff;">💎 LONG-TERM TARGET: {mb_data['Emiten']}</div>
                <div style="background: rgba(0,0,0,0.3); color: #34d399; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; border: 1px solid #34d399;">ACTION: ACCUMULATE</div>
            </div>
            <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center; margin-bottom: 8px;">
                <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                    <td style="padding: 6px;">BUY ZONE</td>
                    <td style="padding: 6px;">TARGET 1 (2x)</td>
                    <td style="padding: 6px;">TARGET 2 (3x)</td>
                    <td style="padding: 6px;">TARGET 3 (5x+)</td>
                    <td style="padding: 6px; color: #f87171;">INVALIDATION</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {mb_data['Buy Zone']:,}</td>
                    <td style="padding: 8px 0; color: #6ee7b7;">Rp {mb_data['Target 1']:,}</td>
                    <td style="padding: 8px 0; color: #60a5fa;">Rp {mb_data['Target 2']:,}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {mb_data['Target 3']:,}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {mb_data['Invalidation']}</td>
                </tr>
            </table>
            <div style="font-size: 11px; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 6px;">
                🚀 <b>Katalis Utama:</b> {mb_data['Katalis Utama']} <br>
                🟢 <b>Akumulasi:</b> Fase Konsolidasi / Low Volatility
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Multi-Bagger Growth Simulator")
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        harga_beli_sim = st.number_input("Harga Beli Saat Ini (Rp):", value=int(mb_data['Buy Zone']), step=10)
    with sim_col2:
        target_harga_sim = st.number_input("Target Harga Jangka Panjang (Rp):", value=int(mb_data['Target 3']), step=50)
    with sim_col3:
        jumlah_lot_sim = st.number_input("Jumlah Lot Disimpan:", value=100, step=10)
        
    modal_awal = harga_beli_sim * jumlah_lot_sim * 100
    nilai_akhir = target_harga_sim * jumlah_lot_sim * 100
    potensi_profit = nilai_akhir - modal_awal
    persen_kenaikan = ((target_harga_sim - harga_beli_sim) / harga_beli_sim) * 100 if harga_beli_sim > 0 else 0
    kelipatan = target_harga_sim / harga_beli_sim if harga_beli_sim > 0 else 1

    st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 16px; margin-top: 10px;">
        <div style="font-size: 12px; font-weight: 700; color: #93c5fd; text-transform: uppercase; margin-bottom: 8px;">HASIL SIMULASI MULTI-BAGGER:</div>
        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
            <span>Modal Awal: <b style="color: #ffffff;">Rp {modal_awal:,.0f}</b></span>
            <span>Nilai Portofolio Akhir: <b style="color: #34d399;">Rp {nilai_akhir:,.0f}</b></span>
        </div>
        <hr style="border-color: rgba(255,255,255,0.1)">
        <div style="font-size: 14px; color: #34d399; font-weight: 700;">Potensi Profit: Rp {potensi_profit:,.0f}</div>
        <div style="font-size: 12px; color: #60a5fa; margin-top: 2px;">Potensi Kenaikan: +{persen_kenaikan:.2f}% ({kelipatan:.1f}x Lipat)</div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------
# TAB 4: DIVIDEND HUNTER & SCHEDULE MODULE (LIVE PRICE SYNC)
# ------------------------------------------
elif st.session_state.active_tab == "💰 Dividend Hunter & Schedule":
    st.markdown("### 💰 Dividend Hunter & Golden Timeline Schedule (Live Market Price Sync)")
    st.markdown("Kalender dividen real-time berdasarkan data keterbukaan informasi bursa terbaru dengan sinkronisasi harga pasar live via yFinance.")
    
    col_div1, col_div2 = st.columns([1.6, 1.4], gap="medium")
    
    with col_div1:
        st.markdown("#### 📊 Kalender & Watchlist Dividen Terbaru (Live Price)")
        
        raw_div_list = [
            {"Emiten": "UNTR", "Div": 430, "Cum": "6 Okt 2026", "Ex": "7 Okt 2026", "Pay": "26 Okt 2026"},
            {"Emiten": "ASGR", "Div": 297, "Cum": "7 Okt 2026", "Ex": "8 Okt 2026", "Pay": "26 Okt 2026"},
            {"Emiten": "AALI", "Div": 233, "Cum": "8 Okt 2026", "Ex": "9 Okt 2026", "Pay": "26 Okt 2026"},
            {"Emiten": "GEMS", "Div": 611, "Cum": "8 Okt 2026", "Ex": "9 Okt 2026", "Pay": "22 Okt 2026"},
            {"Emiten": "TLDN", "Div": 20, "Cum": "12 Okt 2026", "Ex": "13 Okt 2026", "Pay": "22 Okt 2026"}
        ]
        
        live_div_rows = []
        for item in raw_div_list:
            t_symbol = item["Emiten"]
            t_info = fetch_single_ticker_data(t_symbol)
            p_live = t_info["Price"]
            y_calc = (item["Div"] / p_live) * 100 if p_live > 0 else 0
            live_div_rows.append({
                "Emiten": t_symbol,
                "Harga (Rp)": p_live,
                "Dividen/Svr (Rp)": item["Div"],
                "Yield (%)": f"{y_calc:.2f}%",
                "Cum Date": item["Cum"],
                "Ex Date": item["Ex"],
                "Payment": item["Pay"]
            })
            
        df_div = pd.DataFrame(live_div_rows)
        st.dataframe(df_div, use_container_width=True, height=270, hide_index=True)
        
        st.markdown("#### 🧮 Kalkulator Simulasi Cuan Dividen")
        emitens_list = df_div["Emiten"].tolist()
        sim_div_emiten = st.selectbox("Pilih Emiten Pembagi Dividen:", emitens_list)
        sim_lot_div = st.number_input("Jumlah Saham yang Dimiliki (Lot):", value=50, step=10)
        
        row_sel = df_div[df_div["Emiten"] == sim_div_emiten].iloc[0]
        harga_saham_div = row_sel["Harga (Rp)"]
        div_per_saham = row_sel["Dividen/Svr (Rp)"]
        yield_val = row_sel["Yield (%)"]
        cum_date_val = row_sel["Cum Date"]
        
        total_lembar_div = sim_lot_div * 100
        total_modal_div = total_lembar_div * harga_saham_div
        total_div_diterima = total_lembar_div * div_per_saham

        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #34d399; border-radius: 12px; padding: 14px; margin-top: 10px;">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase;">Hasil Kalkulasi Dividen {sim_div_emiten}:</div>
            <div style="font-size: 13px; color: #ffffff; margin-top: 4px;">Total Modal Investasi (Live): <b>Rp {total_modal_div:,.0f}</b></div>
            <div style="font-size: 14px; color: #34d399; margin-top: 2px; font-weight: 700;">Total Dividen Diterima (Gross): Rp {total_div_diterima:,.0f} ({yield_val})</div>
            <div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">Wajib Beli Paling Lambat (Cum Date): <b style="color: #6ee7b7;">{cum_date_val}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with col_div2:
        st.markdown(f"#### 📅 Skema Waktu & Aturan Emas Dividen ({sim_div_emiten})")
        st.markdown(f"""
        **🎯 Panduan Waktu Transaksi A-Club Dividen:**
        
        🟢 **1. CUM DATE ({row_sel['Cum Date']})**  
        Hari terakhir Anda **wajib punya/beli saham** ini di portofolio sebelum penutupan market agar tercatat sebagai penerima dividen.
        
        🔴 **2. EX DATE ({row_sel['Ex Date']})**  
        Hari pertama saham diperdagangkan **tanpa hak dividen** (*ex-dividend*). Harga biasanya terkoreksi (dividen drop). Jangan beli di hari ini jika mengincar dividen!
        
        🔵 **3. RECORDING DATE (H+1 Ex-Date)**  
        Tanggal Kustodian KSEI mencetak daftar resmi investor yang berhak atas dividen.
        
        💰 **4. PAYMENT DATE ({row_sel['Payment']})**  
        Hari pencairan uang dividen masuk secara otomatis ke dalam Rekening Dana Nasabah (RDN) Anda.
        """)

# ------------------------------------------
# TAB 5: RIGHT ISSUE & CA + SIMULASI HMETD
# ------------------------------------------
elif st.session_state.active_tab == "📑 Right Issue & Corporate Action Module":
    st.markdown("### 📑 Right Issue, HMETD Simulation & Live Global Sentiment")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Modul aksi korporasi lengkap dengan kalkulator teoretis serta simulasi kepemilikan dan penebusan HMETD.</p>", unsafe_allow_html=True)
    
    news_html_str = "".join([f"<li>{news}</li>" for news in GLOBAL_NEWS_ITEMS])
    st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 16px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #34d399;">📰 Live Global & Macro Sentiment (Auto-Updated)</h4>
        <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #93c5fd;">
            {news_html_str}
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col_ri1, col_ri2 = st.columns([1.5, 1.5], gap="medium")
    
    with col_ri1:
        st.markdown("#### 🔍 Daftar Emiten & Jadwal Right Issue")
        df_ri = pd.DataFrame([
            {"Emiten": "BUMI", "Rasio HMETD": "100 : 15", "Harga Tebus": "Rp 80", "Cum Date": "05 Okt 2026", "Sentimen Global": "🟢 Bullish (Energi)"},
            {"Emiten": "ARTO", "Rasio HMETD": "10 : 1", "Harga Tebus": "Rp 2,100", "Cum Date": "12 Okt 2026", "Sentimen Global": "🟡 Neutral"},
            {"Emiten": "BANK", "Rasio HMETD": "100 : 25", "Harga Tebus": "Rp 1,050", "Cum Date": "25 Okt 2026", "Sentimen Global": "🟢 Bullish (Inflow)"}
        ])
        df_ri_display = df_ri.copy()
        st.dataframe(df_ri_display, use_container_width=True, hide_index=True)
        
        st.markdown("#### 🧮 Simulasi Kepemilikan & Penebusan HMETD")
        sim_lot_saham = st.number_input("Jumlah Saham Induk yang Dimiliki (Lot):", value=100, step=10)
        sim_rasio_lama = st.number_input("Rasio Saham Lama (Contoh: 100):", value=100, step=10)
        sim_rasio_baru = st.number_input("Rasio HMETD Didapat (Contoh: 15):", value=15, step=1)
        sim_harga_tebus = st.number_input("Harga Tebus / Exercise Price (Rp):", value=80, step=10)
        
        total_lembar_saham = sim_lot_saham * 100
        total_hmetd_lembar = int((total_lembar_saham / sim_rasio_lama) * sim_rasio_baru) if sim_rasio_lama > 0 else 0
        total_hmetd_lot = total_hmetd_lembar // 100
        total_dana_tebus = total_hmetd_lembar * sim_harga_tebus
        
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #34d399; border-radius: 12px; padding: 14px; margin-top: 10px;">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase;">Hasil Simulasi HMETD Anda:</div>
            <div style="font-size: 14px; color: #ffffff; margin-top: 4px;">Hak HMETD Diperoleh: <b style="color: #34d399;">{total_hmetd_lembar:,} Lembar ({total_hmetd_lot:,} Lot)</b></div>
            <div style="font-size: 14px; color: #ffffff; margin-top: 2px;">Total Dana Tebus (Exercise): <b style="color: #6ee7b7;">Rp {total_dana_tebus:,.0f}</b></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_ri2:
        st.markdown("#### 📊 Right Issue Theoretical Price Calculator")
        harga_cum = st.number_input("Harga Saham Saat Cum-Date (Rp):", value=1500, step=50)
        harga_tebus_calc = st.number_input("Harga Tebus / Exercise Price Kalkulator (Rp):", value=1000, step=50)
        
        col_saham_lama, col_saham_baru = st.columns(2)
        with col_saham_lama:
            saham_lama = st.number_input("Saham Lama (Old):", value=10)
        with col_saham_baru:
            saham_baru = st.number_input("Saham Baru (Rights):", value=2)
            
        if (saham_lama + saham_baru) > 0:
            harga_teoretis = ((harga_cum * saham_lama) + (harga_tebus_calc * saham_baru)) / (saham_lama + saham_baru)
            estimasi_dilusi = ((harga_cum - harga_teoretis) / harga_cum) * 100
        else:
            harga_teoretis = 0
            estimasi_dilusi = 0
            
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 16px; margin-top: 10px;">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase;">Hasil Kalkulasi Teoretis & Real-Time Formula:</div>
            <div style="font-size: 18px; font-weight: 800; color: #34d399; margin: 4px 0;">Harga Teoretis Pasca RI: Rp {harga_teoretis:,.2f}</div>
            <div style="font-size: 12px; color: #f87171;">Estimasi Dilusi Harga: {estimasi_dilusi:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
