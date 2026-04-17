from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json, bcrypt, random, os
import smtplib
from email.mime.text import MIMEText

app = FastAPI()

templates = Jinja2Templates(directory="templates")

DB = "users.json"

# ================== DATABASE ==================
def load():
    if not os.path.exists(DB):
        return []
    try:
        with open(DB, "r") as f:
            return json.load(f)
    except:
        return []

def save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=4)

# ================== SECURITY ==================
blocked = ["tempmail", "10min", "mailinator"]

email_otps = {}
verified_emails = set()

def generate_otp():
    return str(random.randint(100000, 999999))

# ================== EMAIL FUNCTION ==================
def send_email_otp(receiver_email, otp):

    sender_email = "rudowner1@gmail.com"        # 🔁 change this
    app_password = "efyg ourp oavj iikx"     # 🔁 change this

    subject = "ManjXrudo OTP Verification"
    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.mail.yahoo.com", 587)
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
    return templates.TemplateResponse(request=request, name="register.html")

# ================== SEND OTP ==================
@app.post("/send-otp")
def send_otp(email: str = Form(...)):

    if any(x in email.lower() for x in blocked):
        return {"msg": "❌ Temporary email not allowed"}

    otp = generate_otp()
    email_otps[email] = otp

    if send_email_otp(email, otp):
        return {"msg": "✅ OTP sent to your Email"}
    else:
        return {"msg": "❌ Email sending failed"}

# ================== VERIFY OTP ==================
@app.post("/verify-otp")
def verify_otp(email: str = Form(...), otp: str = Form(...)):

    if email in email_otps and email_otps[email] == otp:
        verified_emails.add(email)
        return {"msg": "✅ Email Verified"}

    return {"msg": "❌ Invalid OTP"}

# ================== REGISTER ==================
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    if email not in verified_emails:
        return {"msg": "⚠️ Verify email first"}

    db = load()

    for u in db:
        if u["email"] == email:
            return {"msg": "⚠️ Email already registered"}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "email": email,
        "password": hashed
    }

    db.append(user)
    save(db)

    return {"msg": "✅ Registered Successfully"}

# ================== LOGIN ==================
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    db = load()

    for u in db:
        if u["email"] == email:
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                return {"msg": "✅ Login Success"}

    return {"msg": "❌ Invalid Email or Password"}
