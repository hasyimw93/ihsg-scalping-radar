import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="IHSG Scalping Radar - Cyber Edition",
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

    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background: rgba(13, 6, 40, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 15px;
        backdrop-filter: blur(10px);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #00f0ff;
    }

    .metric-label {
        font-size: 12px;
        color: #b3a2c7;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #ffffff;
    }

    .target-green { color: #00f0ff; text-shadow: 0 0 10px rgba(0,240,255,0.6); }
    .target-magenta { color: #ff2a85; text-shadow: 0 0 10px rgba(255,42,133,0.6); }
    .cut-loss-red { color: #ff5252; }

    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stSelectbox label {
        color: #00f0ff !important;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# 3. HEADER BANNER
st.markdown("""
<div class="main-header">
    <h1>⚡ IHSG High-Potential Scalping Radar</h1>
    <p>Aplikasi Smart Screening & Execution Plan untuk Saham dengan Harga &lt; Rp 4.000</p>
</div>
""", unsafe_allow_html=True)

# 4. DATA RADAR SAHAM
data_radar = {
    "Ticker": ["ACES", "AKRA", "BBYB", "ERAA", "JARR", "JPFA", "TEBE", "RAAM", "TPIA", "BUMI"],
    "Price": [338, 1475, 200, 600, 3620, 2110, 2570, 165, 1785, 181],
    "Prediksi Potensi": ["🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", 
                        "🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", 
                        "🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", "🔥 HIGH POTENTIAL (+3%+)", 
                        "⚡ MEDIUM POTENTIAL"],
    "Vol Ratio": ["0.0x", "0.0x", "0.0x", "0.0x", "0.0x", "0.0x", "0.0x", "0.0x", "0.0x", "0.1x"],
    "Target Min (+3%)": [348, 1519, 206, 618, 3729, 2173, 2647, 170, 1839, 186]
}
df_radar = pd.DataFrame(data_radar)

# 5. LAYOUT UTAMA
col_left, col_right = st.columns([1.1, 1.9], gap="medium")

with col_left:
    st.subheader("🎯 Radar Saham Potensi Naik")
    st.dataframe(df_radar, use_container_width=True, hide_index=False, height=420)
    
    selected_ticker = st.selectbox("Pilih Saham untuk Detail Plan:", df_radar["Ticker"].tolist(), index=3)

# 6. KALKULASI PERHITUNGAN DINAMIS BERDASARKAN TICKER TERPILIH
selected_row = df_radar[df_radar["Ticker"] == selected_ticker].iloc[0]
area_beli = int(selected_row["Price"])
target_min = int(round(area_beli * 1.03))  # +3%
target_max = int(round(area_beli * 1.05))  # +5%
cut_loss = int(round(area_beli * 0.982))   # -1.8%

with col_right:
    st.subheader(f"📊 Trading Plan: {selected_ticker}")
    
    # Grid 4 Metric Cards Dinamis
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Area Beli</div>
            <div class="metric-value">Rp {area_beli:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Target Min (+3%)</div>
            <div class="metric-value target-green">Rp {target_min:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Target Max (+5%)</div>
            <div class="metric-value target-magenta">Rp {target_max:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cut Loss</div>
            <div class="metric-value cut-loss-red">Rp {cut_loss:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("") 

    # 7. CHART PLOTLY DINAMIS SESUAI HARGA SAHAM
    time_series = pd.date_range(start="2026-09-30 09:00", periods=50, freq="2min")
    np.random.seed(sum(ord(c) for c in selected_ticker)) # Seed unik tiap saham
    
    # Generate simulasi pergerakan dari harga Area Beli
    price_base = area_beli * 0.985
    price_data = price_base + np.cumsum(np.random.randn(50) * (area_beli * 0.003))
    price_data[30:] += (area_beli * 0.025)  # Jump breakout
    vwap_data = price_data - (area_beli * 0.005)

    fig = go.Figure()

    # Candle / Line Price
    fig.add_trace(go.Scatter(
        x=time_series, y=price_data,
        mode='lines', name='Price',
        line=dict(color='#00f0ff', width=2)
    ))

    # VWAP Line
    fig.add_trace(go.Scatter(
        x=time_series, y=vwap_data,
        mode='lines', name='VWAP',
        line=dict(color='#ff2a85', width=1.5, dash='dot')
    ))

    # Line Target & Cut Loss Dinamis
    fig.add_hline(y=target_min, line_dash="dash", line_color="#00f0ff", annotation_text=f"Target (+3%): {target_min}", annotation_position="top right")
    fig.add_hline(y=cut_loss, line_dash="dash", line_color="#ff5252", annotation_text=f"Cut Loss: {cut_loss}", annotation_position="bottom right")

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13, 6, 40, 0.5)',
        margin=dict(l=10, r=10, t=10, b=10),
        height=330,
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#b3a2c7'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#ffffff"))
    )

    st.plotly_chart(fig, use_container_width=True)
