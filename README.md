# EduGenie SRMIST — AI Attendance & Quiz Bot (Prototype)

A lightweight classroom assistant that **marks attendance**, runs a **quick quiz** with a **yes/no continue flow**, and captures **feedback**, all in a simple web UI.

> **Pitch:** Ditch spreadsheets and manual roll-calls. One page, a few clicks, done.

---

## 🧩 Problem Statement

In fast‑paced classes, **taking attendance** eats time and breaks momentum. Teachers also need a **quick pulse on understanding** without preparing separate tools. Switching between apps (attendance sheet, quiz app, feedback form) costs time and focus.

**Goal:** Build a single, minimal tool that lets a teacher **mark attendance quickly**, **ask short quizzes** for engagement, and **log feedback**—with **zero setup** and **local‑only** data storage.

---

## 🚦 Current Progress Status

- ✅ Core features complete:
  - Add students
  - Mark attendance for today (present/absent auto‑computed)
  - Show today’s attendance stats
  - Start quiz → answer → **“Do you want another question? (yes/no)”** appears **only after each quiz question**
  - Save free‑text feedback
  - Simple frontend with buttons & chat area
- 🔜 Nice‑to‑have / pending:
  - Per‑student quiz history & CSV export
  - Question bank management (CRUD)
  - Authentication / roles
  - Mobile polish & richer chat bubbles
  - Error toasts and validation in frontend

---

## 💡 How the Prototype Solves It

- **One screen** for all actions (attendance, quiz, feedback).
- **Local database (SQLite)** ensures privacy and zero-dependency deployment.
- **Clear state separation**: attendance flow doesn’t leak “yes/no”; quiz is the only place that uses **yes/no continuation**.
- **Stateless frontend + simple REST** makes it easy to extend later (React, Next.js, etc.).

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask‑CORS, SQLite3
- **Frontend:** HTML, CSS, Vanilla JS (Fetch API), Font Awesome
- **Data:** SQLite file `classroom.db`
- **No external AI model** — deterministic, rule‑based logic for reliability in demos

---

## 📂 Repository Structure

```
.
├── app.py                   # Flask backend (attendance, quiz, feedback)
├── classroom.db             # SQLite DB (auto‑created)
├── index.html               # Frontend UI (buttons + chat)
├── screenshots/             # Screenshots here
│── screenshots/home.png
│── screenshots/quiz.png
│── screenshots/attendance.png
└── README.md
```

## ⚙️ Setup & Run (Local)

**Prereqs:** Python 3.10+

```bash
# 1) Clone and enter
git clone Kunal1703.git
cd C:\Users\kunal\Downloads\peroject\ruchuuu>

# 2) (Recommended) Create & activate a virtual env
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

# 3) Install deps
pip install flask flask-cors

# 4) Run backend (http://127.0.0.1:5000)
python app.py
```

### Serve the frontend
Option A — open `index.html` directly in your browser  
Option B — run a static server (prevents some CORS quirks):

```bash
# In the project root (serves at http://127.0.0.1:5500)
python -m http.server 5500
```

Then open: `http://127.0.0.1:5500/index.html`

> **Note:** The frontend expects the backend at `http://127.0.0.1:5000/chat`. If you change ports, update the fetch URL in `index.html`.

---

## 🧪 Using the App (Happy Path)

1. **Add students**  
   In the chat, type:  
   `add students Alice, Bob, Charlie`

2. **Mark attendance**  
   Click **Mark Attendance** → the bot asks for a comma‑separated list of **present** students.  
   Example reply: `Alice, Charlie`  
   (Absent are auto‑computed.)

3. **Start quiz**  
   Click **Start Quiz** → you’ll see a question.  
   - Answer it (e.g., `6`) → bot checks and **then asks**:  
     `Do you want another question? (yes/no)`  
   - Reply `yes` for the next question, `no` to finish (score shown).  
   **Only the quiz** uses this yes/no prompt.

4. **Attendance stats**  
   Click **Stats** to view today’s students counts.

5. **Feedback**  
   Click **Feedback** → type your message → it’s saved locally.

---

## 🔌 API (for reference)

### `POST /chat`
```json
{ "message": "start quiz" }
```
**Response**
```json
{ "response": "Here is a quiz question: ..." }
```

### `GET /students`
Returns all student names.

### `GET /feedback`
Returns saved feedback entries.

### `GET /attendance/<YYYY-MM-DD>`
Returns attendance records for the given date.

---

## 🗃️ Data Model (SQLite)

- **students**: `id (PK)`, `name (UNIQUE)`  
- **attendance**: `id (PK)`, `date`, `student_id (FK)`, `status ('present'|'absent')`  
- **feedback**: `id (PK)`, `text`, `timestamp`

---

## 🖼️ Screenshots (Add before submission)

> Put images in `./screenshots/` and keep file names short.

| Home | Quiz | Attendance |
|---|---|---|
| ![Home](screenshots/home.png) | ![Quiz](screenshots/quiz.png) | ![Attendance](screenshots/attendance.png) |

---

## 🗺️ Roadmap

- CSV export for attendance & feedback
- Per‑student quiz analytics
- Editable question bank
- Authentication (teacher login)
- Better UI/UX (message bubbles, toasts, mobile responsive)

---

MIT — free to use and modify.

---

## 👥 Contributors

- Kunal Panwar (Backend Developer)
- Ruchi Kumari (Frontend Developer)
