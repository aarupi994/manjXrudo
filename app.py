from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json, bcrypt

app = FastAPI()

# Template setup
templates = Jinja2Templates(directory="templates")

DB = "users.json"

def load():
    try:
        return json.load(open(DB))
    except:
        return []

def save(data):
    json.dump(data, open(DB, "w"), indent=4)

# TEMP MAIL BLOCK
blocked = ["tempmail", "10min", "mailinator"]

# ✅ HOME PAGE FIX (IMPORTANT)
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# ✅ REGISTER
@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    
    if any(x in email.lower() for x in blocked):
        return {"msg": "❌ Fake email not allowed"}

    db = load()

    # check already exist
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
