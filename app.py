import subprocess, sys

def _install(pkg):
    print(f"[setup] installing {pkg}...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", pkg,
        "--break-system-packages", "--quiet"
    ], stderr=subprocess.DEVNULL)

def ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        _install(pkg)

ensure("flask")

from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import init_db, insert_doubt, get_doubts, get_doubt, save_resp, get_resp, save_feedback, has_feedback, analytics, is_banned, ban_entity, unban_entity, get_bans
from classify import pred
from moderation import is_toxic
from auth import chk_login, do_login, do_logout, is_teacher, is_admin, curr_user
import threading, webbrowser, socket, os, uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
# changing this later cos its not secure tbh
app.secret_key = "sd_secret_xk29"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5MB maximum file size

init_db()

def find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    ip = request.remote_addr or ""
    print(f"\n[DEBUG] Someone hit SUBMIT!")
    print(f"[DEBUG] Their connection IP is: '{ip}'")
    
    if is_banned("ip", ip.strip()):
        print(f"[DEBUG] BAN HAMMER THROWN! Blocked '{ip}'.")
        flash("Your IP has been banned due to inappropriate behavior.")
        return redirect(url_for("index"))

    txt  = request.form.get("qtxt","").strip()
    subj = request.form.get("subj","General")
    if len(txt) < 10:
        flash("doubt too short, write a bit more")
        return redirect(url_for("index"))
    
    # content moderation check
    toxic, reason = is_toxic(txt)
    if toxic:
        # auto-ban the IP immediately — no second chances for this
        if not is_banned("ip", ip.strip()):
            ban_entity("ip", ip.strip())
            print(f"[moderation] auto-banned IP {ip} for toxic content: '{reason}'")
        flash("Your submission was blocked for inappropriate content. Repeated violations will restrict your access.")
        return redirect(url_for("index"))

    catg = pred(txt)
    # TODO: add spam filter here maybe?
    
    img_file = request.files.get("img")
    img_path = None
    if img_file and img_file.filename != '':
        ext = img_file.filename.rsplit('.', 1)[-1].lower() if '.' in img_file.filename else ''
        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp'}:
            fname = secure_filename(f"{uuid.uuid4().hex[:8]}_{img_file.filename}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            img_file.save(save_path)
            img_path = f"uploads/{fname}"

    qid  = insert_doubt(txt, subj, catg, img_path, ip)
    print("someone clicked submit!")
    print(f"[debug] new doubt qid={qid} catg={catg}")
    return render_template("submitted.html", qid=qid)

@app.route("/lookup", methods=["POST"])
def lookup():
    qid = request.form.get("qid","").strip()
    if not qid or not qid.isdigit():
        flash("enter a valid doubt ID")
        return redirect(url_for("index"))
    return redirect(url_for("check", qid=int(qid)))

@app.route("/check/<int:qid>")
def check(qid):
    q = get_doubt(qid)
    if not q:
        flash("doubt not found")
        return redirect(url_for("index"))
    resp    = get_resp(qid)
    fb_done = has_feedback(qid) # check DB, not URL param
    return render_template("check.html", q=q, resp=resp, fb_done=fb_done)

@app.route("/feedback/<int:qid>", methods=["POST"])
def feedback(qid):
    ip  = request.remote_addr or ""
    cmt = request.form.get("cmt", "").strip()
    
    # check comments too — students shouldn't be rude in feedback
    if cmt:
        toxic, reason = is_toxic(cmt)
        if toxic:
            if not is_banned("ip", ip.strip()):
                ban_entity("ip", ip.strip())
                print(f"[moderation] auto-banned IP {ip} for toxic feedback comment: '{reason}'")
            flash("Your feedback was blocked for inappropriate content.")
            return redirect(url_for("check", qid=qid))

    stars = int(request.form.get("stars", 3))
    save_feedback(qid, stars, cmt)
    return redirect(url_for("check", qid=qid))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u    = request.form.get("usr","")
        p    = request.form.get("pw","")
        if is_banned("teacher", u):
            flash("Your account has been restricted.")
            return render_template("login.html")
        role = chk_login(u, p)
        if role:
            do_login(u, role)
            return redirect(url_for("admin") if role == "admin" else url_for("teacher"))
        flash("wrong credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    # just clear session and go back to home
    do_logout()
    return redirect(url_for("index"))

@app.route("/teacher")
def teacher():
    if not is_teacher():
        return redirect(url_for("login"))
    catf   = request.args.get("cat","all")
    doubts = get_doubts(answered=0)
    if catf != "all":
        doubts = [d for d in doubts if d["catg"] == catf]
    return render_template("teacher.html", doubts=doubts, catf=catf, usr=curr_user())

@app.route("/answer/<int:qid>", methods=["POST"])
def answer(qid):
    if not is_teacher():
        return redirect(url_for("login"))
    if is_banned("teacher", curr_user()):
        flash("Your account has been restricted.")
        return redirect(url_for("teacher"))
    resp = request.form.get("resp","").strip()
    if resp:
        # teachers should also be civil
        toxic, reason = is_toxic(resp)
        if toxic:
            flash("Your response was blocked — it contains inappropriate content. Keep it professional.")
            print(f"[moderation] blocked teacher '{curr_user()}' for toxic response: '{reason}'")
            return redirect(url_for("teacher"))
        save_resp(qid, curr_user(), resp)
    return redirect(url_for("teacher"))

@app.route("/admin")
def admin():
    if not is_admin():
        return redirect(url_for("login"))
    data  = analytics()
    all_q = get_doubts()
    bans  = get_bans()
    return render_template("admin.html", data=data, all_q=all_q, usr=curr_user(), bans=bans)

@app.route("/admin/ban", methods=["POST"])
def ban_user():
    if not is_admin():
        return redirect(url_for("login"))
    btype = request.form.get("btype")
    bval  = request.form.get("bval", "").strip()
    
    # Auto-correct if admin pastes the link/port instead of the raw IP
    if btype == "ip":
        bval = bval.replace("http://", "").replace("https://", "")
        if ":" in bval:
            bval = bval.split(":")[0] # strips the port number

    if btype and bval and not is_banned(btype, bval):
        ban_entity(btype, bval)
        flash(f"Banned {btype}: {bval}")
    return redirect(url_for("admin"))

@app.route("/admin/unban", methods=["POST"])
def unban_user():
    if not is_admin():
        return redirect(url_for("login"))
    btype = request.form.get("btype")
    bval  = request.form.get("bval", "").strip()
    if btype and bval:
        unban_entity(btype, bval)
        flash(f"Unbanned {btype}: {bval}")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    port = find_free_port()

    def open_browser():
        webbrowser.open(f"http://127.0.0.1:{port}")

    t = threading.Timer(1.2, open_browser)
    t.daemon = True
    t.start()

    print(f"\n  SilentDoubt running at → http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
