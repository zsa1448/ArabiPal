import streamlit as st
#from db_setup import init_db, get_connection

st.set_page_config(page_title="Arabic AI Tutor", page_icon="📚", layout="centered")

#init_db()

st.markdown("""
<style>
.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: #3832aa;
    text-align: center;
}

.hero-sub {
    font-size: 18px;
    color: #6b7280;
    text-align: center;
    margin-bottom: 30px;
}

.cta-container {
    display: flex;
    justify-content: center;
    gap: 10px;
}

div.stButton > button {
    border: 1px solid #C3C1F6;
    background-color: #ffffff;
    color: #374151;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
    transition: all 0.2s ease;
    
}

/* Button hover */
div.stButton > button:hover {
    border-color: #4f46e5;
    color: #4f46e5; 
    background-color: #EEF2FF;
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(79, 70, 229, 0.2);
}

/* Primary button */
div.stButton > button[kind="primary"] {
    background-color: #4f46e5;
    color: white;
    border: none;
}

/* Primary hover */
div.stButton > button[kind="primary"]:hover {
    background-color: #4338ca;
}

.fade-in {
    animation: fadeIn 0.8s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.logo-row {
    display: flex;
    justify-content: center;
    gap: 14px;
    margin: 30px 0;
}

.pill {
    width: 60px;
    height: 120px;
    border-radius: 30px;
    animation: bounce 1.8s infinite ease-in-out;
}

.pill:nth-child(1) { background: #4f46e5; animation-delay: 0s; }
.pill:nth-child(2) { background: #6366f1; animation-delay: 0.2s; }
.pill:nth-child(3) { background: #fde68a; animation-delay: 0.4s; }
.pill:nth-child(4) { background: #4f46e5; animation-delay: 0.6s; }

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}





</style>
""", unsafe_allow_html=True)


# ================= HERO =================
st.markdown("""
<div class="logo-row">
    <div class="pill"></div>
    <div class="pill"></div>
    <div class="pill"></div>
    <div class="pill"></div>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="fade-in">', unsafe_allow_html=True)
st.markdown('<div class="hero-title">ArabiPal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub"> Learn Arabic with your AI companion </div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ================= BUTTONS =================
col1, col2, col3 = st.columns([1,2,1])

with col2:
    if st.button("🚀 Start Learning", type="primary", use_container_width=True):
        st.switch_page("pages/Create_Account.py")

    if st.button("Log in", use_container_width=True):
        st.switch_page("pages/login.py")