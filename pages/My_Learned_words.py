import streamlit as st
from db_setup import require_login, get_learned_words, get_connection
import streamlit.components.v1 as components

st.set_page_config(page_title="My Learned Words", page_icon="📚")

user_id, user_level = require_login()

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

arabic_lookup = {
    w["arabic"]: { "english": w["english"], "translit": w["translit"], "category": cat_name}
    for cat_name, words_list in vocab_data[user_level].items()
    for w in words_list}

#getting the vocabulary that is saved (learned) from the db
conn = get_connection()
c = conn.cursor()
c.execute("SELECT word_ar, word_en, transliteration FROM story_vocab")
story_lookup = {
    row[0]: {"english": row[1], "translit": row[2]}
    for row in c.fetchall()}
conn.close()

#st.title("📚 My Learned Words")
st.markdown("<h1 style='text-align:center; color:#3832aa;'> My Learned Words</h1>", unsafe_allow_html=True)

st.markdown(f"""
<div style="
    font-size: 26px;
    font-weight: 700;
    color: #908AFF;
    margin-bottom: 4px;
">
    🧠 Level {user_level} • Learned Vocabulary
</div>
""", unsafe_allow_html=True)

# Get all learned words for the current level
learned_data = get_learned_words(user_id, user_level)

if not learned_data:
    st.info("You haven't learned any words yet. Begin learning words in the Vocabulary Lab.")
    st.stop()
learned_words = []

for item in learned_data:
    word_ar = item[0]        # word_ar
    category = item[1]       # category (could be "from story" or normal category)

    # First, try to find it in the original vocabulary JSON
    if word_ar in arabic_lookup:
        w = arabic_lookup[word_ar]
        learned_words.append({
            "arabic": word_ar,
            "english": w["english"],
            "translit": w["translit"],
            "category": category or w["category"]
        })
    else:
        if word_ar in story_lookup:
            w = story_lookup[word_ar]
            learned_words.append({
                "arabic": word_ar,
                "english": w["english"],
                "translit": w["translit"],
                "category": "From Story"
            })
        else:
            learned_words.append({
                "arabic": word_ar,
                "english": "Translation not available",
                "translit": "-",
                "category": "Unknown"
            })

st.markdown("<br>", unsafe_allow_html=True)

categories = sorted(set(w["category"] for w in learned_words))
categories.insert(0, "All")
selected_category = st.selectbox(" Filter Category", categories)

search_term = st.text_input("Search Learned Words", placeholder="Search for any word")

filtered_words = learned_words
if selected_category != "All":
    filtered_words = [ w for w in filtered_words if w["category"] == selected_category]
if search_term:
    search_term = search_term.lower()
    filtered_words = [w for w in filtered_words
        if search_term in w["arabic"].lower() or search_term in w["english"].lower() or search_term in w["translit"].lower()]
    
cards_html = ""

for word in filtered_words:
    arabic = word["arabic"]
    english = word["english"]
    translit = word["translit"]

    cards_html += f"""
    <div class="card">
        <div class="arabic">{arabic}</div>
        <div class="english">{english}</div>
        <div class="translit">{translit}</div>
    </div>
    """

components.html(f"""
    <style>
    .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 12px;
        padding: 10px;
    }}
    
    .card {{
        background: #f8f7ff;
        border: 1px solid #e0ddff;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        font-family: 'Nunito', sans-serif;
        box-shadow: 0 3px 10px rgba(79, 70, 229, 0.08);
    }}
    
    .card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.15);
    }}
    
    .arabic {{
        font-size: 20px;
        font-weight: 700;
        direction: rtl;
        color: #1f2937;
        margin-bottom: 4px;
    }}
    
    .english {{
        font-size: 16px;
        font-weight: 600;
        color: #4f46e5;
    }}
    
    .translit {{
        font-size: 14px;
        color: #6b7280;
        margin-top: 2px;
    }}
    </style>
    
    <div class="grid">
        {cards_html}
    </div>
    """, height=600)


            

