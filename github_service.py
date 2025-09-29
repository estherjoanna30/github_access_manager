# github_service.py
import os
import requests
from dotenv import load_dotenv

# ✅ Load token from .env instead of hardcoding
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# -------- Core Functions --------

def get_authenticated_user():
    response = requests.get(f"{BASE_URL}/user", headers=HEADERS)
    return _handle_response(response)

def search_user_by_email(email):
    response = requests.get(f"{BASE_URL}/search/users?q={email}+in:email", headers=HEADERS)
    return _handle_response(response)

def get_repositories_by_username(username):
    repos = []
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}/users/{username}/repos",
            headers=HEADERS,
            params={"page": page, "per_page": 100}
        )
        if response.status_code != 200:
            return _handle_response(response)
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_collaborators(owner, repo):
    collaborators = []
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}/repos/{owner}/{repo}/collaborators",
            headers=HEADERS,
            params={"page": page, "per_page": 100}
        )
        if response.status_code != 200:
            return _handle_response(response)
        data = response.json()
        if not data:
            break
        collaborators.extend(data)
        page += 1
    return collaborators

# -------- Access Management --------

def add_collaborator(owner, repo, username, permission="push"):
    url = f"{BASE_URL}/repos/{owner}/{repo}/collaborators/{username}"
    data = {"permission": permission}
    response = requests.put(url, headers=HEADERS, json=data)
    if response.status_code in [201, 204]:
        return {"message": f"✅ {username} added successfully with '{permission}' permission."}
    return _handle_response(response)

def remove_collaborator(owner, repo, username):
    url = f"{BASE_URL}/repos/{owner}/{repo}/collaborators/{username}"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 204:
        return {"message": f"✅ {username} removed successfully."}
    return _handle_response(response)

def update_collaborator_permission(owner, repo, username, permission="push"):
    # GitHub API: re-invite with new permission
    return add_collaborator(owner, repo, username, permission)

# -------- Bulk Management --------

def process_bulk_action(owner, repo, username, permission, action):
    if action == "add":
        return add_collaborator(owner, repo, username, permission)
    elif action == "remove":
        return remove_collaborator(owner, repo, username)
    else:
        return {"error": "Invalid action", "message": f"Action '{action}' is not supported."}

# -------- Audit & Reporting --------

def get_collaborators_report(owner, repo):
    data = get_collaborators(owner, repo)
    if isinstance(data, dict) and "error" in data:
        return data

    report = []
    for user in data:
        report.append({
            "username": user.get("login"),
            "role": user.get("role_name", "N/A"),
            "admin": user.get("permissions", {}).get("admin", False),
            "push": user.get("permissions", {}).get("push", False),
            "pull": user.get("permissions", {}).get("pull", False)
        })
    return report

# -------- Helper --------

def _handle_response(response):
    try:
        return response.json()
    except Exception:
        return {"error": response.status_code, "message": response.text}
