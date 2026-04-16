from flask import session

# credentials
USERS = {
    "hariom":  {"pw": "1234", "role": "teacher"},
    "shriom":  {"pw": "1234", "role": "teacher"},
    "admin":   {"pw": "1234",   "role": "admin"},
}

def chk_login(u, p):
    usr = USERS.get(u)
    if usr and usr["pw"] == p:
        return usr["role"]
    return None

def do_login(u, role):
    session["usr"] = u
    session["role"] = role

def do_logout():
    session.clear()

def is_authed():
    return "usr" in session

def is_admin():
    return session.get("role") == "admin"

def is_teacher():
    return session.get("role") in ("teacher","admin")

def curr_user():
    return session.get("usr","")
