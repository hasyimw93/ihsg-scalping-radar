import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta
import sqlite3
import json
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="Analisis Saham PRO",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #17becf);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .bullish { color: #26a69a; font-weight: bold; }
    .bearish { color: #ef5350; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)


# ==================== DATABASE ====================
def init_db():
    """Inisialisasi database SQLite untuk watchlist & portfolio"""
    conn = sqlite3.connect('saham.db', check_same_thread=False)
    c = conn.cursor()
    
    # Watchlist
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE,
        tanggal_ditambah TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Portfolio
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        jumlah REAL,
        harga_beli REAL,
        tanggal_beli DATE,
        catatan TEXT
    )''')
    
    # Alert
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        harga_target REAL,
        kondisi TEXT,
        aktif INTEGER DEFAULT 1,
        dibuat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    return conn

conn = init_db()

def db_query(query, params=()):
    """Execute query dan return dataframe"""
    return pd.read_sql_query(query, conn, params=params)

def db_execute(query, params=()):
    """Execute query tanpa return"""
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()


# ==================== FUNGSI CACHE ====================
@st.cache_data(ttl=300)
def ambil_data(ticker, periode, interval):
    try:
        data = yf.download(ticker, period=periode, interval=interval,
                           progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return None

@st.cache_data(ttl=3600)
def ambil_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

@st.cache_data(ttl=600)
def ambil_berita(ticker):
    """Ambil berita dari Yahoo Finance"""
    try:
        news = yf.Ticker(ticker).news
        return news if news else []
    except:
        return []


def format_angka(x):
    if x is None or pd.isna(x):
        return "N/A"
    if abs(x) >= 1e12:
        return f"{x/1e12:.2f} T"
    elif abs(x) >= 1e9:
        return f"{x/1e9:.2f} B"
    elif abs(x) >= 1e6:
        return f"{x/1e6:.2f} M"
    elif abs(x) >= 1e3:
        return f"{x/1e3:.2f} K"
    return f"{x:.2f}"


# ==================== PREDIKSI HARGA ====================
def prediksi_harga(data, hari_ke_depan=30):
    """Prediksi harga dengan Linear Regression + Random Forest"""
    df = data.copy()
    df['Hari'] = np.arange(len(df))
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Return'] = df['Close'].pct_change()
    df['Volatilitas'] = df['Return'].rolling(20).std()
    
    df = df.dropna()
    
    if len(df) < 50:
        return None, None
    
    # Fitur
    X = df[['Hari', 'MA5', 'MA20', 'Volatilitas']].values
    y = df['Close'].values
    
    # Model 1: Linear Regression
    lr = LinearRegression()
    lr.fit(X, y)
    
    # Model 2: Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    # Prediksi masa depan
    last_hari = df['Hari'].iloc[-1]
    last_ma5 = df['MA5'].iloc[-1]
    last_ma20 = df['MA20'].iloc[-1]
    last_vol = df['Volatilitas'].iloc[-1]
    
    future_hari = np.arange(last_hari + 1, last_hari + hari_ke_depan + 1)
    future_X = np.column_stack([
        future_hari,
        np.full(hari_ke_depan, last_ma5),
        np.full(hari_ke_depan, last_ma20),
        np.full(hari_ke_depan, last_vol)
    ])
    
    pred_lr = lr.predict(future_X)
    pred_rf = rf.predict(future_X)
    pred_avg = (pred_lr + pred_rf) / 2
    
    future_dates = pd.date_range(
        start=data.index[-1] + timedelta(days=1),
        periods=hari_ke_depan,
        freq='D'
    )
    
    hasil = pd.DataFrame({
        'Tanggal': future_dates,
        'Prediksi_LR': pred_lr,
        'Prediksi_RF': pred_rf,
        'Prediksi_Rata': pred_avg
    })
    
    return hasil, (lr, rf)


# ==================== ANALISIS SENTIMEN ====================
def analisis_sentimen(berita_list):
    """Analisis sentimen berita dengan VADER"""
    analyzer = SentimentIntensityAnalyzer()
    hasil = []
    
    for berita in berita_list[:15]:
        try:
            judul = berita.get('title', '')
            publisher = berita.get('publisher', 'N/A')
            link = berita.get('link', '')
            waktu = berita.get('providerPublishTime', 0)
            
            if waktu:
                tanggal = datetime.fromtimestamp(waktu).strftime('%Y-%m-%d %H:%M')
            else:
                tanggal = 'N/A'
            
            skor = analyzer.polarity_scores(judul)
            compound = skor['compound']
            
            if compound >= 0.05:
                sentimen = "🟢 Positif"
            elif compound <= -0.05:
                sentimen = "🔴 Negatif"
            else:
                sentimen = "⚪ Netral"
            
            hasil.append({
                'Judul': judul,
                'Publisher': publisher,
                'Tanggal': tanggal,
                'Sentimen': sentimen,
                'Skor': round(compound, 3),
                'Link': link
            })
        except:
            continue
    
    return pd.DataFrame(hasil)


# ==================== SIDEBAR ====================
st.sidebar.markdown("# 📈 Saham PRO")
st.sidebar.markdown("---")

# Menu utama
menu = st.sidebar.radio(
    "📍 Menu",
    ["🔍 Analisis Saham", "⭐ Watchlist", "💼 Portfolio", "🔔 Alerts", "📊 Bandingkan"]
)

st.sidebar.markdown("---")

# Daftar saham populer
saham_populer = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "UNVR.JK": "Unilever Indonesia",
    "ICBP.JK": "Indofood CBP",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "META": "Meta Platforms"
}


# ==================== HALAMAN: ANALISIS SAHAM ====================
if menu == "🔍 Analisis Saham":
    
    st.markdown('<div class="main-header"><h1>📈 Analisis Saham Pro</h1></div>', 
                unsafe_allow_html=True)
    
    # Input di sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Pengaturan")
        
        pilihan = st.selectbox(
            "Pilih Saham",
            options=["-- Manual --"] + list(saham_populer.keys()),
            format_func=lambda x: f"{x} - {saham_populer[x]}" if x in saham_populer else x
        )
        
        ticker = st.text_input("Kode Saham", 
                               value=pilihan if pilihan != "-- Manual --" else "BBCA.JK").upper()
        
        periode = st.selectbox("Periode", 
                               ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
        
        st.markdown("### 📊 Indikator Teknikal")
        show_ma = st.checkbox("Moving Average", True)
        show_bb = st.checkbox("Bollinger Bands", False)
        show_rsi = st.checkbox("RSI", True)
        show_macd = st.checkbox("MACD", False)
        
        if show_ma:
            ma_short = st.slider("MA Pendek", 5, 50, 20)
            ma_long = st.slider("MA Panjang", 20, 200, 50)
        
        st.markdown("---")
        if st.button("⭐ Tambah ke Watchlist"):
            try:
                db_execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker,))
                st.success(f"{ticker} ditambahkan ke watchlist!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Ambil data
    with st.spinner("Mengambil data saham..."):
        data = ambil_data(ticker, periode, interval)
        info = ambil_info(ticker)
    
    if data is None or data.empty:
        st.error(f"❌ Data untuk {ticker} tidak ditemukan!")
        st.stop()
    
    # Header info
    nama = info.get("longName", ticker)
    harga_skrg = data['Close'].iloc[-1]
    harga_lalu = data['Close'].iloc[-2] if len(data) > 1 else harga_skrg
    perubahan = harga_skrg - harga_lalu
    persen = (perubahan / harga_lalu) * 100
    
    st.markdown(f"## {nama} ({ticker})")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Harga", f"{harga_skrg:,.2f}",
                 f"{perubahan:+.2f} ({persen:+.2f}%)")
    with col2:
        high_52 = data['High'].tail(252).max() if len(data) >= 252 else data['High'].max()
        st.metric("📊 High 52W", f"{high_52:,.2f}")
    with col3:
        low_52 = data['Low'].tail(252).min() if len(data) >= 252 else data['Low'].min()
        st.metric("📉 Low 52W", f"{low_52:,.2f}")
    with col4:
        st.metric("📦 Volume", format_angka(data['Volume'].iloc[-1]))
    with col5:
        mcap = info.get('marketCap', 0)
        st.metric("🏦 Market Cap", format_angka(mcap))
    
    st.divider()
    
    # TABS UTAMA
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Chart", "💼 Fundamental", "🔮 Prediksi",
        "📰 Sentimen", "📋 Data", "🚦 Sinyal"
    ])
    
    # ============ TAB 1: CHART ============
    with tab1:
        df = data.copy()
        
        if show_ma:
            df[f'MA{ma_short}'] = df['Close'].rolling(ma_short).mean()
            df[f'MA{ma_long}'] = df['Close'].rolling(ma_long).mean()
        
        if show_bb:
            bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
            df['BB_Upper'] = bb.bollinger_hband()
            df['BB_Lower'] = bb.bollinger_lband()
        
        if show_rsi:
            df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        if show_macd:
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Diff'] = macd.macd_diff()
        
        subplot_count = 1
        row_heights = [0.6]
        if show_rsi:
            subplot_count += 1
            row_heights.append(0.2)
        if show_macd:
            subplot_count += 1
            row_heights.append(0.2)
        
        total = sum(row_heights)
        row_heights = [h/total for h in row_heights]
        
        fig = make_subplots(rows=subplot_count, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03, row_heights=row_heights)
        
        fig.add_trace(
            go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                          low=df['Low'], close=df['Close'], name='Harga',
                          increasing_line_color='#26a69a',
                          decreasing_line_color='#ef5350'),
            row=1, col=1
        )
        
        if show_ma:
            fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma_short}'],
                                    name=f'MA {ma_short}',
                                    line=dict(color='orange', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df[f'MA{ma_long}'],
                                    name=f'MA {ma_long}',
                                    line=dict(color='blue', width=1.5)), row=1, col=1)
        
        if show_bb:
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper',
                                    line=dict(color='gray', dash='dash', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower',
                                    line=dict(color='gray', dash='dash', width=1),
                                    fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
        
        current_row = 2
        if show_rsi:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                                    line=dict(color='purple', width=1.5)), row=current_row, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
            fig.update_yaxes(title_text="RSI", row=current_row, col=1)
            current_row += 1
        
        if show_macd:
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD',
                                    line=dict(color='blue', width=1.5)), row=current_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal',
                                    line=dict(color='red', width=1.5)), row=current_row, col=1)
            colors = ['green' if v >= 0 else 'red' for v in df['MACD_Diff'].fillna(0)]
            fig.add_trace(go.Bar(x=df.index, y=df['MACD_Diff'], name='Histogram',
                                marker_color=colors), row=current_row, col=1)
            fig.update_yaxes(title_text="MACD", row=current_row, col=1)
        
        fig.update_layout(height=700, xaxis_rangeslider_visible=False,
                         hovermode='x unified',
                         legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                    xanchor="right", x=1),
                         margin=dict(l=10, r=10, t=30, b=10))
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ============ TAB 2: FUNDAMENTAL ============
    with tab2:
        st.subheader("💼 Data Fundamental")
        
        if info:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Market Cap", format_angka(info.get("marketCap")))
                pe = info.get('trailingPE')
                st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
            with col2:
                eps = info.get('trailingEps')
                st.metric("EPS", f"{eps:.2f}" if eps else "N/A")
                pb = info.get('priceToBook')
                st.metric("P/B Ratio", f"{pb:.2f}" if pb else "N/A")
            with col3:
                dy = info.get('dividendYield')
                st.metric("Dividend Yield", f"{dy*100:.2f}%" if dy else "N/A")
                beta = info.get('beta')
                st.metric("Beta", f"{beta:.2f}" if beta else "N/A")
            with col4:
                st.metric("52W High", f"{info.get('fiftyTwoWeekHigh', 'N/A')}")
                st.metric("52W Low", f"{info.get('fiftyTwoWeekLow', 'N/A')}")
            
            st.divider()
            st.subheader("🏢 Profil")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Sektor:** {info.get('sector', 'N/A')}")
                st.write(f"**Industri:** {info.get('industry', 'N/A')}")
            with c2:
                st.write(f"**Negara:** {info.get('country', 'N/A')}")
                st.write(f"**Karyawan:** {format_angka(info.get('fullTimeEmployees'))}")
            
            deskripsi = info.get('longBusinessSummary', '')
            if deskripsi:
                with st.expander("📖 Deskripsi Bisnis"):
                    st.write(deskripsi)
        else:
            st.warning("Data fundamental tidak tersedia.")
    
    # ============ TAB 3: PREDIKSI ============
    with tab3:
        st.subheader("🔮 Prediksi Harga (Machine Learning)")
        st.caption("Menggunakan Linear Regression + Random Forest")
        
        hari_prediksi = st.slider("Prediksi berapa hari ke depan?", 7, 90, 30)
        
        if st.button("🚀 Jalankan Prediksi", type="primary"):
            with st.spinner("Melatih model..."):
                hasil, models = prediksi_harga(data, hari_prediksi)
            
            if hasil is None:
                st.error("Data tidak cukup untuk prediksi (butuh minimal 50 hari)")
            else:
                # Chart prediksi
                fig = go.Figure()
                
                # Data historis
                fig.add_trace(go.Scatter(
                    x=data.index[-60:], y=data['Close'].tail(60),
                    name='Historis', line=dict(color='blue', width=2)
                ))
                
                # Prediksi
                fig.add_trace(go.Scatter(
                    x=hasil['Tanggal'], y=hasil['Prediksi_Rata'],
                    name='Prediksi Rata-rata',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=hasil['Tanggal'], y=hasil['Prediksi_LR'],
                    name='Linear Regression',
                    line=dict(color='green', width=1, dash='dot')
                ))
                
                fig.add_trace(go.Scatter(
                    x=hasil['Tanggal'], y=hasil['Prediksi_RF'],
                    name='Random Forest',
                    line=dict(color='orange', width=1, dash='dot')
                ))
                
                fig.update_layout(
                    title=f"Prediksi {ticker} - {hari_prediksi} Hari ke Depan",
                    xaxis_title="Tanggal",
                    yaxis_title="Harga",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabel prediksi
                st.subheader("📊 Hasil Prediksi")
                
                harga_pred_akhir = hasil['Prediksi_Rata'].iloc[-1]
                perubahan_pred = ((harga_pred_akhir - harga_skrg) / harga_skrg) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Harga Saat Ini", f"{harga_skrg:,.2f}")
                with col2:
                    st.metric(f"Prediksi {hari_prediksi} Hari", 
                             f"{harga_pred_akhir:,.2f}",
                             f"{perubahan_pred:+.2f}%")
                with col3:
                    if perubahan_pred > 5:
                        st.success("🟢 Potensi NAIK signifikan")
                    elif perubahan_pred > 0:
                        st.info("🟢 Potensi naik")
                    elif perubahan_pred > -5:
                        st.warning("🔴 Potensi turun")
                    else:
                        st.error("🔴 Potensi TURUN signifikan")
                
                st.dataframe(hasil.round(2), use_container_width=True)
                
                st.caption("⚠️ Prediksi ini berdasarkan data historis, bukan jaminan masa depan.")
    
    # ============ TAB 4: SENTIMEN ============
    with tab4:
        st.subheader("📰 Analisis Sentimen Berita")
        
        with st.spinner("Mengambil berita..."):
            berita = ambil_berita(ticker)
        
        if not berita:
            st.warning("Tidak ada berita tersedia untuk saham ini.")
        else:
            df_berita = analisis_sentimen(berita)
            
            if df_berita.empty:
                st.warning("Gagal menganalisis berita.")
            else:
                # Ringkasan sentimen
                positif = len(df_berita[df_berita['Sentimen'].str.contains('Positif')])
                negatif = len(df_berita[df_berita['Sentimen'].str.contains('Negatif')])
                netral = len(df_berita[df_berita['Sentimen'].str.contains('Netral')])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Berita", len(df_berita))
                with col2:
                    st.metric("🟢 Positif", positif)
                with col3:
                    st.metric("🔴 Negatif", negatif)
                with col4:
                    st.metric("⚪ Netral", netral)
                
                # Skor rata-rata
                skor_rata = df_berita['Skor'].mean()
                if skor_rata >= 0.05:
                    st.success(f"### 📊 Sentimen Keseluruhan: POSITIF ({skor_rata:.3f})")
                elif skor_rata <= -0.05:
                    st.error(f"### 📊 Sentimen Keseluruhan: NEGATIF ({skor_rata:.3f})")
                else:
                    st.info(f"### 📊 Sentimen Keseluruhan: NETRAL ({skor_rata:.3f})")
                
                # Chart distribusi
                fig = go.Figure(data=[go.Pie(
                    labels=['Positif', 'Negatif', 'Netral'],
                    values=[positif, negatif, netral],
                    marker_colors=['#26a69a', '#ef5350', '#95a5a6'],
                    hole=0.4
                )])
                fig.update_layout(title="Distribusi Sentimen", height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Daftar berita
                st.subheader("📋 Daftar Berita")
                for _, row in df_berita.iterrows():
                    with st.expander(f"{row['Sentimen']} | {row['Judul'][:80]}..."):
                        st.write(f"**Publisher:** {row['Publisher']}")
                        st.write(f"**Tanggal:** {row['Tanggal']}")
                        st.write(f"**Skor Sentimen:** {row['Skor']}")
                        if row['Link']:
                            st.markdown(f"[🔗 Baca selengkapnya]({row['Link']})")
    
    # ============ TAB 5: DATA ============
    with tab5:
        st.subheader("📋 Data Historis")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rata-rata Close", f"{data['Close'].mean():,.2f}")
        with col2:
            st.metric("Volatilitas", f"{data['Close'].pct_change().std()*100:.2f}%")
        with col3:
            st.metric("Max", f"{data['Close'].max():,.2f}")
        with col4:
            st.metric("Min", f"{data['Close'].min():,.2f}")
        
        st.subheader("📈 Return per Periode")
        returns = {
            "1H": (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100 if len(data) > 1 else 0,
            "1M": (data['Close'].iloc[-1] / data['Close'].iloc[-22] - 1) * 100 if len(data) > 22 else 0,
            "3M": (data['Close'].iloc[-1] / data['Close'].iloc[-66] - 1) * 100 if len(data) > 66 else 0,
            "6M": (data['Close'].iloc[-1] / data['Close'].iloc[-132] - 1) * 100 if len(data) > 132 else 0,
            "1Y": (data['Close'].iloc[-1] / data['Close'].iloc[-252] - 1) * 100 if len(data) > 252 else 0,
        }
        
        cols = st.columns(len(returns))
        for i, (label, ret) in enumerate(returns.items()):
            with cols[i]:
                st.metric(label, f"{ret:+.2f}%")
        
        st.dataframe(data.round(2).sort_index(ascending=False), use_container_width=True)
        
        csv = data.to_csv().encode('utf-8')
        st.download_button("📥 Download CSV", csv, f"{ticker}_data.csv", "text/csv")
    
    # ============ TAB 6: SINYAL ============
    with tab6:
        st.subheader("🚦 Ringkasan Sinyal Trading")
        
        skor = 0
        sinyal = []
        
        if len(data) > 50:
            ma20 = data['Close'].rolling(20).mean().iloc[-1]
            ma50 = data['Close'].rolling(50).mean().iloc[-1]
            if ma20 > ma50:
                skor += 1
                sinyal.append(("✅", "Trend Bullish (MA20 > MA50)"))
            else:
                skor -= 1
                sinyal.append(("❌", "Trend Bearish (MA20 < MA50)"))
        
        rsi_series = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
        rsi_now = rsi_series.iloc[-1]
        if rsi_now < 30:
            skor += 1
            sinyal.append(("✅", f"RSI Oversold ({rsi_now:.1f})"))
        elif rsi_now > 70:
            skor -= 1
            sinyal.append(("❌", f"RSI Overbought ({rsi_now:.1f})"))
        else:
            sinyal.append(("⚪", f"RSI Netral ({rsi_now:.1f})"))
        
        macd_obj = ta.trend.MACD(data['Close'])
        if macd_obj.macd().iloc[-1] > macd_obj.macd_signal().iloc[-1]:
            skor += 1
            sinyal.append(("✅", "MACD Bullish"))
        else:
            skor -= 1
            sinyal.append(("❌", "MACD Bearish"))
        
        for icon, text in sinyal:
            st.write(f"{icon} {text}")
        
        st.divider()
        
        if skor >= 2:
            st.success(f"### 🟢 BULLISH (Skor: {skor})")
        elif skor <= -2:
            st.error(f"### 🔴 BEARISH (Skor: {skor})")
        else:
            st.warning(f"### ⚪ NETRAL (Skor: {skor})")
        
        st.caption("⚠️ Disclaimer: Bukan rekomendasi investasi. DYOR!")


# ==================== HALAMAN: WATCHLIST ====================
elif menu == "⭐ Watchlist":
    st.title("⭐ Watchlist Saya")
    
    with st.sidebar:
        st.markdown("### ➕ Tambah Saham")
        ticker_baru = st.text_input("Kode Saham").upper()
        if st.button("Tambah"):
            if ticker_baru:
                try:
                    db_execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", 
                              (ticker_baru,))
                    st.success(f"✅ {ticker_baru} ditambahkan!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    df_watch = db_query("SELECT * FROM watchlist ORDER BY tanggal_ditambah DESC")
    
    if df_watch.empty:
        st.info("Watchlist masih kosong. Tambahkan saham dari sidebar!")
    else:
        for _, row in df_watch.iterrows():
            tk = row['ticker']
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {tk}")
            with col2:
                try:
                    d = ambil_data(tk, "5d", "1d")
                    if d is not None and not d.empty:
                        h = d['Close'].iloc[-1]
                        h_lalu = d['Close'].iloc[-2] if len(d) > 1 else h
                        delta = ((h - h_lalu) / h_lalu) * 100
                        st.metric("Harga", f"{h:,.2f}", f"{delta:+.2f}%")
                except:
                    st.write("N/A")
            with col3:
                st.caption(f"Ditambahkan: {row['tanggal_ditambah']}")
            with col4:
                if st.button("🗑️", key=f"del_{tk}"):
                    db_execute("DELETE FROM watchlist WHERE ticker = ?", (tk,))
                    st.rerun()
            st.divider()


# ==================== HALAMAN: PORTFOLIO ====================
elif menu == "💼 Portfolio":
    st.title("💼 Portfolio Saya")
    
    with st.sidebar:
        st.markdown("### ➕ Tambah Transaksi")
        tk_p = st.text_input("Kode Saham").upper()
        jml = st.number_input("Jumlah Lembar", min_value=1.0, value=100.0)
        hrg = st.number_input("Harga Beli", min_value=0.01, value=1000.0)
        tgl = st.date_input("Tanggal Beli", datetime.now())
        catatan = st.text_input("Catatan (opsional)")
        
        if st.button("Tambah ke Portfolio"):
            if tk_p:
                db_execute(
                    "INSERT INTO portfolio (ticker, jumlah, harga_beli, tanggal_beli, catatan) VALUES (?,?,?,?,?)",
                    (tk_p, jml, hrg, tgl.strftime('%Y-%m-%d'), catatan)
                )
                st.success(f"✅ {tk_p} ditambahkan!")
                st.rerun()
    
    df_pf = db_query("SELECT * FROM portfolio ORDER BY tanggal_beli DESC")
    
    if df_pf.empty:
        st.info("Portfolio masih kosong. Tambahkan transaksi dari sidebar!")
    else:
        # Hitung nilai portfolio
        hasil = []
        for _, row in df_pf.iterrows():
            try:
                d = ambil_data(row['ticker'], "5d", "1d")
                harga_skrg = d['Close'].iloc[-1] if d is not None and not d.empty else 0
                nilai_beli = row['jumlah'] * row['harga_beli']
                nilai_skrg = row['jumlah'] * harga_skrg
                pnl = nilai_skrg - nilai_beli
                pnl_pct = (pnl /
