from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

# ================== APP ==================
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
    app_password = "efygourpoavjiikx"

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
        del email_otps[email]
        return {"msg": "✅ Email Verified"}

    return {"msg": "❌ Invalid OTP"}

# ================== REGISTER ==================
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    if email not in verified_emails:
        return {"msg": "⚠️ Verify email first"}

    if users_collection.find_one({"email": email}):
        return {"msg": "⚠️ Email already registered"}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "email": email,
        "password": hashed,
        "coins": 2
    }

    users_collection.insert_one(user)
    verified_emails.discard(email)

    return {"msg": "✅ Registered Successfully"}

# ================== LOGIN ==================
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    try:
        user = users_collection.find_one({"email": email})
    except:
        return {"msg": "⚠️ Server error, try again later"}

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return RedirectResponse(url="/dashboard", status_code=303)

    return {"msg": "❌ Invalid Email or Password"}

# ================== DASHBOARD ==================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    try:
        user = users_collection.find_one()
    except:
        return HTMLResponse("❌ Database error")

    if not user:
        return HTMLResponse("❌ No user found. Please register first.")

    username = user.get("username", "User")
    coins = user.get("coins", 0)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "username": username,
            "coins": coins
        }
    )

# ================== EARN COIN ==================
@app.post("/earn-coin")
def earn_coin():

    users_collection.update_one({}, {"$inc": {"coins": 1}})

    return RedirectResponse(url="/dashboard", status_code=303)
