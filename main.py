from fastapi import FastAPI
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

def init_db():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            event TEXT,
            text TEXT,
            sentiment TEXT,
            score REAL,
            pos REAL,
            neu REAL,
            neg REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = SentimentIntensityAnalyzer()

class Feedback(BaseModel):
    name: str
    event: str
    feedback: str

@app.post("/submit")
def submit_feedback(feedback: Feedback):
    scores = analyzer.polarity_scores(feedback.feedback)
    compound = scores['compound']
    label = "positive" if compound > 0.05 else "negative" if compound < -0.05 else "neutral"

    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO feedback (name, event, text, sentiment, score, pos, neu, neg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (feedback.name, feedback.event, feedback.feedback, label,
          compound, scores['pos'], scores['neu'], scores['neg']))
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "sentiment": label,
        "details": scores
    }

@app.get("/admin/summary")
def get_summary():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment")
    summary = dict(cur.fetchall())

    cur.execute("SELECT name, event, text, sentiment, score, pos, neu, neg FROM feedback")
    feedbacks = cur.fetchall()

    conn.close()
    return {"summary": summary, "feedback": feedbacks}
