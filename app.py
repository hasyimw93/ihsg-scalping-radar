import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="IHSG Scalping Radar - Pro Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. INJEKSI CUSTOM CSS UTAMA
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

    .main-header {
        background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(0, 240, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
        font-size: 28px;
    }

    .main-header p {
        color: #00f0ff;
        font-size: 14px;
        margin-top: 5px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #00f0ff;
    }

    .metric-label {
        font-size: 11px;
        color: #b3a2c7;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
    }

    .target-green { color: #00f0ff; text-shadow: 0 0 10px rgba(0,240,255,0.6); }
    .target-magenta { color: #ff2a85; text-shadow: 0 0 10px rgba(255,42,133,0.6); }
    .target-gold { color: #ffd700; text-shadow: 0 0 10px rgba(255,215,0,0.6); }
    .cut-loss-red { color: #ff5252; }
    
    /* CUSTOM KOTAK WATCHLIST */
    .watchlist-card {
        padding: 12px 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: 700;
        margin-bottom: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        transition: all 0.2s ease;
    }
    .card-green {
        background: linear-gradient(135deg, #0e5038, #10b981) !important;
        border: 1px solid #34d399 !important;
        color: #ffffff !important;
    }
    .card-red {
        background: linear-gradient(135deg, #7f1d1d, #ef4444) !important;
        border: 1px solid #f87171 !important;
        color: #ffffff !important;
    }
    .card-white {
        background: linear-gradient(135deg, #374151, #9ca3af) !important;
        border: 1px solid #e5e7eb !important;
        color: #111827 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER BANNER
st.markdown("""
<div class="main-header">
    <h1>⚡ IHSG High-Potential Scalping Terminal</h1>
    <p>Live Real-Time Market, Multi-Timeframe Chart, Risk/Lot Calculator & Custom Watchlist</p>
</div>
""", unsafe_allow_html=True)

# INITIALIZE SESSION STATE FOR WATCHLIST
if 'custom_watchlist' not in st.session_state:
    st.session_state.custom_watchlist = ["TEBE", "JPFA", "TLKM", "BBCA", "BMRI", "UNTR", "ASII", "AMRT", "CPIN", "ANTM"]

# ESTIMATED SHARES OUTSTANDING FOR FALLBACK MARKET CAP
ESTIMATED_SHARES = {
    "TEBE": 1285000000, "JPFA": 11726575001, "TLKM": 99062216600, "CPIN": 16398000000,
    "BBCA": 123275000000, "BMRI": 93333333333, "UNTR": 3730135123, "ASII": 40483553140,
    "JARR": 12000000000, "AMRT": 41524500000, "TPIA": 86522000000, "AKRA": 20073000000,
    "BRIS": 46128000000, "ERAA": 15920000000, "PGAS": 24241000000, "ANTM": 24030000000,
    "ACES": 17150000000, "BBYB": 13320000000, "BUMI": 371000000000, "RAAM": 8500000000
}

# FUNGSI-FUNGSI UTAMA
def hitung_max_ara(price):
    if price <= 200:
        return 35.0
    elif price <= 5000:
        return 25.0
    else:
        return 20.0

def format_market_cap(mc):
    if not mc or pd.isna(mc) or mc == 0:
        return "N/A"
    if mc >= 1e12:
        return f"Rp {mc / 1e12:.2f} T"
    elif mc >= 1e9:
        return f"Rp {mc / 1e9:.2f} B"
    elif mc >= 1e6:
        return f"Rp {mc / 1e6:.2f} M"
    else:
        return f"Rp {mc:,.0f}"

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
            
            # Hitung Intraday/Indikator
            hist_intra = stock.history(period="5d", interval="15m")
            rsi_val = hitung_rsi(hist_intra["Close"]).iloc[-1] if not hist_intra.empty and len(hist_intra) >= 14 else 50
            ma5 = hist_intra["Close"].rolling(5).mean().iloc[-1] if not hist_intra.empty and len(hist_intra) >= 5 else current_price
            
            signal = "🚀 BULLISH" if current_price > ma5 else "🔻 BEARISH"
            if rsi_val > 70:
                signal += " (OVERBOUGHT)"
            elif rsi_val < 30:
                signal += " (OVERSOLD)"
            
            avg_vol = hist_intra["Volume"].mean() if not hist_intra.empty else 1
            last_vol = hist_intra["Volume"].iloc[-1] if not hist_intra.empty else 0
            vol_spike = "⚡ SPIKE" if last_vol > (avg_vol * 1.8) else "NORMAL"

            mc_raw = None
            try:
                mc_raw = stock.fast_info['market_cap']
            except Exception:
                pass
            if not mc_raw or np.isnan(mc_raw):
                shares = ESTIMATED_SHARES.get(clean_symbol)
                if shares:
                    mc_raw = current_price * shares

            mc_fmt = format_market_cap(mc_raw)
            potensi = "🔥 HIGH POTENTIAL" if change_pct >= 0 else "⚡ MEDIUM POTENTIAL"
            
            return {
                "Ticker": clean_symbol,
                "Price": current_price,
                "Market Cap": mc_fmt,
                "Change (%)": f"{change_pct:+.2f}%",
                "Raw Change": change_pct,
                "Signal": signal,
                "Volume": vol_spike,
                "Prediksi Potensi": potensi
            }
    except Exception:
        return None
    return None

@st.cache_data(ttl=15)
def fetch_live_market_data(ticker_list):
    results = []
    for symbol in ticker_list:
        data = fetch_single_ticker_data(symbol)
        if data:
            results.append(data)
    return pd.DataFrame(results)

# PENGAMBILAN DATA MARKET LIVE
with st.spinner("Mengambil analisis harga realtime..."):
    df_master = fetch_live_market_data(st.session_state.custom_watchlist)

change_raw_map = {}
change_str_map = {}
price_map = {}
if not df_master.empty:
    change_raw_map = dict(zip(df_master["Ticker"], df_master["Raw Change"]))
    change_str_map = dict(zip(df_master["Ticker"], df_master["Change (%)"]))
    price_map = dict(zip(df_master["Ticker"], df_master["Price"]))

# 4. AREA MANAGEMENT WATCHLIST DENGAN KOTAK WARNA REALTIME
with st.expander("📌 Custom Watchlist Management (Warna Kotak Live Real-Time)", expanded=True):
    col_w_add, col_w_list = st.columns([1, 2], gap="medium")
    
    with col_w_add:
        new_ticker = st.text_input("Tambah Saham ke Watchlist:", placeholder="Contoh: BUKA, GOTO, MDKA").strip().upper()
        if st.button("➕ Tambahkan ke Watchlist", use_container_width=True):
            if new_ticker:
                if new_ticker not in st.session_state.custom_watchlist:
                    st.session_state.custom_watchlist.append(new_ticker)
                    st.success(f"{new_ticker} berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning(f"{new_ticker} sudah ada di Watchlist.")
            else:
                st.error("Ketik kode ticker terlebih dahulu.")
                
    with col_w_list:
        st.caption("Daftar Watchlist Aktif (Kuning/Kotak Berwarna Sesuai Perubahan Harga):")
        cols_tags = st.columns(4)
        tickers_to_remove = []
        
        for idx, t_code in enumerate(st.session_state.custom_watchlist):
            c_target = cols_tags[idx % 4]
            raw_val = change_raw_map.get(t_code, 0)
            pct_str = change_str_map.get(t_code, "0.00%")
            live_price = price_map.get(t_code, 0)
            
            # PENENTUAN KELAS KOTAK
            if raw_val > 0:
                card_class = "card-green"
            elif raw_val < 0:
                card_class = "card-red"
            else:
                card_class = "card-white"
                
            price_text = f"Rp {live_price:,}" if live_price > 0 else "Loading..."
            
            with c_target:
                # KOTAK BERWARNA RESPONSIF
                st.markdown(f"""
                <div class="watchlist-card {card_class}">
                    <div style="font-size: 15px;">{t_code}</div>
                    <div style="font-size: 13px; opacity: 0.95;">{price_text} ({pct_str})</div>
                </div>
                """, unsafe_allow_html=True)
                
                # TOMBOL HAPUS KECIL DI BAWAH KOTAK
                if st.button(f"Hapus {t_code}", key=f"del_{t_code}", use_container_width=True):
                    tickers_to_remove.append(t_code)
        
        if tickers_to_remove:
            for r_code in tickers_to_remove:
                st.session_state.custom_watchlist.remove(r_code)
            st.rerun()

c_filter, c_search = st.columns([1.5, 1], gap="medium")

with c_filter:
    kategori_harga = st.selectbox(
        "📌 Filter Rentang Harga:",
        ["Semua Saham", "1. > Rp 4.000", "2. Rp 3.000 - Rp 4.000", "3. Rp 2.000 - Rp 3.000", "4. Rp 1.000 - Rp 2.000", "5. Rp 500 - Rp 1.000", "6. Rp 1 - Rp 500"],
        index=0
    )

with c_search:
    search_input = st.text_input("🔍 Cari Ticker Universal (Temporary View):", placeholder="Ketik Ticker (Contoh: UNVR, ITMG)").strip().upper()

# FILTERING DATA
if kategori_harga == "1. > Rp 4.000":
    df_filtered = df_master[df_master["Price"] > 4000].copy() if not df_master.empty else pd.DataFrame()
elif kategori_harga == "2. Rp 3.000 - Rp 4.000":
    df_filtered = df_master[(df_master["Price"] >= 3000) & (df_master["Price"] <= 4000)].copy() if not df_master.empty else pd.DataFrame()
elif kategori_harga == "3. Rp 2.000 - Rp 3.000":
    df_filtered = df_master[(df_master["Price"] >= 2000) & (df_master["Price"] < 3000)].copy() if not df_master.empty else pd.DataFrame()
elif kategori_harga == "4. Rp 1.000 - Rp 2.000":
    df_filtered = df_master[(df_master["Price"] >= 1000) & (df_master["Price"] < 2000)].copy() if not df_master.empty else pd.DataFrame()
elif kategori_harga == "5. Rp 500 - Rp 1.000":
    df_filtered = df_master[(df_master["Price"] >= 500) & (df_master["Price"] < 1000)].copy() if not df_master.empty else pd.DataFrame()
elif kategori_harga == "6. Rp 1 - Rp 500":
    df_filtered = df_master[(df_master["Price"] >= 1) & (df_master["Price"] < 500)].copy() if not df_master.empty else pd.DataFrame()
else:
    df_filtered = df_master.copy() if not df_master.empty else pd.DataFrame()

if not df_filtered.empty:
    df_filtered["Target Min (+3%)"] = (df_filtered["Price"] * 1.03).round().astype(int)
    df_filtered["Max ARA (%)"] = df_filtered["Price"].apply(lambda p: f"+{hitung_max_ara(p):.0f}%")

# 5. LAYOUT UTAMA
col_left, col_right = st.columns([1.4, 1.6], gap="medium")

selected_row = None
selected_ticker = None

with col_left:
    st.subheader("🎯 Watchlist Radar & Signals")
    if not df_filtered.empty:
        st.dataframe(
            df_filtered[["Ticker", "Price", "Change (%)", "Market Cap", "Signal", "Volume", "Target Min (+3%)", "Prediksi Potensi"]],
            use_container_width=True, hide_index=True, height=320
        )
        ticker_options = df_filtered["Ticker"].tolist()
    else:
        st.info("Watchlist kosong atau tidak ada saham yang sesuai dengan filter rentang harga.")
        ticker_options = []

    if search_input:
        st.caption(f"🔎 Menampilkan analisis langsung temporary untuk pencarian: **{search_input}**")
        custom_data = fetch_single_ticker_data(search_input)
        if custom_data:
            selected_ticker = search_input
            selected_row = custom_data
        else:
            st.error(f"Ticker '{search_input}' tidak ditemukan di BEI.")
    else:
        if ticker_options:
            selected_ticker = st.selectbox("Pilih Saham untuk Detail Plan:", ticker_options, index=0)
            selected_row = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0].to_dict()

# TRADING PLAN & METRICS
if selected_ticker and selected_row:
    area_beli = int(selected_row["Price"])
    market_cap_val = selected_row.get("Market Cap", "N/A")
    target_min = int(round(area_beli * 1.03))
    target_opt = int(round(area_beli * 1.05))
    max_ara_pct = hitung_max_ara(area_beli)
    harga_max_ara = int(round(area_beli * (1 + max_ara_pct / 100)))
    cut_loss = int(round(area_beli * 0.982))

    with col_right:
        st.subheader(f"📊 Trading Execution Plan: {selected_ticker}")
        st.caption(f"Cap: **{market_cap_val}** | Signal: **{selected_row.get('Signal', 'N/A')}** | Volume: **{selected_row.get('Volume', 'NORMAL')}**")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">AREA BELI</div><div class="metric-value">Rp {area_beli:,}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET (+3%)</div><div class="metric-value target-green">Rp {target_min:,}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET (+5%)</div><div class="metric-value target-magenta">Rp {target_opt:,}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">MAX ARA (+{max_ara_pct:.0f}%)</div><div class="metric-value target-gold">Rp {harga_max_ara:,}</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-label">CUT LOSS (-1.8%)</div><div class="metric-value cut-loss-red">Rp {cut_loss:,}</div></div>', unsafe_allow_html=True)
        
        st.write("")

        # 🧮 KALKULATOR LOT & POSITION SIZING
        with st.expander("🧮 Kalkulator Lot & Management Risiko (Position Size)", expanded=False):
            c_mod, c_risk = st.columns(2)
            with c_mod:
                modal_user = st.number_input("Modal Trading (Rp):", min_value=100000, value=10000000, step=500000)
            with c_risk:
                max_risk_pct = st.slider("Maksimal Toleransi Risiko (%):", min_value=0.5, max_value=5.0, value=1.8, step=0.1)

            max_rugi_rp = modal_user * (max_risk_pct / 100)
            rugi_per_lembar = area_beli - cut_loss
            if rugi_per_lembar > 0:
                max_lembar = max_rugi_rp / rugi_per_lembar
                max_lot = int(max_lembar // 100)
                total_investasi = max_lot * 100 * area_beli
            else:
                max_lot = 0
                total_investasi = 0

            st.info(f"👉 **Rekomendasi Entry**: **{max_lot:,} Lot** (Total Transaksi: **Rp {total_investasi:,.0f}**)\n\nMaksimal Risiko Kerugian (Cut Loss): **Rp {max_rugi_rp:,.0f}**")

        # TIMEFRAME CONTROL
        timeframe = st.radio("Pilih Timeframe Chart:", ["1m", "5m", "15m", "1d"], index=1, horizontal=True)

        try:
            tf_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "1d": ("1mo", "1d")}
            p, i = tf_map[timeframe]
            intraday = yf.Ticker(f"{selected_ticker}.JK").history(period=p, interval=i)
            
            if not intraday.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=intraday.index, y=intraday["Close"], mode='lines', name='Price', line=dict(color='#00f0ff', width=2)))
                
                # VWAP
                vwap = (intraday["Volume"] * (intraday["High"] + intraday["Low"] + intraday["Close"]) / 3).cumsum() / intraday["Volume"].cumsum()
                fig.add_trace(go.Scatter(x=intraday.index, y=vwap, mode='lines', name='VWAP', line=dict(color='#ff2a85', width=1.5, dash='dot')))

                fig.add_hline(y=target_min, line_dash="dash", line_color="#00f0ff", annotation_text=f"Target Min (+3%): {target_min}")
                fig.add_hline(y=cut_loss, line_dash="dash", line_color="#ff5252", annotation_text=f"Cut Loss: {cut_loss}")

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(13, 6, 40, 0.5)',
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#ffffff"))
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data grafik tidak tersedia saat bursa tutup.")
        except Exception:
            st.warning("Gagal memuat grafik intraday.")
