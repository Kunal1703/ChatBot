# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --------- NLP MODEL ----------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model not found. Run: python -m spacy download en_core_web_sm")
    raise

# --------- DB ----------
DB_FILE = "classroom.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    student_id INTEGER,
                    status TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    timestamp TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

def add_student(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students(name) VALUES(?)", (name,))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM students")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def mark_attendance(date, student_name, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM students WHERE name=?", (student_name,))
    row = c.fetchone()
    if row:
        c.execute("INSERT INTO attendance(date, student_id, status) VALUES(?,?,?)",
                  (date, row[0], status))
    conn.commit()
    conn.close()

def get_attendance(date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""SELECT s.name, a.status
                 FROM attendance a
                 JOIN students s ON s.id = a.student_id
                 WHERE a.date=?""", (date,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_feedback(text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO feedback(text, timestamp) VALUES(?,?)",
              (text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT text, timestamp FROM feedback")
    rows = [{"text": r[0], "timestamp": r[1]} for r in c.fetchall()]
    conn.close()
    return rows

# --------- APP STATE ----------
classroom_state = {
    "is_taking_attendance": False,
    "present_students": [],
    "current_question": None,        # {"q": "...", "a": "..."}
    "asked_questions": [],
    "waiting_for_play_more": False,  # quiz continue? yes/no
    "score": 0,
    "total_answered": 0,
    "quiz_questions": [
        ("What is the powerhouse of the cell?", "mitochondria"),
        ("What is 2 + 2 * 2?", "6"),
        ("Who wrote 'To Kill a Mockingbird'?", "harper lee"),
        ("What is the capital of France?", "paris"),
        ("How many days are in a year?", "365"),
        ("What is the largest planet in our solar system?", "jupiter"),
        ("Who wrote Romeo and Juliet?", "william shakespeare"),
        ("What is H2O?", "water"),
        ("What color is the sky?", "blue"),
    ],
}

# --------- INTENT ----------
def get_intent(text):
    doc = nlp(text.lower())
    # exact phrases first
    if "start quiz" in text.lower() or "quiz" in text.lower():
        return "start_quiz"
    if "take attendance" in text.lower() or "mark attendance" in text.lower():
        return "take_attendance"

    for token in doc:
        if token.lemma_ == "student" and any(t.lemma_ in ["add", "insert", "save"] for t in doc):
            return "add_students"
        if token.lemma_ == "student" and any(t.lemma_ in ["pick", "choose", "random"] for t in doc):
            return "get_random_student"
        if token.lemma_ == "timer":
            for ent in doc.ents:
                if ent.label_ == "CARDINAL":
                    return ("start_timer", ent.text)
            return ("start_timer", None)
        if token.lemma_ == "feedback":
            return "feedback"

    if any(t.lemma_ in ["help", "command"] for t in doc):
        return "help"
    return "unknown"

# --------- CHAT ----------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = (request.json.get("message", "") or "").strip()
    lo = user_message.lower()
    resp = ""

    # --- 1) If a quiz question is currently active, treat input as answer
    if classroom_state["current_question"] is not None:
        qobj = classroom_state["current_question"]
        correct = qobj["a"].lower().strip()
        classroom_state["total_answered"] += 1

        if correct in lo:
            classroom_state["score"] += 1
            resp = "✅ Correct! Well done."
        else:
            resp = f"❌ Incorrect. The correct answer is: <strong>{correct}</strong>."

        # mark asked, clear current
        classroom_state["asked_questions"].append(qobj["q"])
        classroom_state["current_question"] = None

        # ask to continue
        classroom_state["waiting_for_play_more"] = True

        

    # --- 2) If quiz is waiting for yes/no to continue
    if classroom_state["waiting_for_play_more"]:
        if lo in ["yes", "y"]:
            # pick unused question
            unused = [qa for qa in classroom_state["quiz_questions"]
                      if qa[0] not in classroom_state["asked_questions"]]
            if not unused:
                classroom_state["waiting_for_play_more"] = False
                score = classroom_state["score"]
                total = classroom_state["total_answered"]
                return jsonify({"response": f"🎉 No more questions left!<br>Final score: <strong>{score}/{total}</strong>"})
            q, a = random.choice(unused)
            classroom_state["current_question"] = {"q": q, "a": a}
            classroom_state["waiting_for_play_more"] = False
            return jsonify({"response": f"Here is your next question:<br><br><strong>{q}</strong>"})
        elif lo in ["no", "n"]:
            classroom_state["waiting_for_play_more"] = False
            score = classroom_state["score"]
            total = classroom_state["total_answered"]
            return jsonify({"response": f"👍 Okay, quiz ended.<br>Your final score: <strong>{score}/{total}</strong>"})
        else:
            # ignore other text while waiting yes/no for quiz
            return jsonify({"response": "Please reply with <strong>yes</strong> or <strong>no</strong>."})

    # --- 3) Attendance collection mode (explicitly started)
    if classroom_state["is_taking_attendance"]:
        classroom_state["is_taking_attendance"] = False

        present_names = [n.strip() for n in user_message.split(",") if n.strip()]
        all_students = get_all_students()
        classroom_state["present_students"] = []

        today = datetime.now().strftime("%Y-%m-%d")
        lower_present = {p.lower() for p in present_names}

        for s in all_students:
            if s.lower() in lower_present:
                classroom_state["present_students"].append(s)
                mark_attendance(today, s, "present")
            else:
                mark_attendance(today, s, "absent")

        absent = [s for s in all_students if s not in classroom_state["present_students"]]
        resp = f"Attendance complete. {len(classroom_state['present_students'])} present, {len(absent)} absent."
        if absent:
            resp += f"<br><br><strong>Absent:</strong> {', '.join(absent)}"
        else:
            resp += "<br><br>Perfect attendance today!"
        return jsonify({"response": resp})

    # --- 4) Normal intents
    intent_data = get_intent(lo)
    intent = intent_data[0] if isinstance(intent_data, tuple) else intent_data

    if intent == "add_students":
        names = [n.strip() for n in lo.replace("add students", "").split(",") if n.strip()]
        for n in names:
            add_student(n)
        resp = f"Students added: {', '.join(names)}" if names else "Please provide names, e.g., add students Alice, Bob."

    elif intent == "take_attendance":
        if not get_all_students():
            resp = "No students found. Add students first using: <em>add students Alice, Bob</em>."
        else:
            classroom_state["is_taking_attendance"] = True
            resp = "Okay, send a comma-separated list of <strong>present</strong> students for today."

    elif intent == "get_random_student":
        if not classroom_state["present_students"]:
            resp = "Please take attendance first so I know who is here."
        else:
            resp = f"Okay, let's hear from… <strong>{random.choice(classroom_state['present_students'])}</strong>!"

    elif intent == "start_quiz":
        # reset score only if starting fresh
        if not classroom_state["asked_questions"]:
            classroom_state["score"] = 0
            classroom_state["total_answered"] = 0
        # choose a question
        unused = [qa for qa in classroom_state["quiz_questions"]
                  if qa[0] not in classroom_state["asked_questions"]]
        if not unused:
            resp = "All questions already used. Type <em>reset quiz</em> to start over."
        else:
            q, a = random.choice(unused)
            classroom_state["current_question"] = {"q": q, "a": a}
            resp = f"Here is a quiz question:<br><br><strong>{q}</strong>"

    elif isinstance(intent_data, tuple) and intent_data[0] == "start_timer":
        minutes = intent_data[1]
        resp = f"Okay, starting a {minutes}-minute timer (simulated)." if minutes else \
               "Please specify minutes, e.g., <em>start timer for 5 minutes</em>."

    elif lo == "reset quiz":
        classroom_state["asked_questions"] = []
        classroom_state["current_question"] = None
        classroom_state["waiting_for_play_more"] = False
        classroom_state["score"] = 0
        classroom_state["total_answered"] = 0
        resp = "Quiz state has been reset."

    elif intent == "feedback":
        resp = "Sure, please type your feedback and I'll save it."

    elif intent == "help":
        resp = """Here are the commands I understand:
        <ul>
            <li><strong>add students Alice, Bob</strong> — add student names</li>
            <li><strong>take attendance</strong> — start attendance flow</li>
            <li><strong>start quiz</strong> — begin quiz</li>
            <li><strong>reset quiz</strong> — clear quiz progress</li>
            <li><strong>random student</strong> — pick a present student</li>
            <li><strong>start timer for X minutes</strong> — timer demo</li>
            <li><strong>feedback</strong> — give feedback</li>
        </ul>"""

    else:
        # Treat unknown free text as feedback
        add_feedback(user_message)
        resp = "✅ Thank you for your feedback! It has been saved."

    return jsonify({"response": resp})

# --------- EXTRA ENDPOINTS ----------
@app.route("/students", methods=["GET"])
def students():
    return jsonify({"students": get_all_students()})

@app.route("/feedback", methods=["GET"])
def feedback():
    return jsonify({"feedback": get_all_feedback()})

@app.route("/attendance/<date>", methods=["GET"])
def attendance(date):
    rows = get_attendance(date)
    return jsonify({"attendance": [{"student": r[0], "status": r[1]} for r in rows]})

# --------- RUN ----------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
