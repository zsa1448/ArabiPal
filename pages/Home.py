import streamlit as st
import sqlite3
from db_setup import get_user_mistakes, delete_user_mistake, get_learned_words,  get_mastered_words_count,  get_total_words_in_level, count_words_to_review,get_read_stories_count, get_writing_sessions_count, get_writing_exercises_count, get_conversation_days, get_conversation_scenarios, get_writing_accuracy, get_speaking_sessions_count, get_speaking_accuracy, get_level_progress, unlock_next_level, require_login
import streamlit.components.v1 as components


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
.modulecard {
    padding: 16px;
    border-radius: 14px;
    background: #FFFFFA;
    border: 1px solid #e5e7eb;
    margin-bottom: 16px;
    text-align: left;
    cursor: pointer;
}

.modulecard:hover {
    border-color: #4f46e5;
    background-color: #fafaff;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.08);
    transform: translateY(-2px);
}


.moduletitle {
    font-weight: 800;
    font-size: 18px;
    color: #3832aa;
    margin-bottom: 6px;
}

.moduledesc {
    font-size: 16px;
    color: #5A00A3;
    margin-bottom: 12px;
}
div.stButton > button[kind="primary"] {
    background-color: #4f46e5;
    color: white;
    border: none;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #4338ca;
    cursor: pointer;
}

div[data-testid="metric-container"] {
    background-color: #fafafa;
    border: 1px solid #f1f5f9;
    padding: 12px;
    border-radius: 12px;
}


.sectiontitle {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 10px;
    color: #3832aa;
}

div[data-testid="stMetricLabel"] {
    font-size: 20px;
    color: #1F2937;
}

div[data-testid="stMetricValue"] {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}

.sectiondivider {
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, #e5e7eb, transparent);
    margin: 24px 0 18px 0;
}
div.stButton > button {
    border: 1px solid #d1d5db;
    background-color: #ffffff;
    color: #374151;
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: 500;}

div.stButton > button:hover {
    border-color: #4f46e5;
    color: #4f46e5;
    background-color: #eef2ff;}
</style>
""", unsafe_allow_html=True)

@st.dialog("Requirements to Unlock Next Level")
def unlock_requirements(user_level):

    if user_level == "A1":
        st.write("**To unlock A2:**")
        st.write("- 70% vocabulary learned")
        st.write("- 30% vocabulary mastered")
        st.write("- 8 stories completed")
        st.write("- 8 speaking sessions")
        st.write("- 12 writing exercises")
        st.write("- 5 conversation sessions + 2 scenarios")

    elif user_level == "A2":
        st.write("**To unlock B1:**")
        st.write("- 80% vocabulary learned")
        st.write("- 50% vocabulary mastered")
        st.write("- 12 stories completed")
        st.write("- 14 speaking sessions")
        st.write("- 18 writing exercises")
        st.write("- 10 conversation sessions + all scenarios")

user_id, user_level = require_login()


new_level = unlock_next_level(user_id)
if new_level and not st.session_state.level_up:

    st.session_state.level_up = True
    @st.dialog("🎉 Next Level Unlocked")
    def level_up():
        st.success(f"You unlocked {new_level} level!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Stay in current level"):
                st.rerun()
        with col2:
            if st.button("Go to next level"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET level = ? WHERE id = ?", (new_level, user_id))
                conn.commit()
                conn.close()
                
                st.session_state.user["level"] = new_level
                st.toast(f"🎉 You are now {new_level}")
                st.rerun()
    level_up()
    
st.markdown(f'<h1 class="main-title">Welcome, {st.session_state.user["username"]} 👋</h1>', unsafe_allow_html=True)
st.markdown(f"<p style='color:#6b7280;'>Level {user_level} • Keep building your Arabic skills </p>", unsafe_allow_html=True)

progress_percent = get_level_progress(user_id, user_level)
st.progress(progress_percent / 100, text=f"Progress to next level: {int(progress_percent)}%")
if st.button("requirements"):
    unlock_requirements(user_level)
    
st.markdown("<h2 style='text-align:left; color:#000000;'> Progress Dahsboard </h2>", unsafe_allow_html=True)

st.markdown("""
Track your progress and continue your learning journey """)

# Section 1: Progress dashboard
#variables: 
#vocab module 
learned_count = len(get_learned_words(user_id, user_level))
mastered_count = get_mastered_words_count(user_id, user_level)
total_words = get_total_words_in_level(user_level)
review_count= count_words_to_review(user_id, user_level)
learned_percent = int((learned_count / total_words) * 100) if total_words > 0 else 0
mastered_percent = int((mastered_count / total_words) * 100) if total_words > 0 else 0

#reading module
read_count = get_read_stories_count(user_id)
current_level = user_level
milestones = {"A1": 8, "A2": 12, "B1": 18}
target = milestones.get(current_level, 18)
progress = read_count / target if target > 0 else 0
progress_percent = int(progress * 100)

#speaking module
speaking_session = get_speaking_sessions_count(user_id)
speaking_accuracy, speaking_attempts = get_speaking_accuracy(user_id)

# writing module
writing_session = get_writing_sessions_count(user_id)
exercises_count = get_writing_exercises_count(user_id)
writing_accuracy, correct_count, writing_attempts = get_writing_accuracy(user_id)

#convo module
conversation_days = get_conversation_days(user_id)
conversation_scenarios = get_conversation_scenarios(user_id)

# progress dashboard each a row will take

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="sectiontitle">Vocabulary</div>', unsafe_allow_html=True)
    st.metric("Learned", f"{learned_count}/{total_words}", f"{learned_percent}%")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Mastered", f"{mastered_count}/{total_words}", f"{mastered_percent}%")
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Need Review", review_count, "Spaced Repetition")

st.markdown('<hr class="sectiondivider">', unsafe_allow_html=True)

col_r, col_s,col_s2 = st.columns(3)
with col_r:
    st.markdown('<div class="sectiontitle">Reading</div>', unsafe_allow_html=True)
    st.metric("Stories Read", f"{read_count}/{target}", f" {progress_percent}%")
with col_s:
    st.markdown('<div class="sectiontitle">Speaking</div>', unsafe_allow_html=True)
    st.metric("Sessions Completed", speaking_session)
with col_s2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Avg. Pronunciation", f"{speaking_accuracy}%", f"{speaking_attempts} attempts")

st.markdown('<hr class="sectiondivider">', unsafe_allow_html=True)
col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    st.markdown('<div class="sectiontitle"> Writing</div>', unsafe_allow_html=True)
    st.metric("Sessions Completed", writing_session)
with col_w2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Exercises Done", exercises_count)
with col_w3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Writing Accuracy", f"{writing_accuracy}%", f"{correct_count}/{writing_attempts}")

st.markdown('<hr class="sectiondivider">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="sectiontitle"> Conversation </div>', unsafe_allow_html=True)
    st.metric("Practice Days", conversation_days)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric(" Scenarios Practiced", conversation_scenarios)


# Section 2: user mistake flashcards
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:left; color:#000000;'> Review & improve </h2>", unsafe_allow_html=True)
st.markdown(""" Review Your past mistakes and get better """)
mistakes = get_user_mistakes(user_id)

if not mistakes:
    st.info("🎉 You have no mistakes yet. Start practicing to see them here.") #should i make st.success or info is good?

else:
    if "mistake_index" not in st.session_state:
        st.session_state.mistake_index = 0
    
    index = st.session_state.mistake_index
    total = len(mistakes)
    if index >= total:
        st.session_state.mistake_index = 0
        index = 0
        
    mistake = mistakes[index]
    mistake_id = mistake[0]
    original = mistake[1]
    correct = mistake[2]
    explanation = mistake[3]
    
    components.html(f"""
    <style>
    .flashcard {{
        background: linear-gradient(135deg, #e0ddff, #f8f7ff);
        border: 1.5px solid #6C63FF;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        max-width: 480px;
        margin: auto;
        font-family: 'Nunito', sans-serif;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.12);
        transition: 0.2s ease;
    }}
    
    .flashcard:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(79, 70, 229, 0.18);
    }}
    
    .flashtitle-error {{
        color: #dc2626;
        font-weight: 800;
        font-size: 16px;
        margin-top: 4px;
    }}
    
    .flashtitle-correct {{
        color: #16a34a;
        font-weight: 800;
        font-size: 16px;
        margin-top: 10px;
    }}
    
    .flashtext {{
        font-size: 30px;
        font-weight: 800;
        margin: 4px 0 6px 0;
        direction: rtl;
        color: #111827;
    }}
    
    .flashexplanation {{
        direction: ltr;
        color: #6b7280;
        font-size: 20px;
        margin-top: 10px;
        line-height: 1.4;
    }}
    </style>
    
    <div class="flashcard">
        <div class="flashtitle-error">Mistake</div>
        <div class="flashtext">{original}</div>
    
        <div class="flashtitle-correct">Correct</div>
        <div class="flashtext">{correct}</div>
    
        <div class="flashexplanation">{explanation}</div>
    </div>
    """, height=240)
    
    col1, col2, col3 = st.columns([2,3,2])
    with col1:
        if st.button(" Previous", use_container_width=True):
            if index > 0:
                st.session_state.mistake_index -= 1
                st.rerun()
    with col2:
        if st.button("Mark as reviewed", type="primary", use_container_width=True):
            delete_user_mistake(mistake_id) 
            st.session_state.mistake_index = 0
            st.rerun()
    with col3:
        if st.button("Next ", use_container_width=True):
            if index < total - 1:
                st.session_state.mistake_index += 1
                st.rerun()
                
#Section 3: Practice modules
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:left; color:#000000;'> Practice Modules </h2>", unsafe_allow_html=True)
st.markdown(""" Choose a skill to practice your Modern Standard Arabic (Hint: begin your Arabic learning with vocablab)""")

def module_card(title, icon, descreption, page, key):
    with st.container():
        st.markdown(f"""
        <div class="modulecard">
            <div class="moduletitle">{icon} {title}</div>
            <div class="moduledesc">{descreption}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Practice {title}", key=key, type="primary"):
            st.switch_page(page)

col1, col2 = st.columns(2, gap="medium")
with col1:
    module_card("Vocabulary", "🧩", "Build and review your vocabulary", "pages/VocabLab.py", "vocab")
    module_card( "Reading", "📖", "Improve your reading and comprehension", "pages/StoryLab.py", "read" )
    module_card( "Conversation", "💬",  "Have conversation chats in Arabic and practice different scenarios", "pages/ConversationLab.py", "chat" )

with col2:
    module_card("Speaking", "🗣️", "Practice speaking Arabic, get instant feedbak and speaking accuracy score", "pages/SpeakingLab.py", "speak")
    module_card( "Writing", "✍️", "Practice writing and get instant corrections & feedback", "pages/WritingLab.py", "write" )

   