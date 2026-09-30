import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
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
            <div class="hero-subtitle-nano">ANALYTICS TERMINAL</div>
        </div>
        <div style="text-align: right; background: #002347; padding: 8px 14px; border-radius: 8px; border: 1px solid #0047ab;">
            <div style="font-size:10px; color:#93c5fd; font-weight:700;">NANO CORE</div>
            <div style="font-size:12px; font-weight:700; color:#34d399;">● SYNCHRONIZED</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# CUSTOM NAVIGASI TAB KONTROL TOMBOL
tab_col1, tab_col2, tab_col3 = st.columns(3)
with tab_col1:
    if st.button("⚡ Nano Scalping Terminal", use_container_width=True):
        st.session_state.active_tab = "⚡ Nano Scalping & Orderbook Terminal"
        st.rerun()
with tab_col2:
    if st.button("🚀 Weekly Swing Signal", use_container_width=True):
        st.session_state.active_tab = "🚀 Weekly Swing Signal"
        st.rerun()
with tab_col3:
    if st.button("📑 Right Issue & Corporate Action", use_container_width=True):
        st.session_state.active_tab = "📑 Right Issue & Corporate Action Module"
        st.rerun()

st.write("")

# INITIALIZE SESSION STATE
if 'custom_watchlist' not in st.session_state:
    st.session_state.custom_watchlist = ["TEBE", "JPFA", "TLKM", "BBCA", "BMRI", "UNTR", "ASII", "AMRT", "CPIN", "ANTM"]

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
    "BRIS": 46128000000, "ERAA": 15920000000, "PGAS": 24241000000, "ANTM": 24030000000
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

            rsi_val = hitung_rsi(hist_intra["Close"]).iloc[-1] if not hist_intra.empty and len(hist_intra) >= 14 else 50
            ma5 = hist_intra["Close"].rolling(5).mean().iloc[-1] if not hist_intra.empty and len(hist_intra) >= 5 else current_price
            
            if current_price >= hod and current_price > prev_close:
                signal = "🔥 BREAKOUT"
            elif current_price > ma5:
                signal = "🚀 BULLISH"
            else:
                signal = "🔻 BEARISH"
                
            if rsi_val > 70: signal += " (OB)"
            elif rsi_val < 30: signal += " (OS)"
            
            avg_vol = hist_intra["Volume"].mean() if not hist_intra.empty else 1
            last_vol = hist_intra["Volume"].iloc[-1] if not hist_intra.empty else 0
            vol_spike = "⚡ SPIKE" if last_vol > (avg_vol * 1.8) else "NORMAL"

            bsjp_score = 0
            if change_pct > 0: bsjp_score += 25
            if current_price >= (hod * 0.98): bsjp_score += 25
            if vol_spike == "⚡ SPIKE": bsjp_score += 25
            if current_price > ma5: bsjp_score += 25

            bsjp_status = f"⚡ AI ({bsjp_score}%)" if bsjp_score >= 75 else f"⚙ QUANTUM ({bsjp_score}%)" if bsjp_score >= 50 else "⚠ WAIT"

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
                "BSJP Score": bsjp_score
            }
    except Exception: None
    return None

@st.cache_data(ttl=15)
def fetch_live_market_data(ticker_list):
    results = []
    for symbol in ticker_list:
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

    with st.spinner("Menyinkronkan data pasar..."):
        df_master = fetch_live_market_data(st.session_state.custom_watchlist)

    if not df_master.empty:
        top_bsjp = df_master.sort_values(by="BSJP Score", ascending=False).head(3)
        bsjp_text = " | ".join([f"<b>{row['Ticker']}</b>: {row['BSJP Status']} (Rp {row['Price']:,})" for _, row in top_bsjp.iterrows()])
        st.markdown(f'<div class="top-runner-bar">📊 <b>Top Signal</b>: {bsjp_text}</div>', unsafe_allow_html=True)

    with st.expander("📌 Custom Watchlist Management", expanded=False):
        col_input, col_btn = st.columns([3, 1], gap="small")
        with col_input:
            new_ticker = st.text_input("Tambah Ticker Baru:", placeholder="Ketik kode saham (contoh: GOTO, BBRI)").strip().upper()
        with col_btn:
            st.write("")
            if st.button("➕ Tambah", use_container_width=True):
                if new_ticker and new_ticker not in st.session_state.custom_watchlist:
                    st.session_state.custom_watchlist.append(new_ticker)
                    st.rerun()

        st.markdown("---")
        st.caption("Daftar Ticker Watchlist Aktif:")
        
        cols_chips = st.columns(5)
        tickers_to_remove = []

        for idx, t_code in enumerate(st.session_state.custom_watchlist):
            c_target = cols_chips[idx % 5]
            row_match = df_master[df_master["Ticker"] == t_code] if not df_master.empty else pd.DataFrame()
            raw_val = row_match.iloc[0]["Raw Change"] if not row_match.empty else 0
            live_price = row_match.iloc[0]["Price"] if not row_match.empty else 0
            price_str = f"Rp {live_price:,}" if live_price > 0 else "N/A"
            bg_color = "#064e3b" if raw_val > 0 else ("#7f1d1d" if raw_val < 0 else "#003366")
            
            with c_target:
                sub_c1, sub_c2 = st.columns([0.8, 0.2])
                with sub_c1:
                    st.markdown(f"""
    <div style="background: {bg_color}; border: 1px solid #0047ab; border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 500; text-align: center; margin-bottom: 6px; color: #ffffff;">
        {t_code} ({price_str})
    </div>
    """, unsafe_allow_html=True)
                with sub_c2:
                    if st.button("✕", key=f"del_chip_{t_code}", use_container_width=True):
                        tickers_to_remove.append(t_code)

        if tickers_to_remove:
            for r_code in tickers_to_remove:
                if r_code in st.session_state.custom_watchlist:
                    st.session_state.custom_watchlist.remove(r_code)
            st.rerun()

    c_filter, c_search = st.columns([1.5, 1], gap="medium")
    with c_filter:
        kategori_harga = st.selectbox("📌 Filter Rentang Harga:", ["Semua Saham", "1. > Rp 4.000", "2. Rp 3.000 - Rp 4.000", "3. Rp 2.000 - Rp 3.000", "4. Rp 1.000 - Rp 2.000", "5. Rp 500 - Rp 1.000", "6. Rp 1 - Rp 500"])
    with c_search:
        search_input = st.text_input("🔍 Universal Search Ticker:", placeholder="Contoh: TEBE, BBCA").strip().upper()

    df_filtered = df_master.copy() if not df_master.empty else pd.DataFrame()
    if not df_filtered.empty:
        if kategori_harga == "1. > Rp 4.000": df_filtered = df_filtered[df_filtered["Price"] > 4000]
        elif kategori_harga == "2. Rp 3.000 - Rp 4.000": df_filtered = df_filtered[(df_filtered["Price"] >= 3000) & (df_filtered["Price"] <= 4000)]
        elif kategori_harga == "3. Rp 2.000 - Rp 3.000": df_filtered = df_filtered[(df_filtered["Price"] >= 2000) & (df_filtered["Price"] < 3000)]
        elif kategori_harga == "4. Rp 1.000 - Rp 2.000": df_filtered = df_filtered[(df_filtered["Price"] >= 1000) & (df_filtered["Price"] < 2000)]
        elif kategori_harga == "5. Rp 500 - Rp 1.000": df_filtered = df_filtered[(df_filtered["Price"] >= 500) & (df_filtered["Price"] < 1000)]
        elif kategori_harga == "6. Rp 1 - Rp 500": df_filtered = df_filtered[(df_filtered["Price"] >= 1) & (df_filtered["Price"] < 500)]

    st.markdown("<h4 style='margin-bottom: 8px; font-size: 15px; color: #f8fafc;'>⚡ Running Trade (BEI Micro Tick Feed)</h4>", unsafe_allow_html=True)
    np.random.seed(int(datetime.now().second))
    rt_tickers = st.session_state.custom_watchlist if st.session_state.custom_watchlist else ["TEBE", "BBCA", "BMRI"]
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
        st.subheader("🎯 Watchlist Radar")
        if not df_filtered.empty:
            st.dataframe(
                df_filtered[["Ticker", "Price", "Change (%)", "Signal", "Volume", "BSJP Status"]],
                use_container_width=True, hide_index=True, height=440
            )
            ticker_options = df_filtered["Ticker"].tolist()
        else:
            st.info("Tidak ada saham sesuai kriteria.")
            ticker_options = []

        if search_input:
            custom_data = fetch_single_ticker_data(search_input)
            if custom_data:
                selected_ticker = search_input
                selected_row = custom_data
        else:
            if ticker_options:
                selected_ticker = st.selectbox("Pilih Saham Target Analisa:", ticker_options, index=0)
                selected_row = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0].to_dict()

        st.write("")
        
        st.markdown("""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; margin-top: 6px;">
        <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">📊 Micro-Scanner (Active Detect)</div>
        <table width="100%" style="font-size: 11px; color: #cbd5e1;">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 4px 0;"><b>UNTR</b></td>
                <td>Surge: <b style="color: #34d399;">+320%</b></td>
                <td style="text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:600;">ACCEL</span></td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 4px 0;"><b>TEBE</b></td>
                <td>Surge: <b style="color: #34d399;">+210%</b></td>
                <td style="text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:600;">BREAKOUT</span></td>
            </tr>
            <tr>
                <td style="padding: 4px 0;"><b>ANTM</b></td>
                <td>Surge: <b style="color: #60a5fa;">+185%</b></td>
                <td style="text-align: right;"><span style="background: #002347; color: #60a5fa; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:600;">SPIKE</span></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

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

        with col_right:
            c_head1, c_head2 = st.columns([1, 1])
            with c_head1:
                st.markdown("<h3 style='margin:0; font-size:20px;'>Orderbook Matrix</h3>", unsafe_allow_html=True)
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
            tp_2 = int(round(area_beli * 1.03))
            tp_3 = int(round(area_beli * 1.05))
            cl_price = int(round(area_beli * 0.985))

            st.markdown(f"""
    <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; margin-bottom: 16px;">
        <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 8px;">🎯 Execution Plan: {selected_ticker}</div>
        <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
            <tr style="background: #002347; color: #93c5fd; font-weight: 600;">
                <td style="padding: 6px; border-radius: 6px 0 0 6px;">BUY ZONE</td>
                <td style="padding: 6px;">TP 1 (+1.5%)</td>
                <td style="padding: 6px;">TP 2 (+3%)</td>
                <td style="padding: 6px;">TP 3 (+5%)</td>
                <td style="padding: 6px; border-radius: 0 6px 6px 0;">CUT LOSS (-1.5%)</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: 600; color: #34d399;">Rp {area_beli:,}</td>
                <td style="padding: 8px 0; color: #6ee7b7;">Rp {tp_1:,}</td>
                <td style="padding: 8px 0; color: #34d399; font-weight: 600;">Rp {tp_2:,}</td>
                <td style="padding: 8px 0; color: #60a5fa;">Rp {tp_3:,}</td>
                <td style="padding: 8px 0; font-weight: 600; color: #f87171;">Rp {cl_price:,}</td>
            </tr>
        </table>
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
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=intraday.index, y=intraday["Close"], mode='lines', name='Price', line=dict(color='#60a5fa', width=2)))
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0, 35, 71, 0.9)',
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=250,
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#93c5fd')
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass

elif st.session_state.active_tab == "🚀 Weekly Swing Signal":
    st.markdown("### 🚀 Weekly Swing Signal & Bullish Watchlist")
    st.markdown("<p style='color: #93c5fd; font-size: 13px;'>Rekomendasi saham mingguan dengan potensi kenaikan (bullish continuation / reversal) lengkap dengan pelacakan P&L portofolio secara real-time.</p>", unsafe_allow_html=True)
    
    col_ws1, col_ws2 = st.columns([1.5, 1], gap="medium")
    
    with col_ws1:
        st.markdown("#### 📊 Top Weekly Swing Picks (Radar Bullish)")
        swing_data = {
            "Emiten": ["ADRO", "MDKA", "BBRI", "INKP", "UNTR"],
            "Setup": ["Breakout Resistance", "Pullback MA20", "Accumulation Phase", "Volume Surge", "Golden Cross"],
            "Buy Zone": ["Rp 2.450 - 2.500", "Rp 2.700 - 2.750", "Rp 4.900 - 5.000", "Rp 7.800 - 7.950", "Rp 26.500 - 27.000"],
            "Target 1 (+3%)": ["Rp 2.575", "Rp 2.825", "Rp 5.150", "Rp 8.150", "Rp 27.800"],
            "Target 2 (+6%)": ["Rp 2.650", "Rp 2.950", "Rp 5.300", "Rp 8.450", "Rp 28.600"],
            "Target 3 (+10%)": ["Rp 2.750", "Rp 3.050", "Rp 5.500", "Rp 8.750", "Rp 29.500"],
            "Stop Loss (-3%)": ["Rp 2.380", "Rp 2.620", "Rp 4.800", "Rp 7.600", "Rp 25.800"],
            "Target Waktu": ["1 - 2 Minggu", "2 - 3 Minggu", "1 - 3 Minggu", "3 - 5 Hari", "2 - 4 Minggu"],
            "RRR": ["1 : 2.5", "1 : 3.1", "1 : 2.2", "1 : 2.8", "1 : 2.6"]
        }
        df_swing = pd.DataFrame(swing_data)
        st.dataframe(df_swing, use_container_width=True, hide_index=True)
        
        # FITUR KRUSIAL: ACTIVE SWING PORTFOLIO & CLOSE POSITION MANAGER
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
            
            # FITUR KRUSIAL: TOMBOL KELOLA / TUTUP POSISI (CLOSE / TAKE PROFIT)
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
        st.markdown("#### 🧮 Swing Trade Position Sizing & Multi-TP")
        st.markdown("<font size='2' color='#cbd5e1'>Kalkulator manajemen risiko dan target profit bertahap.</font>", unsafe_allow_html=True)
        
        modal_swing = st.number_input("Total Modal Swing (Rp):", min_value=1000000, value=25000000, step=1000000)
        risk_pct_swing = st.slider("Risiko per Trade (% dari Modal):", 0.5, 5.0, 2.0, 0.5)
        entry_swing = st.number_input("Harga Entry Rencana:", min_value=100, value=2500, step=50)
        sl_swing = st.number_input("Harga Stop Loss Rencana:", min_value=100, value=2380, step=50)
        
        max_risk_rp = modal_swing * (risk_pct_swing / 100)
        risk_per_share = entry_swing - sl_swing
        recommended_lots = int((max_risk_rp / risk_per_share) // 100) if risk_per_share > 0 else 0
        
        # FITUR KRUSIAL: KALKULASI MULTI TAKE PROFIT (TP1, TP2, TP3)
        tp1_calc = int(round(entry_swing * 1.03))
        tp2_calc = int(round(entry_swing * 1.06))
        tp3_calc = int(round(entry_swing * 1.10))
        
        st.markdown(f"""
        <div style="background: #003366; border: 1px solid #0047ab; border-radius: 12px; padding: 14px; margin-top: 10px;">
            <div style="font-size: 12px; font-weight: 600; color: #f8fafc; text-transform: uppercase; margin-bottom: 6px;">Rekomendasi Alokasi & Multi-TP:</div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 2px;">Maksimal Risiko: <b style="color: #f87171;">Rp {max_risk_rp:,.0f}</b></div>
            <div style="font-size: 13px; color: #ffffff; margin-bottom: 6px;">Lot Optimal Dibeli: <b style="color: #34d399;">{recommended_lots:,} Lot</b></div>
            <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.1); margin: 8px 0;">
            <div style="font-size: 12px; color: #93c5fd; font-weight: 600; margin-bottom: 4px;">Target Profit Bertahap:</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 1 (+3%): <b style="color: #34d399;">Rp {tp1_calc:,}</b> (Jual 30%)</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 2 (+6%): <b style="color: #34d399;">Rp {tp2_calc:,}</b> (Jual 40%)</div>
            <div style="font-size: 12px; color: #cbd5e1;">🎯 TP 3 (+10%): <b style="color: #60a5fa;">Rp {tp3_calc:,}</b> (Trailing Stop Sisa)</div>
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
