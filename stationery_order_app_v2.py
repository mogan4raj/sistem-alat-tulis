import streamlit as st
import pandas as pd
import datetime
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set Page Config
st.set_page_config(
    page_title="Sistem Pesanan Alat Tulis Stor Pusat",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1E3A8A;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 20px;
        font-weight: 600;
        color: #1F2937;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #E5E7EB;
        margin-bottom: 15px;
    }
    .email-preview {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 13px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State Data
if "inventory" not in st.session_state:
    st.session_state.inventory = pd.DataFrame([
        {"ID": "ST-001", "Item": "Kertas A4 (80gsm)", "Kategori": "Kertas", "Unit": "Ream", "Stok Semasa": 120, "Paras Min": 20},
        {"ID": "ST-002", "Item": "Pen Gel Biru (0.7mm)", "Kategori": "Alat Tulis", "Unit": "Batang", "Stok Semasa": 250, "Paras Min": 50},
        {"ID": "ST-003", "Item": "Pen Gel Hitam (0.7mm)", "Kategori": "Alat Tulis", "Unit": "Batang", "Stok Semasa": 200, "Paras Min": 50},
        {"ID": "ST-004", "Item": "Pen Gel Merah (0.7mm)", "Kategori": "Alat Tulis", "Unit": "Batang", "Stok Semasa": 90, "Paras Min": 30},
        {"ID": "ST-005", "Item": "Fail Poket Plastik A4", "Kategori": "Fail", "Unit": "Keping", "Stok Semasa": 300, "Paras Min": 60},
        {"ID": "ST-006", "Item": "Pengokot (Stapler Heavy Duty)", "Kategori": "Peralatan", "Unit": "Unit", "Stok Semasa": 15, "Paras Min": 5},
        {"ID": "ST-007", "Item": "Dawai Pengokot (Staples No. 10)", "Kategori": "Peralatan", "Unit": "Kotak", "Stok Semasa": 80, "Paras Min": 20},
        {"ID": "ST-008", "Item": "Cecair Pemadam (Correction Tape)", "Kategori": "Alat Tulis", "Unit": "Unit", "Stok Semasa": 45, "Paras Min": 15},
        {"ID": "ST-009", "Item": "Nota Pelekat (Post-it Yellow)", "Kategori": "Kertas", "Unit": "Pad", "Stok Semasa": 110, "Paras Min": 25},
        {"ID": "ST-010", "Item": "Pen Marker Papan Putih (Biru)", "Kategori": "Alat Tulis", "Unit": "Batang", "Stok Semasa": 60, "Paras Min": 15},
    ])

if "orders" not in st.session_state:
    st.session_state.orders = pd.DataFrame([
        {
            "ID Pesanan": "ORD-1001",
            "Tarikh": "2026-09-28",
            "Nama Pemohon": "Ahmad Razali",
            "Emel": "ahmad.razali@kerajaan.gov.my",
            "Bahagian/Unit": "Bahagian Kewangan",
            "Item Pesanan": "Kertas A4 (80gsm) (2 Ream), Pen Gel Biru (0.7mm) (5 Batang)",
            "Jumlah Item": 7,
            "Status": "Diluluskan",
            "Catatan Admin": "Telah diserahkan pada 29/09"
        },
        {
            "ID Pesanan": "ORD-1002",
            "Tarikh": "2026-10-01",
            "Nama Pemohon": "Siti Nurhaliza",
            "Emel": "siti.nurhaliza@kerajaan.gov.my",
            "Bahagian/Unit": "Sektor Pengurusan Aset",
            "Item Pesanan": "Fail Poket Plastik A4 (20 Keping), Pengokot (1 Unit)",
            "Jumlah Item": 21,
            "Status": "Menunggu Kelulusan",
            "Catatan Admin": "-"
        }
    ])

if "email_logs" not in st.session_state:
    st.session_state.email_logs = pd.DataFrame([
        {
            "Masa": "2026-09-28 09:30:15",
            "Penerima": "ahmad.razali@kerajaan.gov.my",
            "Jenis Emel": "Pengesahan Pesanan Baharu",
            "ID Pesanan": "ORD-1001",
            "Status": "Berjaya Dihantar",
            "Subjek": "PENGESAHAN PESANAN ALAT TULIS: ORD-1001"
        },
        {
            "Masa": "2026-09-29 11:15:00",
            "Penerima": "ahmad.razali@kerajaan.gov.my",
            "Jenis Emel": "Kemaskini Status (Diluluskan)",
            "ID Pesanan": "ORD-1001",
            "Status": "Berjaya Dihantar",
            "Subjek": "STATUS PESANAN ALAT TULIS: ORD-1001 (DILULUSKAN)"
        }
    ])

# SMTP Email Configuration Default
if "smtp_config" not in st.session_state:
    st.session_state.smtp_config = {
        "mode": "Simulasi (Demo)",  # 'Simulasi (Demo)' or 'SMTP Sebenar'
        "server": "smtp.gmail.com",
        "port": 587,
        "sender": "stor.pusat@kerajaan.gov.my",
        "password": ""
    }

# Function to Send or Simulate Email
def send_email_notification(recipient_email, recipient_name, subject, message_body, email_type, order_id):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = st.session_state.smtp_config["mode"]
    
    success = True
    status_msg = "Berjaya Dihantar (Simulasi)"
    
    if mode == "SMTP Sebenar":
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = st.session_state.smtp_config["sender"]
            msg["To"] = recipient_email
            msg.attach(MIMEText(message_body, "html"))

            server = smtplib.SMTP(st.session_state.smtp_config["server"], st.session_state.smtp_config["port"])
            server.starttls()
            server.login(st.session_state.smtp_config["sender"], st.session_state.smtp_config["password"])
            server.sendmail(st.session_state.smtp_config["sender"], recipient_email, msg.as_string())
            server.quit()
            status_msg = "Berjaya Dihantar (SMTP)"
        except Exception as e:
            success = False
            status_msg = f"Ralat SMTP: {str(e)}"
    
    # Log the email dispatch
    new_log = {
        "Masa": now_str,
        "Penerima": recipient_email,
        "Jenis Emel": email_type,
        "ID Pesanan": order_id,
        "Status": status_msg,
        "Subjek": subject
    }
    st.session_state.email_logs = pd.concat([st.session_state.email_logs, pd.DataFrame([new_log])], ignore_index=True)
    return success, status_msg

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/stationery.png", width=70)
st.sidebar.title("Stor Pusat Alat Tulis")
st.sidebar.caption("Sistem Permohonan & Pengurusan Stok")

menu = st.sidebar.radio(
    "Navigasi Utama",
    [
        "🛒 Borang Pesanan Staff", 
        "📋 Papan Pemuka Admin", 
        "📧 Log Pengesahan Emel", 
        "📦 Pengurusan Inventori", 
        "📊 Laporan & Tetapan Emel"
    ]
)

st.sidebar.divider()
st.sidebar.info("💡 **Pengesahan Emel Automatik**: Setiap permohonan & perubahan status akan menghantar notifikasi emel secara automatik.")

# ---------------------------------------------------------
# MENU 1: BORANG PESANAN STAFF
# ---------------------------------------------------------
if menu == "🛒 Borang Pesanan Staff":
    st.markdown('<div class="main-header">🛒 Borang Pesanan Alat Tulis Staff</div>', unsafe_allow_html=True)
    st.write("Sila lengkapkan maklumat pemohon dan pilih barangan yang diperlukan daripada katalog di bawah.")

    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama Penuh Pemohon *", placeholder="Cth: Muhammad Ariff bin Rosli")
        email = st.text_input("Emel Rasmi Pemohon * (Untuk Notifikasi Automatik)", placeholder="Cth: ariff@kerajaan.gov.my")
    with col2:
        bahagian = st.selectbox("Bahagian / Unit *", [
            "Bahagian Pengurusan Maklumat (BPM)",
            "Bahagian Kewangan & Akaun",
            "Bahagian Khidmat Pengurusan (BKP)",
            "Sektor Pengurusan Aset",
            "Bahagian Sumber Manusia",
            "Unit Audit Dalam"
        ])
        tarikh = st.date_input("Tarikh Diperlukan", datetime.date.today())

    st.markdown('<div class="sub-header">📦 Pilih Barangan Daripada Katalog</div>', unsafe_allow_html=True)
    
    df_inv = st.session_state.inventory
    
    # Filter by category
    kategori_list = ["Semua"] + list(df_inv["Kategori"].unique())
    selected_kat = st.selectbox("Tapis Mengikut Kategori", kategori_list)

    if selected_kat != "Semua":
        df_filtered = df_inv[df_inv["Kategori"] == selected_kat]
    else:
        df_filtered = df_inv

    # Display selection table / form
    cart = {}
    st.write("Masukkan kuantiti yang diperlukan bagi setiap item:")

    for idx, row in df_filtered.iterrows():
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            st.markdown(f"**{row['Item']}** ({row['ID']})")
            st.caption(f"Kategori: {row['Kategori']} | Unit: {row['Unit']}")
        with c2:
            st.metric("Stok Semasa", f"{row['Stok Semasa']} {row['Unit']}")
        with c3:
            qty = st.number_input(
                f"Kuantiti ({row['Unit']})",
                min_value=0,
                max_value=int(row['Stok Semasa']),
                value=0,
                key=f"qty_{row['ID']}"
            )
            if qty > 0:
                cart[row['Item']] = {"qty": qty, "unit": row['Unit'], "id": row['ID']}
        with c4:
            st.write("")

    st.divider()

    # Order Summary & Submission
    st.markdown('<div class="sub-header">📝 Ringkasan Troli Pesanan</div>', unsafe_allow_html=True)
    if cart:
        summary_list = []
        total_items = 0
        for item_name, details in cart.items():
            summary_list.append(f"• **{item_name}**: {details['qty']} {details['unit']}")
            total_items += details['qty']
        
        st.markdown("\n".join(summary_list))
        st.info(f"**Jumlah Keseluruhan Item:** {total_items} unit/ream/keping")

        catatan_pemohon = st.text_area("Catatan Tambahan (Jika ada)", placeholder="Cth: Untuk kegunaan Mesyuarat Jawatankuasa pada 5 Oktober.")

        if st.button("🚀 Hantar Pesanan & Hantar Emel Pengesahan", type="primary"):
            if not nama or not email:
                st.error("❌ Sila isi Nama dan Emel Rasmi terlebih dahulu sebelum menghantar pesanan.")
            elif "@" not in email:
                st.error("❌ Sila masukkan alamat emel yang sah (cth: nama@domain.gov.my).")
            else:
                # Generate new order ID
                new_id = f"ORD-{1001 + len(st.session_state.orders)}"
                order_summary_str = ", ".join([f"{k} ({v['qty']} {v['unit']})" for k, v in cart.items()])
                
                new_order = {
                    "ID Pesanan": new_id,
                    "Tarikh": str(tarikh),
                    "Nama Pemohon": nama,
                    "Emel": email,
                    "Bahagian/Unit": bahagian,
                    "Item Pesanan": order_summary_str,
                    "Jumlah Item": total_items,
                    "Status": "Menunggu Kelulusan",
                    "Catatan Admin": "-"
                }
                
                # Append to dataframe
                st.session_state.orders = pd.concat([st.session_state.orders, pd.DataFrame([new_order])], ignore_index=True)
                
                # Send Automatic Confirmation Email
                subject = f"PENGESAHAN PESANAN ALAT TULIS: {new_id} [MENUNGGU KELULUSAN]"
                email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #1E3A8A; color: white; padding: 15px; border-radius: 5px;">
                        <h2>Stor Pusat Alat Tulis - Pengesahan Permohonan</h2>
                    </div>
                    <p>Salam sejahtera <b>{nama}</b>,</p>
                    <p>Permohonan pesanan alat tulis anda telah berjaya diterima dan sedang diproses oleh Pegawai Stor Pusat.</p>
                    <hr>
                    <p><b>Butiran Pesanan:</b></p>
                    <ul>
                        <li><b>Nombor Rujukan:</b> {new_id}</li>
                        <li><b>Tarikh Mohon:</b> {tarikh}</li>
                        <li><b>Bahagian/Unit:</b> {bahagian}</li>
                        <li><b>Senarai Barangan:</b> {order_summary_str}</li>
                        <li><b>Jumlah Kuantiti:</b> {total_items} item</li>
                        <li><b>Status Semasa:</b> <span style="color: orange; font-weight: bold;">Menunggu Kelulusan</span></li>
                    </ul>
                    <p>Notifikasi seterusnya akan dihantar sebaik sahaja pesanan anda diluluskan/diproses.</p>
                    <br>
                    <p>Sekian, terima kasih.<br><b>Sistem Pengurusan Stor Pusat</b></p>
                </body>
                </html>
                """
                
                send_status, msg = send_email_notification(
                    recipient_email=email,
                    recipient_name=nama,
                    subject=subject,
                    message_body=email_body,
                    email_type="Pengesahan Pesanan Baharu",
                    order_id=new_id
                )

                st.balloons()
                st.success(f"✅ Pesanan berjaya dihantar! Nombor Rujukan Pesanan anda ialah **{new_id}**.")
                
                st.markdown(f"""
                <div class="email-preview">
                    📧 <b>Emel Pengesahan Automatik Telah Dihantar!</b><br>
                    <b>Penerima:</b> {email}<br>
                    <b>Subjek:</b> {subject}<br>
                    <b>Status Hantaran:</b> {msg}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Troli pesanan anda masih kosong. Sila pilih sekurang-kurangnya satu item di atas.")

# ---------------------------------------------------------
# MENU 2: PAPAN PEMUKA ADMIN (STOREKEEPER)
# ---------------------------------------------------------
elif menu == "📋 Papan Pemuka Admin":
    st.markdown('<div class="main-header">📋 Papan Pemuka Pengurusan Pesanan (Stor Pusat)</div>', unsafe_allow_html=True)
    
    df_orders = st.session_state.orders

    # Metrics Overview
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah Pesanan", len(df_orders))
    m2.metric("Menunggu Kelulusan", len(df_orders[df_orders["Status"] == "Menunggu Kelulusan"]))
    m3.metric("Diluluskan", len(df_orders[df_orders["Status"] == "Diluluskan"]))
    m4.metric("Ditolak", len(df_orders[df_orders["Status"] == "Ditolak"]))

    st.divider()

    st.markdown('<div class="sub-header">🔍 Senarai Permohonan Pesanan</div>', unsafe_allow_html=True)
    status_filter = st.multiselect("Tapis Mengikut Status", ["Menunggu Kelulusan", "Diluluskan", "Ditolak"], default=["Menunggu Kelulusan", "Diluluskan"])

    filtered_df = df_orders[df_orders["Status"].isin(status_filter)] if status_filter else df_orders

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    st.divider()

    # Action / Approval Section
    st.markdown('<div class="sub-header">⚡ Tindakan Kelulusan Pesanan & Notifikasi Emel Automatik</div>', unsafe_allow_html=True)
    
    pending_orders = df_orders[df_orders["Status"] == "Menunggu Kelulusan"]
    
    if not pending_orders.empty():
        selected_order_id = st.selectbox("Pilih ID Pesanan untuk Diproses", pending_orders["ID Pesanan"].tolist())
        order_details = pending_orders[pending_orders["ID Pesanan"] == selected_order_id].iloc[0]

        st.markdown(f"""
        <div class="card">
            <h4>Maklumat Pesanan: {order_details['ID Pesanan']}</h4>
            <p><b>Pemohon:</b> {order_details['Nama Pemohon']} ({order_details['Bahagian/Unit']})</p>
            <p><b>Emel Notifikasi:</b> {order_details['Emel']}</p>
            <p><b>Tarikh Mohon:</b> {order_details['Tarikh']}</p>
            <p><b>Barangan Dimohon:</b> {order_details['Item Pesanan']}</p>
        </div>
        """, unsafe_allow_html=True)

        catatan_admin = st.text_input("Catatan Pegawai Stor (Akan dihantar dalam emel pemohon)", value="Stok mencukupi & sedia untuk diambil di Stor Pusat.")

        col_act1, col_act2 = st.columns(2)

        with col_act1:
            if st.button("✅ Luluskan Pesanan & Emel Pemohon", type="primary", use_container_width=True):
                # Update status
                idx = st.session_state.orders[st.session_state.orders["ID Pesanan"] == selected_order_id].index[0]
                st.session_state.orders.at[idx, "Status"] = "Diluluskan"
                st.session_state.orders.at[idx, "Catatan Admin"] = catatan_admin
                
                # Deduct inventory quantities
                item_str = order_details["Item Pesanan"]
                
                # Send email notification to staff
                subject = f"STATUS PESANAN ALAT TULIS: {selected_order_id} (DILULUSKAN)"
                email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #065F46; color: white; padding: 15px; border-radius: 5px;">
                        <h2>Stor Pusat - Pesanan Diluluskan ✅</h2>
                    </div>
                    <p>Salam sejahtera <b>{order_details['Nama Pemohon']}</b>,</p>
                    <p>Permohonan pesanan alat tulis anda dengan nombor rujukan <b>{selected_order_id}</b> telah <b>DILULUSKAN</b>.</p>
                    <hr>
                    <p><b>Ringkasan Pesanan:</b></p>
                    <ul>
                        <li><b>Barangan:</b> {order_details['Item Pesanan']}</li>
                        <li><b>Catatan Pegawai Stor:</b> {catatan_admin}</li>
                    </ul>
                    <p>Sila ambil barangan tersebut di Stor Pusat dengan mengemukakan Nombor Rujukan ini.</p>
                    <br>
                    <p>Sekian, terima kasih.<br><b>Stor Pusat Alat Tulis</b></p>
                </body>
                </html>
                """
                send_email_notification(
                    recipient_email=order_details['Emel'],
                    recipient_name=order_details['Nama Pemohon'],
                    subject=subject,
                    message_body=email_body,
                    email_type="Kemaskini Status (Diluluskan)",
                    order_id=selected_order_id
                )

                st.success(f" Pesanan {selected_order_id} telah DILULUSKAN dan emel notifikasi telah diproses!")
                st.rerun()

        with col_act2:
            if st.button("❌ Tolak Pesanan & Emel Pemohon", use_container_width=True):
                idx = st.session_state.orders[st.session_state.orders["ID Pesanan"] == selected_order_id].index[0]
                st.session_state.orders.at[idx, "Status"] = "Ditolak"
                st.session_state.orders.at[idx, "Catatan Admin"] = catatan_admin if catatan_admin else "Stok tidak mencukupi"

                # Send email notification to staff
                subject = f"STATUS PESANAN ALAT TULIS: {selected_order_id} (DITOLAK)"
                email_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="background-color: #991B1B; color: white; padding: 15px; border-radius: 5px;">
                        <h2>Stor Pusat - Pesanan Ditolak ❌</h2>
                    </div>
                    <p>Salam sejahtera <b>{order_details['Nama Pemohon']}</b>,</p>
                    <p>Dukacita dimaklumkan bahawa permohonan pesanan alat tulis anda dengan nombor rujukan <b>{selected_order_id}</b> telah <b>DITOLAK</b>.</p>
                    <hr>
                    <p><b>Sebab / Catatan Pegawai Stor:</b> {catatan_admin}</p>
                    <br>
                    <p>Sekian, terima kasih.<br><b>Stor Pusat Alat Tulis</b></p>
                </body>
                </html>
                """
                send_email_notification(
                    recipient_email=order_details['Emel'],
                    recipient_name=order_details['Nama Pemohon'],
                    subject=subject,
                    message_body=email_body,
                    email_type="Kemaskini Status (Ditolak)",
                    order_id=selected_order_id
                )

                st.error(f"Pesanan {selected_order_id} telah DITOLAK dan emel notifikasi telah diproses.")
                st.rerun()
    else:
        st.info("Tiada pesanan baharu yang menunggu kelulusan pada masa ini.")

# ---------------------------------------------------------
# MENU 3: LOG PENGESAHAN EMEL AUTOMATIK
# ---------------------------------------------------------
elif menu == "📧 Log Pengesahan Emel":
    st.markdown('<div class="main-header">📧 Log Pengesahan & Penghantaran Emel Automatik</div>', unsafe_allow_html=True)
    st.write("Semua emel notifikasi yang dihantar secara automatik oleh sistem direkodkan di sini untuk tujuan audit dan semakan.")

    df_logs = st.session_state.email_logs

    c1, c2 = st.columns([3, 1])
    with c1:
        st.metric("Jumlah Emel Dihantar", len(df_logs))
    with c2:
        if st.button("🗑️ Kosongkan Log Emel"):
            st.session_state.email_logs = pd.DataFrame(columns=["Masa", "Penerima", "Jenis Emel", "ID Pesanan", "Status", "Subjek"])
            st.rerun()

    st.dataframe(df_logs, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🔍 Contoh Templat Emel Automatik")
    st.info("""
    **Ciri-ciri Emel Automatik yang Dibina:**
    1. **Emel Pengesahan Permohonan**: Dihantar secara langsung kepada pemohon sebaik sahaja borang dihantar bersama Nombor Rujukan (ORD-XXXX).
    2. **Emel Kelulusan / Penolakan**: Dihantar secara serta-merta apabila Pegawai Stor mengemaskini status permohonan di Papan Pemuka Admin.
    3. **Mod Simulasi & SMTP**: Menyokong penyiapan terus dalam mod demonstrasi serta integrasi pelayan SMTP rasmi organisasi (cth: Gmail SMTP/Exchange Server).
    """)

# ---------------------------------------------------------
# MENU 4: PENGURUSAN INVENTORI
# ---------------------------------------------------------
elif menu == "📦 Pengurusan Inventori":
    st.markdown('<div class="main-header">📦 Pengurusan Inventori & Stok Stor Pusat</div>', unsafe_allow_html=True)

    df_inv = st.session_state.inventory

    # Warning for low stock
    low_stock = df_inv[df_inv["Stok Semasa"] <= df_inv["Paras Min"]]
    if not low_stock.empty():
        st.warning(f"⚠️ **Amaran Stok Rendah**: terdapat {len(low_stock)} item yang telah mencapai atau berada di bawah paras minimum!")
        st.dataframe(low_stock, use_container_width=True, hide_index=True)

    st.markdown('<div class="sub-header">📊 Senarai Stok Semasa</div>', unsafe_allow_html=True)
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

    st.divider()

    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.markdown("### ➕ Tambah Kuantiti Stok (Restock)")
        item_to_update = st.selectbox("Pilih Item", df_inv["Item"].tolist())
        add_qty = st.number_input("Kuantiti Tambahan", min_value=1, value=10)
        
        if st.button("Kemas Kini Stok"):
            idx = st.session_state.inventory[st.session_state.inventory["Item"] == item_to_update].index[0]
            st.session_state.inventory.at[idx, "Stok Semasa"] += add_qty
            st.success(f"Stok bagi {item_to_update} telah ditambah sebanyak {add_qty} unit.")
            st.rerun()

    with col_inv2:
        st.markdown("### 🆕 Tambah Katalog Item Baharu")
        new_id = f"ST-0{len(df_inv)+1:02d}"
        new_name = st.text_input("Nama Item Alat Tulis")
        new_kat = st.selectbox("Kategori", ["Alat Tulis", "Kertas", "Fail", "Peralatan", "Lain-lain"])
        new_unit = st.text_input("Unit Ukuran (cth: Batang, Ream, Kotak)", value="Unit")
        new_stok = st.number_input("Stok Permulaan", min_value=0, value=50)
        new_min = st.number_input("Paras Minima Reorder", min_value=1, value=10)

        if st.button("Tambah Item Baru"):
            if new_name:
                new_row = {
                    "ID": new_id, "Item": new_name, "Kategori": new_kat,
                    "Unit": new_unit, "Stok Semasa": new_stok, "Paras Min": new_min
                }
                st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Item baru '{new_name}' berjaya ditambah ke dalam katalog!")
                st.rerun()

# ---------------------------------------------------------
# MENU 5: LAPORAN & TETAPAN EMEL
# ---------------------------------------------------------
elif menu == "📊 Laporan & Tetapan Emel":
    st.markdown('<div class="main-header">📊 Laporan & Tetapan Emel (SMTP)</div>', unsafe_allow_html=True)
    
    df_orders = st.session_state.orders
    df_inv = st.session_state.inventory

    st.markdown('<div class="sub-header">⚙️ Konfigurasi Pelayan Emel (SMTP)</div>', unsafe_allow_html=True)
    st.write("Tetapkan akaun emel penghantar rasmi untuk penghantaran emel sebenar ke peti masuk staff.")

    c_smtp1, c_smtp2 = st.columns(2)
    with c_smtp1:
        mode = st.radio(
            "Mod Penghantaran Emel",
            ["Simulasi (Demo)", "SMTP Sebenar"],
            index=0 if st.session_state.smtp_config["mode"] == "Simulasi (Demo)" else 1,
            help="Mod simulasi merekodkan emel tanpa menggunakan akaun SMTP sebenar."
        )
        server = st.text_input("Pelayan SMTP (Server)", value=st.session_state.smtp_config["server"])
        port = st.number_input("Port SMTP", value=int(st.session_state.smtp_config["port"]))

    with c_smtp2:
        sender = st.text_input("Emel Pengirim Rasmi", value=st.session_state.smtp_config["sender"])
        password = st.text_input("Kata Laluan / App Password SMTP", type="password", value=st.session_state.smtp_config["password"])

        if st.button("💾 Simpan Tetapan Emel"):
            st.session_state.smtp_config = {
                "mode": mode,
                "server": server,
                "port": port,
                "sender": sender,
                "password": password
            }
            st.success("✅ Tetapan emel berjaya dikemas kini!")

    st.divider()

    st.markdown('<div class="sub-header">📈 Laporan Pesanan & Muat Turun Data</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Pesanan Mengikut Bahagian")
        dept_counts = df_orders["Bahagian/Unit"].value_counts()
        st.bar_chart(dept_counts)

    with c2:
        st.markdown("#### Agihan Stok Mengikut Kategori")
        kat_counts = df_inv.groupby("Kategori")["Stok Semasa"].sum()
        st.bar_chart(kat_counts)

    st.divider()

    st.markdown("#### 📥 Muat Turun Laporan Pesanan")
    csv_data = df_orders.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Muat Turun Data Pesanan (CSV)",
        data=csv_data,
        file_name=f"laporan_pesanan_alat_tulis_{datetime.date.today()}.csv",
        mime="text/csv"
    )
