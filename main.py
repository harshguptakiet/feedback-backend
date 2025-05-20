from fastapi import FastAPI, Form
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import csv
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# DB Setup
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
            rating INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# FastAPI App
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
    rating: int

@app.post("/submit")
def submit_feedback(feedback: Feedback):
    sentiment_score = analyzer.polarity_scores(feedback.feedback)['compound']
    label = "positive" if sentiment_score > 0.05 else "negative" if sentiment_score < -0.05 else "neutral"

    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (name, event, text, sentiment, rating, date) VALUES (?, ?, ?, ?, ?, ?)",
                (feedback.name, feedback.event, feedback.feedback, label, feedback.rating, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    return {"status": "success", "sentiment": label}

@app.get("/admin/summary")
def get_summary():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment")
    summary = dict(cur.fetchall())
    cur.execute("SELECT name, event, text, sentiment, rating, date FROM feedback")
    feedback = cur.fetchall()
    cur.execute("SELECT DISTINCT event FROM feedback")
    events = [row[0] for row in cur.fetchall()]
    conn.close()
    return {"summary": summary, "feedback": feedback, "events": events}

@app.get("/admin/export")
def export_csv():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT name, event, text, sentiment, rating, date FROM feedback")
    rows = cur.fetchall()
    with open("feedback.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Event", "Feedback", "Sentiment", "Rating", "Date"])
        writer.writerows(rows)
    return FileResponse("feedback.csv", media_type='text/csv', filename="feedback.csv")

@app.get("/admin/wordcloud")
def generate_wordcloud():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT text FROM feedback")
    text_data = " ".join(row[0] for row in cur.fetchall())
    wordcloud = WordCloud(width=800, height=400).generate(text_data)
    wordcloud.to_file("wordcloud.png")
    return FileResponse("wordcloud.png", media_type="image/png")

@app.get("/")
def root():
    return {"message": "Backend running"}
