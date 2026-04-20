import streamlit as st
import random
from db_setup import require_login, init_db, get_learned_words, save_listening_attempt, get_connection
import os
import json
from openai import OpenAI
import re
client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))

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
        div.stButton > button {
            border: 1px solid #d1d5db;
            background-color: #ffffff;
            color: #374151;
            border-radius: 10px;
            padding: 6px 10px !important;
            font-weight: 500;}
            
        div.stButton > button:hover {
            border-color: #4f46e5;
            color: #4f46e5;
            background-color: #eef2ff;}
        
        div.stButton > button[kind="primary"] {
            background-color: #4f46e5;
            color: white;
            border: none;}

        div.stButton > button[kind="primary"]:hover {
            background-color: #4338ca; }

        div[role="radiogroup"] > label {
            font-size: 18px !important;
            font-weight: 600;}
            
        div[data-testid="stMetricValue"] {
            color: #4f46e5 !important; 
            font-weight: 700;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#3832aa;'>🎧 ListeningLab</h1>", unsafe_allow_html=True)
st.markdown("""Listen carefully and type the Arabic word you hear.""")


user_id, user_level = require_login()

if "started" not in st.session_state:
    st.session_state.started = False
    
def normalize_arabic(text):
    text = text.strip()
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    return text

def load_vocab_data():
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__)) 
        file_path = os.path.join(base_dir, "data/vocabulary_data.json")
        
        with open(file_path, "r", encoding="utf-8") as f:  
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("Error: File is not found ")
        return {}
    except Exception as e:
        st.error(f" Error in loading data: {str(e)}")
        return {}

def vocabaulary_lookup(user_id, user_level):
    vocab_lookup = {}
    vocab_data = load_vocab_data()
    for level in vocab_data.values():
        for category in level.values():
            for word in category:
                vocab_lookup[word["arabic"]] = word["english"]

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT sv.word_ar, sv.word_en
        FROM story_vocab sv
        JOIN stories us ON sv.story_id = us.id
        WHERE us.user_id = ?
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    for ar, en in rows:
        vocab_lookup[ar] = en

    return vocab_lookup


learned_words = get_learned_words(user_id, user_level)
vocab_list = [w["word_ar"] for w in learned_words] if learned_words else []

if len(vocab_list) == 0:
    st.warning("You need to learn some vocabulary first.")
    st.stop()

mode = st.radio("Choose Mode:",
    ["Word Dictation", "Sentence Dictation"], horizontal=True)

if not st.session_state.started:
    st.button("Start Practice Session", type="primary", on_click=lambda: st.session_state.update({"started": True}))
    st.stop()

if "dictation_items" not in st.session_state:
    selected_words = random.sample(vocab_list, min(4, len(vocab_list)))
    if mode == "Word Dictation":
        st.session_state.dictation_items = selected_words
    else: 
        items = []
        for word in selected_words:
            if user_level == "A1":
                max_words = 4
            elif user_level == "A2":
                max_words = 6
            else:
                max_words = 8
    
            prompt = f"""
            You are an expert Arabic language tutor creating listening exercises based on student level.

            Student level: {user_level}
            Target word: {word}

            Task:
            
            Create ONE simple Arabic sentence for listening practice and its English translation.

            STRICT RULES:
            
            1.The Arabic sentence must be in Modern Standard Arabic.
            2. The Arabic sentence must be grammatically correct 
            3. The English sentence must be a natural and correct translation.
            4. Maximum {max_words} words 
            5. The vocabulary word "{word}" must appear exactly in the Arabic sentence.
            6. English sentence must contain ONLY English words.
            7. English sentence must NOT contain any Arabic words.
            8. English must match the Arabic meaning EXACTLY.
            9. Do NOT add diacritics
            10. Keep it easy to understand when heard
            11. For A1/A2:
                    - Use very simple sentence structure
                    - Prefer short nominal or basic verb sentences
            13. For B1:
                    - Allow slightly more detail (time, place, simple connectors)

            LISTENING-SPECIFIC RULES (VERY IMPORTANT):
            - Avoid rare or difficult words
            - Avoid long or complex verb forms
            - Avoid ambiguous word order
            
            GOOD EXAMPLE:
            Arabic: انا ادرس في البيت اليوم
            English: I study at home today
            
            BAD EXAMPLE (DO NOT DO):
            Arabic: قد كنت ادرس في المنزل سابقا
            English: I had been studying at home previously

            Before returning the answer:
            - Arabic contains only Arabic letters
            - English contains only English letters
            - No diacritics in Arabic
            - Sentence is easy to understand when heard
            - Vocabulary word is included EXACTLY

            Return VALID JSON only:
            {{
            "arabic": "...",
            "english": "...",
            "vocab_used": "{word}"
            }}
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)
            items.append(data)

        st.session_state.dictation_items = items

    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.checked = False
    
if "vocab_lookup" not in st.session_state:
    st.session_state.vocab_lookup = vocabaulary_lookup(user_id, user_level)

idx = st.session_state.index
items = st.session_state.dictation_items

if idx <len(items):
    st.progress((idx + 1) / len(items))
    if mode == "Word Dictation":
        vocab_word = items[idx]
        st.markdown(f"### Word {idx+1} / {len(items)}")
        st.info("🔊 Listen and write the Arabic word")

        tts = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=vocab_word)
        st.audio(tts.read(), format="audio/mp3")

    else:
        exercise = items[idx]
        sentence = exercise["arabic"]
        vocab_word = exercise["vocab_used"]
        english_hint_sen = exercise["english"]
    
        st.markdown(f"### Sentence {idx+1} / {len(items)}")
        st.info("🔊 Listen and write the sentence")
    
        tts = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=sentence)
        st.audio(tts.read(), format="audio/mp3")

    if st.button("💡 English Hint"):
        if mode == "Word Dictation":
            vocab_map = st.session_state.vocab_lookup
            english_hint = vocab_map.get(vocab_word)
            if not english_hint:
                with st.spinner("Getting translation..."):
                    try:
                        prompt = f"""
                            Translate the following Arabic word to natural English.
                            Word: {vocab_word}
                            Return ONLY the English translation.
                            """
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=30,
                            temperature=0.3
                        )
                        english_hint = response.choices[0].message.content.strip()
                        st.session_state.vocab_lookup[vocab_word] = english_hint
                    except:
                        st.warning("Could not retrieve translation.")
        else:
            english_hint = english_hint_sen
        if english_hint:
            st.write(f"English: {english_hint}")

    user_answer = st.text_input("Write the Arabic word", key=f"input_{idx}")
    if not st.session_state.checked:
        if st.button("Check Answer"):
            user_clean = normalize_arabic(user_answer)
    
            if mode == "Word Dictation":
                correct_clean = normalize_arabic(vocab_word)
                is_correct = user_clean == correct_clean
            else:
                correct_clean = normalize_arabic(sentence)
                if user_clean == correct_clean:
                    is_correct = True
                else:
                    correct_words = correct_clean.split()
                    user_words = user_clean.split()
                    overlap = len(set(user_words) & set(correct_words))
                    similarity = overlap / len(correct_words)
                    is_correct = similarity > 0.85
            if is_correct:
                st.session_state.feedback = ("correct", correct_clean)
                st.session_state.score += 1
            else:
                st.session_state.feedback = ("incorrect", correct_clean)
                
            save_listening_attempt(
                user_id=user_id,
                vocab_word=vocab_word,
                user_answer=user_answer,
                is_correct=is_correct
            )
            st.session_state.checked = True
            st.rerun()

    else:
        status, correct_answer = st.session_state.feedback
    
        if status == "correct":
            st.success("Correct ✅")
        else:
            st.error(f"Incorrect ❌ Correct: {correct_answer}")
    
        if st.button("Next ➡️"):
            st.session_state.index += 1
            st.session_state.checked = False
            st.rerun()
                
else:
    st.success("Session Complete 🎉")
    st.metric("Score", f"{st.session_state.score} / {len(items)}")
    
    if st.button("Start New Session"):
        for key in ["dictation_items", "index", "score", "checked", "started"]:
            del st.session_state[key]
        st.rerun()