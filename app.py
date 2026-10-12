import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import ta
import sqlite3

st.set_page_config(page_title="Saham PRO", layout="wide")

def init_db():
    conn = sqlite3.connect('saham.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT UNIQUE, tanggal_ditambah TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, jumlah REAL, harga_beli REAL, tanggal_beli DATE)')
    conn.commit()
    return conn

conn = init_db()

def db_query(query, params=()):
    return pd.read_sql_query(query, conn, params=params)

def db_execute(query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()

@st.cache_data(ttl=300)
def ambil_data(ticker, periode):
    try:
        data = yf.download(ticker, period=periode, interval="1d", progress=False, auto_adjust=True)
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

def format_angka(x):
    if x is None or pd.isna(x):
        return "N/A"
    if abs(x) >= 1e12:
        return str(round(x/1e12, 2)) + " T"
    elif abs(x) >= 1e9:
        return str(round(x/1e9, 2)) + " B"
    elif abs(x) >= 1e6:
        return str(round(x/1e6, 2)) + " M"
    elif abs(x) >= 1e3:
        return str(round(x/1e3, 2)) + " K"
    return str(round(x, 2))

st.sidebar.markdown("# Saham PRO")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Menu", ["Analisis Saham", "Watchlist", "Portfolio"])
st.sidebar.markdown("---")

saham_populer = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet",
    "MSFT": "Microsoft",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA"
}

if menu == "Analisis Saham":
    st.title("Analisis Saham PRO")
    
    with st.sidebar:
        st.markdown("### Pengaturan")
        pilihan = st.selectbox("Pilih Saham", options=["-- Manual --"] + list(saham_populer.keys()))
        default_tk = pilihan if pilihan != "-- Manual --" else "BBCA.JK"
        ticker = st.text_input("Kode Saham", value=default_tk).upper()
        periode = st.selectbox("Periode", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
        show_ma = st.checkbox("Moving Average", True)
        show_rsi = st.checkbox("RSI", True)
        show_macd = st.checkbox("MACD", False)
        
        if show_ma:
            ma_short = st.slider("MA Pendek", 5, 50, 20)
            ma_long = st.slider("MA Panjang", 20, 200, 50)
        
        if st.button("Tambah ke Watchlist"):
            try:
                db_execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker,))
                st.success(ticker + " ditambahkan ke watchlist!")
            except Exception as e:
                st.error("Error: " + str(e))
    
    with st.spinner("Mengambil data..."):
        data = ambil_data(ticker, periode)
        info = ambil_info(ticker)
    
    if data is None or data.empty:
        st.error("Data " + ticker + " tidak ditemukan!")
        st.stop()
    
    nama = info.get("longName", ticker)
    harga_skrg = data['Close'].iloc[-1]
    harga_lalu = data['Close'].iloc[-2] if len(data) > 1 else harga_skrg
    perubahan = harga_skrg - harga_lalu
    persen = (perubahan / harga_lalu) * 100
    
    st.markdown("## " + str(nama) + " (" + ticker + ")")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Harga", str(round(harga_skrg, 2)), str(round(perubahan, 2)) + " (" + str(round(persen, 2)) + "%)")
    with col2:
        st.metric("High 52W", str(round(data['High'].tail(252).max(), 2)))
    with col3:
        st.metric("Low 52W", str(round(data['Low'].tail(252).min(), 2)))
    with col4:
        st.metric("Volume", format_angka(data['Volume'].iloc[-1]))
    
    st.divider()
    tab1, tab2, tab3 = st.tabs(["Chart", "Fundamental", "Data"])
    
    with tab1:
        df = data.copy()
        if show_ma:
            df['MA_S'] = df['Close'].rolling(ma_short).mean()
            df['MA_L'] = df['Close'].rolling(ma_long).mean()
        if show_rsi:
            df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        if show_macd:
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
        
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
        
        fig = make_subplots(rows=subplot_count, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)
        
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Harga'), row=1, col=1)
        
        if show_ma:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA_S'], name='MA ' + str(ma_short), line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA_L'], name='MA ' + str(ma_long), line=dict(color='blue')), row=1, col=1)
        
        current_row = 2
        if show_rsi:
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=current_row, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
            current_row += 1
        
        if show_macd:
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')), row=current_row, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='red')), row=current_row, col=1)
        
        fig.update_layout(height=700, xaxis_rangeslider_visible=False, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Data Fundamental")
        if info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Market Cap", format_angka(info.get("marketCap")))
                pe = info.get('trailingPE')
                st.metric("P/E Ratio", str(round(pe, 2)) if pe else "N/A")
            with col2:
                eps = info.get('trailingEps')
                st.metric("EPS", str(round(eps, 2)) if eps else "N/A")
                pb = info.get('priceToBook')
                st.metric("P/B Ratio", str(round(pb, 2)) if pb else "N/A")
            with col3:
                st.write("**Sektor:** " + str(info.get('sector', 'N/A')))
                st.write("**Industri:** " + str(info.get('industry', 'N/A')))
        else:
            st.warning("Data tidak tersedia")
    
    with tab3:
        st.subheader("Data Historis")
        st.dataframe(data.round(2).sort_index(ascending=False), use_container_width=True)
        csv = data.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, ticker + "_data.csv", "text/csv")

elif menu == "Watchlist":
    st.title("Watchlist Saya")
    
    with st.sidebar:
        st.markdown("### Tambah Saham")
        ticker_baru = st.text_input("Kode Saham").upper()
        if st.button("Tambah"):
            if ticker_baru:
                try:
                    db_execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker_baru,))
                    st.success(ticker_baru + " ditambahkan!")
                    st.rerun()
                except Exception as e:
                    st.error("Error: " + str(e))
    
    df_watch = db_query("SELECT * FROM watchlist ORDER BY tanggal_ditambah DESC")
    
    if df_watch.empty:
        st.info("Watchlist kosong. Tambahkan saham dari sidebar!")
    else:
        for _, row in df_watch.iterrows():
            tk = row['ticker']
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                st.markdown("### " + tk)
            with col2:
                try:
                    d = ambil_data(tk, "5d")
                    if d is not None and not d.empty:
                        h = d['Close'].iloc[-1]
                        h_lalu = d['Close'].iloc[-2] if len(d) > 1 else h
                        delta = ((h - h_lalu) / h_lalu) * 100
                        st.metric("Harga", str(round(h, 2)), str(round(delta, 2)) + "%")
                except:
                    st.write("N/A")
            with col3:
                if st.button("Hapus", key="del_" + tk):
                    db_execute("DELETE FROM watchlist WHERE ticker = ?", (tk,))
                    st.rerun()
            st.divider()

elif menu == "Portfolio":
    st.title("Portfolio Saya")
    
    with st.sidebar:
        st.markdown("### Tambah Transaksi")
        tk_p = st.text_input("Kode Saham").upper()
        jml = st.number_input("Jumlah Lembar", min_value=1.0, value=100.0)
        hrg = st.number_input("Harga Beli", min_value=0.01, value=1000.0)
        tgl = st.date_input("Tanggal Beli", datetime.now())
        
        if st.button("Tambah ke Portfolio"):
            if tk_p:
                db_execute("INSERT INTO portfolio (ticker, jumlah, harga_beli, tanggal_beli) VALUES (?,?,?,?)", (tk_p, jml, hrg, tgl.strftime('%Y-%m-%d')))
                st.success(tk_p + " ditambahkan!")
                st.rerun()
    
    df_pf = db_query("SELECT * FROM portfolio ORDER BY tanggal_beli DESC")
    
    if df_pf.empty:
        st.info("Portfolio kosong. Tambahkan dari sidebar!")
    else:
        hasil = []
        for _, row in df_pf.iterrows():
            try:
                d = ambil_data(row['ticker'], "5d")
                harga_skrg = d['Close'].iloc[-1] if d is not None and not d.empty else 0
                nilai_beli = row['jumlah'] * row['harga_beli']
                nilai_skrg = row['jumlah'] * harga_skrg
                pnl = nilai_skrg - nilai_beli
                if nilai_beli > 0:
                    pnl_pct = (pnl / nilai_beli) * 100
                else:
                    pnl_pct = 0
                hasil.append({'ID': row['id'], 'Ticker': row['ticker'], 'Jumlah': row['jumlah'], 'Harga Beli': row['harga_beli'], 'Harga Kini': round(harga_skrg, 2), 'Nilai Beli': round(nilai_beli, 2), 'Nilai Kini': round(nilai_skrg, 2), 'PnL': round(pnl, 2), 'PnL %': round(pnl_pct, 2)})
            except Exception:
                continue
        
        if hasil:
            df_hasil = pd.DataFrame(hasil)
            total_beli = df_hasil['Nilai Beli'].sum()
            total_kini = df_hasil['Nilai Kini'].sum()
            total_pnl = total_kini - total_beli
            if total_beli > 0:
                total_pnl_pct = (total_pnl / total_beli) * 100
            else:
                total_pnl_pct = 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Modal", "Rp " + format_angka(total_beli))
            with col2:
                st.metric("Nilai Sekarang", "Rp " + format_angka(total_kini))
            with col3:
                st.metric("Total PnL", "Rp " + format_angka(total_pnl), str(round(total_pnl_pct, 2)) + "%")
            
            st.divider()
            st.dataframe(df_hasil, use_container_width=True)
            
            id_hapus = st.selectbox("Hapus posisi (pilih ID)", options=df_hasil['ID'].tolist())
            if st.button("Hapus"):
                db_execute("DELETE FROM portfolio WHERE id = ?", (int(id_hapus),))
                st.rerun()

st.divider()
st.caption("Update: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " | Bukan rekomendasi investasi")
