import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import pytz

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="IHSG Scalping Terminal - Pro",
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
        st_autorefresh(interval=15000, key="bursa_refresh")
    except Exception:
        pass

# 3. INJEKSI CUSTOM CSS DENGAN EFEK NEON GLOW UNIVERSAL (KLIK / HOVER / FOCUS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #0d0628 0%, #1a0b40 40%, #2a125c 70%, #4a228a 100%) !important;
        color: #ffffff;
    }

    /* HEADER BANNER */
    .main-header {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(0, 240, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
        font-size: 24px;
    }

    /* TOP RUNNER QUICK BAR */
    .top-runner-bar {
        background: rgba(0, 240, 255, 0.05);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 10px;
        padding: 8px 14px;
        margin-bottom: 12px;
        font-size: 12px;
    }

    /* KARTU METRIC DENGAN EFEK NEON HOVER & ACTIVE */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 12px 8px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
    }
    .metric-card:hover, .metric-card:active {
        transform: translateY(-4px) scale(1.02);
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.7), 0 0 40px rgba(0, 240, 255, 0.3) !important;
    }

    .metric-label { font-size: 10px; color: #b3a2c7; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 17px; font-weight: 700; color: #ffffff; }

    .target-green { color: #00f0ff; text-shadow: 0 0 10px rgba(0,240,255,0.6); }
    .target-magenta { color: #ff2a85; text-shadow: 0 0 10px rgba(255,42,133,0.6); }
    .target-gold { color: #ffd700; text-shadow: 0 0 10px rgba(255,215,0,0.6); }
    .cut-loss-red { color: #ff5252; text-shadow: 0 0 10px rgba(255,82,82,0.6); }

    /* CARD WATCHLIST DENGAN EFEK NEON HOVER */
    .wl-box {
        padding: 8px 6px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: all 0.2s ease;
    }
    .wl-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 18px rgba(0, 240, 255, 0.8), 0 0 30px rgba(0, 240, 255, 0.4) !important;
    }
    .wl-green { background: linear-gradient(135deg, #0e5038, #10b981); border: 1px solid #34d399; color: #ffffff; }
    .wl-red { background: linear-gradient(135deg, #7f1d1d, #ef4444); border: 1px solid #f87171; color: #ffffff; }
    .wl-white { background: linear-gradient(135deg, #374151, #6b7280); border: 1px solid #d1d5db; color: #ffffff; }

    /* =========================================================
       ✨ GLOBAL NEON HOVER & FOCUS STYLES UNTUK SEMUA ELEMENT STREAMLIT
       ========================================================= */

    /* 1. TOMBOL (BUTTONS) - HOVER & ACTIVE NEON GLOW */
    .stButton > button {
        border-radius: 8px !important;
        transition: all 0.25s ease-in-out !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
    }
    .stButton > button:hover, .stButton > button:focus, .stButton > button:active {
        border-color: #00f0ff !important;
        color: #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.8), 0 0 30px rgba(0, 240, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }

    /* 2. INPUT TEKS & NUMBER INPUT - FOCUS NEON GLOW */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        transition: all 0.25s ease-in-out !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="input"]:hover {
        border-color: #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.7), 0 0 25px rgba(0, 240, 255, 0.3) !important;
    }

    /* 3. SELECTBOX / DROPDOWN - FOCUS NEON GLOW */
    div[data-baseweb="select"] {
        border-radius: 8px !important;
        transition: all 0.25s ease-in-out !important;
    }
    div[data-baseweb="select"]:hover, div[data-baseweb="select"]:focus-within {
        border-color: #ff2a85 !important;
        box-shadow: 0 0 15px rgba(255, 42, 133, 0.8), 0 0 25px rgba(255, 42, 133, 0.4) !important;
    }

    /* 4. EXPANDER HEADER - HOVER NEON GLOW */
    .stExpander {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    .stExpander:hover {
        border-color: #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }

    /* 5. RADIO BUTTON & SLIDER HOVER */
    div[data-testid="stMarkdownContainer"] p {
        transition: all 0.2s ease;
    }
    div[role="radiogroup"] label:hover {
        color: #00f0ff !important;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.8) !important;
    }
</style>
""", unsafe_allow_html=True)

# 4. HEADER BANNER
st.markdown("""
<div class="main-header">
    <h1>⚡ IHSG High-Potential Scalping Terminal</h1>
    <p style="color:#00f0ff; margin:0; font-size:12px;">Live Real-Time Market • HOD/LOD Alert • Fee Calculator • Multi-Timeframe Chart</p>
</div>
""", unsafe_allow_html=True)

# INITIALIZE SESSION STATE
if 'custom_watchlist' not in st.session_state:
    st.session_state.custom_watchlist = ["TEBE", "JPFA", "TLKM", "BBCA", "BMRI", "UNTR", "ASII", "AMRT", "CPIN", "ANTM"]

if 'trade_journal' not in st.session_state:
    st.session_state.trade_journal = []

# ESTIMATED SHARES OUTSTANDING
ESTIMATED_SHARES = {
    "TEBE": 1285000000, "JPFA": 11726575001, "TLKM": 99062216600, "CPIN": 16398000000,
    "BBCA": 123275000000, "BMRI": 93333333333, "UNTR": 3730135123, "ASII": 40483553140,
    "JARR": 12000000000, "AMRT": 41524500000, "TPIA": 86522000000, "AKRA": 20073000000,
    "BRIS": 46128000000, "ERAA": 15920000000, "PGAS": 24241000000, "ANTM": 24030000000
}

def hitung_max_ara(price):
    if price <= 200: return 35.0
    elif price <= 5000: return 25.0
    else: return 20.0

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
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
            
            hist_intra = stock.history(period="1d", interval="1m")
            hod = int(round(hist_intra["High"].max())) if not hist_intra.empty else current_price
            lod = int(round(hist_intra["Low"].min())) if not hist_intra.empty else current_price

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

            mc_raw = None
            try: mc_raw = stock.fast_info['market_cap']
            except Exception: pass
            if not mc_raw or np.isnan(mc_raw):
                shares = ESTIMATED_SHARES.get(clean_symbol)
                if shares: mc_raw = current_price * shares

            mc_fmt = format_market_cap(mc_raw)
            potensi = "🔥 HIGH POTENTIAL" if change_pct >= 0 else "⚡ MEDIUM POTENTIAL"
            
            return {
                "Ticker": clean_symbol,
                "Price": current_price,
                "HOD": hod,
                "LOD": lod,
                "Market Cap": mc_fmt,
                "Change (%)": f"{change_pct:+.2f}%",
                "Raw Change": change_pct,
                "Signal": signal,
                "Volume": vol_spike,
                "Prediksi Potensi": potensi
            }
    except Exception: return None
    return None

@st.cache_data(ttl=15)
def fetch_live_market_data(ticker_list):
    results = []
    for symbol in ticker_list:
        data = fetch_single_ticker_data(symbol)
        if data: results.append(data)
    return pd.DataFrame(results)

# FETCH DATA MARKET LIVE
with st.spinner("Mengambil data pasar..."):
    df_master = fetch_live_market_data(st.session_state.custom_watchlist)

# 5. 🔥 TOP RUNNERS QUICK-BAR
if not df_master.empty:
    top_gainers = df_master.sort_values(by="Raw Change", ascending=False).head(3)
    runner_text = " | ".join([f"🔥 **{row['Ticker']}**: {row['Change (%)']} (Rp {row['Price']:,})" for _, row in top_gainers.iterrows()])
    st.markdown(f'<div class="top-runner-bar">🚀 <b>Top Volatility Runners Watchlist</b>: {runner_text}</div>', unsafe_allow_html=True)

# 6. WATCHLIST MANAGEMENT
with st.expander("📌 Custom Watchlist Management", expanded=True):
    col_w_add, col_w_list = st.columns([1, 2.5], gap="medium")
    
    with col_w_add:
        new_ticker = st.text_input("Tambah Saham:", placeholder="Contoh: GOTO, BUKA").strip().upper()
        if st.button("➕ Tambahkan", use_container_width=True):
            if new_ticker and new_ticker not in st.session_state.custom_watchlist:
                st.session_state.custom_watchlist.append(new_ticker)
                st.rerun()

    with col_w_list:
        cols_tags = st.columns(5)
        tickers_to_remove = []
        
        for idx, t_code in enumerate(st.session_state.custom_watchlist):
            c_target = cols_tags[idx % 5]
            
            row_match = df_master[df_master["Ticker"] == t_code] if not df_master.empty else pd.DataFrame()
            if not row_match.empty:
                raw_val = row_match.iloc[0]["Raw Change"]
                pct_str = row_match.iloc[0]["Change (%)"]
                live_price = row_match.iloc[0]["Price"]
            else:
                raw_val, pct_str, live_price = 0, "0.00%", 0

            card_class = "wl-green" if raw_val > 0 else ("wl-red" if raw_val < 0 else "wl-white")
            price_str = f"Rp {live_price:,}" if live_price > 0 else "N/A"
            
            with c_target:
                st.markdown(f"""
                <div class="wl-box {card_class}">
                    <div style="font-size:12px; font-weight:700;">{t_code}</div>
                    <div style="font-size:10px;">{price_str} ({pct_str})</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"✕ Hapus", key=f"del_{t_code}", use_container_width=True):
                    tickers_to_remove.append(t_code)

        if tickers_to_remove:
            for r_code in tickers_to_remove:
                st.session_state.custom_watchlist.remove(r_code)
            st.rerun()

# 7. FILTER & PENCARIAN
c_filter, c_search = st.columns([1.5, 1], gap="medium")
with c_filter:
    kategori_harga = st.selectbox("📌 Filter Harga:", ["Semua Saham", "1. > Rp 4.000", "2. Rp 3.000 - Rp 4.000", "3. Rp 2.000 - Rp 3.000", "4. Rp 1.000 - Rp 2.000", "5. Rp 500 - Rp 1.000", "6. Rp 1 - Rp 500"])
with c_search:
    search_input = st.text_input("🔍 Cari Ticker Universal:", placeholder="Contoh: UNVR, ITMG").strip().upper()

# FILTERING DATA
df_filtered = df_master.copy() if not df_master.empty else pd.DataFrame()
if not df_filtered.empty:
    if kategori_harga == "1. > Rp 4.000": df_filtered = df_filtered[df_filtered["Price"] > 4000]
    elif kategori_harga == "2. Rp 3.000 - Rp 4.000": df_filtered = df_filtered[(df_filtered["Price"] >= 3000) & (df_filtered["Price"] <= 4000)]
    elif kategori_harga == "3. Rp 2.000 - Rp 3.000": df_filtered = df_filtered[(df_filtered["Price"] >= 2000) & (df_filtered["Price"] < 3000)]
    elif kategori_harga == "4. Rp 1.000 - Rp 2.000": df_filtered = df_filtered[(df_filtered["Price"] >= 1000) & (df_filtered["Price"] < 2000)]
    elif kategori_harga == "5. Rp 500 - Rp 1.000": df_filtered = df_filtered[(df_filtered["Price"] >= 500) & (df_filtered["Price"] < 1000)]
    elif kategori_harga == "6. Rp 1 - Rp 500": df_filtered = df_filtered[(df_filtered["Price"] >= 1) & (df_filtered["Price"] < 500)]

    df_filtered["Target Min (+3%)"] = (df_filtered["Price"] * 1.03).round().astype(int)

# 8. LAYOUT UTAMA
col_left, col_right = st.columns([1.4, 1.6], gap="medium")

selected_row = None
selected_ticker = None

with col_left:
    st.subheader("🎯 Watchlist Radar & Signals")
    if not df_filtered.empty:
        st.dataframe(
            df_filtered[["Ticker", "Price", "Change (%)", "Market Cap", "Signal", "Volume", "Target Min (+3%)", "Prediksi Potensi"]],
            use_container_width=True, hide_index=True, height=300
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
            selected_ticker = st.selectbox("Pilih Saham Plan:", ticker_options, index=0)
            selected_row = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0].to_dict()

# TRADING EXECUTION PLAN & ADVANCED TOOLS
if selected_ticker and selected_row:
    area_beli = int(selected_row["Price"])
    hod_val = selected_row.get("HOD", area_beli)
    lod_val = selected_row.get("LOD", area_beli)
    market_cap_val = selected_row.get("Market Cap", "N/A")
    target_min = int(round(area_beli * 1.03))
    target_opt = int(round(area_beli * 1.05))
    max_ara_pct = hitung_max_ara(area_beli)
    harga_max_ara = int(round(area_beli * (1 + max_ara_pct / 100)))
    cut_loss = int(round(area_beli * 0.982))

    with col_right:
        st.subheader(f"📊 Trading Execution Plan: {selected_ticker}")
        st.caption(f"Cap: **{market_cap_val}** | Signal: **{selected_row.get('Signal', 'N/A')}** | HOD: **Rp {hod_val:,}** | LOD: **Rp {lod_val:,}**")

        # METRIC CARDS DENGAN GLOW HOVER NEON
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.markdown(f'<div class="metric-card"><div class="metric-label">AREA BELI</div><div class="metric-value">Rp {area_beli:,}</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET (+3%)</div><div class="metric-value target-green">Rp {target_min:,}</div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET (+5%)</div><div class="metric-value target-magenta">Rp {target_opt:,}</div></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card"><div class="metric-label">MAX ARA (+{max_ara_pct:.0f}%)</div><div class="metric-value target-gold">Rp {harga_max_ara:,}</div></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card"><div class="metric-label">CUT LOSS (-1.8%)</div><div class="metric-value cut-loss-red">Rp {cut_loss:,}</div></div>', unsafe_allow_html=True)
        
        st.write("")

        # 📊 BUYING VS SELLING PRESSURE METER
        try:
            intra = yf.Ticker(f"{selected_ticker}.JK").history(period="1d", interval="1m")
            if not intra.empty:
                buy_vol = intra[intra["Close"] >= intra["Open"]]["Volume"].sum()
                sell_vol = intra[intra["Close"] < intra["Open"]]["Volume"].sum()
                tot_vol = buy_vol + sell_vol
                buy_pct = (buy_vol / tot_vol) * 100 if tot_vol > 0 else 50
                sell_pct = 100 - buy_pct
                
                st.caption(f"📊 **Intraday Volume Pressure**: 🟩 Beli **{buy_pct:.1f}%** vs 🟥 Jual **{sell_pct:.1f}%**")
                st.progress(int(buy_pct))
        except Exception: pass

        # 🧮 KALKULATOR LOT WITH PRESETS & SIMULATOR NET P&L
        c_calc, c_sim = st.columns(2)
        with c_calc:
            with st.expander("🧮 Position Size / Risk Calculator", expanded=False):
                preset_modal = st.radio("Preset Modal:", ["Rp 5 Jt", "Rp 10 Jt", "Rp 25 Jt", "Custom"], index=1, horizontal=True)
                if preset_modal == "Rp 5 Jt": modal = 5000000
                elif preset_modal == "Rp 10 Jt": modal = 10000000
                elif preset_modal == "Rp 25 Jt": modal = 25000000
                else: modal = st.number_input("Modal Custom (Rp):", min_value=100000, value=10000000, step=500000)

                risk_p = st.slider("Maksimal Risiko (%):", 0.5, 5.0, 1.8, 0.1)
                max_rugi = modal * (risk_p / 100)
                rugi_lembar = area_beli - cut_loss
                max_lot = int((max_rugi / rugi_lembar) // 100) if rugi_lembar > 0 else 0
                st.info(f"👉 Entry Recommended: **{max_lot:,} Lot** (Total: **Rp {max_lot*100*area_beli:,.0f}**)")

        with c_sim:
            with st.expander("📝 Scalping Journal (Net P&L - Broker Fee)", expanded=False):
                entry_p = st.number_input("Entry Price:", value=area_beli)
                exit_p = st.number_input("Exit Price:", value=target_min)
                lot_cnt = st.number_input("Jumlah Lot:", value=max_lot if max_lot > 0 else 10)
                
                buy_val = entry_p * lot_cnt * 100
                sell_val = exit_p * lot_cnt * 100
                fee_buy = buy_val * 0.0015
                fee_sell = sell_val * 0.0025
                net_pnl = (sell_val - fee_sell) - (buy_val + fee_buy)

                if st.button("💾 Simpan Trade"):
                    st.session_state.trade_journal.append({"Ticker": selected_ticker, "Net P&L": net_pnl})
                    st.success(f"Disimpan! Net P&L (Setelah Fee): Rp {net_pnl:,.0f}")

        # TIMEFRAME CONTROL & CHART
        timeframe = st.radio("Pilih Timeframe Chart:", ["1m", "5m", "15m", "1d"], index=1, horizontal=True)

        try:
            tf_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "1d": ("1mo", "1d")}
            p, i = tf_map[timeframe]
            intraday = yf.Ticker(f"{selected_ticker}.JK").history(period=p, interval=i)
            
            if not intraday.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=intraday.index, y=intraday["Close"], mode='lines', name='Price', line=dict(color='#00f0ff', width=2)))
                
                vwap = (intraday["Volume"] * (intraday["High"] + intraday["Low"] + intraday["Close"]) / 3).cumsum() / intraday["Volume"].cumsum()
                fig.add_trace(go.Scatter(x=intraday.index, y=vwap, mode='lines', name='VWAP', line=dict(color='#ff2a85', width=1.5, dash='dot')))

                fig.add_hline(y=target_min, line_dash="dash", line_color="#00f0ff", annotation_text=f"Target (+3%): {target_min}")
                fig.add_hline(y=cut_loss, line_dash="dash", line_color="#ff5252", annotation_text=f"Cut Loss: {cut_loss}")

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(13, 6, 40, 0.5)',
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280,
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#ffffff"))
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data grafik tidak tersedia saat bursa tutup.")
        except Exception:
            st.warning("Gagal memuat grafik intraday.")
