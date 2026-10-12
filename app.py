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
                pnl_pct = (pnl / nilai_beli * 100) if nilai_beli > 0 else 0
                
                hasil.append({
                    'ID': row['id'],
                    'Ticker': row['ticker'],
                    'Jumlah': row['jumlah'],
                    'Harga Beli': row['harga_beli'],
                    'Harga Kini': round(harga_skrg, 2),
                    'Nilai Beli': round(nilai_beli, 2),
                    'Nilai Kini': round(nilai_skrg, 2),
                    'PnL': round(pnl, 2),
                    'PnL %': round(pnl_pct, 2),
                    'Tanggal': row['tanggal_beli']
                })
            except Exception as e:
                continue
        
        if hasil:
            df_hasil = pd.DataFrame(hasil)
            
            # Ringkasan portfolio
            total_beli = df_hasil['Nilai Beli'].sum()
            total_kini = df_hasil['Nilai Kini'].sum()
            total_pnl = total_kini - total_beli
            total_pnl_pct = (total_pnl / total_beli * 100) if total_beli > 0 else 0
            
            st.subheader("📊 Ringkasan Portfolio")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Modal", f"Rp {total_beli:,.0f}")
            with col2:
                st.metric("Nilai Sekarang", f"Rp {total_kini:,.0f}")
            with col3:
                st.metric("Total PnL", f"Rp {total_pnl:,.0f}",
                         f"{total_pnl_pct:+.2f}%")
            with col4:
                st.metric("Jumlah Posisi", len(df_hasil))
            
            st.divider()
            
            # Pie chart alokasi
            col_a, col_b = st.columns(2)
            
            with col_a:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=df_hasil['Ticker'],
                    values=df_hasil['Nilai Kini'],
                    hole=0.4
                )])
                fig_pie.update_layout(title="Alokasi Portfolio", height=350)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_b:
                colors = ['#26a69a' if x >= 0 else '#ef5350' for x in df_hasil['PnL']]
                fig_bar = go.Figure(data=[go.Bar(
                    x=df_hasil['Ticker'],
                    y=df_hasil['PnL'],
                    marker_color=colors,
                    text=df_hasil['PnL'].round(0),
                    textposition='auto'
                )])
                fig_bar.update_layout(title="PnL per Saham", height=350)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            st.divider()
            
            # Tabel detail
            st.subheader("📋 Detail Posisi")
            st.dataframe(df_hasil, use_container_width=True)
            
            # Hapus posisi
            st.subheader("🗑️ Hapus Posisi")
            id_hapus = st.selectbox(
                "Pilih ID untuk dihapus",
                options=df_hasil['ID'].tolist()
            )
            if st.button("Hapus Posisi"):
                db_execute("DELETE FROM portfolio WHERE id = ?", (int(id_hapus),))
                st.success("Posisi dihapus!")
                st.rerun()


# ==================== HALAMAN: ALERTS ====================
elif menu == "🔔 Alerts":
    st.title("🔔 Price Alerts")
    
    with st.sidebar:
        st.markdown("### ➕ Buat Alert")
        tk_a = st.text_input("Kode Saham").upper()
        target = st.number_input("Harga Target", min_value=0.01, value=1000.0)
        kondisi = st.selectbox("Kondisi", ["Di atas (≥)", "Di bawah (≤)"])
        
        if st.button("Buat Alert"):
            if tk_a:
                db_execute(
                    "INSERT INTO alerts (ticker, harga_target, kondisi) VALUES (?,?,?)",
                    (tk_a, target, kondisi)
                )
                st.success(f"✅ Alert untuk {tk_a} dibuat!")
                st.rerun()
    
    df_alerts = db_query("SELECT * FROM alerts WHERE aktif = 1 ORDER BY dibuat DESC")
    
    if df_alerts.empty:
        st.info("Belum ada alert aktif. Buat dari sidebar!")
    else:
        st.subheader("📋 Daftar Alert Aktif")
        
        for _, row in df_alerts.iterrows():
            tk = row['ticker']
            target = row['harga_target']
            kondisi = row['kondisi']
            
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
            
            with col1:
                st.markdown(f"**{tk}**")
            with col2:
                st.write(f"Target: {target:,.2f}")
            with col3:
                st.write(kondisi)
            with col4:
                try:
                    d = ambil_data(tk, "5d", "1d")
                    if d is not None and not d.empty:
                        harga_now = d['Close'].iloc[-1]
                        st.write(f"Kini: {harga_now:,.2f}")
                        
                        # Cek kondisi
                        terpenuhi = False
                        if "atas" in kondisi and harga_now >= target:
                            terpenuhi = True
                        elif "bawah" in kondisi and harga_now <= target:
                            terpenuhi = True
                        
                        if terpenuhi:
                            st.success("🎯 TERCAPAI!")
                        else:
                            st.info("⏳ Menunggu")
                except:
                    st.write("N/A")
            with col5:
                if st.button("🗑️", key=f"del_alert_{row['id']}"):
                    db_execute("DELETE FROM alerts WHERE id = ?", (int(row['id']),))
                    st.rerun()
            
            st.divider()


# ==================== HALAMAN: BANDINGKAN ====================
elif menu == "📊 Bandingkan":
    st.title("📊 Bandingkan Saham")
    
    with st.sidebar:
        st.markdown("### Pilih Saham")
        daftar = st.multiselect(
            "Pilih 2-5 saham untuk dibandingkan",
            options=list(saham_populer.keys()),
            default=["BBCA.JK", "BBRI.JK"]
        )
        periode_cmp = st.selectbox("Periode", 
                                   ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                   index=3)
    
    if len(daftar) < 2:
        st.warning("Pilih minimal 2 saham untuk dibandingkan.")
    else:
        # Ambil data
        data_dict = {}
        for tk in daftar:
            d = ambil_data(tk, periode_cmp, "1d")
            if d is not None and not d.empty:
                data_dict[tk] = d
        
        if not data_dict:
            st.error("Tidak ada data yang bisa dibandingkan.")
            st.stop()
        
        # Chart perbandingan (normalized)
        st.subheader("📈 Perbandingan Performa (Normalized)")
        
        fig = go.Figure()
        for tk, d in data_dict.items():
            normalized = (d['Close'] / d['Close'].iloc[0] - 1) * 100
            fig.add_trace(go.Scatter(
                x=d.index, y=normalized,
                name=tk, mode='lines'
            ))
        
        fig.update_layout(
            title="Performa Relatif (% perubahan dari awal periode)",
            xaxis_title="Tanggal",
            yaxis_title="Return (%)",
            hovermode='x unified',
            height=500
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabel perbandingan
        st.subheader("📋 Tabel Perbandingan")
        
        rows = []
        for tk, d in data_dict.items():
            if len(d) < 2:
                continue
            return_total = (d['Close'].iloc[-1] / d['Close'].iloc[0] - 1) * 100
            volatilitas = d['Close'].pct_change().std() * 100
            max_drawdown = ((d['Close'] / d['Close'].cummax()) - 1).min() * 100
            
            rows.append({
                'Ticker': tk,
                'Harga Awal': round(d['Close'].iloc[0], 2),
                'Harga Akhir': round(d['Close'].iloc[-1], 2),
                'Return %': round(return_total, 2),
                'Volatilitas %': round(volatilitas, 2),
                'Max Drawdown %': round(max_drawdown, 2)
            })
        
        df_cmp = pd.DataFrame(rows).sort_values('Return %', ascending=False)
        st.dataframe(df_cmp, use_container_width=True)
        
        # Bar chart return
        fig_bar = go.Figure(data=[go.Bar(
            x=df_cmp['Ticker'],
            y=df_cmp['Return %'],
            marker_color=['#26a69a' if x >= 0 else '#ef5350' for x in df_cmp['Return %']],
            text=df_cmp['Return %'].round(2),
            textposition='auto'
        )])
        fig_bar.update_layout(title="Total Return per Saham", height=400)
        st.plotly_chart(fig_bar, use_container_width=True)


# ==================== FOOTER ====================
st.divider()
st.caption(f"📅 Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
           f"Sumber: Yahoo Finance | ⚠️ Bukan rekomendasi investasi")
