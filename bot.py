from pyrogram import Client, filters
import requests

bot = Client("bot", bot_token="YOUR_BOT_TOKEN")

@bot.on_message(filters.command("start"))
def start(client, message):
    user = message.from_user
    data = {
        "username": user.username or str(user.id),
        "email": f"{user.id}@telegram.com",
        "password": "telegram_login"
    }
    requests.post("http://127.0.0.1:8000/register", data=data)
    message.reply("Registered")

bot.run()
