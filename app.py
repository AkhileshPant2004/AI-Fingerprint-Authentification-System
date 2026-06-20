import streamlit as st
import cv2
import numpy as np
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Forensic Fingerprint Identification System",
    layout="wide"
)

# =====================================================
# CUSTOM FORENSIC UI
# =====================================================

st.markdown("""
<style>

/* Main Background */

.stApp {
    background-color: #0b1220;
    color: white;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #111827;
}

/* Titles */

h1, h2, h3 {
    color: #00d4ff;
    font-weight: bold;
}

/* Buttons */

.stButton>button {
    background-color: #00d4ff;
    color: black;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    padding: 10px 20px;
}

/* Text Inputs */

.stTextInput>div>div>input {
    background-color: #1c2333;
    color: white;
    border-radius: 8px;
}

/* File Uploader */

.stFileUploader {
    background-color: #1c2333;
    padding: 10px;
    border-radius: 10px;
}

/* Metrics */

[data-testid="metric-container"] {
    background-color: #1c2333;
    border-radius: 12px;
    padding: 15px;
}

/* Tables */

[data-testid="stTable"] {
    background-color: #1c2333;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# CREATE FOLDERS
# =====================================================

os.makedirs("fingerprints", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# =====================================================
# DATABASE CONNECTION
# =====================================================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

c = conn.cursor()

# =====================================================
# CREATE TABLES
# =====================================================

# ---------------- USERS TABLE ---------------- #

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ---------------- FINGERPRINT TABLE ---------------- #

c.execute("""
CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criminal_name TEXT,
    age TEXT,
    crime_type TEXT,
    case_id TEXT UNIQUE,
    image_path TEXT,
    created_at TEXT
)
""")

conn.commit()

# =====================================================
# CREATE DEFAULT ADMIN
# =====================================================

c.execute(
    "SELECT * FROM users WHERE username=?",
    ("admin",)
)

admin_exists = c.fetchone()

if not admin_exists:

    c.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("admin", "admin123")
    )

    conn.commit()

# =====================================================
# SAVE FINGERPRINT
# =====================================================

def save_fingerprint(
    criminal_name,
    age,
    crime_type,
    case_id,
    image
):

    image_path = (
        f"fingerprints/{criminal_name}_{case_id}.png"
    )

    with open(image_path, "wb") as f:
        f.write(image.getbuffer())

    c.execute("""
    INSERT INTO fingerprints (
        criminal_name,
        age,
        crime_type,
        case_id,
        image_path,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        criminal_name,
        age,
        crime_type,
        case_id,
        image_path,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

# =====================================================
# IMAGE PREPROCESSING
# =====================================================

def preprocess_image(path):

    img = cv2.imread(path, 0)

    img = cv2.GaussianBlur(
        img,
        (5, 5),
        0
    )

    img = cv2.equalizeHist(img)

    return img

# =====================================================
# ORB MATCHING
# =====================================================

def orb_similarity(
    img1_path,
    img2_path
):

    img1 = preprocess_image(img1_path)
    img2 = preprocess_image(img2_path)

    orb = cv2.ORB_create(
        nfeatures=1000
    )

    kp1, des1 = orb.detectAndCompute(
        img1,
        None
    )

    kp2, des2 = orb.detectAndCompute(
        img2,
        None
    )

    if des1 is None or des2 is None:
        return 0, None

    bf = cv2.BFMatcher(
        cv2.NORM_HAMMING,
        crossCheck=True
    )

    matches = bf.match(
        des1,
        des2
    )

    matches = sorted(
        matches,
        key=lambda x: x.distance
    )

    good_matches = []

    for match in matches:

        if match.distance < 60:
            good_matches.append(match)

    score = len(good_matches)

    matched_image = cv2.drawMatches(
        img1,
        kp1,
        img2,
        kp2,
        good_matches[:30],
        None,
        flags=2
    )

    return score, matched_image

# =====================================================
# PDF REPORT GENERATION
# =====================================================

def generate_pdf(
    criminal_name,
    crime_type,
    case_id,
    confidence
):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font(
        "Arial",
        "B",
        18
    )

    pdf.cell(
        200,
        10,
        txt="FORENSIC FINGERPRINT REPORT",
        ln=True,
        align="C"
    )

    pdf.ln(20)

    pdf.set_font(
        "Arial",
        size=14
    )

    pdf.cell(
        200,
        10,
        txt=f"Criminal Name: {criminal_name}",
        ln=True
    )

    pdf.cell(
        200,
        10,
        txt=f"Crime Type: {crime_type}",
        ln=True
    )

    pdf.cell(
        200,
        10,
        txt=f"Case ID: {case_id}",
        ln=True
    )

    pdf.cell(
        200,
        10,
        txt=f"Confidence Score: {confidence}%",
        ln=True
    )

    pdf.cell(
        200,
        10,
        txt=f"Generated On: {datetime.now()}",
        ln=True
    )

    pdf.output(
        "forensic_report.pdf"
    )

# =====================================================
# SESSION MANAGEMENT
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =====================================================
# LOGIN PAGE
# =====================================================

if not st.session_state.logged_in:

    st.title("🔐 AI Forensic Login System")

    st.subheader(
        "Fingerprint Criminal Identification Software"
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    # =================================================
    # LOGIN
    # =================================================

    with col1:

        if st.button("Login"):

            c.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )

            user = c.fetchone()

            if user:

                st.session_state.logged_in = True

                st.success(
                    "Login Successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid Username or Password"
                )

    # =================================================
    # CREATE ACCOUNT
    # =================================================

    with col2:

        if st.button("Create Account"):

            if username and password:

                c.execute(
                    "SELECT * FROM users WHERE username=?",
                    (username,)
                )

                existing_user = c.fetchone()

                if existing_user:

                    st.error(
                        "Username Already Exists"
                    )

                else:

                    c.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (username, password)
                    )

                    conn.commit()

                    st.success(
                        "Account Created Successfully"
                    )

# =====================================================
# MAIN APPLICATION
# =====================================================

else:

    st.title(
        "AI-Based Fingerprint Identification System"
    )

    # OPTIONAL BANNER
    # Put banner.png inside project folder

    if os.path.exists("banner.png"):

        st.image(
            "banner.png",
            use_container_width=True
        )

    st.sidebar.success(
        "Logged In Successfully"
    )

    # =================================================
    # LOGOUT
    # =================================================

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False

        st.rerun()

    # =================================================
    # SIDEBAR MENU
    # =================================================

    menu = [
        "Dashboard",
        "Add Criminal Record",
        "View Criminal Database",
        "Search Criminal",
        "Delete Criminal Record",
        "Match Fingerprint"
    ]

    choice = st.sidebar.selectbox(
        "Navigation Menu",
        menu
    )

    # =================================================
    # DASHBOARD
    # =================================================

    if choice == "Dashboard":

        st.header("System Dashboard")

        c.execute(
            "SELECT COUNT(*) FROM fingerprints"
        )

        total_records = c.fetchone()[0]

        c.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = c.fetchone()[0]

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Total Criminal Records",
                total_records
            )

        with col2:

            st.metric(
                "Total Registered Users",
                total_users
            )

        st.info("""
        AI-Based Criminal Fingerprint Identification System

        Features:
        • Criminal fingerprint storage
        • AI-assisted fingerprint matching
        • Authentication system
        • Criminal database management
        • Match visualization
        • PDF forensic report generation
        • Crime analytics dashboard
        """)

        # =============================================
        # CRIME ANALYTICS
        # =============================================

        st.subheader("Crime Analytics")

        c.execute("""
        SELECT crime_type, COUNT(*)
        FROM fingerprints
        GROUP BY crime_type
        """)

        crime_data = c.fetchall()

        if crime_data:

            chart_data = {}

            for row in crime_data:

                chart_data[row[0]] = row[1]

            st.bar_chart(chart_data)

        else:

            st.info(
                "No Crime Data Available"
            )

    # =================================================
    # ADD CRIMINAL RECORD
    # =================================================

    elif choice == "Add Criminal Record":

        st.header("Add Criminal Record")

        criminal_name = st.text_input(
            "Criminal Name"
        )

        age = st.text_input(
            "Age"
        )

        crime_type = st.text_input(
            "Crime Type"
        )

        case_id = st.text_input(
            "Case ID"
        )

        image = st.file_uploader(
            "Upload Fingerprint",
            type=["png", "jpg", "jpeg"]
        )

        if st.button(
            "Save Criminal Record"
        ):

            if (
                criminal_name and
                age and
                crime_type and
                case_id and
                image
            ):

                c.execute(
                    "SELECT * FROM fingerprints WHERE case_id=?",
                    (case_id,)
                )

                existing_case = c.fetchone()

                if existing_case:

                    st.error(
                        "Case ID Already Exists"
                    )

                else:

                    try:

                        save_fingerprint(
                            criminal_name,
                            age,
                            crime_type,
                            case_id,
                            image
                        )

                        st.success(
                            "Criminal Record Saved Successfully"
                        )

                    except Exception as e:

                        st.error(
                            f"Database Error: {e}"
                        )

            else:

                st.warning(
                    "Please Fill All Fields"
                )

    # =================================================
    # VIEW DATABASE
    # =================================================

    elif choice == "View Criminal Database":

        st.header("Criminal Database")

        c.execute("""
        SELECT
            criminal_name,
            age,
            crime_type,
            case_id,
            created_at,
            image_path
        FROM fingerprints
        ORDER BY id DESC
        """)

        records = c.fetchall()

        if records:

            for record in records:

                col1, col2 = st.columns([1, 3])

                with col1:

                    if os.path.exists(record[5]):

                        st.image(
                            record[5],
                            width=150
                        )

                with col2:

                    st.write(
                        f"👤 Criminal Name: {record[0]}"
                    )

                    st.write(
                        f"Age: {record[1]}"
                    )

                    st.write(
                        f"⚠ Crime Type: {record[2]}"
                    )

                    st.write(
                        f"Case ID: {record[3]}"
                    )

                    st.write(
                        f"Added On: {record[4]}"
                    )

                st.markdown("---")

        else:

            st.info(
                "No Criminal Records Found"
            )

    # =================================================
    # SEARCH CRIMINAL
    # =================================================

    elif choice == "Search Criminal":

        st.header("🔎 Search Criminal")

        search_value = st.text_input(
            "Enter Criminal Name or Case ID"
        )

        if st.button("Search"):

            c.execute("""
            SELECT
                criminal_name,
                age,
                crime_type,
                case_id,
                created_at,
                image_path
            FROM fingerprints
            WHERE criminal_name LIKE ?
            OR case_id LIKE ?
            """, (
                f"%{search_value}%",
                f"%{search_value}%"
            ))

            results = c.fetchall()

            if results:

                for result in results:

                    col1, col2 = st.columns([1, 3])

                    with col1:

                        if os.path.exists(result[5]):

                            st.image(
                                result[5],
                                width=150
                            )

                    with col2:

                        st.write(
                            f"👤 Criminal Name: {result[0]}"
                        )

                        st.write(
                            f"Age: {result[1]}"
                        )

                        st.write(
                            f"⚠ Crime Type: {result[2]}"
                        )

                        st.write(
                            f"Case ID: {result[3]}"
                        )

                        st.write(
                            f"Added On: {result[4]}"
                        )

                    st.markdown("---")

            else:

                st.error(
                    "No Criminal Found"
                )

    # =================================================
    # DELETE RECORD
    # =================================================

    elif choice == "Delete Criminal Record":

        st.header("Delete Criminal Record")

        case_id = st.text_input(
            "Enter Case ID"
        )

        if st.button("Delete Record"):

            c.execute(
                "SELECT image_path FROM fingerprints WHERE case_id=?",
                (case_id,)
            )

            record = c.fetchone()

            if record:

                image_path = record[0]

                if os.path.exists(image_path):

                    os.remove(image_path)

                c.execute(
                    "DELETE FROM fingerprints WHERE case_id=?",
                    (case_id,)
                )

                conn.commit()

                st.success(
                    "Record Deleted Successfully"
                )

            else:

                st.error(
                    "Case ID Not Found"
                )

    # =================================================
    # MATCH FINGERPRINT
    # =================================================

    elif choice == "Match Fingerprint":

        st.header("Match Fingerprint")

        uploaded = st.file_uploader(
            "Upload Unknown Fingerprint",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded:

            temp_path = "uploads/temp.png"

            with open(temp_path, "wb") as f:

                f.write(
                    uploaded.getbuffer()
                )

            st.image(
                temp_path,
                caption="Uploaded Fingerprint",
                width=250
            )

            c.execute("""
            SELECT
                criminal_name,
                crime_type,
                case_id,
                image_path
            FROM fingerprints
            """)

            records = c.fetchall()

            best_score = 0
            best_match = None
            best_visual = None

            for (
                criminal_name,
                crime_type,
                case_id,
                image_path
            ) in records:

                score, visual = orb_similarity(
                    temp_path,
                    image_path
                )

                if score > best_score:

                    best_score = score

                    best_match = (
                        criminal_name,
                        crime_type,
                        case_id,
                        image_path
                    )

                    best_visual = visual

            confidence = min(
                best_score,
                100
            )

            st.subheader("📌 Match Result")

            if best_match:

                col1, col2 = st.columns(2)

                with col1:

                    st.image(
                        best_match[3],
                        caption="Matched Fingerprint",
                        width=250
                    )

                with col2:

                    st.write(
                        f"👤 Criminal Name: {best_match[0]}"
                    )

                    st.write(
                        f"⚠ Crime Type: {best_match[1]}"
                    )

                    st.write(
                        f"Case ID: {best_match[2]}"
                    )

                    st.write(
                        f"Confidence Score: {confidence}%"
                    )

                    if confidence > 20:

                        st.success(
                            "Fingerprint Match Found"
                        )

                        # =============================
                        # GENERATE PDF REPORT
                        # =============================

                        generate_pdf(
                            best_match[0],
                            best_match[1],
                            best_match[2],
                            confidence
                        )
                        

                        with open(
                            "forensic_report.pdf",
                            "rb"
                        ) as pdf_file:

                            st.download_button(
                                label="📄 Download Forensic Report",
                                data=pdf_file,
                                file_name="forensic_report.pdf",
                                mime="application/pdf"
                            )

                    else:

                        st.warning(
                            "Weak Match Detected"
                        )

                # =====================================
                # MATCH VISUALIZATION
                # =====================================

                if best_visual is not None:

                    st.subheader(
                        "AI Match Visualization"
                    )

                    st.image(
                        best_visual,
                        channels="BGR",
                        use_container_width=True
                    )

            else:

                st.error(
                    "No Match Found"
                )