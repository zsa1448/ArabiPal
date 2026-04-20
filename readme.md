# ArabiPal: AI Arabic Learning Companion
## Project Title

**ArabiPal** is an interactive AI-powered web-based platform that helps beginners and intermediate learners & master Modern Standard Arabic (MSA) through integrated skill practice, real-time feedback, and automatic level progression (A1 → A2 → B1).

## Problem Statement & Motivation

Many Arabic learners, face challenges with existing Arabic langauge apps:

- heavily on passive vobaulary memorization
- Skills are taught in **isolation**
- There is no clear, structured progression between levels so learners don’t know when they are truly ready to advance.
  
As a result, many Arabic learners get frustrated, or struggle to form their vocabulary usage in real communication.

As a motivation, **ArabiPal** was built to solve these problems by creating a cohesive, intelligent learning experience that connects all language skills and provides personalized, real-time feedback.

## Dataset description & sources

- **Vocabulary Dataset**: Custom JSON file containing categorized words and phrases per CEFR level 
- **Alphabet Dataset**: 28 Arabic letters with their different forms (initial, medial, final) and high-quality (TTS-1) pronunciation audio .
- **Dynamic Content**: Generated in real-time using GPT-4o-mini for:
- **User Data**: Stored in SQLite

## Model Architecture

**Hybrid Architecture** (LLM + Rule-based):

- **Frontend**: Streamlit (multi-page web app)
- **AI Core**: OpenAI GPT-4o-mini (used for content generation like questions, stories corrections, exercises, personalized feedback)
- **Speech Processing**:
  - Whisper-1 / DeepGram Nova-3 for speech-to-text
  - TTS-1 (shimmer voice)
- **Database**: SQLite DB to store users and data
- **Progress Engine**: Custom rule-based logic that trackes user learning journey and their progress:

## Evaluation Results 
ArabiPal approach to evaluate success:
- learning engagement across all modules 
- skill improvements & reduction in mistakes
- real ability to hold conversation
- Level progression 
- 
## How to Run the Project                     

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
streamlit run app.py
```
## Limitations
1. The speaking module is a simplidied pronounciation evaluation, it evaluates user performance using:
Speech-to-text transcription
Word-level similarity scoring
Basic phoneme-aware feedback for difficult Arabic sounds
2. limited level scope coverage (beginner and intermediate only)

## future work
1. Improve pronunciation scoring using advanced dedicated models (phoneme-level)
2. Include more curated learning resources (grammar explanations, videos, articles, books)
3. Add a comprehensive Progress History dashboard with trends and statistics over time

## Video Demo 
https://canva.link/e9t1p5c1zieek0s

   

   







