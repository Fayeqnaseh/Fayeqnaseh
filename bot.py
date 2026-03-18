"""
Telegram Bot with Multi-mode AI (GPT-4o, DALL·E, etc.) Integration

Features:
- Multi-mode: Text, Image, Video, Code, Social Media, Anime, 3D, Music, Restoration.
- Inline keyboards for mode selection, cancel/reset, random mode.
- Async handlers; modular, clean Application.builder() style.
- OpenAI GPT-4o-mini (or GPT-4) for text/code/story; DALL·E for images.
- Example code generation (Flask API, Discord bot, generic Python).
- Logging enabled, graceful API key handling.
- Free chat mode.
- Suitable for Railway/Render.

Requires:
- python-telegram-bot v20.7+
- openai

Bot Deployment:
- Set environment variables: TELEGRAM_TOKEN, OPENAI_KEY
"""

import os
import logging
import random
import asyncio
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    constants,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ========================== LOGGING SETUP ==========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ====================== ENVIRONMENT VARIABLES ======================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")

# If missing API keys, log warning and disable affected features
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not found in environment!")
if not OPENAI_KEY:
    logger.warning("OPENAI_KEY (OpenAI) missing; AI text/code/image functions will be disabled.")

# =========================== CONSTANTS ============================
MODES = [
    "Text", "Image", "Video", "Code", "Social Media",
    "Anime", "3D", "Music", "Restoration"
]
MODE_TO_PROMPT = {
    "Text": "Generate creative stories, conversations, or text.",
    "Image": "Describe an image you want to generate.",
    "Video": "Describe a video idea you want to create.",
    "Code": "Generate Python code, Flask API, Discord bot, or others.",
    "Social Media": "Write a post for Twitter, Facebook, etc.",
    "Anime": "Describe an anime character, scene, or story.",
    "3D": "Describe a 3D model, scene, or animation.",
    "Music": "Describe a song, melody, or musical piece.",
    "Restoration": "Describe damaged content to restore (photo, audio, etc.).",
}

# States for ConversationHandler
SELECTING_MODE, ENTERING_PROMPT, AI_OUTPUT = range(3)


# ==================== OPENAI INTEGRATION ==========================
try:
    import openai
    openai.api_key = OPENAI_KEY
except ImportError:
    openai = None

async def ask_openai(
    mode: str,
    user_prompt: str,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Query OpenAI API (GPT-4o-mini or GPT-4) for response.
    Handles code, stories, text.
    """
    if not openai or not OPENAI_KEY:
        return "OpenAI API key missing. AI features are currently unavailable."

    # Compose system prompt based on mode
    mode_instruction = MODE_TO_PROMPT.get(mode, "You are a creative AI assistant.")
    if system_prompt:
        mode_instruction += "\n" + system_prompt

    chat_prompt = [
        {"role": "system", "content": mode_instruction},
        {"role": "user", "content": user_prompt}
    ]

    # Use GPT-4o-mini if available, otherwise GPT-4
    try:
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-4o",
            messages=chat_prompt,
            temperature=0.7,
            max_tokens=700,
        )
        text = response.choices[0].message.content
        return text
    except Exception as e:
        logger.warning(f"OpenAI error: {e}")
        return f"AI service error: {str(e)}"

async def generate_dalle_image(prompt: str) -> Optional[str]:
    """
    Generate image using OpenAI DALL·E.
    Returns image URL, or None if not available.
    """
    if not openai or not OPENAI_KEY:
        return None

    try:
        response = await asyncio.to_thread(
            openai.Image.create,
            prompt=prompt,
            n=1,
            size="512x512",
        )
        url = response.data[0].url
        return url
    except Exception as e:
        logger.warning(f"DALL·E error: {e}")
        return None

# ====================== INLINE KEYBOARDS ===========================
def mode_selection_keyboard():
    """
    Inline keyboard for mode selection (with random, cancel/reset)
    """
    buttons = [
        [InlineKeyboardButton(mode, callback_data=f"mode_{mode}")]
        for mode in MODES
    ]
    # Add random/cancel row
    buttons.append([
        InlineKeyboardButton("🎲 Random", callback_data="mode_RANDOM"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(buttons)

def cancel_reset_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("↩️ Back to Modes", callback_data="reset"),
        InlineKeyboardButton("❌ End", callback_data="cancel")
    ]])

# ========================= HANDLERS ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start command handler.
    """
    await update.message.reply_text(
        "Hello! I'm your AI-powered creative Telegram bot.\n"
        "Choose a mode to begin:",
        reply_markup=mode_selection_keyboard(),
    )
    logger.info(f"User {update.effective_user.id} started the bot.")
    return SELECTING_MODE

async def mode_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles mode selection via inline keyboard.
    """
    query = update.callback_query
    await query.answer()
    logger.info(f"User selected callback: {query.data}")

    if query.data == "cancel":
        await query.edit_message_text("Session canceled. Use /start or /help to restart.")
        return ConversationHandler.END
    if query.data == "reset":
        await query.edit_message_text(
            "Select a mode:",
            reply_markup=mode_selection_keyboard(),
        )
        return SELECTING_MODE

    # Random mode
    if query.data == "mode_RANDOM":
        mode = random.choice(MODES)
        logger.info(f"Random mode selected: {mode}")
    else:
        mode = query.data.replace("mode_", "")
    
    context.user_data["mode"] = mode
    await query.edit_message_text(
        f"You chose: *{mode}*\n"
        f"{MODE_TO_PROMPT.get(mode, '')}\n"
        "Please send your topic, idea, or prompt:",
        parse_mode=constants.ParseMode.MARKDOWN,
        reply_markup=cancel_reset_keyboard(),
    )
    return ENTERING_PROMPT

async def prompt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles user prompt for chosen mode.
    """
    mode = context.user_data.get("mode", "Text")
    user_prompt = update.message.text.strip()
    context.user_data["prompt"] = user_prompt
    logger.info(f"Prompt for mode {mode}: {user_prompt}")

    # Notify user typing...
    await update.message.reply_chat_action(constants.ChatAction.TYPING)

    output = ""

    # AI integration by mode
    if mode == "Image":
        # DALL·E integration
        img_url = await generate_dalle_image(user_prompt)
        if img_url:
            await update.message.reply_photo(
                img_url,
                caption=f"AI-generated image for your prompt:\n`{user_prompt}`",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=cancel_reset_keyboard(),
            )
            return AI_OUTPUT
        else:
            output = "Image generation failed or unavailable."
    elif mode == "Code":
        output = await ask_openai(
            mode="Code",
            user_prompt=f"Generate Python code for:\n{user_prompt}\n"
                        "Format as a ready-to-copy code block. Example: Flask API, Discord bot, generic Python."
        )
        # Reply with formatted code block if detected
        if "```" in output:
            await update.message.reply_text(
                output,
                reply_markup=cancel_reset_keyboard(),
                parse_mode=constants.ParseMode.MARKDOWN,
            )
            return AI_OUTPUT
        else:
            await update.message.reply_text(
                f"`{output}`",
                parse_mode=constants.ParseMode.MARKDOWN,
                reply_markup=cancel_reset_keyboard(),
            )
            return AI_OUTPUT
    else:
        # Text, Story, Social, etc.
        output = await ask_openai(mode, user_prompt)
        await update.message.reply_text(
            output,
            reply_markup=cancel_reset_keyboard(),
            parse_mode=constants.ParseMode.MARKDOWN,
        )
        return AI_OUTPUT

    # Fallback in case output is not set
    await update.message.reply_text(
        output,
        reply_markup=cancel_reset_keyboard(),
        parse_mode=constants.ParseMode.MARKDOWN,
    )
    return AI_OUTPUT

async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles 'reset' button to go back to mode selection.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Select a mode:",
        reply_markup=mode_selection_keyboard(),
    )
    return SELECTING_MODE

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles 'cancel' button or /cancel command.
    """
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Session canceled. Use /start or /help to restart.")
    else:
        await update.message.reply_text("Session canceled. Use /start or /help to restart.")
    return ConversationHandler.END

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help command handler.
    """
    await update.message.reply_text(
        "AI Telegram Bot Help:\n"
        "- Select a mode using the inline keyboard.\n"
        "- Enter your topic, story, or prompt.\n"
        "- Use 'Random' for a surprise mode.\n"
        "- Cancel or reset anytime via buttons.\n"
        "Supported modes: Text, Image, Video, Code, Social Media, Anime, 3D, Music, Restoration.\n"
        "You can generate code blocks (Python, Flask, Discord bot, etc.), creative stories, prompts, multimedia.\n"
        "\n"
        "To restart: /start\nTo end: /cancel\n"
        "All interactions are in English.",
    )

async def free_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Free chat mode. When user messages outside conversation,
    bot responds as a creative AI.
    """
    user_prompt = update.message.text.strip()
    await update.message.reply_chat_action(constants.ChatAction.TYPING)
    reply = await ask_openai("Text", user_prompt)
    await update.message.reply_text(reply, parse_mode=constants.ParseMode.MARKDOWN)
    logger.info(f"Free chat: {user_prompt}")

# ==================== MAIN APP BUILDER =============================
def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN missing! Bot cannot run.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Conversation handler flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_MODE: [
                CallbackQueryHandler(mode_button, pattern=r"^mode_.*"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            ],
            ENTERING_PROMPT: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), prompt_entry),
                CallbackQueryHandler(reset_handler, pattern="^reset$"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            ],
            AI_OUTPUT: [
                CallbackQueryHandler(reset_handler, pattern="^reset$"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler)
        ],
        allow_reentry=True,
        per_user=True,
    )

    # Handlers
    application.add_handler(conv_handler)

    # Universal commands
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("cancel", cancel_handler))

    # Fallback: free chat in private or group
    application.add_handler(
        MessageHandler(
            filters.TEXT & (~filters.COMMAND),
            free_chat_handler
        )
    )

    logger.info("Bot is starting with polling mode...")
    application.run_polling()  # For Railway/Render deployment

if __name__ == "__main__":
    main()