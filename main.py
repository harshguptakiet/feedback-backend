from fastapi import FastAPI, Query
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
            sentiment TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can change this to just your frontend URL for better security
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
    sentiment_score = analyzer.polarity_scores(feedback.feedback)['compound']
    label = "positive" if sentiment_score > 0.05 else "negative" if sentiment_score < -0.05 else "neutral"

    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (name, event, text, sentiment) VALUES (?, ?, ?, ?)",
                (feedback.name, feedback.event, feedback.feedback, label))
    conn.commit()
    conn.close()

    return {"status": "success", "sentiment": label}

@app.get("/admin/summary")
def get_summary(event: str = Query(None)):
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()

    if event:
        cur.execute("SELECT sentiment, COUNT(*) FROM feedback WHERE event = ? GROUP BY sentiment", (event,))
        summary = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT name, event, text, sentiment FROM feedback WHERE event = ?", (event,))
    else:
        cur.execute("SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment")
        summary = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT name, event, text, sentiment FROM feedback")

    all_feedback = cur.fetchall()
    conn.close()
    return {"summary": summary, "feedback": all_feedback}

@app.get("/")
def root():
    return {"message": "Backend running!"}
