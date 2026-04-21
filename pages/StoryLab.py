import streamlit as st
from openai import OpenAI
import os
import re
import json
from db_setup import mark_word_learned, save_story, get_user_stories, mark_story_as_read, save_quiz_score, get_read_stories_count, init_db, save_vocab, get_story_vocab, get_learned_words
from datetime import datetime
import streamlit.components.v1 as components

init_db()



client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))

if "view" not in st.session_state:
    st.session_state.view = "create"

def display_full_story(title, story_text, user_level):
    st.markdown(f'<div class="story-title">{title}</div>', unsafe_allow_html=True)
    sentences = re.split(r'(?<=[.؟!])\s+', story_text.strip())
    unique_words = set()
    for sentence in sentences:
            words = re.findall(r'\S+', sentence)
            for w in words:
                clean_w = re.sub(r'[^\w\s]', '', w)
                if clean_w and f"trans_{clean_w}" not in st.session_state:
                    unique_words.add(clean_w)
    if unique_words:
        with st.spinner(" ✨ Creating your story ..."):
            for clean_w in unique_words:
                if f"trans_{clean_w}" not in st.session_state:
                    try:
                        trans_prompt = f"Translate the Arabic word '{clean_w}' to natural English. Return only the translation, no extra text."
                        resp = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": trans_prompt}],
                                max_tokens=20,
                                temperature=0.3
                            )
                        translation = resp.choices[0].message.content.strip()
                        st.session_state[f"trans_{clean_w}"] = translation
                    except:
                        st.session_state[f"trans_{clean_w}"] = " No translation  "
    interactive_html = []
    for sent_idx, sentence in enumerate(sentences):
        words = re.findall(r'\S+', sentence)
        sentence_html = []
        for w in words:
            clean_w = re.sub(r'[^\w\s]', '', w)
            tooltip_text = st.session_state.get(f"trans_{clean_w}", "trans...")
            sentence_html.append( f'<span class="word" title="{tooltip_text}">{w}</span>')
        interactive_html.append(f'<div class="sentence" id="sent_{sent_idx}">{" ".join(sentence_html)}</div>')
    
    full_html = f'''
        <style>
            .story-box {{
                    max-width: 760px;
                    margin: auto;
                    background: #ffffff;
                    padding: 26px;
                    border-radius: 16px;
                    box-shadow: 0 8px 30px rgba(79,70,229,0.08);
                    font-size: 22px;
                    line-height: 2.2;
                    direction: rtl;
                    text-align: right;
                    border: 1px solid #e0e7ff
                    color: #1e293b;
                    font-family: 'Noto Sans Arabic', sans-serif;
                }}

            .word {{ 
                cursor: help; 
                color: inherit; 
                text-decoration: none; 
                padding: 2px 3px;
                border-radius: 4px;
            }}
            
            .word:hover {{ 
                background-color: #e0e7ff;  
            }}
            
            .sentence {{ 
                margin-bottom: 22px; 
                padding: 10px 14px; 
                border-radius: 10px; 
                font-size: 22px;
            }}
            .sentence:hover {{
                background-color: #eef2ff;
            }}
        </style>
    
        <div class="story-box">{"".join(interactive_html)} </div>
        '''
    st.markdown(full_html, unsafe_allow_html=True)


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
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif;}
        .story-title {
            text-align: center;
            font-size: 34px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 20px;
            color: #1e3a8a; }

        div.stButton > button[kind="secondary"] {
            border: 1px solid #d1d5db;
            background-color: #ffffff;
            color: #374151;
            border-radius: 10px;
            padding: 6px 10px !important;
            font-weight: 500;}
        
        div.stButton > button[kind="secondary"]:hover {
            border-color: #4f46e5;
            color: #4f46e5;
            background-color: #eef2ff;}
            
        div.stButton > button[kind="primary"] {
            background-color: #4f46e5;
            color: white;
            border: none;}
            
        div.stButton > button[kind="primary"]:hover {
            background-color: #4338ca;}
        
        div.stButton > button[kind="tertiary"] {
            background: transparent;
            border: none;
            color: #1E3A8A;
            box-shadow: none;
            padding: 6px;}
    
        div.stButton > button[kind="tertiary"]:hover {
            background-color: #eef2ff;
            color: #4338ca;}
</style>
""", unsafe_allow_html=True)


st.markdown("<h1 style='text-align:center; color:#3832aa;'> StoryLab</h1>", unsafe_allow_html=True)

if "generated_story" not in st.session_state:
    if "user" not in st.session_state or "level" not in st.session_state.user:
        st.warning("ًPlease login first to generate and read a story")
        st.stop()

st.markdown(
    "<div style='color:#666; font-size:16px; margin-bottom:20px;'>"
    "Choose a topic to instantly generate a personalized Arabic story based on your level. "
    "Read, listen and explore different vocabulary"
    "</div>",
    unsafe_allow_html=True
)

user_level = st.session_state.user["level"]
user_id = st.session_state.user["id"]

learned_words = get_learned_words(user_id, user_level)
vocab_list = [w["word_ar"] for w in learned_words]

#----- tab 1: Create -----
if st.session_state.view == "create":
    
    tab1, tab2 = st.tabs(["📝 Create a Story", "📚 My Stories"])
    
    with tab1:
        st.subheader("Create a Quick Story")
        story_type = st.selectbox("Story Type", ["Fiction", "Educational"])
        
        fiction_topics = {
            "Adventure": "🏔️ Adventure", "Romance": "❤️ Romance", "Sports": "⚽ Sports", "Travel": "✈️ Travel",
            "Nature": "🌳 Nature", "Daily Life": "🏠 Daily Life", "Celebrations": "🎉 Celebrations",
            "Family": "👨‍👩‍👧 Family", "Shopping": "🛍️ Shopping", "Technology": "📱 Technology", "Food": "🍎 Food",
            "School": "🏫 School"}
        
        educational_topics = { "Science": "🔬 Science", "History": "📜 History", "Culture": "🌍 Culture",
            "Math": "🔢 Math","Health & Wellness": "🧘 Health & Wellness","Work & Jobs": "💼 Work & Jobs" }
        
        if story_type == "Fiction":
            topics = fiction_topics
        else:
            topics = educational_topics
        
        cols = st.columns(3)
        for i, (topic_key, display_topic) in enumerate(topics.items()):
            with cols[i % 3]:
                container = st.container()
                with container:
                    if st.button(display_topic, key=f"topic_{topic_key}"):
                        st.session_state["selected_topic"] = topic_key
                        st.rerun()
        # there was an errror when coming from the mystories tab or create the generation of story we need to check and have validation so iadd validation
        if "selected_topic" in st.session_state:
            topic = st.session_state["selected_topic"]
            
            if "generated_story" not in st.session_state or st.session_state.get("last_generated_topic") != topic:
                with st.spinner(""):
                    prompt = f"""
                    You are an Arabic language teacher.
                    
                    Generate a short Arabic story for an Arabic learner.
                    
                    student Level: {user_level}
                    Topic: {topic}
                    Story Type: {story_type}

                    IMPORTANT VOCABULARY (priority words for reinforcement):
                    {vocab_list}
                    
                    Vocabulary Usage Rules (IMPORTANT):
                    - Try to naturally include 1–3 words from the list
                    - ONLY include a word if it fits the sentence naturally
                    - Do NOT force vocabulary into unnatural sentences
                    - It is OK to skip a word if it does not fit the context
                    - Prioritize clarity and natural Arabic over vocabulary usage

                    ---------------------------------------------------------------------
                    
                    Story Generation RULES (IMPORTANT):
                    - Use Modern Standard Arabic only
                    - Vocabulary must match CEFR level {user_level}
                    - Use simple grammar for beginner user level (A1-A2)
                    - If student level is A1, story MUST BE 8 sentences ONLY
                    - If student level is A2, story MUST BE 10 sentneces ONLY
                    - If student level is B1, story MUST BE  12 sentneces ONLY
                    - Sentences should be simple and clear
                    - Story must be engaging and coherent
                    - Do NOT include explanations or translations
                    - Extract 5-6 key vocabulary words from the story that are useful for learners.

                    --------------------------------------------------------------------------------

                    Vocabulary Extraction Rules:
                    - Extract 5–7 useful words FROM the story
                    - Words must be meaningful for learners (not trivial words like "في", "من")
                    - Avoid duplicates
                    - Words should not be in the in the vocab list given to you: {vocab_list}
                    - Provide:
                        - Arabic word
                        - English meaning
                        - Simple transliteration

                     -------------------------------------------------------------------------------
                    
                    BEFORE Returning the story ensure:
                
                    - If student level is A1, the story generated has 8 sentences ONLY
                    - If student level is A2, the story generated has 10 sentneces ONLY
                    - If student level is B1, the story generated has 12 sentneces ONLY

                    OUTPUT :
                    
                    Return ONLY valid JSON (no extra text):
                    {{
                      "title": "...",
                      "story": "...",
                      "key_vocab": [
                        {{
                          "arabic": "...",
                          "english": "...",
                          "transliteration": "..."
                        }}
                      ]
                     }}
                    
                """
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
            
                    try:
                        raw = response.choices[0].message.content.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1].strip()
                        data = json.loads(raw)
                    
                        title = data.get("title", f"Story: {topic}")
                        story_text = data.get("story", "")
                        key_vocab = data.get("key_vocab", [])
                        if not isinstance(key_vocab, list):
                            key_vocab = []
                    
                    except Exception as e:
                        st.error("Error parsing story response")
                        st.code(raw)
                        st.stop()
                    
                    st.session_state.generated_story = story_text
                    st.session_state.generated_title = title
                    st.session_state.generated_vocab = key_vocab
                    st.session_state.last_generated_topic = topic
                    story_id= save_story( 
                        user_id=user_id,
                        title=title,
                        content=story_text,
                        topic=topic,
                        story_type=story_type,
                        level=user_level
                    )
                    save_vocab(story_id, key_vocab)
                    
                    st.session_state.current_story = {"id": story_id, "title": title, "content": story_text, "vocab": key_vocab}
                    st.session_state.view = "read"
                    st.rerun()         
    with tab2:
        read_count = get_read_stories_count(user_id)
        current_level = st.session_state.user.get("level", "A1")
        
        st.subheader("My Stories")
        stories = get_user_stories(user_id)
        if stories:
            for s in stories:
                vocab = get_story_vocab(s[0])
                status_html = ""
                if s[6]:
                    status_html = """
                    <span style="
                        background:#a7f3d0;
                        color:#166534;
                        padding:6px 14px;
                        border-radius:9999px;
                        font-size:13px;
                        font-weight:600;
                    ">✓ Read</span>
                """
                with st.container(border=True):
                    html_code = f"""
                           <div style="
                            background: #eef2ff; 
                            padding:16px 18px;
                            border-radius:16px;
                            margin-bottom:12px;
                            border: 1px solid #e2e8f0;
                            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
                            direction: rtl;
                            position: relative;
                            overflow: hidden;
                        ">
                            <div style="
                                position:absolute;
                                left:0;
                                top:0;
                                bottom:0;
                                width:5px;
                                background:#dbeafe;
                            "></div>
                            
                            <div style="display:flex; justify-content:space-between; align-items:center; padding-left:12px;">
                                <div style="text-align:right; flex:1;">
                                    <div style="
                                        font-size:26px;
                                        font-weight:700;
                                        color:#1e2937;
                                        margin-bottom:6px;
                                        line-height:1.3;
                                    ">
                                        {s[1]}
                                    </div>

                                    <div style="
                                        font-size:14px;
                                        color:#64748b;
                                    ">
                                        {s[3]} • {s[4]} • {s[5][:10] if s[5] else ''}
                                    </div>
                                </div>

                                <div>
                                    {status_html}
                                </div>
                            </div>
                        </div>
                    """
                    components.html(html_code, height=100)
                    if s[6]:
                    # If already read only one button show and should be centered
                        col = st.columns([1, 2, 1])[1]
                        with col:
                            vocab = get_story_vocab(s[0])
                            if st.button("📖 Read Again", key=f"read_again_{s[0]}", use_container_width=True):
                                st.session_state.current_story = {'id': s[0], 'title': s[1], 'content': s[2], 'vocab': vocab }
                                st.session_state.view = "read"
                                st.rerun()
                    else:
                        vocab = get_story_vocab(s[0])
                        col1, col2 = st.columns(2, gap="small")
                        with col1:
                            if st.button("📖 Read", key=f"read_{s[0]}", use_container_width=True):
                                    st.session_state.current_story = { 'id': s[0], 'title': s[1],  'content': s[2], 'vocab': vocab }
                                    st.session_state.view = "read"
                                    st.rerun()
                        with col2:
                            if st.button("✔ Mark as read", key=f"mark_{s[0]}", use_container_width=True):
                                mark_story_as_read(user_id, s[0])
                                st.rerun()
                                
                    st.markdown("<br>", unsafe_allow_html=True)                                       
        else:
            st.info(" You have not created any stories yet")
            
# reading view is when you click on a story to read from my stories tab, or when you first create a story will redirect to view
elif st.session_state.view == "read":
    story = st.session_state.current_story

    st.markdown('<div class="top-bar">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 6, 1], vertical_alignment="center")
    with col1:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Back ", key="top_back", type="tertiary", use_container_width=True):
            st.session_state.view = "create"
            st.session_state.pop("current_story", None)
            st.session_state.pop("quiz_questions", None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🔊", key="top_audio", type="tertiary", use_container_width=True):
            try:
                tts = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    input=story["content"]
                )
                with open("temp.mp3", "wb") as f:
                    tts.stream_to_file(f.name)
                st.audio("temp.mp3")
                os.remove("temp.mp3")
            except:
                st.error("Error in audio ")
    
    with col3:
        dark = st.toggle("🌙", key="dark_mode")
        if dark:
            st.markdown("""
            <style>
            .story-box {
                background:#0f172a !important;
                color:#e2e8f0 !important;
            }
            .sentence:hover {
                background:#1e293b !important;
            }
            .word:hover {
                background:#334155 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
    st.divider()
    
    display_full_story( story["title"], story["content"], user_level )
    if "vocab" in story and story["vocab"]:
        st.markdown("###  Key Vocabulary")
        cols = st.columns(3)
        for i, vocab in enumerate(story["vocab"]):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="text-align:center; direction:rtl;">
                        <div style="font-size:20px; font-weight:700;">
                            {vocab['arabic']}
                        </div>
                        <div style="color:#64748b;">
                            {vocab['transliteration']}
                        </div>
                        <div style="margin-top:6px; color:#065f46;">
                            {vocab['english']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                learned_words = get_learned_words(user_id, user_level)
                vocab_list = [w["word_ar"] for w in learned_words]
                
                if vocab["arabic"] in vocab_list:
                    st.markdown(
                        "<div style='text-align:center; color:#16a34a; font-weight:600;'>✔ Saved</div>",
                        unsafe_allow_html=True
                    )
                else:
                    if st.button("Save", key=f"save_vocab_{i}_{story['id']}"):
                        mark_word_learned(
                            user_id,
                            vocab["arabic"],
                            category="story",
                            level=user_level
                        )
                        st.rerun()
    st.divider()
    
    col_btn = st.columns([3, 2, 1])[1]
    with col_btn:
        if st.button(" Test Your Comprehension ", type="primary"):
            with st.spinner(" Generating quiz comprehesion questions ... "):
                #prompt should be editted because the given question and correct answer is not working there is a lot of issues , so i try another way where i have answer index 
                prompt_questions = f"""
                You are an Arabic language teacher.
                
                Based on this story:
                {story['content']}
                
                Generate 3 comprehension questions for a {user_level} level learner.
                
                Requirements:
                
                - Questions should be in Arabic MSA only
                - Include 3 multiple-choice questions with 3 options each (A, B, C)
                - Only one correct answer per question
                - Questions should test understanding of main ideas or vocabulary
                - Return ONLY the questions in valid JSON format (no extra text, markdown, no explanation):
                [
                  {{
                    "question": "السؤال الأول؟",
                    "options": ["الخيار أ", "الخيار ب", "الخيار ج"],
                    "answer_index": 0
                  }},
                  ...
                ]
                """
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_questions}],
                    temperature=0.4
                )
                
                raw = resp.choices[0].message.content.strip()
                # debugging because there some issues with the response from the prompt
                try:
                    if raw.startswith("```json"):
                        raw = raw.split("```json")[1].split("```")[0].strip()
                    questions = json.loads(raw)
                    
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_user_answers = [None] * len(questions)
                    st.rerun()
                    
                    # this is debugging becaus there was soem issues lol 
                except Exception as e:
                    st.error(f" Error : {e}")
                    st.write(" raw response :", raw)

    if "quiz_questions" in st.session_state and st.session_state.quiz_questions:
        questions = st.session_state.quiz_questions
        answers = st.session_state.quiz_user_answers
        for i, q in enumerate(questions):
            st.markdown(f"""
                <div style="direction: rtl; text-align: right; margin: 25px 0 12px 0;">
                    <strong style="font-size: 1.15rem; color: #1e3a8a;">{q['question']}</strong>
                </div>
            """, unsafe_allow_html=True)
                        
            for option in q["options"]:
                is_selected = answers[i] == option
                btn_style = "primary" if is_selected else "secondary"
                btn_col = st.columns([1, 5])[1]  
                with btn_col:
                    if st.button(
                        option,
                        key=f"q_{i}_{option}",
                        use_container_width=True,
                        type=btn_style
                    ):
                        answers[i] = option

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            submit_clicked = st.button("Submit Answers",  type="primary", use_container_width=True )
        
        with col2:
            close_clicked = st.button( "Close Questions",  use_container_width=True)

        if submit_clicked:
            if None in answers:
                st.warning(" Please answer all questions first")
                st.stop()
            else:
                score = 0
                feedback = []
                for i, q in enumerate(questions):
                    correct_option = q["options"][q["answer_index"]]
                    if answers[i] == correct_option:
                        score += 1
                        feedback.append({"text": f"Question {i+1}: Correct ✅","is_correct": True})
                    else:
                        feedback.append({"text": f"Question {i+1}: Incorrect ❌ (Answer: {correct_option})", "is_correct": False})

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
                        {score} / {len(questions)}
                    </span>
                </div>
                """
                st.markdown(score_html, unsafe_allow_html=True)
                for f in feedback:
                    is_correct = f["is_correct"]
                    background = "#ecfdf5" if is_correct else "#fef2f2"
                    #border = "#16a34a" if is_correct else "#dc2626"
                    text = "#065f46" if is_correct else "#7f1d1d"
                
                    st.markdown(f"""
                    <div style="
                        background:{background};
                        padding:12px 14px;
                        border-radius:10px;
                        margin-top:10px;
                        font-size:17px;
                        color:{text};
                    ">
                        {f["text"]}
                    </div>
                    """, unsafe_allow_html=True)
                # auto mark story a read after doing teh comprehenion test and save score
                mark_story_as_read(user_id, story['id'])
                save_quiz_score(user_id, story['id'], score, len(questions))
        if close_clicked:
            for k in ["quiz_questions", "quiz_user_answers"]:
                st.session_state.pop(k, None)
            st.rerun()

    