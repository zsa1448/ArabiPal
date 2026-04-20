import sqlite3
from datetime import datetime
import os
import streamlit as st
import json
from datetime import timedelta

DB_FILE = "tutor.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  
    return conn

#function to create all tables i would need for all modules, and to make it easier for me i did the look up indexes for when i want to have progress dashboard 

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = ON;")

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            level TEXT DEFAULT 'A1',          -- default to A1
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    ''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')

    # Vocab mastery table 
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocab_mastery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            word_ar TEXT NOT NULL,
            category TEXT,
            level TEXT,
            is_learned BOOLEAN DEFAULT FALSE,
            is_mastered BOOLEAN DEFAULT FALSE,
            marked_learned_at TEXT,
            times_reviewed INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            last_reviewed TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_user_word ON vocab_mastery(user_id, word_ar)')

    #Writing module
    c.execute('''
        CREATE TABLE IF NOT EXISTS writing_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vocab_word TEXT,
            sentence_en TEXT,
            correct_sentence TEXT,
            user_answer TEXT,
            is_correct BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_writing_user 
        ON writing_attempts(user_id)
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_writing_vocab 
        ON writing_attempts(vocab_word)
    ''')
    # reading module
    c.execute('''
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        topic TEXT,
        story_type TEXT,
        level TEXT,
        created_at TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            story_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
    ''')


  
    # Conversation module 
    # save messages between stdent and ai(tutor)
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scenario TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversation_user
        ON conversations(user_id)
    ''')
    
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_conversation_scenario
        ON conversations(scenario)
    ''')
    # save memory to make it perosnalized the more user convere with the ai
    c.execute('''
    CREATE TABLE IF NOT EXISTS conversation_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        memory TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_memory_user
        ON conversation_memory(user_id)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_word TEXT NOT NULL,
            correct_word TEXT NOT NULL,
            explanation TEXT,
            module TEXT DEFAULT 'writing',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_mistakes_user
        ON user_mistakes(user_id)
    ''') 
    
   #speaking module
    c.execute('''
        CREATE TABLE IF NOT EXISTS speaking_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vocab_word TEXT,
            sentence TEXT,
            transcript TEXT,
            score REAL,                    
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS story_vocab (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        story_id INTEGER NOT NULL,
        word_ar TEXT,
        word_en TEXT,
        transliteration TEXT,
        FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
        UNIQUE(story_id, word_ar, word_en)
    )
''')
    
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_story_vocab_story
    ON story_vocab(story_id)
''')
   #listening module
   
    c.execute('''
        CREATE TABLE IF NOT EXISTS listening_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vocab_word TEXT NOT NULL,
            user_answer TEXT,
            is_correct BOOLEAN DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_listening_user ON listening_attempts(user_id)')
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_FILE}")



def get_current_user():
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    return None


def require_login():
    user = get_current_user()
    if not user:
        st.warning("Please login first to continue.")
        st.stop()
    return user["id"], user["level"]
    
##--- Vocab module helper functions --- ###

@st.cache_data
def load_vocab_data():
    try:
        with open("data/vocabulary_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading vocab data: {e}")
        return {}

def mark_word_mastered(user_id, word_ar, category, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE vocab_mastery 
        SET is_mastered = TRUE
        WHERE user_id = ? AND word_ar = ?
    ''', (user_id, word_ar))
    conn.commit()
    conn.close()

def mark_word_correct(user_id, word_ar):
    # iwould need this function for two things, to save if word is corrected, and if>3 then it will auto master this word
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE vocab_mastery 
        SET times_correct = times_correct + 1, last_reviewed = ?
        WHERE user_id = ? AND word_ar = ? ''', (datetime.now().isoformat(), user_id, word_ar))
    c.execute('SELECT times_correct FROM vocab_mastery WHERE user_id = ? AND word_ar = ?', (user_id, word_ar))
    
    row = c.fetchone()
    if row and row['times_correct'] >= 3:
        c.execute('UPDATE vocab_mastery SET is_mastered = TRUE WHERE user_id = ? AND word_ar = ?', (user_id, word_ar))
    conn.commit()
    conn.close()

def mark_word_not_mastered(user_id, word_ar): # i have comment or remove this this maybe we did not need will see after done with module
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE vocab_mastery 
        SET is_mastered = FALSE, last_reviewed = ?
        WHERE user_id = ? AND word_ar = ?
    ''', (datetime.now().isoformat(), user_id, word_ar))
    conn.commit()
    conn.close()

def get_mastered_words_count(user_id, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM vocab_mastery 
        WHERE user_id = ? AND level = ? AND is_mastered = TRUE ''', (user_id, level))
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_word_learned(user_id, word_ar, category, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO vocab_mastery 
        (user_id, word_ar, category, level, is_learned, marked_learned_at)
        VALUES (?, ?, ?, ?, TRUE, ?) ''', (user_id, word_ar, category, level, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def mark_word_not_learned(user_id, word_ar,category=None, level=None):
    conn = get_connection()
    c = conn.cursor()
    # check if word exists
    c.execute("""
        SELECT id FROM vocab_mastery
        WHERE user_id=? AND word_ar=? """, (user_id, word_ar))
    exists = c.fetchone()
    if exists:
        c.execute("""
            UPDATE vocab_mastery
            SET is_learned = FALSE, last_reviewed = ?
            WHERE user_id=? AND word_ar=? """, (datetime.now().isoformat(), user_id, word_ar))
    else:
        c.execute("""
            INSERT INTO vocab_mastery
            (user_id, word_ar, category, level, is_learned, last_reviewed)
            VALUES (?, ?, ?, ?, FALSE, ?) """, (user_id, word_ar, category, level, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_total_words_in_level(level):
    vocab_data = load_vocab_data()  
    if level not in vocab_data:
        return 0
    total = 0
    for category in vocab_data[level].values():
        total += len(category)
    return total

def get_learned_words(user_id, level):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT word_ar, category FROM vocab_mastery 
        WHERE user_id = ? AND level = ? AND is_learned = TRUE
    ''', (user_id, level))
    words = c.fetchall()
    conn.close()
    return words

def get_words_to_review(user_id, category, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT word_ar FROM vocab_mastery 
        WHERE user_id = ? AND category = ? AND level = ? 
        AND (is_learned = FALSE OR is_mastered = FALSE OR last_reviewed < ?)
        ORDER BY last_reviewed ASC
    ''', (user_id, category, level, (datetime.now() - timedelta(days=3)).isoformat()))
    words_ar = [row['word_ar'] for row in c.fetchall()]
    conn.close()
    return words_ar

def count_words_to_review(user_id, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) FROM vocab_mastery 
        WHERE user_id = ? AND level = ? AND is_learned = FALSE """, (user_id, level))
    review_count = c.fetchone()[0]
    conn.close()
    return review_count
    
def is_word_learned(user_id, arabic_word):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT is_learned FROM vocab_mastery 
        WHERE user_id = ? AND word_ar = ? ''', (user_id, arabic_word))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

### ---- Module: Writing ------###

### guided writing part ###
def save_writing_attempt(user_id, vocab_word, sentence_en, correct_sentence, user_answer, is_correct):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO writing_attempts
        (user_id, vocab_word, sentence_en, correct_sentence, user_answer, is_correct)
        VALUES (?, ?, ?, ?, ?, ?) """, (user_id, vocab_word, sentence_en, correct_sentence, user_answer, is_correct))
    conn.commit()
    conn.close()

def get_writing_sessions_count(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(DISTINCT DATE(created_at)) 
        FROM writing_attempts 
        WHERE user_id = ? ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    
    return count if count is not None else 0


def get_writing_exercises_count(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM writing_attempts WHERE user_id = ? ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_writing_accuracy(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            COUNT(CASE WHEN is_correct = 1 THEN 1 END) as correct,
            COUNT(*) as total
        FROM writing_attempts 
        WHERE user_id = ? ''', (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row and row['total'] > 0:
        accuracy = int((row['correct'] / row['total']) * 100)
        return accuracy, row['correct'], row['total']
    return 0, 0, 0
    
### free writing part ###
def save_user_mistake(user_id, original, correct, explanation, module="writing"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM user_mistakes
        WHERE user_id=? AND original_word=? AND correct_word=? """, (user_id, original, correct))
    mistakes = cursor.fetchone()

    if not mistakes:
        cursor.execute("""
            INSERT INTO user_mistakes
            (user_id, original_word, correct_word, explanation, module)
            VALUES (?, ?, ?, ?, ?) """, (user_id, original, correct, explanation, module))
        conn.commit()
    conn.close()

def get_user_mistakes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    # i dont know if i should add it more than 10 the limit like make it 15 or 20, depend son how?
    cursor.execute("""
        SELECT id, original_word, correct_word, explanation, module
        FROM user_mistakes
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 10 """, (user_id,))
    mistakes = cursor.fetchall()
    conn.close()
    return mistakes

def delete_user_mistake(mistake_id):
    # i have deleted as a method because i would not use it as another thing? so like whats the point so when learned i will delyte
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM user_mistakes
        WHERE id=? """, (mistake_id,))
    conn.commit()
    conn.close()


# module: reading 
def save_story(user_id, title, content, topic, story_type, level):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO stories (user_id, title, content, topic, story_type, level, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?) ''', (user_id, title, content, topic, story_type, level, datetime.now().isoformat()))
    conn.commit()
    story_id = c.lastrowid
    conn.close()
    return story_id
    
def save_vocab(story_id, vocab_list):
    conn = get_connection()
    c = conn.cursor()
    for vocab in vocab_list:
        c.execute("""
            INSERT INTO story_vocab (story_id, word_ar, word_en, transliteration)
            VALUES (?, ?, ?, ?)
        """, (
            story_id,
            vocab["arabic"],
            vocab["english"],
            vocab["transliteration"]
        ))
    conn.commit()
    conn.close()

def get_story_vocab(story_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT word_ar, word_en, transliteration
        FROM story_vocab
        WHERE story_id = ?
    """, (story_id,))
    rows = c.fetchall()
    conn.close()

    return [{"arabic": r[0],  "english": r[1],  "transliteration": r[2] } for r in rows ]
    
def get_user_stories(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
    SELECT id, title, content, topic, story_type, created_at, is_read 
    FROM stories 
    WHERE user_id = ? 
    ORDER BY created_at DESC ''', (user_id,))
    
    stories = c.fetchall()
    conn.close()
    return stories

def mark_story_as_read(user_id, story_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE stories 
        SET is_read = TRUE 
        WHERE id = ? AND user_id = ? ''', (story_id, user_id))
    
    conn.commit()
    conn.close()

def save_quiz_score(user_id, story_id, score, total_questions):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO quiz_scores (user_id, story_id, score, total_questions, taken_at)
        VALUES (?, ?, ?, ?, ?) ''', (user_id, story_id, score, total_questions, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_read_stories_count(user_id):
    """Count how many stories the user has marked as read"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM stories 
        WHERE user_id = ? AND is_read = TRUE
    ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count


# conversation moduleee
def save_conversation_message(user_id, scenario, role, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute(""" INSERT INTO conversations (user_id, scenario, role, message)
        VALUES (?, ?, ?, ?)
    """, (user_id, scenario, role, message))
    conn.commit()
    conn.close()

def load_conversation_history(user_id, scenario, limit=20):
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""SELECT role, message FROM conversations
        WHERE user_id = ?
        AND scenario = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, scenario, limit))
    
    rows = c.fetchall()
    conn.close()

    rows.reverse()
    messages = []

    for role, message in rows:
        messages.append({ "role": role, "content": message })
    return messages

def clear_conversation_history(user_id, scenario):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        DELETE FROM conversations
        WHERE user_id = ?
        AND scenario = ?
    """, (user_id, scenario))

    conn.commit()
    conn.close()

def save_conversation_memory(user_id, memory):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO conversation_memory (user_id, memory)
        VALUES (?, ?) """, (user_id, memory))
    conn.commit()
    conn.close()

def load_conversation_memory(user_id, limit=5):

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT memory
        FROM conversation_memory
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))

    rows = c.fetchall()
    conn.close()

    rows.reverse()
    return [row[0] for row in rows]

def clear_conversation_memory(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        DELETE FROM conversation_memory
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def get_conversation_days(user_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(DISTINCT DATE(created_at))
        FROM conversations
        WHERE user_id = ?
        AND role = 'user'
    """, (user_id,))

    count = c.fetchone()[0]
    conn.close()
    return count if count else 0

def get_conversation_scenarios(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(DISTINCT scenario)
        FROM conversations
        WHERE user_id = ?
        AND role = 'user' """, (user_id,))

    count = c.fetchone()[0]
    conn.close()
    
    return count if count else 0


def save_speaking_attempt(user_id, vocab_word, sentence, transcript, score):
    #Save one speaking practice attempt and how much it score in the table
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO speaking_attempts 
        (user_id, vocab_word, sentence, transcript, score)
        VALUES (?, ?, ?, ?, ?) ''', (user_id, vocab_word, sentence, transcript, score))
    conn.commit()
    conn.close()
    

def get_speaking_sessions_count(user_id):
    #return how many days user practiced speaking
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(DISTINCT DATE(created_at)) 
        FROM speaking_attempts 
        WHERE user_id = ? ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count if count is not None else 0

def get_speaking_accuracy(user_id):
    #return average pronunciation score (0-100%)
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT AVG(score) as avg_score, COUNT(*) as total
        FROM speaking_attempts 
        WHERE user_id = ? ''', (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row['total'] > 0:
        accuracy = int(row['avg_score'] * 100)
        return accuracy, row['total']
    return 0, 0

#listening module
def save_listening_attempt(user_id, vocab_word, user_answer, is_correct):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO listening_attempts 
        (user_id, vocab_word, user_answer, is_correct, created_at)
        VALUES (?, ?, ?, ?, ?) ''', (user_id, vocab_word, user_answer, is_correct, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def listening_sessions_count(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(DISTINCT DATE(created_at))
        FROM listening_attempts
        WHERE user_id = ?
    ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count if count is not None else 0


def listening_exercises_count(user_id):
    """Count total listening exercises attempted"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COUNT(*) FROM listening_attempts WHERE user_id = ?
    ''', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count


def listening_accuracy(user_id):
    """Return average listening accuracy and total attempts"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            COUNT(CASE WHEN is_correct = 1 THEN 1 END) as correct,
            COUNT(*) as total
        FROM listening_attempts
        WHERE user_id = ?
    ''', (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row and row['total'] > 0:
        accuracy = int((row['correct'] / row['total']) * 100)
        return accuracy, row['total']
    return 0, 0

#how to unlock next level, here alogic that i simply did:
def unlock_next_level(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT level FROM users WHERE id = ?", (user_id,))
    
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    current_level = row[0]

    if current_level == "B1":
        conn.close()
        return None  #since i only have 3 levels and B1 is the highest
    
    # Vocab
    learned_count = len(get_learned_words(user_id, current_level))
    mastered_count = get_mastered_words_count(user_id, current_level)
    total_words = get_total_words_in_level(current_level)
    learned_percent = (learned_count / total_words * 100) if total_words > 0 else 0
    mastered_percent = (mastered_count / total_words * 100) if total_words > 0 else 0
    # Reading 
    c.execute("SELECT COUNT(*) FROM stories WHERE user_id = ? AND is_read = TRUE", (user_id,))
    stories_completed = c.fetchone()[0]
    # Speaking 
    speaking_sessions = get_speaking_sessions_count(user_id)
    # Writing  
    writing_exercises = get_writing_exercises_count(user_id)
    # Conversation
    conversation_sessions = get_conversation_days(user_id)
    unique_scenarios = get_conversation_scenarios(user_id)
    listening_sessions = listening_sessions_count(user_id)
    
    next_level = None
    
    if current_level == "A1":
        if (learned_percent >= 70 and mastered_percent >= 30 and stories_completed >= 8 and speaking_sessions >= 8 and
            writing_exercises >= 12 and  conversation_sessions >= 5 and unique_scenarios >= 2 and listening_sessions >= 8):
            next_level = "A2"
            
    elif current_level == "A2":
        if (learned_percent >= 80 and mastered_percent >= 50 and stories_completed >= 12 and speaking_sessions >= 14 and
            writing_exercises >= 18 and conversation_sessions >= 10 and unique_scenarios >= 7 and listening_sessions >= 14):
            next_level = "B1"  
    if next_level:
        return next_level
    conn.close()
    return None


def get_level_progress(user_id, current_level):
    # Vocabulary Progress
    learned_count = len(get_learned_words(user_id, current_level))
    mastered_count = get_mastered_words_count(user_id, current_level)
    total_words = get_total_words_in_level(current_level)
    learned_p = (learned_count / total_words * 100) if total_words > 0 else 0
    mastered_p = (mastered_count / total_words * 100) if total_words > 0 else 0
    
    # Reading and speaking and writing and conversation
    stories_completed = get_read_stories_count(user_id)
    speaking_sessions = get_speaking_sessions_count(user_id)
    writing_exercises = get_writing_exercises_count(user_id)
    conversation_sessions = get_conversation_days(user_id)
    unique_scenarios = get_conversation_scenarios(user_id)

    if current_level == "A1":
        learned_progress = min(100, learned_p / 70 * 100)
        mastered_progress = min(100, mastered_p / 30 * 100)
        reading_progress = min(100, stories_completed / 8 * 100)
        speaking_progress = min(100, speaking_sessions / 8 * 100)
        writing_progress = min(100, writing_exercises / 12 * 100)

        conversation_progress = (
            min(100, conversation_sessions / 5 * 100) * 0.7 +
            min(100, unique_scenarios / 2 * 100) * 0.3
        )

        listening_sessions = listening_sessions_count(user_id)

        overall = (
            learned_progress * 0.35 +
            mastered_progress * 0.15 +
            reading_progress * 0.20 +
            speaking_progress * 0.15 +
            writing_progress * 0.10 +
            conversation_progress * 0.05 +
            (listening_sessions / 8 * 100) * 0.05
            
        )

    elif current_level == "A2":
        learned_progress = min(100, learned_p / 80 * 100)
        mastered_progress = min(100, mastered_p / 50 * 100)

        reading_progress = min(100, stories_completed / 12 * 100)
        speaking_progress = min(100, speaking_sessions / 14 * 100)
        writing_progress = min(100, writing_exercises / 18 * 100)

        conversation_progress = (
            min(100, conversation_sessions / 10 * 100) * 0.7 +
            min(100, unique_scenarios / 7 * 100) * 0.3
        )

        overall = (
            learned_progress * 0.35 +
            mastered_progress * 0.20 +
            reading_progress * 0.10 +
            speaking_progress * 0.15 +
            writing_progress * 0.10 +
            conversation_progress * 0.10 +
            (listening_sessions / 14 * 100) * 0.05
        )

    else:
        overall = 100

    return min(100, max(0, overall))

if __name__ == "__main__":
    init_db()

    
