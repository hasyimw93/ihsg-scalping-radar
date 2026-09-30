import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="IHSG Scalping Radar",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Radar Saham Potensi Naik (IHSG)")

# ---------------------------------------------------------
# 1. Daftar Saham Berdasarkan Kategori Harga
# ---------------------------------------------------------
CATEGORIES = {
    "1. Rp 50 – Rp 500": [
        "BUKA.JK", "GOTO.JK", "BUMI.JK", "ENRG.JK", "DOOH.JK", 
        "FREN.JK", "DEWA.JK", "BIPI.JK", "KAYU.JK", "NATO.JK"
    ],
    "2. Rp 500 – Rp 2.000": [
        "BBHI.JK", "BRIS.JK", "PGAS.JK", "ANTM.JK", "PTBA.JK", 
        "MEDC.JK", "ADRO.JK", "MDKA.JK", "MBMA.JK", "EMTK.JK"
    ],
    "3. Rp 2.000 – Rp 3.000": [
        "TEBE.JK", "JPFA.JK", "TLKM.JK", "CPIN.JK"
    ],
    "4. Di atas Rp 3.000": [
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", 
        "UNTR.JK", "INDF.JK", "GGRM.JK", "ICBP.JK", "KLBF.JK"
    ]
}

selected_category = st.selectbox(
    "📌 Pilih Kategori Harga Saham:",
    options=list(CATEGORIES.keys()),
    index=2  # Default ke Kategori 3 (Rp 2.000 - Rp 3.000)
)

tickers_to_scan = CATEGORIES[selected_category]

# ---------------------------------------------------------
# 2. Fungsi Pembantu Ambil Data & Format Market Cap
# ---------------------------------------------------------
def get_stock_data(ticker_symbol):
    clean_ticker = ticker_symbol.replace(".JK", "")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Ambil Harga Terakhir & Market Cap menggunakan fast_info (Tahan Rate Limit Cloud)
    price = None
    market_cap = None
    
    try:
        fast_info = ticker.fast_info
        price = fast_info.last_price
        market_cap = fast_info.market_cap
    except Exception:
        pass

    # Fallback jika fast_info gagal
    if price is None or np.isnan(price):
        try:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        except Exception:
            price = 0

    if market_cap is None or np.isnan(market_cap):
        try:
            market_cap = ticker.info.get('marketCap', 0)
        except Exception:
            market_cap = 0

    # Format Tampilan Market Cap
    if isinstance(market_cap, (int, float)) and market_cap > 0:
        if market_cap >= 1e12:
            market_cap_str = f"Rp {market_cap / 1e12:.2f} T"
        elif market_cap >= 1e9:
            market_cap_str = f"Rp {market_cap / 1e9:.2f} B"
        else:
            market_cap_str = f"Rp {market_cap:,.0f}"
    else:
        market_cap_str = "N/A"

    # Perhitungan Target & Prediksi Potensi
    if price and price > 0:
        price_int = int(round(price))
        target_min = int(round(price_int * 1.03))  # Target Minimum +3%
        
        # Logika Prediksi Sederhana
        if clean_ticker in ["TEBE", "JPFA", "CPIN"]:
            prediksi = "🔥 HIGH POTENTIAL"
        else:
            prediksi = "⚡ MEDIUM POTENTIAL"
            
        max_potensi = "+25% (ARA)"
    else:
        price_int = 0
        target_min = 0
        max_potensi = "N/A"
        prediksi = "N/A"

    return {
        "Ticker": clean_ticker,
        "Price": price_int,
        "Market Cap": market_cap_str,
        "Target Min (+3%)": target_min,
        "Max Potensi (%)": max_potensi,
        "Prediksi Potensi": prediksi
    }

# ---------------------------------------------------------
# 3. Proses Ambil Data Semua Ticker
# ---------------------------------------------------------
with st.spinner("Mengambil data saham..."):
    data_list = []
    for symbol in tickers_to_scan:
        data_list.append(get_stock_data(symbol))

df = pd.DataFrame(data_list)

# Tampilkan Tabel Radar
st.markdown("### 🎯 Radar Saham Potensi Naik")
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------------
# 4. Detail Plan Pilihan Saham
# ---------------------------------------------------------
st.markdown("---")
selected_ticker = st.selectbox(
    "Pilih Saham untuk Detail Plan:",
    options=df["Ticker"].tolist()
)

selected_row = df[df["Ticker"] == selected_ticker].iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Harga Saat Ini", f"Rp {selected_row['Price']:,}")
with col2:
    st.metric("Target Min (+3%)", f"Rp {selected_row['Target Min (+3%)']:,}")
with col3:
    st.metric("Market Cap", selected_row["Market Cap"])
