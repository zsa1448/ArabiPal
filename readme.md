# ArabiPal: AI Arabic Learning Companion

**An intelligent web-based tutor for learning Modern Standard Arabic (MSA)**

## Project Title

**ArabiPal** is an interactive AI-powered web-based platform that helps beginners and intermediate learners & master Modern Standard Arabic (MSA) through integrated skill practice, real-time feedback, and automatic level progression (A1 → A2 → B1).

## Problem Statement & Motivation

Many Arabic learners, face challenges with existing Arabic langauge apps:

- Most apps focus heavily on passive vobaulary memorization but offer limited active practice in other skills like conversation, speaking, writing, and reading.
- Skills (vocabulary, reading, speaking, writing, conversation) are taught in **isolation**
- Feedback on pronunciation and grammar is either missing or not very helpful.
- There is no clear, structured progression between levels (A1 → A2 → B1), so learners don’t know when they are truly ready to advance.
  
As a result, many Arabic learners get frustrated, lose motivation, repeat mistakes, or struggle to form their vocabulary usage in real communication.

As a motivation, **ArabiPal** was built to solve these problems by creating a cohesive, intelligent learning experience that connects all language skills and provides personalized, real-time feedback.

## Dataset description & sources

- **Vocabulary Dataset**: Custom JSON file containing categorized words and phrases per CEFR level (A1, A2, B1) with Arabic text, English translation, and transliteration.
- **Alphabet Dataset**: 28 Arabic letters with their different forms (initial, medial, final) and high-quality (TTS-1) pronunciation audio .
- **Dynamic Content**: Generated in real-time using GPT-4o-mini for:
  - Short stories (Reading Lab)
  - Conversation responses and role-play scenarios
  - Writing exercises and grammar corrections
  - Comprehension quiz questions
  - speaking exercices
- **User Data**: Stored in SQLite (`tutor.db`) including user progress, learned/mastered words, stories read, practice sessions, and mistakes.
- 
No large pre-existing dataset was used — the system relies on a curated vocabulary base + LLM-generated content guided by careful prompt engineering.

## Model Architecture

**Hybrid Architecture** (LLM + Rule-based):

- **Frontend**: Streamlit (multi-page web app)
- **AI Core**: OpenAI GPT-4o-mini (used for content generation like questions, stories corrections, exercises, personalized feedback)
- **Speech Processing**:
  - Whisper-1 / DeepGram Nova-3 for speech-to-text
  - TTS-1 (shimmer voice) + pre-recorded MP3 files for accurate letter pronunciation
- **Database**: SQLite DB to store users, conversation history & memory, spekaing attempts, writing attempts, user mistakes, stories & comprehension scores
- **Progress Engine**: Custom rule-based logic that trackes user learning journey and their progress:
- Mastery Logic: Manual “Learned” status + automatic “Mastered” status (after 3 correct quiz answers)
- Spaced Repetition: Prioritizes words that need review in Vocabulary Lab
- Cross-Module Integration: Vocabulary learned in one module becomes available in Speaking, Writing, and Reading
- Level Progression System: Automatic unlocking from A1 → A2 → B1 based on multi-skill thresholds
- Progress Dashboard: Real-time overview of learned/mastered words, stories read, speaking sessions, writing accuracy, and overall level progress
- Persistent Storage: All progress is saved in SQLite database per user

**No fine-tuning** was performed. Instead, we relied on strong prompt engineering and structured outputs combined with rule-based systems for reliability.

## Key Achievements

- Successfully implemented **5 integrated modules** (Vocabulary, Reading, Speaking, Writing, Conversation)
- Built a working **automatic level progression system** based on measurable thresholds
- Achieved reliable real-time feedback on writing and basic speaking scoring & feedback 
- Created a clean, user-friendly interface 
- Demonstrated hybrid approach effectiveness: LLM for creativity + rules for structured progress

## Evaluation Results 
ArabiPal approach to evaluate success:
- learning engagement across all modules (vocabulary, speaking, writing, reading, conversation)
- skill improvements across all modules & reduction in mistakes
- real ability to hold conversation
- Level progression (A1 -> A2 -> B1)

**Key Insight**: Combining LLM flexibility with rule-based progress tracking proved more effective and reliable than using LLM alone.

## How to Run the Project

ArabiPal/
│
├── data/
│   └── vocabulary_data.json        
│
├── app.py
│                       
│── pages/                      
│       ├── alphabets.py
│       ├── Create_Account.py
│       ├── ConversationLab.py
│       ├── Flashcards.py
│       ├── VocabLab.py
│       ├── Home.py
|       ├── level_selection.py
│       ├── login.py
│       ├── SpeakingLab.py
│       ├── StoryLab.py
│       ├── WritingLab.py
├── db_setup.py
├── outputs/
│   ├── ArabiPalproject.pptx        
│   └── ArabiPaldemo.mp4                    
│
├── LICENSE                         
├── requirements.txt               
├── .gitignore                     
└── README.md                      

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ArabiPal
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```
### 5. Set up environment variables

Create a `.env` file in the root folder and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### 6. Run the application
```bash
streamlit run app.py
```
## Repo structure


## Limitations
1. The speaking module is a simplidied pronounciation evaluation, it evaluates user performance using:
Speech-to-text transcription
Word-level similarity scoring
Basic phoneme-aware feedback for difficult Arabic sounds
2. limited level scope coverage (beginner and intermediate only)

## future work
1. Improve pronunciation scoring using advanced dedicated models (phoneme-level)
2. Expand to advanced levels
3. Include more curated learning resources (grammar explanations, videos, articles, books)
4. Add a comprehensive Progress History dashboard with trends and statistics over time
5. deploy web application publically
   
## License
This is done for educational purpose
   
## Acknowledgments

- **OpenAI** for providing GPT-4o-mini, Whisper-1, and TTS-1 models that power the AI features.
- **Streamlit** for the easy-to-use web framework that made building the frontend fast and intuitive.
- **Bcrypt** for secure password hashing.








