from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import bcrypt

app = FastAPI()

# Template setup
templates = Jinja2Templates(directory="templates")

DB = "users.json"

# Load users
def load():
    try:
        with open(DB, "r") as f:
            return json.load(f)
    except:
        return []

# Save users
def save(data):
    with open(DB, "w") as f:
        json.dump(data, f, indent=4)

# Block temp emails
blocked = ["tempmail", "10min", "mailinator"]

# ✅ HOME PAGE (FIXED)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

# ✅ REGISTER
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):

    # Block fake email
    if any(x in email.lower() for x in blocked):
        return {"msg": "❌ Fake email not allowed"}

    db = load()

    # Check duplicate
    for u in db:
        if u["email"] == email:
            return {"msg": "⚠️ Email already registered"}

    # Hash password
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "email": email,
        "password": hashed
    }

    db.append(user)
    save(db)

    return {"msg": "✅ Registered Successfully"}

# ✅ LOGIN (basic)
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):

    db = load()

    for u in db:
        if u["email"] == email:
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                return {"msg": "✅ Login Success"}

    return {"msg": "❌ Invalid Email or Password"}
