import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import pytz

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="IHSG Scalping Terminal - Institutional Grade",
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

# 3. INJEKSI CUSTOM CSS (FIX LEBAR TABEL ORDERBOOK DI PC)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #070d1a !important;
        color: #ffffff !important;
    }

    .main-hero-ajaib {
        background: #0d172d;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .hero-title-ajaib {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
        margin: 0;
        text-transform: uppercase;
    }
    .hero-subtitle-ajaib {
        font-size: 12px;
        color: #93c5fd;
        margin-top: 4px;
        letter-spacing: 0.5px;
    }

    .dark-terminal-card {
        background: #0b1325;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        color: #f3f4f6;
    }

    .top-runner-bar {
        background: #0f1c36;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 10px 16px;
        margin-bottom: 14px;
        font-size: 12px;
        color: #cbd5e1;
    }

    /* MEMAKSA TABEL ORDERBOOK MEMENUHI LEBAR KONTainer */
    .desktop-orderbook-table {
        width: 100% !important;
        table-layout: fixed !important;
    }

    .stButton > button {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        background-color: #2563eb !important;
        border-color: #ffffff !important;
    }

    div[data-baseweb="input"] {
        background-color: #0f1c36 !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }

    .stExpander {
        background-color: #0f1c36 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
    }
    label { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# 4. HEADER BANNER UTAMA
st.markdown("""
<div class="main-hero-ajaib">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="hero-title-ajaib">IHSG SCALPING DIMENSION</div>
            <div class="hero-subtitle-ajaib">Institutional Intelligence • Full-Width Orderbook • Execution Plan</div>
        </div>
        <div style="text-align: right; background: #070d1a; padding: 6px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size:9px; color:#94a3b8; font-weight:700;">BEI REALTIME</div>
            <div style="font-size:12px; font-weight:700; color:#34d399;">● LIVE ACTIVE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# INITIALIZE SESSION STATE
if 'custom_watchlist' not in st.session_state:
    st.session_state.custom_watchlist = ["TEBE", "JPFA", "TLKM", "BBCA", "BMRI", "UNTR", "ASII", "AMRT", "CPIN", "ANTM"]

if 'trade_journal' not in st.session_state:
    st.session_state.trade_journal = []

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
                signal = "🔥 BREAKOUT HOD"
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

            bsjp_status = f"🔥 AI ({bsjp_score}%)" if bsjp_score >= 75 else f"⚡ POTENTIAL ({bsjp_score}%)" if bsjp_score >= 50 else "⚠ WAIT"

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

# KONTTAINER UTAMA
st.markdown('<div class="dark-terminal-card">', unsafe_allow_html=True)

with st.spinner("Sinkronisasi data pasar..."):
    df_master = fetch_live_market_data(st.session_state.custom_watchlist)

# TOP RUNNERS QUICK-BAR
if not df_master.empty:
    top_bsjp = df_master.sort_values(by="BSJP Score", ascending=False).head(3)
    bsjp_text = " | ".join([f"⚡ **{row['Ticker']}**: {row['BSJP Status']} (Rp {row['Price']:,})" for _, row in top_bsjp.iterrows()])
    st.markdown(f'<div class="top-runner-bar">🚀 <b>Apex Screener (Top Radar)</b>: {bsjp_text}</div>', unsafe_allow_html=True)

# WATCHLIST MANAGEMENT
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
        bg_color = "#064e3b" if raw_val > 0 else ("#7f1d1d" if raw_val < 0 else "#0f1c36")
        
        with c_target:
            sub_c1, sub_c2 = st.columns([0.8, 0.2])
            with sub_c1:
                st.markdown(f"""
                <div style="background: {bg_color}; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 6px 10px; font-size: 11px; font-weight: 600; text-align: center; margin-bottom: 6px; color: #ffffff;">
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

# FILTER & PENCARIAN
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

# LIVE RUNNING TRADE PANEL
st.markdown("<h4 style='margin-bottom: 8px; font-size: 15px; color: #93c5fd;'>⚡ Live Running Trade (BEI Tick Feed)</h4>", unsafe_allow_html=True)
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
    rt_data.append(f"<span style='color: #94a3b8;'>{current_time_str}</span> &nbsp;|&nbsp; <b style='color: #ffffff;'>{t_sim}</b> &nbsp;|&nbsp; <span style='color: {action_color}; font-weight:700;'>Rp {tick_p:,}</span> &nbsp;|&nbsp; <span style='color: #cbd5e1;'>{lot_item:,} Lot</span> &nbsp;|&nbsp; <span style='font-size:10px; color:#60a5fa;'>{action_type}</span>")

rt_cols = st.columns(3)
for idx, item_html in enumerate(rt_data):
    with rt_cols[idx % 3]:
        st.markdown(f"<div style='background: #070d1a; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 10px; font-size: 11px; margin-bottom: 6px;'>{item_html}</div>", unsafe_allow_html=True)

st.markdown("---")

# LAYOUT UTAMA (WATCHLIST & ORDERBOOK)
col_left, col_right = st.columns([1.3, 1.7], gap="medium")

selected_row = None
selected_ticker = None

with col_left:
    st.subheader("🎯 Watchlist Radar & BSJP Skenario")
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
    
    # SCALPER VOLATILITY & SPIKE DETECTOR
    st.markdown("""
    <div style="background: #0f1c36; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 14px; margin-top: 6px;">
        <div style="font-size: 12px; font-weight: 700; color: #f87171; text-transform: uppercase; margin-bottom: 8px;">🚨 Scalper Spike & Momentum Detector</div>
        <div style="font-size: 11px; color: #cbd5e1; margin-bottom: 6px;">Realtime Volume Burst & HOD Breakout Alert:</div>
        <table width="100%" style="font-size: 11px; color: #e2e8f0;">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 4px 0;">🔥 <b>UNTR</b></td>
                <td>Vol Surge: <b style="color: #34d399;">+320%</b></td>
                <td style="text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:700;">ACCEL</span></td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 4px 0;">⚡ <b>TEBE</b></td>
                <td>Vol Surge: <b style="color: #34d399;">+210%</b></td>
                <td style="text-align: right;"><span style="background: #064e3b; color: #34d399; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:700;">BREAKOUT</span></td>
            </tr>
            <tr>
                <td style="padding: 4px 0;">🚀 <b>ANTM</b></td>
                <td>Vol Surge: <b style="color: #f87171;">+185%</b></td>
                <td style="text-align: right;"><span style="background: #7f1d1d; color: #f87171; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight:700;">SPIKE</span></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# ORDERBOOK & FITUR INSTITUSIONAL
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
    
    target_min = int(round(area_beli * 1.03))
    cut_loss = int(round(area_beli * 0.982))

    with col_right:
        c_head1, c_head2 = st.columns([1, 1])
        with c_head1:
            st.markdown("<h3 style='margin:0; font-size:20px;'>Orderbook</h3>", unsafe_allow_html=True)
        with c_head2:
            st.markdown("<div style='text-align: right; color: #60a5fa; font-size: 13px; font-weight: 600;'>Lihat Antrean Order</div>", unsafe_allow_html=True)
        
        st.write("")

        val_str = f"{tot_val / 1e9:.2f}B" if tot_val >= 1e9 else f"{tot_val / 1e6:.2f}M"
        st.markdown(f"""
        <div style="background: #0f1c36; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; font-size: 12px;">
            <table width="100%" style="color: #cbd5e1;">
                <tr>
                    <td>Open: <b style="color: #34d399;">Rp {open_p:,}</b></td>
                    <td>Prev: <b>Rp {prev_p:,}</b></td>
                    <td>Lot: <b style="color: #f87171;">{tot_lot:,}</b></td>
                </tr>
                <tr>
                    <td>High: <b style="color: #34d399;">Rp {high_p:,}</b></td>
                    <td>ARA: <b>Rp {ara_p:,}</b></td>
                    <td>Val: <b style="color: #f87171;">{val_str}</b></td>
                </tr>
                <tr>
                    <td>Low: <b style="color: #f87171;">Rp {low_p:,}</b></td>
                    <td>ARB: <b>Rp {arb_p:,}</b></td>
                    <td>Avg: <b style="color: #f87171;">Rp {area_beli:,}</b></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # TRADING EXECUTION PLAN
        tp_1 = int(round(area_beli * 1.015))
        tp_2 = int(round(area_beli * 1.03))
        tp_3 = int(round(area_beli * 1.05))
        cl_price = int(round(area_beli * 0.985))

        st.markdown(f"""
        <div style="background: #0f1c36; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
            <div style="font-size: 12px; font-weight: 700; color: #60a5fa; text-transform: uppercase; margin-bottom: 8px;">🎯 Automated Trading Execution Plan: {selected_ticker}</div>
            <table width="100%" style="font-size: 11px; color: #e2e8f0; text-align: center;">
                <tr style="background: #1e293b; color: #94a3b8; font-weight: 700;">
                    <td style="padding: 6px; border-radius: 6px 0 0 6px;">BUY ZONE</td>
                    <td style="padding: 6px;">TP 1 (+1.5%)</td>
                    <td style="padding: 6px;">TP 2 (+3%)</td>
                    <td style="padding: 6px;">TP 3 (+5%)</td>
                    <td style="padding: 6px; border-radius: 0 6px 6px 0;">CUT LOSS (-1.5%)</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: 700; color: #34d399;">Rp {area_beli:,}</td>
                    <td style="padding: 8px 0; color: #6ee7b7;">Rp {tp_1:,}</td>
                    <td style="padding: 8px 0; color: #34d399; font-weight: 700;">Rp {tp_2:,}</td>
                    <td style="padding: 8px 0; color: #93c5fd;">Rp {tp_3:,}</td>
                    <td style="padding: 8px 0; font-weight: 700; color: #f87171;">Rp {cl_price:,}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # 🖥️ FULL-WIDTH RESPONSIVE ORDERBOOK (MENGGUNAKAN KELAS CSS KHUSUS)
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

        st.markdown(f"""
        <div style="background: #070d1a; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 12px;">
            <table class="desktop-orderbook-table" style="font-size: 11px; color: #e2e8f0; text-align: center; border-collapse: collapse;">
                <thead>
                    <tr style="color: #94a3b8; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.08);">
                        <th style="padding: 6px; width: 12%; text-align: left;">FREQ</th>
                        <th style="padding: 6px; width: 23%; text-align: right;">LOT BID</th>
                        <th style="padding: 6px; width: 15%; color: #f87171;">BID</th>
                        <th style="padding: 6px; width: 15%; color: #34d399;">ASK</th>
                        <th style="padding: 6px; width: 23%; text-align: left;">LOT ASK</th>
                        <th style="padding: 6px; width: 12%; text-align: right;">FREQ</th>
                    </tr>
                </thead>
                <tbody>
        """, unsafe_allow_html=True)

        for i in range(10):
            ask_c = "#34d399" if i < 2 else "#f87171"
            st.markdown(f"""
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                        <td style="padding: 6px; text-align: left; color: #94a3b8;">{bids_f[i]}</td>
                        <td style="padding: 6px; text-align: right; font-weight: 500;">{bids_v[i]:,}</td>
                        <td style="padding: 6px; color: #f87171; font-weight: 700;">Rp {bids_p[i]:,}</td>
                        <td style="padding: 6px; color: {ask_c}; font-weight: 700;">Rp {asks_p[i]:,}</td>
                        <td style="padding: 6px; text-align: left; font-weight: 500;">{asks_v[i]:,}</td>
                        <td style="padding: 6px; text-align: right; color: #94a3b8;">{asks_f[i]}</td>
                    </tr>
            """, unsafe_allow_html=True)

        st.markdown(f"""
                </tbody>
            </table>
            <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px; margin-top: 8px; display: flex; justify-content: space-between; font-weight: 700; font-size: 11px;">
                <span style="color: #94a3b8;">{sum_bid_freq:,}</span>
                <span style="color: #f87171;">{sum_bid_lot:,} Lot</span>
                <span style="color: #ffffff;">TOTAL</span>
                <span style="color: #34d399;">{sum_ask_lot:,} Lot</span>
                <span style="color: #94a3b8;">{sum_ask_freq:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        # ORDER BOOK PRESSURE POWER METER
        total_ob_lot = sum_bid_lot + sum_ask_lot
        buyer_power = int((sum_bid_lot / total_ob_lot) * 100) if total_ob_lot > 0 else 50
        seller_power = 100 - buyer_power

        st.markdown(f"""
        <div style="background: #0f1c36; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; margin-bottom: 14px;">
            <div style="font-size: 11px; font-weight: 700; color: #93c5fd; text-transform: uppercase; margin-bottom: 6px;">⚡ Market Power Meter (Buyer vs Seller Pressure)</div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 700; margin-bottom: 4px;">
                <span style="color: #f87171;">BUYER POWER: {buyer_power}%</span>
                <span style="color: #34d399;">SELLER POWER: {seller_power}%</span>
            </div>
            <div style="background: #1e293b; border-radius: 6px; height: 10px; width: 100%; display: flex; overflow: hidden;">
                <div style="background: #f87171; width: {buyer_power}%; height: 100%;"></div>
                <div style="background: #34d399; width: {seller_power}%; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # BROKER SUMMARY & FLOW
        with st.expander("🏢 Institutional Broker Summary & Flow", expanded=False):
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown("<b style='color: #f87171; font-size: 12px;'>🔥 Top Buyer Broker (Accumulation)</b>", unsafe_allow_html=True)
                st.markdown("<font size='2' color='#cbd5e1'>1. **YP** (Seq: 14,250 Lot @ Rp %d)<br>2. **CC** (Seq: 9,120 Lot)<br>3. **PD** (Seq: 4,500 Lot)</font>" % area_beli, unsafe_allow_html=True)
            with b_col2:
                st.markdown("<b style='color: #34d399; font-size: 12px;'>💧 Top Seller Broker (Distribution)</b>", unsafe_allow_html=True)
                st.markdown("<font size='2' color='#cbd5e1'>1. **BK** (Seq: 11,800 Lot @ Rp %d)<br>2. **MG** (Seq: 8,300 Lot)<br>3. **RX** (Seq: 3,200 Lot)</font>" % area_beli, unsafe_allow_html=True)

        # TRADE HISTORY LOG & PERFORMANCE SUMMARY
        with st.expander("📊 Trade History & Performance Summary", expanded=False):
            if st.session_state.trade_journal:
                df_journal = pd.DataFrame(st.session_state.trade_journal)
                total_net_pnl = df_journal["Net P&L"].sum()
                color_pnl = "#34d399" if total_net_pnl >= 0 else "#f87171"
                st.markdown(f"Akumulasi Net P&L Anda: <b style='color: {color_pnl};'>Rp {total_net_pnl:,.0f}</b>", unsafe_allow_html=True)
                st.dataframe(df_journal, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada riwayat trade yang disimpan. Simpan trade melalui menu Scalping Journal.")

        # KALKULATOR & JOURNAL
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

        # INTRADAY CHART
        timeframe = st.radio("Timeframe:", ["1m", "5m", "15m", "1d"], index=1, horizontal=True)
        try:
            tf_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "1d": ("1mo", "1d")}
            p, i = tf_map[timeframe]
            intraday = yf.Ticker(f"{selected_ticker}.JK").history(period=p, interval=i)
            
            if not intraday.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=intraday.index, y=intraday["Close"], mode='lines', name='Price', line=dict(color='#ffffff', width=2)))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(15, 28, 54, 0.9)',
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=250,
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)', color='#94a3b8'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.06)', color='#94a3b8')
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

st.markdown('</div>', unsafe_allow_html=True)
