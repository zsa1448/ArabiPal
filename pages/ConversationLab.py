import streamlit as st
from openai import OpenAI 
import tempfile
from db_setup import ( save_conversation_message, load_conversation_history, clear_conversation_history, save_conversation_memory, load_conversation_memory, clear_conversation_memory, require_login)
import os

client = OpenAI(api_key=os.getenv("OpenAI_Capstone_key"))

st.set_page_config(page_title="ConversationLab", page_icon="🤖")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Lora&family=Nunito&display=swap" rel="stylesheet">
    <style>
        body, .stTextArea, .stInfo, .stMarkdown {font-family: 'Nunito', serif !important;}
        
        h1, h2, h3, h4, h5, h6 {font-family: 'Lora', sans-serif !important; }

        .css-1d391kg {font-family: 'Lora', sans-serif !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stChatMessage"]:has(div[aria-label="assistant"]) {
    direction: rtl;
    text-align: right;}

[data-testid="stChatMessage"]:has(div[aria-label="user"]) {
    direction: ltr;
    text-align: left;}

[data-testid="stMarkdownContainer"] p {
    line-height: 1.8;
    font-size: 16px;}
audio {
    width: 100%;
    margin-top: 8px;}
</style>
""", unsafe_allow_html=True)

st.markdown( "<h1 style='text-align:center; color:#3832aa;'> 🤖 🗪 ConversationLab </h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
Practice real-life Arabic conversations with different interactive scenarios. Respond naturally, learn from corrections, and focus on improving your conversational skills
""")
st.divider()


user_id, user_level = require_login()

if "scenario" not in st.session_state:
    st.session_state.scenario = "Normal Conversation"

if "messages" not in st.session_state:
    st.session_state.messages = load_conversation_history(user_id, st.session_state.scenario)
    
if "translations" not in st.session_state:
    st.session_state.translations = {}

if "scenario_started" not in st.session_state:
    st.session_state.scenario_started = False

if "conversation_memory" not in st.session_state:
    st.session_state.conversation_memory = load_conversation_memory(user_id)

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None


with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if st.button(" Clear Conversation ", use_container_width=True):
        clear_conversation_history(user_id, st.session_state.scenario)
        clear_conversation_memory(user_id)
        st.session_state.messages = []
        st.session_state.translations = {}
        st.session_state.conversation_memory = []
        st.session_state.scenario_started = False
        st.rerun()

scenario_instructions = {
    "Normal Conversation": "Have a free conversation with the AI tutor.",
    "Meeting Someone": " You are meeting with someone for the first time. Start with a friendly greeting and start with small talk",
    "Restaurant": " You are ordering food from a restaurant",
    "Shopping": "You are buying something from a traditional market.",
    "Airport": "You are at the airport. Answer questions about your travel and complete check-in or boarding.",
    "Hospital":"You are visiting a doctor. Describe your symptoms and answer basic health questions.",
    "Hotel":"You are checking into a hotel. Talk about your reservation and ask for basic information about your stay."
}


def parse_assistant_response(response):
    correction = None
    reason = None
    reply = response

    if "[CORRECTION]" in response:
        parts = response.split("[REPLY]")
        before_reply = parts[0]
        reply = parts[1].strip() if len(parts) > 1 else ""

        if "[REASON]" in before_reply:
            corr_part, reason_part = before_reply.split("[REASON]")
            correction = corr_part.replace("[CORRECTION]", "").strip()
            reason = reason_part.strip()
            
    return correction, reason, reply

def build_system_prompt(level,scenario, memory):
    level_rules = {
        "A1": "Use very short sentences (2-5 words), simple vocabulary, avoid complex grammar, slow conversation, ask easy questions.",
        "A2": "Use short sentences, simple grammar, basic past and present tense.",
        "B1": "Use natural sentences, moderate length, explanations allowed."
    }
    memory_text = "\n".join(f"- {m}" for m in memory) if memory else "No memory yet."

    base_prompt= f"""
            You are a friendly, professional Arabic language tutor helping a student learn Modern Standard Arabic (MSA).
            
            Student Level: {level}
            
            Rules:
            
            - Speak only in Arabic.
            - {level_rules.get(level)}
            - Use vocabulary appropriate for the student's level.
            - Stay in the scenario the whole conversation session
            - Keep responses short
            - Encourage conversation.
            - Ask simple follow-up questions.
            - Be supportive and motivating.

            Correction Rules (VERY IMPORTANT):
            
                Only correct REAL language mistakes.
                
                REAL mistakes include:
                - Grammar errors
                - Wrong verb conjugation
                - Incorrect sentence structure
                - Wrong vocabulary usage
                - Missing important words that change meaning
                - spelling mistakes that change the meaning of sentence
                
                DO NOT correct:
                - punctuation (مثل: مرحبا بدون !)
                - writing style
                - optional diacritics
                - small variations
                - natural greetings
                - informal but correct Arabic
                - short answers like: نعم، لا، مرحبا، شكرا

            Response Format:

                If there is a mistake, respond EXACTLY like this:
                
                [CORRECTION]
                wrong sentence ⇾ correct sentence
                
                [REASON]
                short simple explanation in Arabic
                
                [REPLY]
                continue the conversation naturally
                
                --------------------------------
                
                If there is NO mistake:
                
                [REPLY]
                continue the conversation normally
                            
            Conversation Memory:
                {memory_text}
                
            """

    scenario_roles = {
        "Meeting Someone": "You are meeting someone for the first time. The student is a new acquaintance. Continue the conversation with simple small talk (name, where they are from, how they are, etc.). Encourage the student to use basic introductions and greetings",
        
        "Restaurant": "You are a waiter in a restaurant. The student is a customer. Continue the conversation by explaining the menu briefly and helping them order food and drinks. Encourage the student to use food vocabulary and simple ordering phrases.",
        
        "Shopping": "You are a shopkeeper in a traditional market. The student wants to buy something. Continue the conversation by asking what they are looking for, discussing price, and completing the purchase. Encourage the student to use numbers, prices, and negotiation phrases.",
        
        "Normal Conversation": "You are having a normal conversation with the student.",
        
        "Airport": "You are an airport officer or airline staff member. The student is a traveler. Continue the conversation by asking for travel details (passport, destination, ticket) and helping them with check-in or boarding. Encourage the student to use travel-related vocabulary and answer questions clearly.",
        
        "Hospital": "You are a doctor speaking with a patient. The student is the patient. Continue the conversation by asking about symptoms, duration, and pain, and help them describe their health condition. Encourage the student to describe symptoms using simple sentences.",
        
        "Hotel": "You are a hotel receptionist. The student is a guest. Continue the conversation by helping them check in, asking about their reservation, and providing basic information about their stay. Encourage the student to use polite expressions and booking-related vocabulary."}

    return base_prompt + "\n" + scenario_roles.get(scenario, "You are having a normal Arabic conversation.")


def update_conversation_memory(user_message, ai_reply):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=100,
            messages=[
                { "role": "system",  "content": "Extract short learning memory from this conversation. Return only 1 short sentence."},
                { "role": "user", "content": f"User: {user_message}\nTutor: {ai_reply}"}])

        memory = resp.choices[0].message.content.strip()
        if memory and len(st.session_state.conversation_memory) < 5:
            if memory not in st.session_state.conversation_memory:
                st.session_state.conversation_memory.append(memory)
                save_conversation_memory(user_id, memory)             
    except:
        pass

def generate_ai_response(user_message):
    system_prompt = build_system_prompt(user_level, st.session_state.scenario, st.session_state.conversation_memory )
    conversation = [{"role": "system", "content": system_prompt}]

    for msg in st.session_state.messages[-10:]:
        conversation.append({"role": msg["role"], "content": msg["content"] })
    conversation.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            temperature=0.4,
            max_tokens=200
        )

        reply = response.choices[0].message.content
        update_conversation_memory(user_message, reply)
        return reply
        
    except Exception as e:
        return f"Error in the system: {str(e)}"

#a function so the started for scenario be consistent instead of ai will generate each time
def start_scenario(scenario):
    scenario_starters = {
    "Meeting Someone": "مرحبا! أنا سعيد بلقائك. ما اسمك؟ من أين أنت؟",
    "Restaurant": "أهلاً وسهلاً! مرحبا بك في مطعمنا. اليوم لدينا كباب، سلطة، وأرز. ماذا تريد أن تطلب؟",
    "Shopping": "مرحباً! ماذا تريد أن تشتري؟",
    "Airport": "مرحباً! هل يمكنك إظهار جواز السفر والتذكرة؟ إلى أين تسافر؟",
    "Hospital": "مرحباً. ماذا تشعر؟ هل لديك ألم أو تعب؟",
    "Hotel": "مرحباً! أهلاً بك في الفندق. هل لديك حجز؟"
}
    return scenario_starters.get(scenario, "مرحباً!")
    
selected_scenario = st.selectbox(
    "🎭 Choose a Scenario",
    ["Normal Conversation", "Meeting Someone", "Restaurant", "Shopping", "Airport", "Hospital", "Hotel" ]
)

if selected_scenario != st.session_state.scenario:
    st.session_state.scenario = selected_scenario
    st.session_state.messages = load_conversation_history(user_id, selected_scenario)
    st.session_state.translations = {}
    st.session_state.scenario_started = False 

    if not st.session_state.messages and selected_scenario != "Normal Conversation":
        ai_first = start_scenario(selected_scenario)
        st.session_state.messages.append({"role": "assistant", "content": ai_first} )
        save_conversation_message(
            user_id,
            selected_scenario,
            "assistant",
            ai_first
        )
        #st.session_state.scenario_started = True 
    st.rerun()

st.markdown(f"""
<div style="
    background-color:#eef2ff;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
">
    <span style="color:#4B0082;">
    {scenario_instructions[st.session_state.scenario]}
    </span>
</div>
""", unsafe_allow_html=True)
#st.info(scenario_instructions[st.session_state.scenario]

def translate_to_english(text):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",  "content": "Translate Arabic to clear natural English."},
                {"role": "user",  "content": text}   ],  max_tokens=150)
        return resp.choices[0].message.content.strip()

    except:
        return "Translation error"

for idx, msg in enumerate(st.session_state.messages):
    #role = "user" if msg["role"] == "user" else "assistant"
    role = msg["role"]
    avatar = "🧑‍🏫" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        if role == "assistant":
            correction, reason, reply = parse_assistant_response(msg["content"])
            if correction:
                st.markdown(f"""
                <div style="
                    background-color:#FFF7ED;
                    padding:10px;
                    border-radius:10px;
                    margin-top:8px;
                    direction:rtl;
                    text-align:right;
                    font-size:16px;
                ">
                 <b>Correction</b><br>
                {correction}
                </div>
                """, unsafe_allow_html=True)
            if reason:
                st.markdown(f"""
                <div style="
                    background-color:#eef2ff;
                    padding:10px;
                    border-radius:10px;
                    margin-top:5px;
                    direction:rtl;
                    text-align:right;
                    font-size:16px;
                ">
                <b>Reason</b><br>
                {reason}
                </div>
                """, unsafe_allow_html=True)

            st.markdown(
    f"<div style='direction: rtl; text-align: right;padding-right: 10px;'>{reply}</div>",
    unsafe_allow_html=True
)
        else:
            st.markdown(msg["content"])
        if role == "assistant" and "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3", autoplay=True)
            
        if role == "assistant":
            if idx in st.session_state.translations:
                st.markdown(
                f"<div style='color: gray; font-size: 14px; margin-top:4px;'>🇬🇧 {st.session_state.translations[idx]}</div>",
                unsafe_allow_html=True
            )
            else:
                if st.button(" 🌐 Translate", key=f"trans_{idx}"):
                    translation = translate_to_english(msg["content"])
                    st.session_state.translations[idx] = translation
                    st.rerun()

st.divider()
col1, col2 = st.columns([6, 1])
with col1:
    user_text = st.chat_input(" 💬 Write your message here")
with col2:
    audio_data = st.audio_input("",key="voice_input")
user_message = None
if user_text:
    user_message = user_text

elif audio_data is not None:
    audio_bytes = audio_data.getvalue()
    if st.session_state.last_audio_bytes == audio_bytes:
        user_message = None  
    else:
        st.session_state.last_audio_bytes = audio_bytes
        with st.spinner(" recognizing your voice..."):
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    language="ar",
                    response_format="text",
                    prompt="مرحبا، السلام عليكم، أهلاً، كيف حالك"  
                )
                user_message = transcript.strip()
                if "اشتركوا في القناة" in user_message or len(user_message) < 3: #this was the hallucination i always get so ia dded it
                    st.warning("Had a problem recognizing your voice, please try agian and talk more clearly.")
                    user_message = None
    
            except Exception as e:
                st.error(f"Error in recognizing voice input : {str(e)}")
                user_message = None

if user_message:
    #with st.chat_message("user", avatar="👤"):
        #st.markdown(user_message)
    st.session_state.messages.append({"role": "user", "content": user_message})
    save_conversation_message(
            user_id,
            st.session_state.scenario,
            "user",
            user_message
        )

    ai_reply = generate_ai_response(user_message)
    if ai_reply:
        #with st.chat_message("assistant"):
            #st.markdown(ai_reply)
        audio_path = None
        try:
            tts_response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=ai_reply
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts_response.stream_to_file(f.name)
                audio_path = f.name
                #st.audio(audio_path, format="audio/mp3", autoplay=True)
            st.session_state.last_audio = audio_path

        except Exception as e:
            st.warning("Audio have not worked")

        st.session_state.messages.append({"role": "assistant", "content": ai_reply, "audio": audio_path})
        save_conversation_message(
                user_id,
                st.session_state.scenario,
                "assistant",
                ai_reply
            )
    st.rerun()

st.write("")
st.write("")

#if "last_audio" in st.session_state:
    #st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)