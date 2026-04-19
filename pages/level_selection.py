import streamlit as st
from db_setup import get_connection


st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Nunito&display=swap" rel="stylesheet">
    <style>
        body, .stTextArea, .stInfo, .stMarkdown { font-family: 'Nunito', serif !important; }
        
        h1, h2, h3, h4, h5, h6 {font-family: 'Lora', sans-serif !important; }
        
        .css-1d391kg { font-family: 'Lora', sans-serif !important;}
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

.level-card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 10px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.03);
    transition: 0.3s;}

.level-card:hover {
    border-color: #4f46e5;
    box-shadow: 0 12px 25px rgba(79,70,229,0.10);}

div.stButton {
    margin-bottom: 10px;}

.level-title {
    font-size: 22px; 
    font-weight: 700;
    color: #4f46e5;  
    margin-bottom: 12px;
}

.level-desc {
    font-size: 17px;  
    color: #3f3f46;  
    margin-bottom: 20px;
    margin-top: 8px;}

div.stButton > button[kind="primary"] {
    background-color: #4f46e5 !important;  
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 20px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: background-color 0.3s ease;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #4338ca !important; 
    box-shadow: none !important;}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state or not st.session_state.user.get("id"):
    st.warning("Please login or sign up first.")
    st.stop()

user_id = st.session_state.user["id"]

st.markdown("<h1> Choose Your Arabic Level</h1>", unsafe_allow_html=True)

levels = {
    "A1": {
        "name": "Absolute Beginner (A1)",
        "desc": "Start from the basics. Learn the Arabic alphabet,  greetings, numbers, and essential vocabulary to build your first sentences."
    },
    "A2": {
        "name": "Beginner (A2)",
        "desc": "Talk about daily routines, family, shopping, and common situations using simple sentences."
    },
    "B1": {
        "name": "Intermediate (B1)",
        "desc": "Express yourself with more confidence. Describe experiences, share opinions, and understand longer conversations."
    }
}

selected_level = None

for lvl_key, info in levels.items():
    card = st.container()
    
    with card:
        st.markdown(f"""
        <div class="level-card">
            <div class="level-title">{info['name']}</div>
            <div class="level-desc">{info['desc']}</div>
        """, unsafe_allow_html=True)

        clicked = st.button("Select Level", type="primary", key=f"btn_{lvl_key}" )
        st.markdown("</div>", unsafe_allow_html=True) 
    if clicked:
        selected_level = lvl_key
        break

if selected_level:
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET level = ? WHERE id = ?", (selected_level, user_id))
    conn.commit()
    conn.close()

    st.session_state.user["level"] = selected_level
    st.success(f"Level set to {levels[selected_level]['name']} ")
    st.switch_page("pages/Home.py")