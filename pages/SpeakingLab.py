import streamlit as st
import random
from openai import OpenAI
import os
from db_setup import get_learned_words, save_speaking_attempt, get_user_mistakes
import difflib
import re
from deepgram import DeepgramClient
import io

if "dg_client" not in st.session_state:
    api_key = os.getenv("DeepGram_Capstone_Key")
    if not api_key:
        st.error("Missing Deepgram API key")
        st.stop()

    st.session_state.dg_client = DeepgramClient(api_key=api_key)

dg_client = st.session_state.dg_client

client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))

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
        div.stButton > button {
            border: 1px solid #d1d5db;
            background-color: #ffffff;
            color: #374151;
            border-radius: 10px;
            padding: 6px 10px !important;
            font-weight: 500;
            transition: all 0.2s ease;
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

        div[role="radiogroup"] > label {
            font-size: 18px !important;
            font-weight: 600;
        }
        .vocab-badge {
            background-color: #eef2ff;
            padding: 6px 12px;
            border-radius: 8px;
            font-weight: 600;
        }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#3832aa;'>🗣️ SpeakLab</h1>", unsafe_allow_html=True)

def normalize_arabic(text):
    text = text.strip()
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    
    # normalize letters
    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    return text
    
def extract_weak_vocab(mistakes):
    weak_words = []
    for m in mistakes:
        correct = normalize_arabic(m["correct_word"])
        # filter short junk like "في", "من"
        if len(correct.split()) <= 2:
            weak_words.append(correct)
    return list(set(weak_words))
    
def calculate_score(expected, actual, vocab_word, user_id=None):
    expected = normalize_arabic(expected)
    actual = normalize_arabic(actual)
    vocab_word = normalize_arabic(vocab_word)
    expected_words = expected.split()
    actual_words = actual.split()

    used_words = set()
    word_matches = []
    matched_positions = []

    # Word matching 
    for i, exp_word in enumerate(expected_words):
        best_similarity = 0
        best_index = -1
        for k, act_word in enumerate(actual_words):
            if k in used_words:
                continue
            similarity = difflib.SequenceMatcher(None, exp_word, act_word).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = k

        if best_similarity >= 0.85:
            used_words.add(best_index)
            word_matches.append((exp_word, True))
            matched_positions.append(best_index)
        else:
            word_matches.append((exp_word, False))

    # word accuracy
    word_score = sum(1 for _, m in word_matches if m) / len(expected_words)
    # Order 
    order_score = 1.0
    if len(matched_positions) > 1:
        correct_order = sum( 1 for i in range(len(matched_positions) - 1) if matched_positions[i] < matched_positions[i + 1] )
        order_score = correct_order / (len(matched_positions) - 1)
    score = (0.75 * word_score) + (0.25 * order_score)

    #  Extra words 
    extra_words = max(0, len(actual_words) - len(expected_words))
    score -= extra_words * 0.05
    # Vocab penalty
    vocab_in_transcript = any( difflib.SequenceMatcher(None, vocab_word, w).ratio() >= 0.75 for w in actual_words )
    if not vocab_in_transcript:
        score -= 0.25

    # 5. Memory-aware penalty
    try:
        if user_id:
            mistakes = get_user_mistakes(user_id)
            weak_words = [normalize_arabic(m[2]) for m in mistakes]
            missed_weak = [ w for w, matched in word_matches if not matched and normalize_arabic(w) in weak_words]
            if missed_weak:
                score -= 0.05 * len(missed_weak)  
    except:
        pass  

    score = max(0, min(score, 1))
    return score, expected_words, actual_words, word_matches

def pronunciation_issues(expected_words, actual_words):
    problematic_letters = {}
    for exp_word in expected_words:
        best_similarity = 0
        best_match = ""
        for act_word in actual_words:
            similarity = difflib.SequenceMatcher(None, exp_word, act_word).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = act_word

        # weak similarity
        if best_similarity < 0.85 and best_match:
            diff = difflib.ndiff(exp_word, best_match)
            for d in diff:
                # missing from speech
                if d.startswith("- "):  
                    letter = d[-1]
                    problematic_letters[letter] = problematic_letters.get(letter, 0) + 1
    return problematic_letters

def highlight_sentence(word_matches):
    highlighted = []
    for word, matched in word_matches:
        if matched:
            highlighted.append(f"<span style='color:#16a34a; font-weight:600'>{word}</span>" )
        else:
            highlighted.append(f"<span style='color:#dc2626; font-weight:600'>{word}</span>")
    return " ".join(highlighted)

def sound_map(problematic_letters):
    sound_map = {"س": "س (soft s sound)", "ش": "ش (sh sound)", "ق": "ق (deep q sound)", "ر": "ر (rolling r)",  "ح": "ح (breathy h)",
        "خ": "خ (kh sound)", "ع": "ع (deep throat sound)", "غ": "غ (gh sound)",  "ص": "ص (heavy s sound)", "ض": "ض (emphatic d sound)",
        "ط": "ط (heavy t sound)"}
    detect = []
    for letter, count in problematic_letters.items():
        if letter in sound_map and count >= 1:
            detect.append(sound_map[letter])
    return detect

if "user" not in st.session_state or "level" not in st.session_state.user:
    st.warning("Please login first")
    st.stop()

user_id = st.session_state.user["id"]
user_level = st.session_state.user["level"]

# 1- speaking session when word from flashcards if coming from there
target_word = st.session_state.get("speaking_target_word", None)
st.markdown(""" Practice speaking Arabic out loud with short exercises. Read each word or sentence, say it clearly, and get instant feedback on your pronunciation. Focus on being clear, not perfect. """)

if st.button(" Start Speaking ", type="primary"):
    if target_word:
        selected_words = [target_word]
        is_from_flashcard = True
    else:
        # Standalone not from flashcard
        learned_words = get_learned_words(user_id, user_level)
        if not learned_words:
            st.warning(" You have not learned any vocabulary words, start learning words from the vocabulary lab ")
            st.stop()
        
        vocab_list = [row[0] for row in learned_words]
        selected_words = random.sample(vocab_list, min(4, len(vocab_list)))
        is_from_flashcard = False

    exercises = []
    with st.spinner(" Generating sentences ..."):
        for word in selected_words:
            if is_from_flashcard:
                exercises.append({"word": word, "sentence": word})
            else:
                prompt = f"""
                You are an expert Arabic (MSA) Language tutor, creating arabic sentence for students to practice speaking.
                
                student level:
                {user_level}
    
                Target vocabulary word that MUST be used: {word}

                Create ONE short, natural Arabic sentence (Modern Standard Arabic) that must include the word: {word}.
                
                Rules:
                - Generate one short Arabic sentence in Modern Standard Arabic (MSA)
                - Arabic sentence should be grammatically correct and accurate
                - Arabic sentence should include the exact word: "{word}".
                - If student level is A1, Arabic sentence must include 4 words only
                - If student level is A2, Arabic sentence must include 6 words only
                - If student level is B1, Arabic sentence must include 7-8 words only
                - Use natural beginner expressions for student level A1/A2 and intermediate expressions for student level B1
            
                Before returning the sentence:
                -Verify the sentence is in Arabic
                -Verify the {word} is included in the generated Arabic sentence
                -Verify the Arabic sentence structure is suitable for the student level
                
                Return ONLY the Arabic sentence, nothing else.
            
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=80,
                    temperature=0.3
                )
                sentence = response.choices[0].message.content.strip()
                exercises.append({"word": word, "sentence": sentence})
                
    st.session_state.speaking_exercises = exercises
    st.session_state.speaking_index = 0
    st.rerun()

#ecercises display
if "speaking_exercises" in st.session_state and st.session_state.speaking_exercises:
    idx = st.session_state.speaking_index
    exercises = st.session_state.speaking_exercises
    if idx < len(exercises):
        exercise = exercises[idx]
        sentence = exercise["sentence"]
        vocab_word = exercise["word"]
        
        st.progress((idx + 1) / len(exercises))
        st.markdown(f"""### Exercise {idx+1} / {len(exercises)}""")
        st.markdown(f"""<span class="vocab-badge">Vocabulary target word: {vocab_word}</span> """, unsafe_allow_html=True)
        st.markdown(f"""
            <div style="
                background: #f8fafc;
                padding: 30px;
                border-radius: 16px;
                text-align: center;
                font-size: 34px;
                font-weight: 600;
                direction: rtl;
                line-height: 1.8;
                border: 1px solid #e2e8f0;
                margin: 25px 0;
            ">
                {sentence}
            </div>
            """, unsafe_allow_html=True)
        
        st.info("💡 Tip: Speak slowly and clearly for best results")
        audio_data = st.audio_input("🎤 Tap the mic and speak clearly  ", key=f"speaking_input_{idx}")
        if audio_data is not None:
            with st.spinner(" Analyzing your voice ..."):
                try:
                    if hasattr(audio_data, "getvalue"):
                        buffer_data = audio_data.getvalue()
                    else:
                        buffer_data = audio_data.read()

                    response = dg_client.listen.v1.media.transcribe_file(
                        request=buffer_data,         
                        model="nova-3",               
                        language="ar",                
                        smart_format=True,
                        punctuate=True,
                        detect_language=False,
                    )
                    
                    transcript = response.results.channels[0].alternatives[0].transcript.strip()
        
                    hallucinations = [ "اشتركوا في القناة", "subscribe", "like", "thank you"]
                    if any(h in transcript.lower() for h in hallucinations) or len(transcript.strip()) < 2:
                        transcript = ""
                        st.warning(" Error in recognizing your voice, please try to spekai again with clarity.")
                    if not transcript:
                        st.stop()

                    score, expected_words, actual_words, word_matches = calculate_score(sentence, transcript, vocab_word, user_id)
                    problemletters = pronunciation_issues(expected_words, actual_words)
                    sound_feedback = sound_map(problemletters)

                    missed_words = [w for w, m in word_matches if not m]                    
                    percentage = int(score * 100)
                    
                    save_speaking_attempt(
                        user_id=user_id,
                        vocab_word=vocab_word,
                        sentence=sentence,
                        transcript=transcript,
                        score=score)
                    
                    highlighted_sentence = highlight_sentence(word_matches)
                    st.markdown(f"### 🎤︎︎ Speaking Accuracy ")
                    st.markdown(f"""
                        <div style="text-align:left; font-size:28px; font-weight:800; color:#4f46e5;">
                            {percentage}%
                        </div>
                        """, unsafe_allow_html=True)
     
                    st.markdown("### 🎤︎︎ Your Pronounciation")
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
                            <div style="font-size:18px; color:#401607;"> Expected Sentence: </div>
                            <div style="font-size:22px; font-weight:600;">{sentence}</div>
                        </div>
                    
                        <hr style="border:none; border-top:1px solid #fcd34d; margin:10px 0;">
                    
                        <div>
                            <div style="font-size:18px; color:#401607;"> What you said: </div>
                            <div style="font-size:20px; font-weight:600; color:#065f46;">
                                {highlighted_sentence}
                            </div>
                        </div>
                    
                        </div>
                        """,
                        unsafe_allow_html=True)
                    
                    st.markdown("""
                        <div style="font-size:13px; color:#64748b;">
                        <span style="color:#16a34a;">● Correct</span> &nbsp;&nbsp;
                        <span style="color:#dc2626;">● Needs improvement</span>
                        </div>
                        """, unsafe_allow_html=True)

                    if score >= 0.85:
                        st.success("Your pronounciation was great, continue speaking confidentially 🔥")
                    elif score >= 0.6:
                        st.info("Good job, try to speak again better and more confident👍")
                    else:
                        st.warning("❌ incorrect pronounciation, listen again and try to pronounce it better")

                    if sound_feedback:
                        st.markdown("### 🎤︎ Pronunciation Tips")
                        st.warning( "Focus on these sounds:\n\n" + " • " + "\n • ".join(sound_feedback))
                    if missed_words:
                        st.caption(f"Focus on: {' , '.join(missed_words)}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔊 Hear it again"):
                            try:
                                tts = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=sentence)
                                with open("correct.mp3", "wb") as f:
                                    tts.stream_to_file(f.name)
                                st.audio("correct.mp3", autoplay=True)
                                os.remove("correct.mp3")
                            except:
                                st.error("Error in audio ")
                    
                    with col2:
                        if st.button(" ➡️ Next"):
                            st.session_state.speaking_index += 1
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"Error in analyzing your voice : {str(e)}")
    else:
        st.success("🎉 Session is completed !")
        if st.button(" Start new session "):
            for key in ["speaking_exercises", "speaking_index"]:
                st.session_state.pop(key, None)
            st.rerun()