from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import bcrypt, random
import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient

# ================== MONGODB ==================
MONGO_URL = "mongodb+srv://rudowner1_db_user:manjXrudo@rudo.esfs5m0.mongodb.net/?appName=Rudo"

client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["manjxrudo"]
users_collection = db["users"]

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ================== SECURITY ==================
blocked = ["tempmail", "10min", "mailinator"]

email_otps = {}
verified_emails = set()

def generate_otp():
    return str(random.randint(100000, 999999))

# ================== EMAIL FUNCTION ==================
def send_email_otp(receiver_email, otp):

    sender_email = "rudowner1@gmail.com"
    app_password = "efygourpoavjiikx"  # ❗ no spaces

    subject = "ManjXrudo OTP Verification"
    body = f"Your OTP is: {otp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
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
        del email_otps[email]   # 🔥 IMPORTANT
        return {"msg": "✅ Email Verified"}

    return {"msg": "❌ Invalid OTP"}
# ================== REGISTER ==================
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    if email not in verified_emails:
        return {"msg": "⚠️ Verify email first"}

    # Check duplicate
    if users_collection.find_one({"email": email}):
        return {"msg": "⚠️ Email already registered"}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "email": email,
        "password": hashed
    }

    users_collection.insert_one(user)

    verified_emails.discard(email)   # ✅ YAHI Sahi jagah hai

    return {"msg": "✅ Registered Successfully"}

# ================== LOGIN ==================
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    try:
        user = users_collection.find_one({"email": email})
    except:
        return {"msg": "⚠️ Server error, try again later"}

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return {"msg": "✅ Login Success"}

    return {"msg": "❌ Invalid Email or Password"}
