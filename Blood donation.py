import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Blood Donation System",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== RESPONSIVE & BEAUTIFUL CSS ======================
st.markdown("""
<style>
    /* Main container padding for mobile */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #d32f2f, #ff4b4b);
        color: white;
    }

    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 1rem;
    }

    /* Sidebar navigation items */
    .stRadio > div {
        gap: 0.8rem;
    }

    .stRadio label {
        font-size: 1.1rem !important;
        font-weight: 500;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        transition: all 0.3s;
        margin-bottom: 0.5rem;
        background-color: rgba(255, 255, 255, 0.1);
    }

    .stRadio label:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(8px);
    }

    /* Selected radio item */
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: rgba(255, 255, 255, 0.3) !important;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Header styling */
    h1 {
        text-align: center;
        color: #d32f2f;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
        }
    }

    /* Metrics responsive grid */
    .stMetric {
        background-color: #ffe0e0;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 6px 15px rgba(211, 47, 47, 0.15);
        text-align: center;
    }

    .stMetric > label {
        font-size: 1rem !important;
        color: #d32f2f;
        font-weight: bold;
    }

    .stMetric > div {
        font-size: 1.8rem !important;
        font-weight: bold;
        color: #c62828;
    }

    /* Dataframe responsive */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Form inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #ff8a80;
        padding: 0.8rem;
    }

    /* Buttons */
    .stButton > button {
        background-color: #d32f2f;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.8rem 1.5rem;
        font-weight: bold;
        font-size: 1.1rem;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
    }

    .stButton > button:hover {
        background-color: #b71c1c;
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(211, 47, 47, 0.4);
    }

    /* Empty state messages */
    .stInfo, .stSuccess {
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.2rem;
        border-left: 6px solid #d32f2f;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 1rem;
        color: #666;
        font-size: 0.9rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ====================== TITLE ======================
st.markdown("<h1>🩸 Blood Donation Management System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.2rem;'>Saving Lives, One Donation at a Time ❤️</p>", unsafe_allow_html=True)
st.markdown("---")

# ====================== DATABASE SETUP ======================
DB_FILE = "blood_donation.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS blood_types (
        blood_type TEXT PRIMARY KEY,
        can_donate_to TEXT NOT NULL,
        can_receive_from TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS donors (
        donor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        blood_type TEXT NOT NULL REFERENCES blood_types(blood_type),
        phone TEXT,
        last_donation_date DATE
    );

    CREATE TABLE IF NOT EXISTS blood_inventory (
        bag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        blood_type TEXT NOT NULL REFERENCES blood_types(blood_type),
        donor_id INTEGER REFERENCES donors(donor_id),
        donation_date DATE NOT NULL DEFAULT (date('now')),
        expiry_date DATE NOT NULL,
        volume_ml INTEGER DEFAULT 450,
        status TEXT CHECK(status IN ('available', 'used', 'expired', 'discarded')) DEFAULT 'available'
    );

    CREATE TABLE IF NOT EXISTS hospital_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_name TEXT NOT NULL,
        blood_type TEXT NOT NULL REFERENCES blood_types(blood_type),
        quantity_needed INTEGER NOT NULL,
        request_date DATE DEFAULT (date('now')),
        urgency TEXT CHECK(urgency IN ('routine', 'urgent', 'emergency')) DEFAULT 'routine',
        status TEXT DEFAULT 'pending'
    );
    """)

    cur.execute("SELECT COUNT(*) FROM blood_types")
    if cur.fetchone()[0] == 0:
        cur.executescript("""
        INSERT INTO blood_types (blood_type, can_donate_to, can_receive_from) VALUES
        ('A+', 'A+,AB+', 'A+,A-,O+,O-'),
        ('A-', 'A+,A-,AB+,AB-', 'A-,O-'),
        ('B+', 'B+,AB+', 'B+,B-,O+,O-'),
        ('B-', 'B+,B-,AB+,AB-', 'B-,O-'),
        ('AB+', 'AB+', 'A+,A-,B+,B-,AB+,AB-,O+,O-'),
        ('AB-', 'AB+,AB-', 'A-,B-,AB-,O-'),
        ('O+', 'A+,B+,AB+,O+', 'O+,O-'),
        ('O-', 'A+,A-,B+,B-,AB+,AB-,O+,O-', 'O-');
        """)

    conn.commit()
    conn.close()

init_db()

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

conn = get_conn()

# ====================== RESPONSIVE SIDEBAR NAVIGATION ======================
with st.sidebar:
    st.markdown("<h2 style='color: white; text-align: center;'>🩸 Menu</h2>", unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "",
        [
            "🏠 Dashboard",
            "🩺 Blood Inventory",
            "🚨 Urgent Requests",
            "⏳ Expiring Soon",
            "➕ Add Donation",
            "👥 Donors",
            "🏥 Hospital Requests",
            "📝 Add Hospital Request"
        ],
        label_visibility="collapsed"
    )

# ====================== RESPONSIVE CONTENT ======================
if page == "🏠 Dashboard":
    st.header("📊 Dashboard Overview")

    # Responsive metrics grid
    cols = st.columns(4 if st.get_option("client.width") > 768 else 2)
    metrics = [
        ("🩸 Available Bags", "SELECT COUNT(*) FROM blood_inventory WHERE status='available'"),
        ("🚨 Urgent Requests", "SELECT COUNT(*) FROM hospital_requests WHERE urgency IN ('urgent','emergency') AND status='pending'"),
        ("👥 Registered Donors", "SELECT COUNT(*) FROM donors"),
        ("⏳ Expiring Soon", "SELECT COUNT(*) FROM blood_inventory WHERE status='available' AND expiry_date <= date('now','+7 days')")
    ]

    for col, (label, query) in zip(cols, metrics):
        with col:
            value = pd.read_sql(query, conn).iloc[0,0]
            st.metric(label, value)

    st.markdown("### 🩸 Available Blood by Type")
    avail = pd.read_sql("""
        SELECT blood_type, COUNT(*) as bags, SUM(volume_ml) as total_ml 
        FROM blood_inventory WHERE status='available' 
        GROUP BY blood_type
        ORDER BY blood_type
    """, conn)
    if avail.empty:
        st.info("No blood in inventory yet. Start by adding a donation! ➕")
    else:
        st.dataframe(avail, use_container_width=True)

elif page == "🩺 Blood Inventory":
    st.header("🩺 Blood Inventory")
    df = pd.read_sql("SELECT bag_id, blood_type, donation_date, expiry_date, volume_ml, status FROM blood_inventory ORDER BY expiry_date", conn)
    if df.empty:
        st.info("Inventory is currently empty.")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "🚨 Urgent Requests":
    st.header("🚨 Urgent & Emergency Requests")
    df = pd.read_sql("""
        SELECT hospital_name, blood_type, quantity_needed, urgency, request_date
        FROM hospital_requests 
        WHERE status='pending' AND urgency IN ('urgent', 'emergency')
        ORDER BY CASE urgency WHEN 'emergency' THEN 1 ELSE 2 END
    """, conn)
    if df.empty:
        st.success("🎉 No urgent requests at the moment!")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "⏳ Expiring Soon":
    st.header("⏳ Blood Expiring in Next 7 Days")
    df = pd.read_sql("""
        SELECT bag_id, blood_type, donation_date, expiry_date,
               ROUND(julianday(expiry_date) - julianday('now')) AS days_left
        FROM blood_inventory 
        WHERE status='available' AND expiry_date <= date('now','+7 days')
        ORDER BY expiry_date
    """, conn)
    if df.empty:
        st.success("All blood bags are fresh! No expirations soon. ✅")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "➕ Add Donation":
    st.header("➕ Record New Blood Donation")
    with st.form("donation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            donor_name = st.text_input("👤 Donor Name*", placeholder="Full name")
            donor_blood = st.selectbox("🩸 Blood Type*", ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
        with col2:
            donor_phone = st.text_input("📞 Phone (optional)")
            volume = st.number_input("💉 Volume (ml)", min_value=300, max_value=550, value=450, step=10)

        submitted = st.form_submit_button("💾 Record Donation")

        if submitted:
            if not donor_name.strip():
                st.error("Donor name is required!")
            else:
                today = datetime.now().strftime('%Y-%m-%d')
                expiry = (datetime.now() + timedelta(days=42)).strftime('%Y-%m-%d')

                cur = conn.cursor()
                cur.execute("SELECT donor_id FROM donors WHERE name = ? AND blood_type = ?", (donor_name.strip(), donor_blood))
                row = cur.fetchone()

                if row:
                    donor_id = row[0]
                    cur.execute("UPDATE donors SET last_donation_date = ?, phone = COALESCE(?, phone) WHERE donor_id = ?",
                                (today, donor_phone or None, donor_id))
                else:
                    cur.execute("INSERT INTO donors (name, blood_type, phone, last_donation_date) VALUES (?, ?, ?, ?)",
                                (donor_name.strip(), donor_blood, donor_phone or None, today))
                    donor_id = cur.lastrowid

                cur.execute("INSERT INTO blood_inventory (blood_type, donor_id, donation_date, expiry_date, volume_ml) VALUES (?, ?, ?, ?, ?)",
                            (donor_blood, donor_id, today, expiry, volume))
                conn.commit()
                st.success(f"✅ Donation recorded! Bag expires on {expiry}")
                st.rerun()

elif page == "👥 Donors":
    st.header("👥 Registered Donors")
    df = pd.read_sql("SELECT name, blood_type, phone, last_donation_date FROM donors ORDER BY name", conn)
    if df.empty:
        st.info("No donors registered yet.")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "🏥 Hospital Requests":
    st.header("🏥 All Hospital Requests")
    df = pd.read_sql("SELECT hospital_name, blood_type, quantity_needed, urgency, status, request_date FROM hospital_requests ORDER BY request_date DESC", conn)
    if df.empty:
        st.info("No hospital requests yet.")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "📝 Add Hospital Request":
    st.header("📝 Add New Hospital Request")
    with st.form("request_form"):
        col1, col2 = st.columns(2)
        with col1:
            hospital = st.text_input("🏥 Hospital Name*")
            blood_type = st.selectbox("🩸 Required Blood Type*", ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
        with col2:
            quantity = st.number_input("🔢 Bags Needed*", min_value=1)
            urgency = st.selectbox("⚡ Urgency", ['routine', 'urgent', 'emergency'])

        submitted = st.form_submit_button("📤 Submit Request")

        if submitted:
            if not hospital.strip():
                st.error("Hospital name is required!")
            else:
                cur = conn.cursor()
                cur.execute("INSERT INTO hospital_requests (hospital_name, blood_type, quantity_needed, urgency) VALUES (?, ?, ?, ?)",
                            (hospital.strip(), blood_type, quantity, urgency))
                conn.commit()
                st.success("Hospital request submitted successfully!")
                st.rerun()

# ====================== FOOTER ======================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>❤️ <strong>Blood Donation Management System</strong> • Responsive • Beautiful • Built to Save Lives</p>
    <p>December 30, 2025</p>
</div>
""", unsafe_allow_html=True)

conn.close()
