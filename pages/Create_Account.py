import streamlit as st
import bcrypt
from datetime import datetime
from db_setup import get_connection
import sqlite3


st.set_page_config(page_title="Sign Up", layout="centered")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Nunito&display=swap" rel="stylesheet">
    <style>
        /* Body text uses Lora */
        body, .stTextArea, .stInfo, .stMarkdown {
            font-family: 'Nunito', serif !important;
        }
        
        /* Headings (h1, h2, h3) use Nunito */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Lora', sans-serif !important;
        }
        
        /* You can target specific classes if needed */
        .css-1d391kg {  /* example Streamlit header class */
            font-family: 'Lora', sans-serif !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

div[data-baseweb="input"] {
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
    background-color: white;
}
div[data-baseweb="input"] input {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    padding: 10px !important;
    background: transparent !important;
}

div[data-baseweb="input"]:focus-within {
    border: 1px solid #4f46e5 !important;
    box-shadow: 0 0 0 2px #eef2ff !important;
}

div[data-baseweb="input"][aria-invalid="true"] {
    border: 1px solid #e5e7eb !important;
    box-shadow: none !important;
}
label {
    font-weight: 900 !important;
    color: #3832aa !important;
}

div.stButton > button {
    border: 1px solid #d1d5db;
    background-color: #ffffff;
    color: #374151;
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: 500;
}
div.stButton > button:hover {
    border-color: #4f46e5;
    color: #4f46e5;
    background-color: #eef2ff;
}

div.stButton > button[kind="primary"] {
    background-color: #4f46e5;
    color: white;
    border: none;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #4338ca;
}
div.stButton > button[kind="tertiary"] {
            background: transparent;
            border: none;
            color: #1E3A8A;
            box-shadow: none;
            padding: 0px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: underline;
            cursor: pointer;

        }
div.stButton > button[kind="tertiary"]:hover {
    background-color: none;
    color: #4338ca;
    }


</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#3832aa; '>Create Your Account</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Start learning Arabic today with ArabiPal</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])
with col2:
    username = st.text_input("Choose Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Get Started", type="primary",use_container_width=True):
        if not username or not password:
            st.warning("Please fill all fields")
        #should i put it?
        elif " " in username:
            st.warning("Username cannot contain spaces")

        elif len(password) < 6:
            st.warning("Password must be at least 6 characters")

        elif password != confirm:
            st.error("Passwords do not match")

        else:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            conn = get_connection()
            c = conn.cursor()

            try:
                c.execute("""
                    INSERT INTO users (username, password_hash, created_at, level) VALUES (?, ?, ?, ?) 
                    """, (username, hashed, datetime.now().isoformat(), "A1"))
                conn.commit()
                c.execute("SELECT id FROM users WHERE username = ?", (username,))
                
                user_id = c.fetchone()["id"]
                st.session_state.user = { "id": user_id,  "username": username, "level": "A1"}
                st.success("Account created successfully 🎉")
                st.switch_page("pages/level_selection.py")

            except sqlite3.IntegrityError:
                st.error("Username already exists")

            finally:
                conn.close()

    
    st.markdown("""
        <div style='text-align:center; margin-top:8px; font-size:14px;'>
            <span style='color:#6b7280;'>Already have an account? </span>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("Log in", type="tertiary"):
            st.switch_page("pages/login.py")