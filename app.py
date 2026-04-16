from fastapi import FastAPI, Form
import json, bcrypt

app = FastAPI()
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

@app.post("/register")
def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if any(x in email.lower() for x in blocked):
        return {"msg": "Fake email not allowed"}

    db = load()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "email": email,
        "password": hashed
    }

    db.append(user)
    save(db)

    return {"msg": "Registered Successfully"}
