import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# 🔑 تنظیمات
BOT_TOKEN = "YOUR_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_API_KEY"

user_mode = {}

# کیبورد حرفه‌ای
keyboard = [
    ["🎨 Image Prompt", "🖼 Generate Image"],
    ["✍️ Text Prompt", "💻 Code Prompt"],
    ["📱 Social Media", "🎬 Cinematic"],
    ["🏛 Restoration Timelapse"]
]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ارسال امن
async def safe_send(update, text):
    for _ in range(3):
        try:
            await update.message.reply_text(text)
            return
        except:
            await asyncio.sleep(2)

# ساخت پرامپت با API سبک
async def generate_prompt(topic, mode):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    systems = {
        "image": "You are a professional AI image prompt engineer.",
        "text": "You are a high-level content writer.",
        "code": "You are a senior software engineer.",
        "social": "You are a viral social media expert.",
        "cinematic": "You are a cinematic director.",
        "restoration": "You create historical restoration timelapse prompts."
    }

    system = systems.get(mode, "You are an expert.")

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Create a highly detailed and professional output about: {topic}"}
        ],
        "temperature": 0.9
    }

    try:
        res = requests.post(url, headers=headers, json=data).json()
        return res["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {e}"

# تولید تصویر واقعی (DALL·E)
async def generate_image(prompt):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1024"
    }
    try:
        res = requests.post(url, headers=headers, json=data).json()
        return res["data"][0]["url"]
    except Exception as e:
        return f"⚠️ Error: {e}"

# ارسال عکس
async def send_photo(update, url):
    for _ in range(3):
        try:
            await update.message.reply_photo(url)
            return
        except:
            await asyncio.sleep(2)

# هندل پیام‌ها
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    modes = {
        "🎨 Image Prompt": "image",
        "🖼 Generate Image": "gen_image",
        "✍️ Text Prompt": "text",
        "💻 Code Prompt": "code",
        "📱 Social Media": "social",
        "🎬 Cinematic": "cinematic",
        "🏛 Restoration Timelapse": "restoration"
    }

    if text in modes:
        user_mode[user_id] = modes[text]
        await safe_send(update, "✅ Mode selected\nSend your topic 👇")
        return

    if user_mode.get(user_id) is None:
        await safe_send(update, "⚠️ First select a mode")
        return

    mode = user_mode[user_id]
    topic = text

    await safe_send(update, "⏳ Processing...")

    if mode == "gen_image":
        prompt = await generate_prompt(topic, "image")
        await safe_send(update, f"🎯 Prompt:\n{prompt}")
        image_url = await generate_image(prompt)
        await send_photo(update, image_url)
        return

    result = await generate_prompt(topic, mode)
    await safe_send(update, result)

# شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode[update.effective_user.id] = None
    await update.message.reply_text("👋 Welcome!\nSelect mode:", reply_markup=markup)

# اجرای ربات
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

print("✅ Bot is running...")
app.run_polling()