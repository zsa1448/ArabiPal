import streamlit as st
from openai import OpenAI
import json
import streamlit.components.v1 as components
import tempfile
import io

import os

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
    .buttons {
        margin-top: 30px;
    }

    div.stButton > button {
        border: 1px solid #d1d5db;
        background-color: #f9fafb;
        color: #374151;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    div.stButton > button:hover {
        border-color: #4f46e5;
        color: #4f46e5;
        background-color: #eef2ff;
    }

    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:left; color:#3832aa;'>Arabic Alphabets</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<div style='color:#666; font-size:16px; margin-bottom:20px;'>"
    "Build your foundation skills, by learning all 28 letters of the Arabic Alphabets, listen to its pronounciation, and review different forms of its letters "
    "</div>",
    unsafe_allow_html=True
)

alphabet_data = {
    "Alif": {"letter": "ا", "start": "ا", "middle": None, "end": "ـا", "name": "Alif"},
    "Baa": {"letter": "ب", "start": "بـ", "middle": "ـبـ", "end": "ـب", "name": "Baa" },
    "Taa": {"letter": "ت", "start": "تـ", "middle": "ـتـ", "end": "ـت", "name": "Taa" },
    "Thaa": {"letter": "ث", "start": "ثـ", "middle": "ـثـ", "end": "ـث", "name": "Thaa" },
    "Jeem": {"letter": "ج", "start": "جـ", "middle": "ـجـ", "end": "ـج", "name": "Jeem" },
    "Haa": {"letter": "ح", "start": "حـ", "middle": "ـحـ", "end": "ـح", "name": "Haa" },
    "Khaa": {"letter": "خ", "start": "خـ", "middle": "ـخـ", "end": "ـخ", "name": "Khaa" },

    # ❗ لا تتصل بما بعدها
    "Dal": {"letter": "د", "start": "د", "middle": None, "end": "ـد", "name": "Dal" },
    "Dhal": {"letter": "ذ", "start": "ذ", "middle": None, "end": "ـذ", "name": "Dhal" },
    "Raa": {"letter": "ر", "start": "ر", "middle": None, "end": "ـر", "name": "Raa" },
    "Zay": {"letter": "ز", "start": "ز", "middle": None, "end": "ـز", "name": "Zay" },

    "Seen": {"letter": "س", "start": "سـ", "middle": "ـسـ", "end": "ـس", "name": "Seen"},
    "Sheen": {"letter": "ش", "start": "شـ", "middle": "ـشـ", "end": "ـش", "name": "Sheen"  },
    "Saad": {"letter": "ص", "start": "صـ", "middle": "ـصـ", "end": "ـص", "name": "Saad"},
    "Daad": {"letter": "ض", "start": "ضـ", "middle": "ـضـ", "end": "ـض", "name": "Daad" },
    "Taa_emphatic": {"letter": "ط", "start": "طـ", "middle": "ـطـ", "end": "ـط", "name": "Taa" },
    "Dhaa": {"letter": "ظ", "start": "ظـ", "middle": "ـظـ", "end": "ـظ", "name": "Dhaa" },
    "Ayn": {"letter": "ع", "start": "عـ", "middle": "ـعـ", "end": "ـع", "name": "Ayn"  },
    "Ghayn": {"letter": "غ", "start": "غـ", "middle": "ـغـ", "end": "ـغ", "name": "Ghayn"  },
    "Faa": {"letter": "ف", "start": "فـ", "middle": "ـفـ", "end": "ـف", "name": "Faa"  },
    "Qaaf": {"letter": "ق", "start": "قـ", "middle": "ـقـ", "end": "ـق", "name": "Qaaf"  },
    "Kaaf": {"letter": "ك", "start": "كـ", "middle": "ـكـ", "end": "ـك", "name": "Kaaf" },
    "Laam": {"letter": "ل", "start": "لـ", "middle": "ـلـ", "end": "ـل", "name": "Laam"},
    "Meem": {"letter": "م", "start": "مـ", "middle": "ـمـ", "end": "ـم", "name": "Meem" },
    "Noon": {"letter": "ن", "start": "نـ", "middle": "ـنـ", "end": "ـن", "name": "Noon" },
    "Haa_end": {"letter": "ه", "start": "هـ", "middle": "ـهـ", "end": "ـه", "name": "Haa" },
    "Waw": {"letter": "و", "start": "و", "middle": None, "end": "ـو", "name": "Waw"},

    "Yaa": {"letter": "ي", "start": "يـ", "middle": "ـيـ", "end": "ـي", "name": "Yaa"}
}

#-- pronounciation map actually i tried without it but its bad for both the letter and the name , so this was the last resort as its the most reliable there

pronunciation_map = {
    "ا": "أَلِف",
    "ب": "بَاء",
    "ت": "تَاء",
    "ث": "ثَاء",
    "ج": "جِيم",
    "ح": "حَاء",
    "خ": "خَاء",
    "د": "دَال",
    "ذ": "ذَال",
    "ر": "رَاء",
    "ز": "زَاي",
    "س": "سِين",
    "ش": "شِين",
    "ص": "صَاد",
    "ض": "ضَاد",
    "ط": "طَاء",
    "ظ": "ظَاء",
    "ع": "عَيْن",
    "غ": "غَيْن",
    "ف": "فَاء",
    "ق": "قَاف",
    "ك": "كَاف",
    "ل": "لَام",
    "م": "مِيم",
    "ن": "نُون",
    "ه": "هَاء",
    "و": "وَاو",
    "ي": "يَاء"
}

letters = list(alphabet_data.values())
total = len(letters)
if "alpha_index" not in st.session_state:
    st.session_state.alpha_index = 0

index = st.session_state.alpha_index
letter = letters[index]

arabic = letter["letter"]
name = letter["name"]
start = letter["start"] or "-"
middle = letter["middle"] or "-"
end = letter["end"] or "-"

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
    min-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin: 20px auto;
    max-width: 600px;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.15);
    direction: rtl;
    position: relative;
}}

.front {{
    font-weight: bold;
    color: #312e81;
    font-size: 64px;
}}

.name {{
    font-size: 28px;
    margin-top: 10px;
    color: #4f46e5;
    font-weight: 800;
}}

.forms {{
    margin-top: 15px;
    font-size: 20px;
    color: #374151;
}}

.forms {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 18px;
}}

.form-box {{
    background: #F2F0F0;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 7px;
}}

.label {{
    font-size: 16px;
    color: #6b7280;
    margin-bottom: 6px;
}}

.value {{
    font-size: 22px;
    font-weight: bold;
    color: #312e81;
}}
</style>
</head>

<body>
<div class="flashcard">
    <div class="front">{arabic}</div>
    <div class="name">{name}</div>

    <div class="forms">
    <div class="form-box">
        <div class="label">Start</div>
        <div class="value">{start}</div>
    </div>

    <div class="form-box">
        <div class="label">Middle</div>
        <div class="value">{middle}</div>
    </div>

    <div class="form-box">
        <div class="label">End</div>
        <div class="value">{end}</div>
    </div>
</div>

</div>

</body>
</html>
""", height=340)
if st.button("🔊"):
    letter_pronounciation = pronunciation_map.get(arabic, arabic)
    audio_bytes = io.BytesIO()

    tts = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=letter_pronounciation
    )
        
    audio_bytes = tts.read()
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

col_prev, col_next = st.columns(2)
with col_prev:
    if index > 0:
        if st.button("Previous", use_container_width=True):
            st.session_state.alpha_index -= 1
            st.rerun()
with col_next:
    if index < total - 1:
        if st.button("Next", use_container_width=True):
            st.session_state.alpha_index += 1
            st.rerun() 
    

