import streamlit as st
import random
from db_setup import require_login, init_db, get_learned_words, save_writing_attempt, save_user_mistake, get_user_mistakes
from openai import OpenAI
import json
import re
import os
from sentence_transformers import SentenceTransformer, util
import difflib
from googleapiclient.discovery import build

client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))
youtube = build("youtube", "v3", developerKey=os.getenv('Youtube_API_Key'))

init_db()
@st.cache_resource
def load_embedding_model():
    try:
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        st.error(f"Embedding model failed to load: {str(e)}")
        return None

model = load_embedding_model()

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
        .word-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;}
            
        .word-container button {
            padding: 6px 12px !important;
            font-size: 14px !important;
            border-radius: 8px !important;
            width: auto !important; }
            
        .exercise-card {
            padding: 15px;
            border-radius: 12px; 
            background-color: #eef2ff;
            border: 1px solid #e6e6e6;
            margin-bottom: 15px;}

        .arabic-text {
            font-size: 22px;
            font-weight: 600;
            direction: rtl;}
            
        .english-text {
            font-size: 20px;}

        .vocab-badge {
            background-color: #eef2ff;
            padding: 6px 12px;
            border-radius: 8px;
            font-weight: 600;
        }

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

st.markdown("<h1 style='text-align:center; color:#3832aa;'>💡 WritingLab</h1>", unsafe_allow_html=True)
st.markdown(""" Write freely or follow guided exercises to improve your Arabic writing skills – see your mistakes and progress instantly. """)

def normalize_arabic(text):
    text = text.strip()
    
    #text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())

    return text

# this function id for the leyr 3 grading (Linguistic intelligence AI based evaluation)
def grade_translation(user_answer, correct_answer):

    prompt = f"""
        You are an Arabic teacher grading a student's translation.
        
        Correct sentence:
        {correct_answer}
        
        Student sentence:
        {user_answer}
        
        Evaluate STRICTLY.
        
        Accept the answer ONLY if:
        - The meaning is the same
        - Grammar is correct
        - Sentence is natural Arabic in MSA
        - The main vocabulary word is included in the student answer
        
        Reject if:
        - Grammar is incorrect
        - Word order makes sentence unnatural
        - Key meaning changed
        - Important words missing
        
        Return VALID JSON only 
        Do NOT include any explanation or extra text.
        outout SHOULD be: 
        
        {{
        "is_correct": true or false,
        "feedback": "short explanation of ALL mistakes in student sentence"
        }}
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=80,
        temperature=0,
         response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return result["is_correct"], result["feedback"]

# check if vocab has been used or not (this is important because of teh practice and reinforcement learning i have implemented for my project idea)
def is_vocab_used(vocab_word, user_text):
    vocab_clean = normalize_arabic(vocab_word)
    user_clean = normalize_arabic(user_text)
    if vocab_clean in user_clean:
        return True 
    similarity = difflib.SequenceMatcher(None, vocab_clean, user_clean).ratio()
    if similarity >= 0.6:
        return True
    return False


def extract_weak_vocab(mistakes):
    weak_words = []
    for m in mistakes:
        correct = normalize_arabic(m["correct_word"])
        if len(correct.split()) <= 2:
            weak_words.append(correct)
    return list(set(weak_words))
    
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

        
#if "user" not in st.session_state:
    #st.warning("Please login first.")
    #st.stop()

#user_id = st.session_state.user["id"]
#user_level = st.session_state.user["level"]
user_id, user_level = require_login()


learned_words = get_learned_words(user_id, user_level)
vocab_list = [w["word_ar"] for w in learned_words] if learned_words else []

tab1, tab2 = st.tabs(["🧩 Guided Writing", "✍️ Free Writing"])

with tab1:

    st.subheader("Guided Writing")
    mode = st.radio(
        "Choose Practice Mode:",
        ["Sentence Translation", "Word Ordering"], horizontal=True )

    if st.button("Start Practice Session", type="primary"):

        if len(vocab_list) == 0:
            st.warning("You need to learn some vocabulary first.")
            st.stop()
        # memory - aware --> instrutor asked to add this
        mistakes = get_user_mistakes(user_id)
        weak_vocab = extract_weak_vocab(mistakes)
        priority_words = weak_vocab[:2]
        remaining_words = 5 - len(priority_words)  
        
        other_words = [w for w in vocab_list if normalize_arabic(w) not in weak_vocab]
        if len(other_words) > 0:
            random_words = random.sample(other_words, min(remaining_words, len(other_words)))
        else:
            random_words = []
            
        selected_words = priority_words + random_words
        exercises = []

    #simple difficulty adaptivity
        if user_level == "A1":
            max_words = 4
            structure_hint = "Use a very simple sentence (2–4 words). You can use a basic nominal sentence (e.g., أنا طالب) or a simple verb sentence or simple descriptions with basic adjectives."

        elif user_level == "A2":
            max_words = 6
            structure_hint = "Use a simple complete sentence. You may add time or place or basic connectors or adjectives (e.g., اليوم، في البيت)."

        else:  # B1+
            max_words = 8
            structure_hint = "Use a natural sentence with more detail, such as adjectives, time expressions, or reasons."
        

        with st.spinner("Generating exercises..."):

            for word in selected_words:

                prompt = f"""
            You are an expert Arabic language tutor creating writing exercises based on student level.
            
            Student level based on CEFR level: {user_level}
            
            Vocabulary word that MUST appear in the Arabic sentence:
            {word}
            
            TASK:
            Create ONE very simple Arabic sentence and its English translation.
            
            STRICT RULES:
            
            1. The Arabic sentence must be in Modern Standard Arabic.
            2. The Arabic sentence must be grammatically correct 
            3. The English sentence must be a natural and correct translation.
            4. Maximum {max_words} words 
            5. The vocabulary word "{word}" must appear exactly in the Arabic sentence.
            6. English sentence must contain ONLY English words.
            7. English sentence must NOT contain any Arabic words.
            8. English must match the Arabic meaning EXACTLY.
            9. Use natural beginner expressions for student level A1/A2 and intermediate expressions for student level B1
            10. if student level is A1 or A2 use simple sentence structure.
            11. Do NOT include Arabic diacritics (تشكيل).
            12. Prefer natural time expressions like:
               يوم الاثنين
               يوم الثلاثاء
               يوم الاربعاء
            13. IMPORTANT: Keep vocabulary simple and common , Do NOT generate complex grammar


            Sentence Structure Guidance Rules:
              - sentence should MUST follow the structure: {structure_hint}
            
            GOOD EXAMPLE:
            Arabic: انا اذهب الى المدرسة يوم الاربعاء
            English: I go to school on Wednesday
            
            BAD EXAMPLE (DO NOT DO):
            Arabic: اذهب الى المدرسة في الاربعاء
            
            Before returning the answer:
            - Verify English contains only English letters
            - Verify Arabic contains only Arabic
            - Verify the English meaning matches the Arabic exactly.
            - Verify the sentence contains NO diacritics.
            
            
            Return JSON only:
            
            {{
            "english": "...",
            "arabic": "...",
            "vocab_used": "{word}"
            }}
            """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=120,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )

                sentence_data = json.loads(response.choices[0].message.content)

                exercises.append(sentence_data)

        st.session_state.exercises = exercises
        st.session_state.exercise_index = 0
        st.session_state.score = 0
        st.session_state.checked = False

    if "exercises" in st.session_state:
        idx = st.session_state.exercise_index
        exercises = st.session_state.exercises

        if idx < len(exercises):
            exercise = exercises[idx]

            english_sentence = exercise["english"]
            arabic_sentence = exercise["arabic"]
            vocab_word = exercise["vocab_used"]
            
            vocab_data = load_vocab_data()
            arabic_to_english = {}
            for level in vocab_data.values():
                for category in level.values():
                    for word in category:
                        arabic_to_english[word["arabic"]] = word["english"]

            st.progress((idx + 1) / len(exercises))
            st.markdown(f"""### Exercise {idx+1} / {len(exercises)}""")
            st.divider()
            # Sentence Translation
            if mode == "Sentence Translation":
                st.markdown("Translate this sentence to Arabic")
                st.markdown(f"""<div class="exercise-card">
                                <div class="english-text">{english_sentence}</div>
                                </div>
                                """, unsafe_allow_html=True)
            
                user_answer = st.text_input("Your Answer",placeholder="Type the Arabic sentence ...", key=f"translation_input_{idx}")
                user_clean = normalize_arabic(user_answer)
                correct_clean = normalize_arabic(arabic_sentence)
            
                if not st.session_state.checked:
            
                    if st.button("Check Answer"):
                        is_correct = False
                        feedback_text = ""
                        
                        if not user_answer.strip():
                            st.warning("Please write your translation first.")
                            st.stop()
            
                        # Layer 1 --> if user write the exact match 
                        if user_clean == correct_clean:
                            is_correct = True
                            feedback_text = ""
            
                        else:
                            # Layer 2 ---> check if vocab word is written + similarity of teh user words with the correct words
                            correct_words = correct_clean.split()
                            user_words = user_clean.split()
            
                            vocab_present = is_vocab_used(vocab_word, user_answer)
    
                            if model is not None:
                                emb1 = model.encode(correct_clean, convert_to_tensor=True)
                                emb2 = model.encode(user_clean, convert_to_tensor=True)
                                similarity = util.cos_sim(emb1, emb2).item()
                            else:
                                similarity = 0

                            if similarity > 0.85:
                                is_correct = True
                                if not vocab_present:
                                    feedback_text = f"Correct, but try to include: {vocab_word}"
                                else:
                                    feedback_text = ""
                            elif similarity < 0.5:
                                is_correct = False
                                feedback_text = "Your sentence is too different from the expected answer."

# Layer 3 → AI check
                            else:
                                is_correct, feedback_text = grade_translation(user_answer, arabic_sentence)
    # still encourage vocab since this project idea is to reinforce learning vocab through other modulesafter AI check
                                if is_correct and not vocab_present:
                                    feedback_text += f" (Try to include: {vocab_word})"
                        if is_correct:
                            st.session_state.feedback = ("correct", arabic_sentence, feedback_text)
                            st.session_state.score += 1
                        else:
                            st.session_state.feedback = ("incorrect", arabic_sentence, feedback_text)
            
                        save_writing_attempt(
                            user_id=user_id,
                            vocab_word=vocab_word,
                            sentence_en=english_sentence,
                            correct_sentence=arabic_sentence,
                            user_answer=user_answer,
                            is_correct=is_correct
                        )
            
                        st.session_state.checked = True
                        st.rerun()
            
                else:
                    status, correct_sentence, feedback_text = st.session_state.feedback
                    if status == "correct":
                        st.success("Correct! ✅")
                    else:
                        st.error(f"Not quite right ❌ , Correct answer: {correct_sentence}")
                        if feedback_text:
                            st.caption(feedback_text)
            
                    if st.button("Next Exercise ➡️"):
                        st.session_state.exercise_index += 1
                        st.session_state.checked = False
                        st.rerun()
            #word ordering
            if mode == "Word Ordering":
            
                clean_sentence = normalize_arabic(arabic_sentence)
                words = clean_sentence.split()
            
                scramble_key = f"scramble_{idx}"
                selected_key = f"selected_{idx}"
            
                if scramble_key not in st.session_state:
                    scrambled = words.copy()
                    random.shuffle(scrambled)
                    st.session_state[scramble_key] = scrambled

                if selected_key not in st.session_state:
                    st.session_state[selected_key] = []
            
                scrambled_words = st.session_state[scramble_key]
                selected_words = st.session_state[selected_key]
                st.markdown("Tap words to build the sentence:")
                rows = [scrambled_words[i:i+4] for i in range(0, len(scrambled_words), 4)]

                for row in rows:  # this is me trying to make the button close to each other , its not working this is the best i could
                    left, *cols, right = st.columns([1] + [2]*len(row) + [1])
                    for i, word in enumerate(row):
                        with cols[i]:
                            if st.button(word, key=f"{idx}_{word}_{i}"):
                                selected_words.append(word)
                                st.session_state[selected_key] = selected_words
                                st.rerun()
                constructed_sentence = " ".join(selected_words)
            
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="arabic-text">
                        {constructed_sentence if constructed_sentence else "—"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2, _ = st.columns([1,1,6])
                with col1:
                    if st.button("Undo"):
                        if selected_words:
                            selected_words.pop()
                            st.session_state[selected_key] = selected_words
                            st.rerun()
                with col2:
                    if st.button("Clear"):
                        st.session_state[selected_key] = []
                        st.rerun()

                user_answer = " ".join(st.session_state[selected_key])
                if not st.session_state.checked:
                    if st.button("Check Answer"):
                        if not user_answer.strip():
                            st.warning("Build the sentence first.")
                            st.stop()
                                
                        user_clean = normalize_arabic(user_answer)
                        correct_clean = normalize_arabic(arabic_sentence)

                        if user_clean == correct_clean:
                            is_correct = True
                            feedback_text = ""

                        else:
                            correct_words = correct_clean.split()
                            user_words = user_clean.split()
                            vocab_present = vocab_word in user_clean
                            word_overlap = len(set(user_words) & set(correct_words))
                            similarity = word_overlap / max(len(correct_words), 1)
                    
                            if vocab_present and similarity >= 0.7:
                                is_correct = True
                                feedback_text = ""

                            else:
                                is_correct, feedback_text = grade_translation(user_answer, arabic_sentence)

                        if is_correct:
                            st.session_state.feedback = ("correct", arabic_sentence, feedback_text)
                            st.session_state.score += 1
                        else:
                            st.session_state.feedback = ("incorrect", arabic_sentence, feedback_text)
    
                        save_writing_attempt(
                            user_id=user_id,
                            vocab_word=vocab_word,
                            sentence_en=english_sentence,
                            correct_sentence=arabic_sentence,
                            user_answer=user_answer,
                            is_correct=is_correct
                        )
                
                        st.session_state.checked = True
                        st.rerun()
            
                else:
                    status, correct_sentence, feedback_text = st.session_state.feedback
                    if status == "correct":
                        st.success("Correct! ✅")
                    else:
                        st.error(f"Not quite right ❌ , Correct answer: {correct_sentence}")
                        if feedback_text:
                            st.caption(feedback_text)
            
                    if st.button("Next Exercise ➡️"):
                        if scramble_key in st.session_state:
                            del st.session_state[scramble_key]
                        if selected_key in st.session_state:
                            del st.session_state[selected_key]
            
                        st.session_state.exercise_index += 1
                        st.session_state.checked = False
                        st.rerun()
        else:
            st.success("Practice Session Complete ")

            score = st.session_state.score
            total = len(st.session_state.exercises)
            st.metric("Your Score", f"{score} / {total}")
            if st.button("Start New Session"):
                del st.session_state.exercises
                del st.session_state.exercise_index
                del st.session_state.score
                st.rerun()

                
with tab2:
    st.subheader("Free Writing")
    topic = st.selectbox(
        "Choose a topic",
        ["My Day", "My Family", "My Hobby", "My Weekend"] )
    
    st.info(f"Write a short paragraph about: {topic}")

    user_text = st.text_area(
        "Write your paragraph here",
        height=200
    )

    if st.button("Check my writing ✨"):
        if not user_text:
            st.warning("Please write something first.")
            st.stop()

        # added the memory aware instructor wanted
        mistakes = get_user_mistakes(user_id)
        weak_vocab = extract_weak_vocab(mistakes)
        focus_hint = ""
        if weak_vocab:
            focus_hint = f"Pay special attention to these words the student struggles with: {', '.join(weak_vocab[:3])}"
        prompt = f"""
        You are a professional Arabic language tutor (Modern Standard Arabic).
        
        Student level: {user_level}
        Topic: {topic}

        {focus_hint}
        
        Student paragraph:
        {user_text}
        
        Your task is to carefully analyze the paragraph and correct ALL types of mistakes.
        
        Important Correction Rules:
        
        1. Fix ALL grammar mistakes, such as (examples):
               - verb conjugation
               - subject-verb agreement
               - gender agreement
               - sentence structure
               - plural/singular
               - sentence order
               - difinite article misuse
               
        2. Fix ALL spelling mistakes.
        
        3. Fix incorrect word usage, and if meaning is wrong then correct the sentence.
        
        4. Fix Tense mistakes BUT ensure to:
           - Keep present tense if the paragraph describes routines, habits, or general actions.
           - Keep past tense if the paragraph clearly describes completed events in the past.
           - Keep future tense if the paragraph describes planned or expected actions (e.g., using سوف / سـ).
           - Do NOT change tense if it is already correct and consistent with the context.
           - If multiple tenses are used incorrectly in the same paragraph, correct them to be consistent ONLY if the context clearly requires one               timeline.
           
        5. Fix prepositions and particles (مثل: إلى، في، على، بعد).
        
        6. Do NOT add tashkeel (diacritics) unless necessary for the word.
        
        7. Hamza Rule:
             - Do NOT add Hamza if the word is correct
             - ONLY fix Hamza if it creates a spelling mistake
             - Correct hamza only in cases like:
                الى → إلى  
                ان → أن  
                انا → أنا 
    
        8. Apply MINIMAL correction:
               - Only change what is necessary to make the sentence correct.
               - Do NOT improve style, formality, or add optional grammar.
               - Do NOT add optional elements like tanween if the sentence is already correct.
               
        9. If the paragraph is very short, still provide correction and feedback.
        
        10. Remove unnecessary repeated pronouns if verb already shows the subject.
        
        11.Do NOT invent mistakes if the sentence is correct

        12. Only include words/phrases that were changed.
                - Each mistake entry must include the FULL original span and corrected span.
                - Do NOT include unchanged text.

        13. Do NOT add tanween (ً ٍ ٌ) if the word is correct in meaning, unless it creates a mistake.
                - Prefer writing without tanween in normal sentences.

    -----------------------------------------------------------------

       Correction Style:
       
        1. Keep corrections suitable for the student level {user_level}.
        2. Do NOT invent mistakes if the sentence is correct.
        3. Maintain the original meaning  
        4. Each mistake must represent ONE logical correction.
            - Combine correction only if they affect the same word/phrase.
            - Separate correction if they affect different parts of the sentence.
        5. Do NOT add corrections for words that are not changed.
        
    -----------------------------------------------------------------

       Explanation Rules:
       
       1. Explanations should be very short and in simple English
       2. Each mistake MUST include explanations for ALL corrections made.
       15. The explanation MUST exactly match the correction made.
            - Do NOT mention rules that were not applied.
            - Example: Do NOT say "definite article needed" if "ال" was not added.
       3- If multiple issues exist in the same word or phrase, combine them in one short explanation using "+".
       4. Prefer using simple standard phrases such as:
           - verb must match subject
           - pronoun unnecessary
           - spelling mistake
           - hamza missing
           - definite article needed
           - wrong tense
           - incorrect word usage

       5. If none of the standard phrases fit, create a SHORT custom explanation that EXACTLY describes the mistake.
       6. Do NOT include explanations for words that are correct and did not change.
       7. If the error involves Hamza, ALWAYS use: "hamza missing" or "hamza incorrect" , Do NOT label Hamza errors as "spelling mistake" or "definite article needed" .
       8.  If the mistake depends on context (such as subject, tense, or sentence meaning):
               - Include a SHORT context hint inside parentheses.
               - Example: "verb must match subject (أنا → أذهب)"
               - Keep it minimal (2–4 words only), do NOT include full sentences.
       
    -----------------------------------------------------------------

       Feedback Rules:

       1. Feedback must be SPECIFIC to the student's mistakes.
       2. avoid generic feedback like "Good job".
         Provide short feedback:
            grammar → short evaluation  
            clarity → short evaluation  
            vocabulary → short evaluation  
            suggestion → one simple improvement suggestion

    -----------------------------------------------------------------

        Output Rules:
        
        1. Ensure the output is strictly valid JSON with no extra text or markdown before or after.
        2. If there are NO mistakes, return: "mistakes": []
        
        Return ONLY valid JSON and it SHOULD be in this format:

        {{
        "original": "...",
        "corrected": "...",
        "mistakes": [
            {{
                "original": "...",
                "correction": "...",
                "explanation": "..."
            }}
        ],
        "feedback": {{
            "grammar": "...",
            "clarity": "...",
            "vocabulary": "...",
            "suggestion": "..."
        }}
        }}
        
        """

        with st.spinner("Checking your writing..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )

                raw_output = response.choices[0].message.content
                data = json.loads(raw_output)
            except Exception as e:
                st.error("Error processing writing. Try again.")
                st.code(raw_output)
                st.stop()

        st.divider()
        st.markdown("### 📝 Writing Check ")

        st.markdown(
            f"""
            <div dir="rtl" style="
                background:#FFF7ED;
                padding:18px;
                border-radius:14px;
                border:1px solid #fde68a;
                margin-bottom:20px;
                text-align:center;
            ">
        
            <div style="margin-bottom:12px;">
                <div style="font-size:16px; color:#9a3412;">النص الأصلي</div>
                <div style="font-size:18px; font-weight:600;">{data["original"]}</div>
            </div>
        
            <hr style="border:none; border-top:1px solid #fcd34d; margin:10px 0;">
        
            <div>
                <div style="font-size:16px; color:#065f46;">النص المصحح</div>
                <div style="font-size:18px; font-weight:600; color:#065f46;">
                    {data["corrected"]}
                </div>
            </div>
        
            </div>
            """,
            unsafe_allow_html=True)
        st.markdown("### 📝 Detailed Mistake Analysis")
        if data["mistakes"]: 
            for m in data["mistakes"]:
                save_user_mistake(
                    user_id=user_id,
                    original=m["original"],
                    correct=m["correction"],
                    explanation=m["explanation"],
                    module="free_writing"
                )
                

                st.markdown(
                    f"""
                    <div dir="rtl" style="
                        background:#EEF2FF;
                        padding:14px;
                        border-radius:12px;
                        margin-bottom:12px;
                        border:1px solid #c7d2fe;
                        text-align: center;
                    ">
                    <div style="margin-bottom:6px;">
                        <span style="color:#b91c1c; font-weight:600;">الخطأ:</span>
                        <span style="font-size:18px;">{m["original"]}</span>
                    </div>
                    <div style="margin-bottom:6px;">
                        <span style="color:#065f46; font-weight:600;">التصحيح:</span>
                        <span style="font-size:18px;">{m["correction"]}</span>
                    </div>
                    <div>
                        <span style="color:#1e3a8a; font-weight:600;">الشرح:</span>
                        <div dir="ltr" style="text-align:center; margin-top:4px; font-size:16px; color:#374151;">
                            {m["explanation"]}
                        </div>
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True)
                
            all_explanations = " ".join([m["explanation"] for m in data["mistakes"]])
            learning_prompt = f"""
                You are an Arabic language teaching assistant.
                
                Student level: {user_level}
                
                Analyze these grammar mistake explanations:
                
                {all_explanations}

                CRITICAL RULES:
                - You MUST ONLY generate topics about MODERN STANDARD ARABIC (MSA)
                - You MUST NOT include any other language (French, English grammar, etc.)
                - You MUST NOT output general language learning
                - You MUST NOT include examples from other languages
                - Output must be ONLY about Arabic grammar
                
                TASK:
                1. Identify the MAIN grammar weakness
                2. Convert it into a SHORT learning topic for YouTube search 
                3. Make it suitable for CEFR level {user_level}
                4. Keep it under 8 words
                5. Return ONLY the learning topic NOTHING else

               VALID OUTPUT EXAMPLES: 
                - Arabic verb conjugation present tense 
                - Arabic sentence structure basics 
                - Arabic hamza rules beginner

                INVALID OUTPUT (DO NOT PRODUCE):
                - French verbs
                - English grammar
                - General linguistics
                """
            learning_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": learning_prompt}],
                    temperature=0.0,
                    max_tokens=50
                )

            learning_topic = learning_response.choices[0].message.content.strip()
            


            #query_prompt = f"""
            #Turn this into a YouTube search query:
            
            #Topic: {learning_topic}
            #Level: {user_level}
            
            #Rules:
            #- max 10 words
            #- must be searchable
            #- include "Arabic grammar" if possible
            
            #Return ONLY the query NOTHING else.
            #"""
            
            #query_response = client.chat.completions.create(
                #model="gpt-4o-mini",
                #messages=[{"role": "user", "content": query_prompt}],
                #temperature=0.0,
                #max_tokens=50
            #)
            #search_query = query_response.choices[0].message.content.strip()

            search_query = f"Arabic grammar {learning_topic} {user_level}"

            st.info(f"Learning topic: {learning_topic}")
            request = youtube.search().list(
                    q=search_query,
                    part="snippet",
                    maxResults=3,
                    type="video"
                )

            response = request.execute()
            
            st.markdown("### 🎬 Recommended Learning Videos")
            for item in response["items"]:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
            
                st.video(f"https://www.youtube.com/watch?v={video_id}", width=500)
        else:
            st.success("No mistakes found. Great writing! 🎉")

        st.markdown("### 📝 Writing Feedback")

        feedback = data["feedback"]
        col1, col2, col3, col4 = st.columns(4)
        def show_feedback(title, value):
            return f"""
            <div style="
                padding:15px;
                border-radius:12px;
                border:1px solid #fde68a;
                background-color:#FFF7ED;
                color:black;
                text-align:center;
                font-weight:500;
                min-height:100px;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <div style="font-size:16px; opacity:0.8;">{title}</div>
                <div style="font-size:16px; margin-top:8px;">{value}</div>
            </div>
            """
        
        with col1:
            st.markdown(show_feedback("Grammar", feedback["grammar"]), unsafe_allow_html=True)
        
        with col2:
            st.markdown(show_feedback("Writing Clarity", feedback["clarity"]), unsafe_allow_html=True)
        
        with col3:
            st.markdown(show_feedback("Vocabulary", feedback["vocabulary"]), unsafe_allow_html=True)
        
        with col4:
            st.markdown(show_feedback("Suggestion", feedback["suggestion"]), unsafe_allow_html=True)




