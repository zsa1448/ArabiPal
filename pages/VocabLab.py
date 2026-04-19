import streamlit as st
import json
from db_setup import get_connection, init_db, get_learned_words

init_db()

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Nunito&display=swap" rel="stylesheet">
    <style>
        body, .stTextArea, .stInfo, .stMarkdown {font-family: 'Nunito', serif !important;}
        
        h1, h2, h3, h4, h5, h6 {font-family: 'Lora', sans-serif !important;}
        
        .css-1d391kg { font-family: 'Lora', sans-serif !important;}
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

.card {
    padding: 28px 24px;
    border-radius: 18px;
    border: 1px solid #e6e6e6;
    background-color: white;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 280px;}

.card:hover {
   transform: translateY(-8px) scale(1.02);
    box-shadow: 0 12px 30px rgba(108, 99, 255, 0.15);
    border-color: #6C63FF;}

.card-title {
   font-size: 20.5px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #1f2937;
    line-height: 1.3;
    min-height: 54px;              
    display: flex;
    align-items: center;}

.card-sub {
    color: #64748b;
    font-size: 14.5px;
    margin-bottom: 24px;
    flex-grow: 1;}
    
.icon-circle {
    width: 57px;
    height: 67px;
    border-radius: 50%;
    background: linear-gradient(135deg, #c4c1ff, #e0ddff);  
    color: #4f46e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin-bottom: 18px;
    box-shadow: 0 4px 12px rgba(108, 99, 255, 0.25);
    flex-shrink: 0;}
    
.progress-container {
    margin: 12px 0 20px 0;
    flex-grow: 1;}

.progress-bar {
    height: 7px;
    background: #e2e8f0;
    border-radius: 9999px;
    overflow: hidden;}

.progress-fill {
    height: 100%;
    background: linear-gradient(to right, #6C63FF, #a29bfe);
    border-radius: 9999px;
    transition: width 0.5s ease;}
.stButton > button {
    width: 100%;
    background: #6C63FF;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 13px 16px;
    font-weight: 600;
    font-size: 15.5px;
    transition: all 0.25s ease;
    margin-top: auto;
}

.stButton > button:hover {
    background: #5a52e0;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(108, 99, 255, 0.3);}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center; color:#3832aa;'> 🧩 VocabLab </h1>",
    unsafe_allow_html=True
)

#load from my cutom made json for the vocabulary of user level
@st.cache_data
def load_vocab_data():
    try:
        with open("data/vocabulary_data.json", "r", encoding="utf-8") as f:  
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("Error: File is not found ")
        return {}
    except Exception as e:
        st.error(f" Error in loading data: {str(e)}")
        return {}

vocab_data = load_vocab_data()
#check if user is logged in or not
if "user" not in st.session_state or "level" not in st.session_state.user:
    st.warning(" Login first or select level of language profession.")
    st.stop()
#define user id and leevl
user_level = st.session_state.user["level"]
user_id = st.session_state.user["id"]

st.markdown(f"""
<div style="
    font-size: 26px;
    font-weight: 700;
    color: #908AFF;
    margin-bottom: 4px;
">
    🧠 Level {user_level} • Vocabulary
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    font-size: 17px;
    color: #000000;
    margin-bottom: 18px;
">
    Pick a category and grow your Arabic vocabulary one word at a time.
</div>
""", unsafe_allow_html=True)

if user_level not in vocab_data:
    st.error(f" No vocabulary found for this level {user_level}  ")
    st.stop()

categories = vocab_data[user_level]  
icon_map = {
    # A1 + A2 + B1
    "Greetings": "👋", "Numbers": "🔢", "Days of the Week": "📅", "Essential Nouns": "📝", "Expressions": "💬", "Places": "📍",
    "Verbs": "🏃‍♂️", "Family": "👨‍👩‍👧", "Colors": "🌈", "Body Parts": "🦵", "Basic Adjectives": "✨", "Pronouns": "👤", "Question Words": "❓",
    "Food & Drinks": "🍎", "Daily Routine & Time Expressions": "⏰", "Clothes": "👕", "Shopping": "🛍️", "House & Furniture": "🏠", "Weather & Seasons": "☀️",  "Jobs": "💼",  "Hobbies": "🎨", "Directions": "🧭",  "Health": "🩺", "Basic Connectors": "🔗",
    "Past Tense Verbs": "⏳", "Opinions": "💭", "Time Expressions & Sequencing": "📆", "Media, News & Technology": "📰",
    "Work & Education": "📚",  "Environment & Nature": "🌳", "Travel & Holidays": "✈️", "Future Tense Verbs": "🔮", "Default": "📖"
}

def count_learned_words(user_id, level, category_name):
    learned_words = get_learned_words(user_id, level) 
    count = sum(1 for word_ar, cat in learned_words if cat == category_name)
    return count

cols = st.columns(3)  

for index, (category_name, words) in enumerate(categories.items()):
    word_count = len(words)
    learned_count = count_learned_words(user_id, user_level, category_name)
    progress_percent = int((learned_count / word_count) * 100) if word_count > 0 else 0
    is_completed = learned_count >= word_count and word_count > 0
    
    icon = icon_map.get(category_name, icon_map["Default"])
    
    with cols[index % 3]:
        if is_completed:
            st.markdown(f"""
            <div class="card">
                <div class="icon-circle">{icon}</div>
                <div class="card-title">{category_name}</div>
                <div class="card-sub" style="color: #10b981; font-weight: 600;">
                    Completed 
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Practice Again →", key=f"practice_{category_name}_{index}", use_container_width=True):
                st.session_state.selected_category = category_name
                st.switch_page("pages/Flashcards.py")
        else:
            st.markdown(f"""
            <div class="card">
                <div class="icon-circle">{icon}</div>
                <div class="card-title">{category_name}</div>
                <div class="card-sub">
                        {learned_count} of {word_count} words learned
                </div>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_percent}%"></div>
                    </div>
            </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Start Practice → ", key=f"start_{category_name}_{index}", use_container_width=True):
                st.session_state.selected_category = category_name
                st.switch_page("pages/Flashcards.py")   
            
if not categories:
    st.info("No categories is found for this level")