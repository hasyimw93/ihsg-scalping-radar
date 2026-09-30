import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="IHSG Scalping Radar - Live Data",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. INJEKSI CUSTOM CSS
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
        margin-bottom: 25px;
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
        padding: 14px;
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
        margin-bottom: 6px;
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
</style>
""", unsafe_allow_html=True)

# 3. HEADER BANNER
st.markdown("""
<div class="main-header">
    <h1>⚡ IHSG High-Potential Scalping Radar</h1>
    <p>Aplikasi Smart Screening, Profit Target (+3% s/d Max ARA) & Execution Plan</p>
</div>
""", unsafe_allow_html=True)

# LIST TICKER REKOMENDASI DEFAULT
TICKERS_RADAR = ["TEBE", "JPFA", "TLKM", "BBCA", "BMRI", "UNTR", "ASII", "JARR", "AMRT", "CPIN", "TPIA", "AKRA", "BRIS", "ERAA", "PGAS", "ANTM", "ACES", "BBYB", "BUMI", "RAAM"]

# KAMUS SHARES OUTSTANDING (KAPITALISASI STABIL JIKA API DI-BLOCK CLOUD)
ESTIMATED_SHARES = {
    "TEBE": 1285000000,
    "JPFA": 11726575001,
    "TLKM": 99062216600,
    "CPIN": 16398000000,
    "BBCA": 123275000000,
    "BMRI": 93333333333,
    "UNTR": 3730135123,
    "ASII": 40483553140,
    "JARR": 12000000000,
    "AMRT": 41524500000,
    "TPIA": 86522000000,
    "AKRA": 20073000000,
    "BRIS": 46128000000,
    "ERAA": 15920000000,
    "PGAS": 24241000000,
    "ANTM": 24030000000,
    "ACES": 17150000000,
    "BBYB": 13320000000,
    "BUMI": 371000000000,
    "RAAM": 8500000000
}

# FUNGSI HITUNG ARA
def hitung_max_ara(price):
    if price <= 200:
        return 35.0
    elif price <= 5000:
        return 25.0
    else:
        return 20.0

# FUNGSI FORMAT MARKET CAP
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

# FUNGSI AMBIL DATA TICKER DENGAN FALLBACK AMAN CLOUD
def fetch_single_ticker_data(symbol):
    try:
        clean_symbol = symbol.strip().upper()
        ticker_jk = f"{clean_symbol}.JK"
        stock = yf.Ticker(ticker_jk)
        hist = stock.history(period="1d")
        
        if not hist.empty:
            current_price = int(round(hist["Close"].iloc[-1]))
            prev_close = int(round(hist["Open"].iloc[0]))
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
            
            # AMBIL MARKET CAP: JIKA FAST_INFO/INFO DI-BLOCK CLOUD, HITUNG DARI HARGA * SHARES
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
                "Prediksi Potensi": potensi
            }
    except Exception:
        return None
    return None

# FUNGSI FETCH DENGAN CACHE
@st.cache_data(ttl=60)
def fetch_live_market_data(ticker_list):
    results = []
    for symbol in ticker_list:
        data = fetch_single_ticker_data(symbol)
        if data:
            results.append(data)
    return pd.DataFrame(results)

with st.spinner("Mengambil data pasar live & Market Cap dari BEI..."):
    df_master = fetch_live_market_data(TICKERS_RADAR)

# 4. KONTROL FILTER & PENCARIAN SAHAM
c_filter, c_search = st.columns([1.5, 1], gap="medium")

with c_filter:
    kategori_harga = st.selectbox(
        "📌 Pilih Kategori Harga Saham:",
        [
            "Semua Saham",
            "1. Di atas Rp 4.000",
            "2. Rp 3.000 - Rp 4.000",
            "3. Rp 2.000 - Rp 3.000",
            "4. Rp 1.000 - Rp 2.000",
            "5. Rp 500 - Rp 1.000",
            "6. Rp 1 - Rp 500"
        ],
        index=3
    )

with c_search:
    search_input = st.text_input(
        "🔍 Cari Saham di luar Sinyal Rekomendasi:",
        placeholder="Ketik kode ticker (contoh: UNVR, GOTO, BBRI)",
        help="Ketik kode saham apa saja dari Bursa Efek Indonesia untuk dianalisis langsung"
    ).strip().upper()

# FILTERING DATA UNTUK TABEL RADAR
if kategori_harga == "1. Di atas Rp 4.000":
    df_filtered = df_master[df_master["Price"] > 4000].copy()
elif kategori_harga == "2. Rp 3.000 - Rp 4.000":
    df_filtered = df_master[(df_master["Price"] >= 3000) & (df_master["Price"] <= 4000)].copy()
elif kategori_harga == "3. Rp 2.000 - Rp 3.000":
    df_filtered = df_master[(df_master["Price"] >= 2000) & (df_master["Price"] < 3000)].copy()
elif kategori_harga == "4. Rp 1.000 - Rp 2.000":
    df_filtered = df_master[(df_master["Price"] >= 1000) & (df_master["Price"] < 2000)].copy()
elif kategori_harga == "5. Rp 500 - Rp 1.000":
    df_filtered = df_master[(df_master["Price"] >= 500) & (df_master["Price"] < 1000)].copy()
elif kategori_harga == "6. Rp 1 - Rp 500":
    df_filtered = df_master[(df_master["Price"] >= 1) & (df_master["Price"] < 500)].copy()
else:
    df_filtered = df_master.copy()

if not df_filtered.empty:
    df_filtered["Target Min (+3%)"] = (df_filtered["Price"] * 1.03).round().astype(int)
    df_filtered["Max Potensi (%)"] = df_filtered["Price"].apply(lambda p: f"+{hitung_max_ara(p):.0f}% (ARA)")

# 5. LAYOUT UTAMA
col_left, col_right = st.columns([1.4, 1.6], gap="medium")

selected_row = None
selected_ticker = None

with col_left:
    st.subheader("🎯 Radar Saham Potensi Naik")
    
    if not df_filtered.empty:
        st.dataframe(
            df_filtered[["Ticker", "Price", "Market Cap", "Target Min (+3%)", "Max Potensi (%)", "Prediksi Potensi"]], 
            use_container_width=True, 
            hide_index=True, 
            height=340
        )
        ticker_list_options = df_filtered["Ticker"].tolist()
    else:
        st.info("Tidak ada saham rekomendasi di rentang harga ini.")
        ticker_list_options = []

    if search_input:
        st.caption(f"🔎 Menampilkan analisis langsung untuk pencarian: **{search_input}**")
        custom_data = fetch_single_ticker_data(search_input)
        if custom_data:
            selected_ticker = search_input
            selected_row = custom_data
        else:
            st.error(f"Ticker '{search_input}' tidak ditemukan di BEI. Pastikan kode ticker benar.")
    else:
        if ticker_list_options:
            selected_ticker = st.selectbox("Pilih Saham untuk Detail Plan:", ticker_list_options, index=0)
            selected_row = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0].to_dict()

# DISPLAY TRADING PLAN & METRICS
if selected_ticker and selected_row:
    area_beli = int(selected_row["Price"])
    market_cap_val = selected_row.get("Market Cap", "N/A")
    target_min = int(round(area_beli * 1.03))
    target_opt = int(round(area_beli * 1.05))
    max_ara_pct = hitung_max_ara(area_beli)
    harga_max_ara = int(round(area_beli * (1 + max_ara_pct / 100)))
    cut_loss = int(round(area_beli * 0.982))

    with col_right:
        st.subheader(f"📊 Trading Plan: {selected_ticker}")
        st.caption(f"Market Capitalization: **{market_cap_val}**")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">AREA BELI</div><div class="metric-value">Rp {area_beli:,}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET MIN (+3%)</div><div class="metric-value target-green">Rp {target_min:,}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">TARGET 2 (+5%)</div><div class="metric-value target-magenta">Rp {target_opt:,}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-card"><div class="metric-label">MAX ARA (+{max_ara_pct:.0f}%)</div><div class="metric-value target-gold">Rp {harga_max_ara:,}</div></div>', unsafe_allow_html=True)
        with m5:
            st.markdown(f'<div class="metric-card"><div class="metric-label">CUT LOSS (-1.8%)</div><div class="metric-value cut-loss-red">Rp {cut_loss:,}</div></div>', unsafe_allow_html=True)
        
        st.write("") 

        # CHART INTRADAY
        try:
            intraday = yf.Ticker(f"{selected_ticker}.JK").history(period="1d", interval="5m")
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
                    height=320,
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#ffffff"))
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data grafik intraday tidak tersedia saat pasar tutup.")
        except Exception:
            st.warning("Gagal memuat grafik intraday.")
