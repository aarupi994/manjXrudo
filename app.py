from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import bcrypt, random, time
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient

# ================== APP ==================
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# ================== MONGODB ==================
MONGO_URL = "mongodb+srv://rudowner1_db_user:manjXrudo@rudo.esfs5m0.mongodb.net/?appName=Rudo"
client = MongoClient(MONGO_URL)
db = client["manjxrudo"]
users_collection = db["users"]

# ================== TEMP STORAGE ==================
email_otps = {}
pending_users = {}

# ================== OTP ==================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_otp(receiver_email, otp):
    sender_email = "rudowner1@gmail.com"
    app_password = "efygourpoavjiikx"

    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email Error:", e)
        return False

# ================== HOME ==================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth.html"
    )

# ================== OTP PAGE ==================
@app.get("/otp", response_class=HTMLResponse)
def otp_page(request: Request):
    email = request.cookies.get("pending_email")

    return templates.TemplateResponse(
        request=request,
        name="otp.html",
        context={"email": email}
    )

# ================== REGISTER ==================
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    if users_collection.find_one({"email": email}):
        return {"msg": "❌ Email already registered"}

    if users_collection.find_one({"username": username}):
        suggestion = username + str(random.randint(1000, 9999))
        return {"msg": "❌ Username exists", "suggestion": suggestion}

    otp = generate_otp()
    email_otps[email] = otp

    pending_users[email] = {
        "username": username,
        "password": password
    }

    send_email_otp(email, otp)

    res = RedirectResponse("/otp", status_code=303)
    res.set_cookie("pending_email", email, max_age=300)

    return res

# ================== VERIFY OTP ==================
@app.post("/verify-otp")
def verify_otp(response: Response, email: str = Form(...), otp: str = Form(...)):

    if email in email_otps and email_otps[email] == otp:

        data = pending_users.get(email)

        if not data:
            return {"msg": "❌ Session expired"}

        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

        user = {
            "username": data["username"],
            "email": email,
            "password": hashed,
            "coins": 2,
            "is_premium": False,
            "theme": "default",
            "ad_start_time": 0
        }

        users_collection.insert_one(user)

        del email_otps[email]
        del pending_users[email]

        res = RedirectResponse("/dashboard", status_code=303)
        res.set_cookie("user", email, max_age=86400)

        return res

    return {"msg": "❌ Invalid OTP"}

# ================== LOGIN ==================
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    user = users_collection.find_one({"email": email})

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        res = RedirectResponse("/dashboard", status_code=303)
        res.set_cookie("user", email, max_age=86400)
        return res

    return {"msg": "❌ Invalid login"}

# ================== DASHBOARD ==================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    email = request.cookies.get("user")

    if not email:
        return RedirectResponse("/")

    user = users_collection.find_one({"email": email})

    if not user:
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "username": user["username"],
            "coins": user.get("coins", 0),
            "theme": user.get("theme", "default")
        }
    )

# ================== START AD ==================
@app.get("/start-ad")
def start_ad(request: Request):

    email = request.cookies.get("user")

    if not email:
        return RedirectResponse("/")

    users_collection.update_one(
        {"email": email},
        {"$set": {"ad_start_time": int(time.time())}}
    )

    return RedirectResponse("/ads", status_code=303)

# ================== ADS PAGE ==================
@app.get("/ads", response_class=HTMLResponse)
def ads_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="ads.html"
    )

# ================== COMPLETE AD ==================
@app.get("/complete-ad")
def complete_ad(request: Request):

    email = request.cookies.get("user")

    if not email:
        return RedirectResponse("/")

    user = users_collection.find_one({"email": email})

    if not user:
        return RedirectResponse("/")

    watch_time = int(time.time()) - user.get("ad_start_time", 0)

if watch_time >= 8:
    if user.get("is_premium"):
        users_collection.update_one(
            {"email": email},
            {"$inc": {"coins": 2}}
        )
    else:
        users_collection.update_one(
            {"email": email},
            {"$inc": {"coins": 1}}
        )
    return RedirectResponse("/dashboard", status_code=303)
        return RedirectResponse("/dashboard", status_code=303)
    else:
        return HTMLResponse("<h2 style='color:red'>❌ Watch full ad</h2>")

# ================== LOGOUT ==================
@app.get("/logout")
def logout():
    res = RedirectResponse("/")
    res.delete_cookie("user")
    return res
