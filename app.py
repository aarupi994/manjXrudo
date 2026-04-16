from fastapi import FastAPI, Form
import json, bcrypt, random

app = FastAPI()
DB = "users.json"

def load():
    try:
        return json.load(open(DB))
    except:
        return []

def save(data):
    json.dump(data, open(DB, "w"), indent=4)

@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = load()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = {"username": username, "email": email, "password": hashed, "premium": False}
    db.append(user)
    save(db)
    return {"msg": "Registered"}

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    db = load()
    for u in db:
        if u["email"] == email and bcrypt.checkpw(password.encode(), u["password"].encode()):
            return {"msg": "Login Success"}
    return {"msg": "Invalid"}

