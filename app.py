from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import bcrypt, random, time
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient

# ================== MONGODB ==================
MONGO_URL = "mongodb+srv://rudowner1_db_user:manjXrudo@rudo.esfs5m0.mongodb.net/?appName=Rudo"

client = MongoClient(MONGO_URL)
db = client["manjxrudo"]
users_collection = db["users"]

# ================== APP ==================
app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
    return templates.TemplateResponse("register.html", {"request": request})

# ================== REGISTER ==================
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    # Email check
    if users_collection.find_one({"email": email}):
        return {"msg": "❌ Email already registered"}

    # Username check
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

    return {"msg": "✅ OTP sent"}

# ================== VERIFY OTP ==================
@app.post("/verify-otp")
def verify_otp(email: str = Form(...), otp: str = Form(...)):

    if email in email_otps and email_otps[email] == otp:

        data = pending_users.get(email)

        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

        user = {
            "username": data["username"],
            "email": email,
            "password": hashed,
            "coins": 2
        }

        users_collection.insert_one(user)

        del email_otps[email]
        del pending_users[email]

        # ✅ FIXED COOKIE
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user", value=email, max_age=86400)

        return response

    return {"msg": "❌ Invalid OTP"}

# ================== LOGIN ==================
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    user = users_collection.find_one({"email": email})

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user", value=email, max_age=86400)
        return response

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

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user.get("username", "User"),
        "coins": user.get("coins", 0)
    })

# ================== START AD ==================
@app.get("/start-ad")
def start_ad(request: Request):

    email = request.cookies.get("user")

    if not email:
        return RedirectResponse("/")

    current_time = int(time.time())

    users_collection.update_one(
        {"email": email},
        {"$set": {"ad_start_time": current_time}}
    )

    return RedirectResponse("/ads", status_code=303)

# ================== ADS PAGE ==================
@app.get("/ads", response_class=HTMLResponse)
def ads_page(request: Request):
    return templates.TemplateResponse("ads.html", {"request": request})

# ================== COMPLETE AD ==================
@app.get("/complete-ad")
def complete_ad(request: Request):

    email = request.cookies.get("user")

    if not email:
        return RedirectResponse("/")

    user = users_collection.find_one({"email": email})

    if not user:
        return RedirectResponse("/")

    start_time = user.get("ad_start_time", 0)
    now = int(time.time())

    watch_time = now - start_time

    if watch_time >= 8:
        users_collection.update_one(
            {"email": email},
            {"$inc": {"coins": 1}}
        )
        return RedirectResponse("/dashboard", status_code=303)
    else:
        return HTMLResponse("<h2 style='color:red'>❌ Mission Failed! Watch full ad</h2>")
