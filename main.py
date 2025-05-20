from fastapi import FastAPI
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sqlite3

app = FastAPI()
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
    cur.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY,
        name TEXT,
        event TEXT,
        feedback TEXT,
        sentiment TEXT)''')
    cur.execute("INSERT INTO feedback (name, event, feedback, sentiment) VALUES (?, ?, ?, ?)",
                (feedback.name, feedback.event, feedback.feedback, label))
    conn.commit()
    conn.close()

    return {"status": "success", "sentiment": label}

@app.get("/admin/summary")
def get_summary():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment")
    summary = dict(cur.fetchall())
    conn.close()
    return {"summary": summary}

@app.get("/")
def root():
    return {"message": "Backend running!"}
