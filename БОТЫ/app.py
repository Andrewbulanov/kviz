import os, sys, threading, webbrowser
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session

# Удобный хелпер на будущее (если будешь собирать в .exe — работать тоже будет)
def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.secret_key = "barinov-show-secret"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# --- Defaults ---
def default_teams():
    return [{"name": f"Команда {i+1}", "score": 1000, "bet": 0} for i in range(4)]

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def setup():
    if "teams" not in session:
        session["teams"] = default_teams()
    if "topics" not in session:
        session["topics"] = []
    if "current_round" not in session:
        session["current_round"] = 0

    teams = session["teams"]
    topics = session["topics"]

    if request.method == "POST":
        if "add_team" in request.form:
            if len(teams) < 6:
                teams.append({"name": f"Команда {len(teams)+1}", "score": 1000, "bet": 0})
        elif "remove_team" in request.form:
            if len(teams) > 2:
                teams.pop()
        elif "start_game" in request.form:
            updated = []
            for i in range(len(teams)):
                name = (request.form.get(f"name_{i}", f"Команда {i+1}") or "").strip() or f"Команда {i+1}"
                try:
                    score = int(request.form.get(f"score_{i}", teams[i]["score"]))
                except ValueError:
                    score = teams[i]["score"]
                updated.append({"name": name, "score": score, "bet": 0})
            session["teams"] = updated

            topics_text = (request.form.get("topics", "") or "").strip()
            topics = [t.strip() for t in topics_text.splitlines() if t.strip()]
            session["topics"] = topics
            session["current_round"] = 0
            # Если темы есть — сначала экран темы, иначе сразу игра
            return redirect(url_for("round_screen") if topics else url_for("game"))

        session["teams"] = teams
        session.modified = True

    return render_template("setup.html", teams=teams, topics="\n".join(topics))

@app.route("/round")
def round_screen():
    topics = session.get("topics", [])
    current = session.get("current_round", 0)
    if not topics or current >= len(topics):
        return redirect(url_for("game"))
    topic = topics[current]
    # На этом экране просто показываем тему; кнопка «Далее» ведёт в /game
    return render_template("round.html", topic=topic, current=current + 1, total=len(topics))

@app.route("/game", methods=["GET", "POST"])
def game():
    teams = session.get("teams", [])
    correct = session.get("correct_answer", "")

    if request.method == "POST":
        # 1) Считываем ставки и ограничиваем их имеющимися очками
        for i in range(len(teams)):
            try:
                bet = int(request.form.get(f"bet_{i}", teams[i].get("bet", 0)))
            except ValueError:
                bet = 0
            bet = max(0, min(bet, teams[i]["score"]))  # ставка ≤ очки
            teams[i]["bet"] = bet

        # 2) Применяем формулу: вычесть |ставка - правильный ответ|
        correct_val = request.form.get("correct_answer", "").strip()
        if correct_val != "":
            try:
                correct_int = int(correct_val)
                for t in teams:
                    diff = abs(t["bet"] - correct_int)
                    t["score"] = max(0, t["score"] - diff)
                session["correct_answer"] = correct_int
            except ValueError:
                pass  # игнорируем некорректный ввод

        session["teams"] = teams
        session.modified = True

        # 3) Проверяем победителя: если жива ровно 1 команда с очками > 0
        alive = [t for t in teams if t["score"] > 0]
        if len(alive) == 1:
            return redirect(url_for("game", winner=alive[0]["name"]))

        return redirect(url_for("game"))

    winner = request.args.get("winner")
    return render_template("game.html", teams=teams, correct_answer=correct, winner=winner)

@app.route("/next_round", methods=["POST"])
def next_round():
    topics = session.get("topics", [])
    current = session.get("current_round", 0)
    teams = session.get("teams", [])

    # Сбрасываем ставки и правильный ответ (очки сохраняем)
    for t in teams:
        t["bet"] = 0
    session["teams"] = teams
    session["correct_answer"] = ""
    session.modified = True

    # Если тем нет — сразу продолжаем игру
    if not topics:
        return redirect(url_for("game"))

    # Если темы есть — увеличиваем индекс и идём на экран новой темы (если есть ещё темы)
    session["current_round"] = current + 1
    if session["current_round"] < len(topics):
        return redirect(url_for("round_screen"))
    # Тем больше нет — идём играть без экрана темы
    return redirect(url_for("game"))

@app.route("/reset")
def reset():
    for key in ["teams", "topics", "current_round", "correct_answer"]:
        session.pop(key, None)
    return redirect(url_for("setup"))

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    # Авто-открытие браузера
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)
