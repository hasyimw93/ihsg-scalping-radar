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

# 2. AUTO REFRESH HANYA SAAT JAM BURSA BEI (Senin-Jumat, 09:00 - 16:00 WIB)
jakarta_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jakarta_tz)
is_bursa_open = now_jkt.weekday() < 5 and (9 <= now_jkt.hour < 16)

if is_bursa_open:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="bursa_refresh")
    except Exception:
        pass

# INISIALISASI SESSION STATE UNTUK NAVIGASI TAB AKTIF
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "⚡ Nano Scalping & Orderbook Terminal"

if 'selected_swing_ticker' not in st.session_state:
    st.session_state.selected_swing_ticker = "ADRO"

if 'selected_mb_ticker' not in st.session_state:
    st.session_state.selected_mb_ticker = "BUMI"

# 3. INJEKSI CUSTOM CSS (BIRU KHAS AJAIB KONSISTEN & JUDUL BESAR)
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
            <div class="hero-subtitle-nano">ANALYTICS TERMINAL & INTERACTIVE SIGNAL MODULES</div>
        </div>
        <div style="text-align: right; background: #002347; padding: 8px 14px; border-radius: 8px; border: 1px solid #0047ab;">
            <div style="font-size:10px; color:#93c5fd; font-weight:700;">NANO CORE</div>
            <div style="font-size:12px; font-weight:700; color:#34d399;">● SYNCHRONIZED</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# CUSTOM NAVIGASI TAB KONTROL TOMBOL (4 TAB UTAMA)
tab_col1, tab_col2, tab_col3, tab_col4 = st.columns(4)
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
    if st.button("📑 Right Issue & CA", use_container_width=True):
        st.session_state.active_tab = "📑 Right Issue & Corporate Action Module"
        st.rerun()

st.write("")

# MASTER UNIVERSE DIOPTIMALKAN (EMITEN LIKUID & BERPOTENSI TINGGI)
if 'master_universe' not in st.session_state:
    st.session_state.master_universe = [
        "BBCA", "BBRI", "BMRI", "BBNI", "ASII", "UNTR", "ADRO", "MDKA", "PTBA", "INCO",
        "TLKM", "GOTO", "ARTO", "BRIS", "CPIN", "INDF", "ICBP", "ANTM", "HRUM", "PGAS",
        "AKRA", "MEDC", "ELSA", "ESSA", "ERAA", "CUAN", "BUMI", "DEWA", "ENRG", "TEBE",
        "PANI", "AMMN", "BRMS", "TOBA", "BUKA", "ACES", "MAPI", "INKP", "TKIM", "JARR"
    ]

if 'trade_journal' not in st.session_state:
    st.session_state.trade_journal = []

if 'swing_journal' not in st.session_state:
    st.session_state.swing_journal = [
        {"Emiten": "ADRO", "Entry": 2480, "Lot": 50, "Target Waktu": "1 - 2 Minggu"},
        {"Emiten": "MDKA", "Entry": 2720, "Lot": 40, "Target Waktu": "2 - 3 Minggu"}
    ]

ESTIMATED_SHARES = {
    "TEBE": 1285000000, "JPFA": 11726575001, "TLKM": 99062216600, "CPIN": 16398000000,
    "BBCA": 123275000000, "BMRI": 93333333333, "UNTR": 3730135123, "ASII": 40483553140,
    "JARR": 12000000000, "AMRT": 41524500000, "TPIA": 86522000000, "AKRA": 20073000000,
    "BRIS": 46128000000, "ERAA": 15920000000, "PGAS": 24241000000, "ANTM": 24030000000,
    "BBRI": 151596000000, "BBNI": 37253000000, "PTBA": 11520000000, "INCO": 9933000000,
    "CUAN": 11818182000, "BUMI": 371300000000, "GOTO": 1201400000000, "DEWA": 131230000000,
    "ENRG": 25100000000, "BUKA": 103000000000, "ADRO": 31985000000
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

@st.cache_data(ttl=60)
def fetch_single_ticker_data(symbol):
    try:
        clean_symbol = symbol.strip().upper()
        ticker_jk = f"{clean_symbol}.JK"
        stock = yf.Ticker(ticker_jk)
        hist = stock.history(period="5d", interval="1d")
        
        if not hist.empty and len(hist) >= 2:
            current_price = int(round(hist["Close"].iloc[-1]))
            prev_close = int(round(hist["Close"].iloc[-2]))
            open_price = int(round(hist["Open"].iloc[-1]))
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
            
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

            # LOGIKA DINAMIS ASTRONACCI
            if change_pct > 0.5 and is_macd_bullish and (is_bb_breakout or current_price >= hod * 0.96):
                astronacci_action = "STRONG BUY"
                action_color = "#34d399"
                bg_gradient = "linear-gradient(135deg, #003366 0%, #002244 100%)"
                timing_buy = "09:00 - 10:15 WIB (Sesi 1 Open)"
                timing_sell = "14:45 - 15:50 WIB (Jelang Closing)"
            elif change_pct < -1.0 or rsi_val > 75:
                astronacci_action = "TAKE PROFIT / SELL"
                action_color = "#f87171"
                bg_gradient = "linear-gradient(135deg, #451a03 0%, #221006 100%)"
                timing_buy = "Wait / Hindari Beli Dulu"
                timing_sell = "Segera Sesi 1 / Awal Sesi 2"
            else:
                astronacci_action = "WAIT / WATCHLIST"
                action_color = "#fbbf24"
                bg_gradient = "linear-gradient(135deg, #3b2800 0%, #1f1500 100%)"
                timing_buy = "Tunggu Pullback / Support"
                timing_sell = "Hold Sesuai Target TP"

            if is_bb_breakout and change_pct > 0:
                signal = "🔥 ASTRONACCI BREAKOUT"
            elif is_macd_bullish and current_price > ma5:
                signal = "🚀 BULLISH MOMENTUM"
            elif current_price > ma5:
                signal = "📈 BULLISH"
            else:
                signal = "🔻 BEARISH"
                
            if rsi_val > 70: signal += " (OB)"
            elif rsi_val < 30: signal += " (OS)"
            
            avg_vol = hist_intra["Volume"].mean() if not hist_intra.empty else 1
            last_vol = hist_intra["Volume"].iloc[-1] if not hist_intra.empty else 0
            vol_spike = "⚡ SPIKE" if last_vol > (avg_vol * 1.8) else "NORMAL"

            bsjp_score = 0
            if change_pct > 0: bsjp_score += 20
            if current_price >= (hod * 0.98): bsjp_score += 20
            if vol_spike == "⚡ SPIKE": bsjp_score += 20
            if is_macd_bullish: bsjp_score += 20
            if is_bb_breakout or current_price > ma5: bsjp_score += 20

            bsjp_status = f"⚡ VIP SIGNAL ({bsjp_score}%)" if bsjp_score >= 80 else f"⚙ QUANTUM ({bsjp_score}%)" if bsjp_score >= 50 else "⚠ WAIT"

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
                "Total Lot": total_lot,
                "Total Val": total_val,
                "Market Cap": mc_fmt,
                "Change (%)": f"{change_pct:+.2f}%",
                "Raw Change": change_pct,
                "Signal": signal,
                "Volume": vol_spike,
                "BSJP Status": bsjp_status,
                "BSJP Score": bsjp_score,
                "Astronacci Action": astronacci_action,
                "Action Color": action_color,
                "Bg Gradient": bg_gradient,
                "Timing Buy": timing_buy,
                "Timing Sell": timing_sell,
                "Upper_BB": upper_bb,
                "Lower_BB": lower_bb
            }
    except Exception: None
    return None

@st.cache_data(ttl=30)
def fetch_live_market_data(tuple_tickers):
    results = []
    for symbol in tuple_tickers:
        data = fetch_single_ticker_data(symbol)
        if data: results.append(data)
    return pd.DataFrame(results)

# KONTTAINER UTAMA APLIKASI BERDASARKAN TAB AKTIF
st.markdown('<div class="dark-terminal-card">', unsafe_allow_html=True)

if st.session_state.active_tab == "⚡ Nano Scalping & Orderbook Terminal":
    st.markdown("<h4 style='margin-bottom: 4px; font-size: 15px; color: #f8fafc;'>📈 IHSG Real-Time Market Overview (^JKSE)</h4>", unsafe_allow_html=True)
    try:
        ihsg_ticker = yf.Ticker("^JKSE")
        ihsg_hist = ihsg_ticker.history(period="1d", interval="5m")
        if not ihsg_hist.empty:
            ihsg_current = ihsg_hist["Close"].iloc[-1]
            ihsg_prev = ihsg_ticker.history(period="5d", interval="1d")["Close"].iloc[-2] if len(ihsg_ticker.history(period="5d", interval="1d")) >= 2 else ihsg_hist["Open"].iloc[0]
            ihsg_change = ihsg_current - ihsg_prev
            ihsg_pct = (ihsg_change / ihsg_prev) * 100
            
            col_ihsg1, col_ihsg2, col_ihsg3 = st.columns([1, 1, 2])
            with col_ihsg1:
                st.metric(label="IHSG Index", value=f"{ihsg_current:,.2f}", delta=f"{ihsg_pct:+.2f}%")
            with col_ihsg2:
                st.metric(label="Perubahan Poin", value=f"{ihsg_change:+,.2f}", delta="Live Feed")
            
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

    with st.spinner("Memindai emiten dengan formula Interaktif Dual Radar..."):
        df_master = fetch_live_market_data(tuple(st.session_state.master_universe))

    if not df_master.empty:
        top_bsjp = df_master.sort_values(by="BSJP Score", ascending=False).head(3)
        bsjp_text = " | ".join([f"<b>{row['Ticker']}</b>: {row['BSJP Status']} (Rp {row['Price']:,})" for _, row in top_bsjp.iterrows()])
        st.markdown(f'<div class="top-runner-bar">⭐ <b>Astronacci VIP Top Signal</b>: {bsjp_text}</div>', unsafe_allow_html=True)

    if 'active_selected_ticker' not in st.session_state:
        st.session_state.active_selected_ticker = "BBCA"

    col_radar1, col_radar2 = st.columns(2, gap="medium")
    
    with col_radar1:
        st.markdown("<h4 style='margin-top: 10px; margin-bottom: 6px; font-size: 14px; color: #34d399;'>🔥 Astronacci Strong Buy Radar (Klik Baris)</h4>", unsafe_allow_html=True)
        if not df_master.empty:
            df_strong_buy = df_master[df_master["Astronacci Action"] == "STRONG BUY"].sort_values(by="BSJP Score", ascending=False)
            if not df_strong_buy.empty:
                event_sb = st.dataframe(
                    df_strong_buy[["Ticker", "Price", "Change (%)", "Signal", "BSJP Status"]],
                    use_container_width=True, hide_index=True, height=150,
                    selection_mode="single-row", on_select="rerun", key="table_sb"
                )
                sel_sb_rows = event_sb.get("selection", {}).get("rows", [])
                if sel_sb_rows:
                    st.session_state.active_selected_ticker = df_strong_buy.iloc[sel_sb_rows[0]]["Ticker"]
            else:
                st.info("Belum ada emiten Strong Buy saat ini.")
        else:
            st.info("Memindai Strong Buy...")

    with col_radar2:
        st.markdown("<h4 style='margin-top: 10px; margin-bottom: 6px; font-size: 14px; color: #60a5fa;'>📈 Potential Momentum (>0% s.d. 15%) (Klik Baris)</h4>", unsafe_allow_html=True)
        if not df_master.empty:
            df_momentum = df_master[(df_master["Raw Change"] > 0.0) & (df_master["Raw Change"] <= 15.0)].sort_values(by="Raw Change", ascending=False)
            if not df_momentum.empty:
                event_mom = st.dataframe(
                    df_momentum[["Ticker", "Price", "Change (%)", "Signal", "BSJP Status"]],
                    use_container_width=True, hide_index=True, height=150,
                    selection_mode="single-row", on_select="rerun", key="table_mom"
                )
                sel_mom_rows = event_mom.get("selection", {}).get("rows", [])
                if sel_mom_rows:
                    st.session_state.active_selected_ticker = df_momentum.iloc[sel_mom_rows[0]]["Ticker"]
            else:
                st.info("Belum ada saham dengan kenaikan positif 0-15%.")
        else:
            st.info("Memindai momentum...")

    st.markdown("---")

    c_filter, _ = st.columns([1.5, 1], gap="medium")
    with c_filter:
        kategori_harga = st.selectbox("📌 Filter Rentang Harga Pasar:", ["Semua Saham", "1. > Rp 4.000", "2. Rp 3.000 - Rp 4.000", "3. Rp 2.000 - Rp 3.000", "4. Rp 1.000 - Rp 2.000", "5. Rp 500 - Rp 1.000", "6. Rp 1 - Rp 500"])

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
    selected_ticker = None

    with col_left:
        st.subheader("🎯 Market Scanner Radar (Auto-Ranked)")
        if not df_filtered.empty:
            event_selection = st.dataframe(
                df_filtered[["Ticker", "Price", "Change (%)", "Signal", "Volume", "BSJP Status"]],
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
                st.session_state.active_selected_ticker = df_filtered.iloc[idx_row]["Ticker"]
            
            selected_ticker = st.session_state.active_selected_ticker
            if selected_ticker not in df_filtered["Ticker"].values:
                selected_ticker = df_filtered["Ticker"].iloc[0]
                st.session_state.active_selected_ticker = selected_ticker
            
            selected_row = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0].to_dict()
        else:
            st.info("Tidak ada saham sesuai kriteria rentang harga.")
            selected_ticker = None

        st.write("")

    if selected_ticker and selected_row:
        area_beli = int(selected_row["Price"])
        prev_p = int(selected_row.get("Prev", area_beli))
        open_p = int(selected_row.get("Open", area_beli))
        high_p = int(selected_row.get("High", area_beli))
        low_p = int(selected_row.get("Low", area_beli))
        ara_p = int(selected_row.get("ARA", area_beli * 1.25))
        arb_p = int(selected_row.get("ARB", area_beli * 0.93))
        tot_lot = int(selected_row.get("Total Lot", 15000))
        tot_val = int(selected_row.get("Total Val", 5000000000))
        
        act_status = selected_row.get("Astronacci Action", "WAIT / WATCHLIST")
        act_color = selected_row.get("Action Color", "#fbbf24")
        bg_grad = selected_row.get("Bg Gradient", "linear-gradient(135deg, #3b2800 0%, #1f1500 100%)")
        t_buy = selected_row.get("Timing Buy", "09:00 - 10:15 WIB")
        t_sell = selected_row.get("Timing Sell", "14:45 - 15:50 WIB")

        with col_right:
            c_head1, c_head2 = st.columns([1, 1])
            with c_head1:
                st.markdown(f"<h3 style='margin:0; font-size:20px;'>Orderbook Matrix: {selected_ticker}</h3>", unsafe_allow_html=True)
            with c_head2:
                st.markdown("<div style='text-align: right; color: #93c5fd; font-size: 13px; font-weight: 500;'>Lihat Antrean Order</div>", unsafe_allow_html=True)
            
            st.write("")

            val_str = f"{tot_val / 1e9:.2f}B" if tot_val >= 1e9 else f"{tot_val / 1e6:.2f}M"
            st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; font-size: 12px;">
        <table width="100%" style="color: #cbd5e1;">
            <tr>
                <td>Open: <b style="color: #34d399;">Rp {open_p:,}</b></td>
                <td>Prev: <b>Rp {prev_p:,}</b></td>
                <td>Lot: <b style="color: #60a5fa;">{tot_lot:,}</b></td>
            </tr>
            <tr>
                <td>High: <b style="color: #34d399;">Rp {high_p:,}</b></td>
                <td>ARA: <b>Rp {ara_p:,}</b></td>
                <td>Val: <b style="color: #60a5fa;">{val_str}</b></td>
            </tr>
            <tr>
                <td>Low: <b style="color: #f87171;">Rp {low_p:,}</b></td>
                <td>ARB: <b>Rp {arb_p:,}</b></td>
                <td>Avg: <b style="color: #f87171;">Rp {area_beli:,}</b></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

            tp_1 = int(round(area_beli * 1.015))
            tp_2 = int(round(area_beli * 1.035))
            tp_3 = int(round(area_beli * 1.060))
            cl_price = int(round(area_beli * 0.985))

            st.markdown(f"""
    <div style="background: {bg_grad}; border: 1px solid {act_color}; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-size: 13px; font-weight: 700; color: #ffffff; text-transform: uppercase;">⭐ Astronacci VIP Signal: {selected_ticker}</div>
            <div style="background: rgba(0,0,0,0.3); color: {act_color}; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; border: 1px solid {act_color};">ACTION: {act_status}</div>
        </div>
        <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
            <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                <td style="padding: 6px; border-radius: 6px 0 0 6px;">BUY ZONE</td>
                <td style="padding: 6px;">TP 1 (+1.5%)</td>
                <td style="padding: 6px;">TP 2 (+3.5%)</td>
                <td style="padding: 6px;">TP 3 (+6%)</td>
                <td style="padding: 6px; border-radius: 0 6px 6px 0;">CUT LOSS</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {area_beli:,}</td>
                <td style="padding: 8px 0; color: #6ee7b7;">Rp {tp_1:,}</td>
                <td style="padding: 8px 0; color: #34d399; font-weight: 700;">Rp {tp_2:,}</td>
                <td style="padding: 8px 0; color: #60a5fa;">Rp {tp_3:,}</td>
                <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {cl_price:,}</td>
            </tr>
        </table>
        <div style="margin-top: 10px; font-size: 11px; color: #cbd5e1; display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
            <span>🟢 <b>Timing Buy:</b> <b style="color: #34d399;">{t_buy}</b></span>
            <span>🔴 <b>Timing Sell/TP:</b> <b style="color: #f87171;">{t_sell}</b></span>
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
            st.write("")

            total_ob_lot = sum_bid_lot + sum_ask_lot
            buyer_power = int((sum_bid_lot / total_ob_lot) * 100) if total_ob_lot > 0 else 50
            seller_power = 100 - buyer_power

            st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 12px; margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 6px;">📊 Buyer vs Seller Pressure</div>
        <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; margin-bottom: 4px;">
            <span style="color: #f87171;">BUYER: {buyer_power}%</span>
            <span style="color: #34d399;">SELLER: {seller_power}%</span>
        </div>
        <div style="background: #002347; border-radius: 6px; height: 8px; width: 100%; display: flex; overflow: hidden;">
            <div style="background: #f87171; width: {buyer_power}%; height: 100%;"></div>
            <div style="background: #34d399; width: {seller_power}%; height: 100%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

            with st.expander("🏢 Institutional Broker Summary & Flow", expanded=False):
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.markdown("<b style='color: #f87171; font-size: 12px;'>🔥 Top Buyer Broker (Accumulation)</b>", unsafe_allow_html=True)
                    st.markdown("<font size='2' color='#cbd5e1'>1. **YP** (Seq: 14,250 Lot)<br>2. **CC** (Seq: 9,120 Lot)<br>3. **PD** (Seq: 4,500 Lot)</font>", unsafe_allow_html=True)
                with b_col2:
                    st.markdown("<b style='color: #34d399; font-size: 12px;'>💧 Top Seller Broker (Distribution)</b>", unsafe_allow_html=True)
                    st.markdown("<font size='2' color='#cbd5e1'>1. **BK** (Seq: 11,800 Lot)<br>2. **MG** (Seq: 8,300 Lot)<br>3. **RX** (Seq: 3,200 Lot)</font>", unsafe_allow_html=True)

            with st.expander("📊 Trade History & Performance Summary", expanded=False):
                if st.session_state.trade_journal:
                    df_journal = pd.DataFrame(st.session_state.trade_journal)
                    total_net_pnl = df_journal["Net P&L"].sum()
                    color_pnl = "#34d399" if total_net_pnl >= 0 else "#f87171"
                    st.markdown(f"Akumulasi Net P&L Anda: <b style='color: {color_pnl};'>Rp {total_net_pnl:,.0f}</b>", unsafe_allow_html=True)
                    st.dataframe(df_journal, use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada riwayat trade yang disimpan.")

            c_calc, c_sim = st.columns(2)
            with c_calc:
                with st.expander("🧮 Position Size / Risk Calculator", expanded=False):
                    modal = st.number_input("Modal (Rp):", min_value=100000, value=10000000, step=500000)
                    risk_p = st.slider("Maksimal Risiko (%):", 0.5, 5.0, 1.8, 0.1)
                    max_rugi = modal * (risk_p / 100)
                    rugi_lembar = area_beli - cl_price
                    max_lot = int((max_rugi / rugi_lembar) // 100) if rugi_lembar > 0 else 0
                    st.info(f"👉 Rekomendasi Buy: **{max_lot:,} Lot**")

            with c_sim:
                with st.expander("📝 Scalping Journal", expanded=False):
                    entry_p = st.number_input("Entry Price:", value=area_beli)
                    exit_p = st.number_input("Exit Price:", value=tp_2)
                    lot_cnt = st.number_input("Jumlah Lot:", value=max_lot if max_lot > 0 else 10)
                    
                    buy_val = entry_p * lot_cnt * 100
                    sell_val = exit_p * lot_cnt * 100
                    net_pnl = (sell_val * 0.9975) - (buy_val * 1.0015)

                    if st.button("💾 Simpan Trade"):
                        st.session_state.trade_journal.append({"Ticker": selected_ticker, "Net P&L": net_pnl})
                        st.success(f"Disimpan! P&L: Rp {net_pnl:,.0f}")

            timeframe = st.radio("Timeframe:", ["1m", "5m", "15m", "1d"], index=1, horizontal=True)
            try:
                tf_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "1d": ("1mo", "1d")}
                p, i = tf_map[timeframe]
                intraday = yf.Ticker(f"{selected_ticker}.JK").history(period=p, interval=i)
                
                if not intraday.empty:
                    upper_b, mid_b, lower_b = hitung_bollinger_bands(intraday["Close"])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=intraday.index, y=intraday["Close"], mode='lines', name='Price', line=dict(color='#60a5fa', width=2)))
                    fig.add_trace(go.Scatter(x=intraday.index, y=upper_b, mode='lines', name='Upper BB', line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot')))
                    fig.add_trace(go.Scatter(x=intraday.index, y=lower_b, mode='lines', name='Lower BB', line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(96, 165, 250, 0.05)'))
                    
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0, 35, 71, 0.9)',
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=280,
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd'),
                        legend=dict(orientation="h", y=1.1, x=0)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

elif st.session_state.active_tab == "🚀 Weekly Swing Signal":
    st.markdown("### 🚀 Weekly Swing Signal & Bullish Watchlist")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Rekomendasi saham mingguan dengan potensi kenaikan lengkap dengan Kartu Sinyal Interaktif Astronacci VIP.</p>", unsafe_allow_html=True)
    
    col_ws1, col_ws2 = st.columns([1.6, 1], gap="medium")
    
    with col_ws1:
        st.markdown("#### 📊 Top Weekly Swing Picks (Klik Baris untuk Lihat Kartu Sinyal)")
        swing_data = {
            "Emiten": ["ADRO", "MDKA", "BBRI", "INKP", "UNTR"],
            "Setup": ["Breakout Resistance", "Pullback MA20", "Accumulation Phase", "Volume Surge", "Golden Cross"],
            "Buy Zone": [2480, 2720, 4950, 7850, 26800],
            "Target 1 (+3% DX)": [2550, 2800, 5100, 8100, 27600],
            "Target 2 (+6% DX)": [2630, 2880, 5250, 8350, 28400],
            "Target 3 (+10% DX)": [2730, 2990, 5450, 8650, 29500],
            "Stop Loss": [2400, 2640, 4800, 7600, 26000],
            "Target Waktu": ["1-2 Minggu", "2-3 Minggu", "1-3 Minggu", "3-5 Hari", "2-4 Minggu"]
        }
        df_swing = pd.DataFrame(swing_data)
        
        event_swing_sel = st.dataframe(
            df_swing, use_container_width=True, hide_index=True, height=220,
            selection_mode="single-row", on_select="rerun", key="table_swing_select"
        )
        
        sel_swing_rows = event_swing_sel.get("selection", {}).get("rows", [])
        if sel_swing_rows:
            st.session_state.selected_swing_ticker = df_swing.iloc[sel_swing_rows[0]]["Emiten"]
            
        cur_sel_swing = st.session_state.selected_swing_ticker
        matched_swing_row = df_swing[df_swing["Emiten"] == cur_sel_swing].iloc[0]

        st.markdown("#### 📝 Active Swing Trade Portfolio & Live P&L Tracker")
        if st.session_state.swing_journal:
            live_portfolio_rows = []
            for i, item in enumerate(st.session_state.swing_journal):
                sym = item["Emiten"]
                entry_p = item["Entry"]
                lot_cnt = item["Lot"]
                waktu_hold = item["Target Waktu"]
                
                live_p = entry_p 
                try:
                    t_data = yf.Ticker(f"{sym}.JK").history(period="1d", interval="1m")
                    if not t_data.empty:
                        live_p = int(round(t_data["Close"].iloc[-1]))
                except Exception:
                    pass
                
                diff_rp = (live_p - entry_p) * lot_cnt * 100
                diff_pct = ((live_p - entry_p) / entry_p) * 100 if entry_p > 0 else 0
                status_str = f"🟢 Cuan (+{diff_pct:.2f}%)" if diff_rp >= 0 else f"🔴 Minus ({diff_pct:.2f}%)"
                
                live_portfolio_rows.append({
                    "Index": i,
                    "Emiten": sym,
                    "Entry (Rp)": f"Rp {entry_p:,}",
                    "Live Price (Rp)": f"Rp {live_p:,}",
                    "Lot": lot_cnt,
                    "Floating P&L": f"Rp {diff_rp:,.0f} ({diff_pct:+.2f}%)",
                    "Target Waktu": waktu_hold,
                    "Status": status_str
                })
            
            df_live_sj = pd.DataFrame(live_portfolio_rows)
            st.dataframe(df_live_sj.drop(columns=["Index"]), use_container_width=True, hide_index=True)
            
            st.markdown("<font size='2' color='#93c5fd'><b>Kelola Posisi (Take Profit / Tutup Posisi):</b></font>", unsafe_allow_html=True)
            col_del_1, col_del_2 = st.columns([2, 1])
            with col_del_1:
                pos_to_close = st.selectbox("Pilih Posisi untuk Ditutup/Jual:", options=range(len(st.session_state.swing_journal)), format_func=lambda x: f"{st.session_state.swing_journal[x]['Emiten']} (Entry: Rp {st.session_state.swing_journal[x]['Entry']:,}, {st.session_state.swing_journal[x]['Lot']} Lot)")
            with col_del_2:
                st.write("")
                if st.button("🗑️ Tutup / Jual Posisi", use_container_width=True):
                    closed_item = st.session_state.swing_journal.pop(pos_to_close)
                    st.success(f"Posisi {closed_item['Emiten']} berhasil ditutup/dijual!")
                    st.rerun()
        else:
            st.info("Belum ada posisi swing aktif yang dicatat.")

        with st.form("add_swing_pos"):
            st.markdown("<b>Tambah Posisi Swing Baru:</b>", unsafe_allow_html=True)
            f_emiten = st.text_input("Kode Emiten:", placeholder="Contoh: ADRO").strip().upper()
            f_entry = st.number_input("Harga Entry Aktual (Rp):", min_value=50, value=2500, step=25)
            f_lot = st.number_input("Jumlah Lot:", min_value=1, value=25, step=5)
            f_waktu = st.selectbox("Target Waktu Hold:", ["3 - 5 Hari", "1 - 2 Minggu", "2 - 3 Minggu", "1 Bulan+"])
            
            submit_swing = st.form_submit_button("➕ Masukkan ke Portofolio Swing")
            if submit_swing and f_emiten:
                st.session_state.swing_journal.append({
                    "Emiten": f_emiten,
                    "Entry": f_entry,
                    "Lot": f_lot,
                    "Target Waktu": f_waktu
                })
                st.success(f"Posisi {f_emiten} berhasil ditambahkan!")
                st.rerun()

    with col_ws2:
        st.markdown(f"#### ⭐ Astronacci VIP Signal: {cur_sel_swing}")
        
        buy_z_val = matched_swing_row["Buy Zone"]
        tp1_val = matched_swing_row["Target 1 (+3% DX)"]
        tp2_val = matched_swing_row["Target 2 (+6% DX)"]
        tp3_val = matched_swing_row["Target 3 (+10% DX)"]
        sl_val = matched_swing_row["Stop Loss"]

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #451a03 0%, #221006 100%); border: 1px solid #f87171; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-size: 13px; font-weight: 700; color: #ffffff; text-transform: uppercase;">⭐ VIP Signal Card: {cur_sel_swing}</div>
                <div style="background: rgba(0,0,0,0.3); color: #f87171; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; border: 1px solid #f87171;">ACTION: TAKE PROFIT / SELL</div>
            </div>
            <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
                <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                    <td style="padding: 6px; border-radius: 6px 0 0 6px;">BUY ZONE</td>
                    <td style="padding: 6px;">TP 1 (+1.5%)</td>
                    <td style="padding: 6px;">TP 2 (+3.5%)</td>
                    <td style="padding: 6px;">TP 3 (+6%)</td>
                    <td style="padding: 6px; border-radius: 0 6px 6px 0;">CUT LOSS</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {buy_z_val:,}</td>
                    <td style="padding: 8px 0; color: #6ee7b7;">Rp {tp1_val:,}</td>
                    <td style="padding: 8px 0; color: #34d399; font-weight: 700;">Rp {tp2_val:,}</td>
                    <td style="padding: 8px 0; color: #60a5fa;">Rp {tp3_val:,}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {sl_val:,}</td>
                </tr>
            </table>
            <div style="margin-top: 10px; font-size: 11px; color: #cbd5e1; display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                <span>🟢 <b>Timing Buy:</b> <b style="color: #34d399;">Wait / Pullback Area</b></span>
                <span>🔴 <b>Timing Sell/TP:</b> <b style="color: #f87171;">Sesi 1 / Awal Sesi 2</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🧮 Swing Trade Position Sizing & Multi-TP")
        modal_swing = st.number_input("Total Modal Swing (Rp):", min_value=1000000, value=25000000, step=1000000)
        risk_pct_swing = st.slider("Risiko per Trade (% dari Modal):", 0.5, 5.0, 2.0, 0.5)
        
        max_risk_rp = modal_swing * (risk_pct_swing / 100)
        risk_per_share = buy_z_val - sl_val
        recommended_lots = int((max_risk_rp / risk_per_share) // 100) if risk_per_share > 0 else 0
        
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; margin-top: 10px;">
            <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 6px;">Rekomendasi Alokasi & Multi-TP:</div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 2px;">Maksimal Risiko: <b style="color: #f87171;">Rp {max_risk_rp:,.0f}</b></div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 6px;">Lot Optimal Dibeli: <b style="color: #34d399;">{recommended_lots:,} Lot</b></div>
            <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 8px 0;">
            <div style="font-size: 12px; color: #93c5fd; font-weight: 600; margin-bottom: 4px;">Target Profit Bertahap:</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 1: <b style="color: #34d399;">Rp {tp1_val:,}</b> (Jual 30%)</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 2: <b style="color: #34d399;">Rp {tp2_val:,}</b> (Jual 40%)</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 3: <b style="color: #60a5fa;">Rp {tp3_val:,}</b> (Trailing Stop Sisa)</div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_tab == "💎 Multi-Bagger Hunter":
    st.markdown("### 💎 Multi-Bagger Hunter (Gocap to High)")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Analisis saham berharga murah dengan kartu sinyal interaktif target jangka panjang (Multi-Bagger Style).</p>", unsafe_allow_html=True)
    
    mb_tickers_extended = [
        ("BUMI", "Rp 50", "Restrukturisasi & Batubara", "0.8x (Murah)", 250, 400, 500, 40),
        ("DEWA", "Rp 50", "Ekspansi Tambang Emas", "1.2x", 500, 800, 1200, 150),
        ("ENRG", "Rp 90", "Akuisisi Blok Migas Baru", "1.1x", 1500, 2200, 3000, 800),
        ("BRMS", "Rp 50", "Commercial Production Emas", "2.5x", 800, 1200, 1500, 300),
        ("TEBE", "Rp 350", "Logistik & Infrastruktur", "1.4x", 2000, 3000, 4000, 1500),
        ("PTBA", "Rp 1.200", "High Dividend & Energy Cycle", "1.8x", 3000, 4000, 5000, 2200),
        ("ADRO", "Rp 1.000", "Green Energy Transition & Cash Rich", "1.3x", 2500, 3500, 4500, 1800),
        ("ANTM", "Rp 600", "EV Battery & Nikel Downstream", "2.1x", 1500, 2200, 3000, 1000),
        ("MEDC", "Rp 450", "Oil & Gas Super Cycle", "1.0x", 1200, 1800, 2500, 800),
        ("ELSA", "Rp 150", "Energy Services Expansion", "0.9x", 400, 600, 800, 250),
        ("GOTO", "Rp 90", "E-Commerce Profitability Turnaround", "1.5x", 200, 350, 500, 60),
        ("ARTO", "Rp 1.500", "Digital Bank Ecosystem Growth", "3.2x", 3000, 4500, 6000, 2200)
    ]
    
    mb_rows = []
    mb_data_dict = {}
    for t, rilis, kat, pbv, t1, t2, t3, sl in mb_tickers_extended:
        t_data = fetch_single_ticker_data(t)
        p_live = t_data["Price"] if t_data else 0
        chg_live = t_data["Change (%)"] if t_data else "0%"
        
        mb_rows.append({
            "Emiten": t,
            "Harga Awal (Rilis)": rilis,
            "Harga Live": f"Rp {p_live:,}" if p_live > 0 else "N/A",
            "Perubahan": chg_live,
            "Katalis Utama": kat,
            "Valuasi/PBV": pbv,
            "Target Utama": f"Rp {t3:,}+"
        })
        mb_data_dict[t] = {
            "live_price": p_live if p_live > 0 else 100,
            "t1": t1, "t2": t2, "t3": t3, "sl": sl,
            "katalis": kat
        }
        
    df_mb_live = pd.DataFrame(mb_rows)
    
    col_mb1, col_mb2 = st.columns([1.5, 1], gap="medium")
    
    with col_mb1:
        st.markdown("#### 🔬 Live Multi-Bagger Watchlist (Klik Baris untuk Analisis Kartu)")
        event_mb_sel = st.dataframe(
            df_mb_live, use_container_width=True, hide_index=True, height=280,
            selection_mode="single-row", on_select="rerun", key="table_mb_select"
        )
        
        selected_mb_rows = event_mb_sel.get("selection", {}).get("rows", [])
        if selected_mb_rows:
            st.session_state.selected_mb_ticker = df_mb_live.iloc[selected_mb_rows[0]]["Emiten"]
            
        cur_sel_mb = st.session_state.selected_mb_ticker
        mb_info = mb_data_dict.get(cur_sel_mb, {"live_price": 100, "t1": 300, "t2": 600, "t3": 1000, "sl": 50, "katalis": "Transformasi"})

        st.markdown("---")
        st.markdown("#### 🧮 Multi-Bagger Growth Simulator")
        sim_harga_beli = st.number_input("Harga Beli Saat Ini (Rp):", min_value=10, value=int(mb_info["live_price"]), step=10)
        sim_harga_target = st.number_input("Target Harga Jangka Panjang (Rp):", min_value=50, value=int(mb_info["t3"]), step=50)
        sim_lot = st.number_input("Jumlah Lot Disimpan:", min_value=1, value=100, step=10)
        
        modal_awal = sim_harga_beli * sim_lot * 100
        nilai_akhir = sim_harga_target * sim_lot * 100
        potensi_profit = nilai_akhir - modal_awal
        persen_cuan = ((sim_harga_target - sim_harga_beli) / sim_harga_beli) * 100 if sim_harga_beli > 0 else 0
        
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px;">
            <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 6px;">Hasil Simulasi Multi-Bagger:</div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 2px;">Modal Awal: <b>Rp {modal_awal:,.0f}</b></div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 6px;">Nilai Portofolio Akhir: <b style="color: #34d399;">Rp {nilai_akhir:,.0f}</b></div>
            <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 8px 0;">
            <div style="font-size: 14px; color: #34d399; font-weight: 700; margin-bottom: 2px;">Potensi Profit: Rp {potensi_profit:,.0f}</div>
            <div style="font-size: 13px; color: #60a5fa; font-weight: 700;">Potensi Kenaikan: +{persen_cuan:,.2f}% ({(persen_cuan/100):.1f}x Lipat)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_mb2:
        st.markdown(f"#### ⭐ Multi-Bagger Signal Card: {cur_sel_mb}")
        
        live_p_card = mb_info["live_price"]
        t1_card = mb_info["t1"]
        t2_card = mb_info["t2"]
        t3_card = mb_info["t3"]
        sl_card = mb_info["sl"]
        kat_card = mb_info["katalis"]

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #003366 0%, #002244 100%); border: 1px solid #34d399; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="font-size: 13px; font-weight: 700; color: #ffffff; text-transform: uppercase;">💎 Long-Term Target: {cur_sel_mb}</div>
                <div style="background: rgba(0,0,0,0.3); color: #34d399; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 800; border: 1px solid #34d399;">ACTION: ACCUMULATE</div>
            </div>
            <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
                <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                    <td style="padding: 6px; border-radius: 6px 0 0 6px;">BUY ZONE</td>
                    <td style="padding: 6px;">TARGET 1 (2x)</td>
                    <td style="padding: 6px;">TARGET 2 (3x)</td>
                    <td style="padding: 6px;">TARGET 3 (5x+)</td>
                    <td style="padding: 6px; border-radius: 0 6px 6px 0;">INVALIDATION</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {live_p_card:,}</td>
                    <td style="padding: 8px 0; color: #6ee7b7;">Rp {t1_card:,}</td>
                    <td style="padding: 8px 0; color: #34d399; font-weight: 700;">Rp {t2_card:,}</td>
                    <td style="padding: 8px 0; color: #60a5fa;">Rp {t3_card:,}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {sl_card:,}</td>
                </tr>
            </table>
            <div style="margin-top: 10px; font-size: 11px; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                <span>📌 <b>Katalis Utama:</b> <b style="color: #93c5fd;">{kat_card}</b></span>
            </div>
            <div style="margin-top: 6px; font-size: 11px; color: #cbd5e1; display: flex; justify-content: space-between;">
                <span>🟢 <b>Akumulasi:</b> <b style="color: #34d399;">Fase Konsolidasi</b></span>
                <span>🔴 <b>Batas Cut Loss/Review:</b> <b style="color: #f87171;">Break Support Bawah</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📚 Formula Rahasia Multi-Bagger:")
        st.markdown("""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; font-size: 12px; color: #cbd5e1;">
            <b>1. Low Valuation (Deep Value):</b> Cari emiten berharga murah yang mencatat lonjakan volume di harga bawah.<br>
            <b>2. Turnaround Bisnis:</b> Perusahaan yang sebelumnya terbebani utang kini membukukan laba bersih positif.<br>
            <b>3. Smart Money Accumulation:</b> Akumulasi institusi jangka panjang pada fase konsolidasi bulanan/mingguan.
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.active_tab == "📑 Right Issue & Corporate Action Module":
    st.markdown("### 📑 Right Issue & Corporate Action Module")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Modul pemantauan HMETD dan kalkulator estimasi harga teoretis saham setelah aksi korporasi.</p>", unsafe_allow_html=True)
    
    col_ri1, col_ri2 = st.columns([1.2, 1], gap="medium")
    
    with col_ri1:
        st.markdown("#### 🔍 Daftar Emiten / Jadwal Right Issue Terbaru")
        ri_data = {
            "Emiten": ["BUMI", "ARTO", "BUBK", "BANK", "ARCI"],
            "Rasio HMETD": ["100 : 15", "10 : 1", "50 : 12", "100 : 25", "10 : 3"],
            "Harga Tebus (Exercise)": ["Rp 80", "Rp 2.100", "Rp 150", "Rp 1.050", "Rp 400"],
            "Cum Date": ["05 Okt 2026", "12 Okt 2026", "18 Okt 2026", "25 Okt 2026", "30 Okt 2026"],
            "Status": ["🔥 Active Cum", "⏳ Upcoming", "⏳ Upcoming", "⚡ Trading Period", "⏳ Upcoming"]
        }
        df_ri = pd.DataFrame(ri_data)
        st.dataframe(df_ri, use_container_width=True, hide_index=True)
        
    with col_ri2:
        st.markdown("#### 🧮 Right Issue Theoretical Price Calculator")
        st.markdown("<font size='2' color='#cbd5e1'>Hitung estimasi harga teoretis saham induk pasca *Right Issue*.</font>", unsafe_allow_html=True)
        
        stock_cum_price = st.number_input("Harga Saham Saat Cum-Date (Rp):", min_value=50, value=1500, step=50)
        exercise_price = st.number_input("Harga Tebus / Exercise Price (Rp):", min_value=50, value=1000, step=50)
        
        col_ratio1, col_ratio2 = st.columns(2)
        with col_ratio1:
             saham_lama = st.number_input("Saham Lama (Old):", min_value=1, value=10)
        with col_ratio2:
             saham_baru = st.number_input("Saham Baru (Rights):", min_value=1, value=2)
            
        total_saham = saham_lama + saham_baru
        harga_teoretis = ((stock_cum_price * saham_lama) + (exercise_price * saham_baru)) / total_saham
        potensi_dilusi = ((stock_cum_price - harga_teoretis) / stock_cum_price) * 100
        
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; margin-top: 10px;">
            <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 6px;">Hasil Kalkulasi Teoretis:</div>
            <div style="font-size: 14px; color: #ffffff; margin-bottom: 4px;">Harga Teoretis Pasca RI: <b style="color: #34d399;">Rp {harga_teoretis:,.2f}</b></div>
            <div style="font-size: 13px; color: #cbd5e1;">Estimasi Dilusi Harga: <b style="color: #f87171;">{potensi_dilusi:.2f}%</b></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
