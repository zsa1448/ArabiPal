import streamlit as st
import json
from db_setup import init_db, mark_word_learned, mark_word_not_learned, mark_word_correct, get_mastered_words_count, get_learned_words, get_words_to_review, is_word_learned
from openai import OpenAI
import os
from datetime import datetime
import tempfile
import random
import streamlit.components.v1 as components
import re

init_db()

client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))

def normalize_arabic(text):
    text = text.strip().lower()
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())

    return text

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
    .buttons {
        margin-top: 30px;}
        
    div.stButton > button {
        border: 1px solid #d1d5db;
        background-color: #f9fafb;
        color: #374151;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: 500;
        transition: all 0.2s ease; }
    
    div.stButton > button:hover {
        border-color: #4f46e5;
        color: #4f46e5;
        background-color: #eef2ff;}
    
    div.stButton > button[kind="primary"] {
        background-color: #4f46e5;
        color: white;
        border: none;}
    
    div.stButton > button[kind="primary"]:hover {
        background-color: #4338ca;}
    </style>
""", unsafe_allow_html=True)

st.markdown( "<h1 style='text-align:left; color:#3832aa;'>Flashcards</h1>", unsafe_allow_html=True)


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
#check if user is logged in or not and level is set
if "user" not in st.session_state or "level" not in st.session_state.user:
    st.warning("Please log in first .")
    st.stop()

user = st.session_state.user
user_id = user.get("id")
user_level = user.get("level")

if not user_id or not user_level:
    st.error("invalid data entered")
    st.stop()
    
if "selected_category" not in st.session_state:
    st.warning(" You did not select a category, please select a category to proceed")
    st.stop()

selected_category = st.session_state.selected_category

if user_level not in vocab_data or selected_category not in vocab_data[user_level]:
    st.error(f" No vocab words were found for {selected_category} category < {user_level} >.")
    st.stop()

# this was added before the spaced repetion if want to go back just uncomment this and remove the below codes: words = vocab_data[user_level][selected_category]# list of dicts

#spaced repetetion 
review_words = get_words_to_review(user_id, selected_category, user_level)
all_words = vocab_data[user_level][selected_category]
words_prioritized = review_words + [w["arabic"] for w in all_words if w["arabic"] not in review_words]
words = [w for w in all_words if w["arabic"] in words_prioritized]

total = len(words)

st.subheader(f"{selected_category} – {len(words)} words")

if "current_card_index" not in st.session_state:
    st.session_state.current_card_index = 0

current_index = st.session_state.current_card_index
total_words = len(words)


# Display flashcard
if "card_index" not in st.session_state:
    st.session_state.card_index = 0

index = st.session_state.card_index
word = words[index]
progress = (index + 1) / total
st.progress(progress)

arabic = word["arabic"]
translit = word["translit"]
english = word["english"]

col_speak = st.columns([4, 1])[1] 
with col_speak:
    if st.button("🗣️Speak it?", key=f"speak_{index}", type="secondary"):
        st.session_state.speaking_target_word = arabic
        st.switch_page("pages/SpeakingLab.py")


is_learned = is_word_learned(user_id, arabic)

components.html(f"""
        <html>
        <head>
        <style>
        .flashcard {{
            background: linear-gradient(135deg, #e0ddff, #f3f1ff);
            border: 2px solid #6C63FF;
            border-radius: 14px;
            padding: 26px;
            text-align: center;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            margin: 20px auto;
            max-width: 600px;
            box-shadow: 0 8px 20px rgba(79, 70, 229, 0.15);
            direction: rtl;
            position: relative;
            transition: 0.2s ease;
        }}

        .flashcard:hover {{
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.25);}}

        .front {{
            font-weight: bold;
            color: #312e81;
            font-size: 51px;
        }}
        
        .back {{
            font-size: 22px;
            color: #374151;
            margin-top: 10px;
            line-height: 1.6;
        }}
        .back strong {{
            color: #4f46e5;}}
        
        .badge {{
            position: absolute;
            top: 12px;
            right: 12px;
            background: #a7f3d0;
            color: #166534;
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #bbf7d0;
        }}
        </style>
        </head>
        
        <body>
        
        <div class="flashcard">
        
            {"<div class='badge'>✔ Learned</div>" if is_learned else ""}
        
            <div class="front">{arabic}</div>
        
            <div class="back">
                <strong>Translit:</strong> {translit}<br>
                <strong>English meaning:</strong> {english}
            </div>
        
        </div>
        
        </body>
        </html>
        """, height=320)

col_listen, col_action = st.columns([1, 2])
with col_listen:
    if st.button("🔊", use_container_width=True):
        try:
            tts = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=arabic
            )
            with open("temp_audio.mp3", "wb") as f:
                tts.stream_to_file(f.name)
            st.audio("temp_audio.mp3", format="audio/mp3", autoplay=True)
            os.remove("temp_audio.mp3")
        except Exception as e:
            st.error("Error in loading audio")

with col_action:
    if is_learned:
        if st.button("Not Learned ✗", use_container_width=True):
            mark_word_not_learned(user_id, arabic)
            st.rerun()

    else:
        col_learned, col_review = st.columns(2, gap="small")
        with col_learned:
            if st.button("Learned ✓", type="primary", use_container_width=True):
                mark_word_learned(user_id, arabic, selected_category, user_level)
                st.rerun()
        with col_review:
            if st.button("Not Learned ✗", use_container_width=True):
                mark_word_not_learned(user_id, arabic)
                st.rerun()

col_prev, col_prog, col_next = st.columns([1, 3, 1])

with col_prev:
    if index > 0:
        if st.button("Previous", use_container_width=True):
            st.session_state.card_index -= 1
            st.rerun()

with col_prog:
    st.markdown(f"<p style='text-align:center; font-size:18px;'>كلمة {index+1} من {total}</p>", unsafe_allow_html=True)

with col_next:
    if index < total - 1:
        if st.button("Next", use_container_width=True):
            st.session_state.card_index += 1
            st.rerun()
    else:
        #put something congratualtory??? or no need i think its no need  or maybe taast?
        if st.button(" Start quick quiz  "):
                st.session_state.quiz_active = True
                st.session_state.quiz_questions = random.sample(words, 6)
                st.session_state.quiz_index = 0
                st.session_state.quiz_correct = 0
                st.rerun()

# quiz after to make sure you actually understand teh elarned words --> help auto master words
if "quiz_active" in st.session_state and st.session_state.quiz_active:
    if st.session_state.quiz_index >= 6:
        final_score = st.session_state.quiz_correct
        st.success(f" Thnak you for taking the quiz")
        score_html = f"""
                <div style="
                    background:#FFFAE5;
                    padding:12px 16px;
                    border-radius:10px;
                    margin-top:16px;
                    border:1px solid #FCF3C7;
                    font-size:18px;
                    color:#475569;
                ">
                    <span style="font-weight:800;">Score:</span>
                    <span style="font-weight:900; color:#4f46e5; margin-left:6px;">
                        {final_score} / 
                    </span>
                </div>
                """
        st.markdown(score_html, unsafe_allow_html=True)
        st.session_state.quiz_active = False


        for key in ["quiz_questions", "quiz_index", "quiz_correct","current_q_type", "direction", "quiz_feedback"]:
            st.session_state.pop(key, None)
        
        if st.button(" Back to vocabulary words "):
            st.rerun()
        st.stop()
        
    st.subheader(f"Quick quiz – Question {st.session_state.quiz_index + 1} of 6")

    if "quiz_questions" not in st.session_state or not st.session_state.quiz_questions:
        st.session_state.quiz_questions = random.sample(words, 6)
        st.session_state.quiz_index = 0
        st.session_state.quiz_correct = 0
        learned_in_category = []
        for w in words:   # 'words' is already the prioritized list for this category
            if is_word_learned(user_id, w["arabic"]):
                learned_in_category.append(w)

        num_questions = min(6, len(learned_in_category))
        st.session_state.quiz_questions = random.sample(learned_in_category, num_questions)
        st.session_state.quiz_index = 0
        st.session_state.quiz_correct = 0
    
    if "quiz_feedback" not in st.session_state:
        st.session_state.quiz_feedback = None
    
    if "current_q_type" not in st.session_state:
        st.session_state.current_q_type = random.choice(["mcq", "fill"])
# i have added both en to ar and ar to en for recall which is better
    if "direction" not in st.session_state:
        st.session_state.direction = random.choice(["ar_to_en", "en_to_ar"])
        

    q_type = st.session_state.current_q_type
    direction = st.session_state.direction

    q_word = st.session_state.quiz_questions[st.session_state.quiz_index]
    arabic = q_word["arabic"]
    english = q_word["english"]

    # Question 1: MCQ – Choose correct meaning
    if q_type == "mcq":
        if direction == "ar_to_en":
            st.write(f"ما معنى الكلمة **{arabic}** ؟")
            correct = english
            pool = [w["english"] for w in words if w["english"] != english]
        else:
            st.write(f"What is the Arabic word for **{english}**?")
            correct = arabic
            pool = [w["arabic"] for w in words if w["arabic"] != arabic]
            
        if "current_options" not in st.session_state:
            sampled = random.sample(pool, min(3, len(pool)))
            options = [correct] + sampled
            random.shuffle(options)
            st.session_state.current_options = options
        else:
            options = st.session_state.current_options
            
        if st.session_state.quiz_feedback is None:    
            for opt in options:
                if st.button(opt, use_container_width=True):
                    if opt == correct:
                        st.session_state.quiz_correct += 1
                        mark_word_correct(user_id, arabic)
                        st.session_state.quiz_feedback = ("correct", correct)
                    else:
                        st.session_state.quiz_feedback = ("wrong", correct)

        if st.session_state.quiz_feedback:
            status, correct_answer = st.session_state.quiz_feedback
            if status == "correct":
                st.success("Correct answer!")
            else:
                st.error(f"Incorrect ❌ (Answer: {correct_answer})")
            
            if st.button("Next Question"):
                st.session_state.quiz_index += 1
                st.session_state.quiz_feedback = None
                st.session_state.current_q_type = random.choice(["mcq", "fill"])
                st.session_state.direction = random.choice(["ar_to_en", "en_to_ar"])
                st.session_state.pop("current_options", None)
                st.rerun()

    # Question 2: Fill-in-the-blank 
    elif q_type == "fill":
        if direction == "en_to_ar":
            st.write(f"اكتب الكلمة العربية التي تعني **{english}**")
            correct = arabic
        else:
            st.write(f"Type the English meaning of **{arabic}**")
            correct = english
            
        user_ans = st.text_input("Your answer:", key=f"fill_{st.session_state.quiz_index}")
        if st.session_state.quiz_feedback is None:
            if st.button(" Submit answer "):
                if not user_ans.strip():
                    st.warning("Please enter an answer")
                else:
                    if normalize_arabic(user_ans) == normalize_arabic(correct):
                        st.session_state.quiz_correct += 1
                        mark_word_correct(user_id, arabic)
                        st.session_state.quiz_feedback = ("correct", correct)
                    else:
                        st.session_state.quiz_feedback = ("wrong", correct)
                        
        if st.session_state.quiz_feedback:
            status, correct_answer = st.session_state.quiz_feedback
        
            if status == "correct":
                st.success("Correct answer!")
            else:
                st.error(f"Incorrect ❌ (Answer: {correct_answer})")
        
            if st.button("Next Question"):
                st.session_state.quiz_index += 1
                st.session_state.quiz_feedback = None
                st.session_state.current_q_type = random.choice(["mcq", "fill"])
                st.session_state.direction = random.choice(["ar_to_en", "en_to_ar"])
                st.rerun()

            