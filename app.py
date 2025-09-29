from flask import Flask, request, jsonify, send_file, redirect, url_for, render_template
import csv
import pandas as pd
from fpdf import FPDF
import sqlite3
from datetime import datetime
from github_service import (
    get_authenticated_user,
    get_repositories_by_username,
    get_collaborators,
    add_collaborator,
    remove_collaborator,
    update_collaborator_permission,
    process_bulk_action,
    get_collaborators_report
)

# ✅ Initialize Flask app
app = Flask(__name__)

# ---------------- Database Setup ----------------

def init_db():
    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    # Email Mapping Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS email_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        username TEXT
    )
    """)
    # Logs Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        action TEXT,
        owner TEXT,
        repo TEXT,
        username TEXT,
        permission TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_action(action, owner, repo, username, permission, status):
    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, action, owner, repo, username, permission, status) VALUES (?,?,?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, owner, repo, username, permission, status))
    conn.commit()
    conn.close()

def get_username_from_email(email):
    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    c.execute("SELECT username FROM email_mapping WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

init_db()

# ---------------- Web Dashboard ----------------

@app.route("/")
def home():
    return "✅ GitHub Access Management App is Running!"

@app.route("/dashboard")
def dashboard():
    # This will render templates/dashboard.html
    return render_template("dashboard.html")

# ---------------- Email Mapping Management ----------------

@app.route("/add_mapping", methods=["POST"])
def add_mapping():
    data = request.get_json()
    email = data.get("email")
    username = data.get("username")

    if not email or not username:
        return {"error": "Email and Username are required."}

    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO email_mapping (email, username) VALUES (?, ?)", (email, username))
    conn.commit()
    conn.close()
    return {"message": f"✅ Mapping added: {email} → {username}"}

@app.route("/get_mappings")
def get_mappings():
    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    c.execute("SELECT email, username FROM email_mapping")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"email": row[0], "username": row[1]} for row in rows])

# ---------------- Logs Management ----------------

@app.route("/get_logs")
def get_logs():
    conn = sqlite3.connect("access_manager.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, action, owner, repo, username, permission, status FROM logs ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    logs = [
        {
            "timestamp": row[0],
            "action": row[1],
            "owner": row[2],
            "repo": row[3],
            "username": row[4],
            "permission": row[5],
            "status": row[6]
        }
        for row in rows
    ]
    return jsonify(logs)

# ---------------- Core Features ----------------

@app.route("/user")
def user_details():
    return jsonify(get_authenticated_user())

@app.route("/search_email")
def search_email_route():
    email = request.args.get("email")
    if not email:
        return {"error": "Please provide an email."}

    username = get_username_from_email(email)
    if username:
        return {"email": email, "username": username, "status": "✅ Found in internal mapping"}
    else:
        return {"email": email, "username": None, "status": "❌ Not found in internal mapping. Add it manually."}

@app.route("/repos")
def list_repositories():
    username = request.args.get("username")
    if not username:
        return {"error": "Please provide a username."}
    return jsonify(get_repositories_by_username(username))

@app.route("/collaborators")
def list_collaborators():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    if not owner or not repo:
        return {"error": "Please provide both owner and repo."}
    return jsonify(get_collaborators(owner, repo))

# ---------------- Access Management ----------------

@app.route("/add_collaborator")
def add_collaborator_route():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    username = request.args.get("username")
    permission = request.args.get("permission", "push")

    if not owner or not repo or not username:
        return {"error": "Please provide owner, repo, and username."}

    result = add_collaborator(owner, repo, username, permission)
    log_action("add", owner, repo, username, permission, "success" if "✅" in str(result) else "failed")
    return jsonify(result)

@app.route("/remove_collaborator")
def remove_collaborator_route():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    username = request.args.get("username")

    if not owner or not repo or not username:
        return {"error": "Please provide owner, repo, and username."}

    result = remove_collaborator(owner, repo, username)
    log_action("remove", owner, repo, username, "", "success" if "✅" in str(result) else "failed")
    return jsonify(result)

@app.route("/modify_permission")
def modify_permission_route():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    username = request.args.get("username")
    permission = request.args.get("permission")

    if not owner or not repo or not username or not permission:
        return {"error": "Please provide owner, repo, username, and permission."}

    result = update_collaborator_permission(owner, repo, username, permission)
    log_action("modify", owner, repo, username, permission, "success" if "✅" in str(result) else "failed")
    return jsonify(result)

# ---------------- Bulk Management ----------------

@app.route("/bulk_preview", methods=["POST"])
def bulk_preview():
    file = request.files.get("file")
    if not file:
        return {"error": "Please upload a CSV file."}

    preview = []
    csv_reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())
    for row in csv_reader:
        preview.append({
            "username": row["username"],
            "action": row["action"],
            "permission": row.get("permission", "")
        })
    return jsonify({"preview": preview})

@app.route("/bulk_apply", methods=["POST"])
def bulk_apply():
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    file = request.files.get("file")

    if not owner or not repo or not file:
        return {"error": "Please provide owner, repo, and CSV file."}

    results = []
    csv_reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())
    for row in csv_reader:
        username = row["username"]
        permission = row.get("permission", "push")
        action = row["action"]
        result = process_bulk_action(owner, repo, username, permission, action)
        log_action(action, owner, repo, username, permission, "success" if "✅" in str(result) else "failed")
        results.append({"username": username, "result": result})
    return jsonify({"results": results})

# ---------------- Audit & Reporting ----------------

@app.route("/report_excel")
def report_excel():
    owner = request.args.get("owner")
    repo = request.args.get("repo")

    if not owner or not repo:
        return {"error": "Please provide owner and repo."}

    data = get_collaborators_report(owner, repo)
    if isinstance(data, dict) and "error" in data:
        return data

    df = pd.DataFrame(data)
    file_path = f"{repo}_access_report.xlsx"
    df.to_excel(file_path, index=False)
    return {"message": f"✅ Excel report generated: {file_path}"}

@app.route("/report_pdf")
def report_pdf():
    owner = request.args.get("owner")
    repo = request.args.get("repo")

    if not owner or not repo:
        return {"error": "Please provide owner and repo."}

    data = get_collaborators_report(owner, repo)
    if isinstance(data, dict) and "error" in data:
        return data

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Access Report for {repo}", ln=True, align="C")
    for user in data:
        pdf.cell(
            200, 10,
            txt=f"{user['username']} | Role: {user['role']} | Admin: {user['admin']} | Push: {user['push']} | Pull: {user['pull']}",
            ln=True
        )
    file_path = f"{repo}_access_report.pdf"
    pdf.output(file_path)
    return {"message": f"✅ PDF report generated: {file_path}"}

# ---------------- Debugging Helper ----------------

@app.route("/test_routes")
def test_routes():
    return jsonify({
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    })

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
