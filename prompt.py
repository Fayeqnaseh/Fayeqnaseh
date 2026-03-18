
"""
Professional Telegram Prompt Generator Bot
Features: 6 modes (Text/Image/Code/Social/Cinematic/Restoration), DALL-E integration, Inline keyboards
Deployment: Railway/Render + UptimeRobot ready
"""

import os
import logging
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# States for ConversationHandler
SELECTING_MODE, ENTERING_TOPIC = range(2)

# OpenAI Setup
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

# Modes configuration
MODES = {
    "text": "📝 Text Generation",
    "image": "🖼️ Image Generation", 
    "code": "💻 Code Snippets",
    "social": "📱 Social Media Content",
    "cinematic": "🎬 Cinematic Scenes",
    "restoration": "🔧 Restoration Timelapse"
}

def create_mode_keyboard():
    """Create inline keyboard for mode selection"""
    keyboard = []
    for key, display in MODES.items():
        keyboard.append([InlineKeyboardButton(display, callback_data=key)])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - show mode selection"""
    welcome_text = """
🤖 **Welcome to AI Prompt Generator Bot!**

Select a mode to create professional, detailed prompts:

*(Click a button below)*
    """
    await update.message.reply_text(welcome_text, reply_markup=create_mode_keyboard(), parse_mode='Markdown')
    return SELECTING_MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle mode selection callback"""
    query = update.callback_query
    await query.answer()
    
    mode = query.data
    
    if mode == "cancel":
        await query.edit_message_text("Operation cancelled. Use /start for new prompt!")
        return ConversationHandler.END
    
    context.user_data['mode'] = mode
    mode_display = MODES[mode]
    
    await query.edit_message_text(
        f"✅ **{mode_display}** mode selected!\n\n"
        f"**Enter your topic/theme:**\n"
        f"*Examples:*\n"
        f"`sci-fi adventure`\n"
        f"`futuristic city`\n"
        f"`Python web scraper`\n"
        f"`Instagram reel`\n"
        f"`car restoration`",
        parse_mode='Markdown'
    )
    return ENTERING_TOPIC

async def generate_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate detailed prompt based on mode and topic"""
    topic = update.message.text.strip()
    mode = context.user_data.get('mode')
    
    if not mode:
        await update.message.reply_text("❌ Error: No mode selected. Use /start")
        return ConversationHandler.END
    
    mode_display = MODES[mode]
    
    # Generate prompt based on mode
    if mode == "text":
        prompt = generate_text_prompt(topic)
    elif mode == "image":
        prompt = generate_image_prompt(topic)
        # Generate actual image with DALL-E
        await generate_dalle_image(update, context, prompt)
        return ConversationHandler.END
    elif mode == "code":
        prompt = generate_code_prompt(topic)
    elif mode == "social":
        prompt = generate_social_prompt(topic)
    elif mode == "cinematic":
        prompt = generate_cinematic_prompt(topic)
    elif mode == "restoration":
        prompt = generate_restoration_prompt(topic)
    
    # Send the detailed prompt
    await update.message.reply_text(
        f"🎯 **{mode_display} Prompt Ready!**\n\n"
        f"```\n{prompt}\n```\n\n"
        f"💡 *Copy-paste directly into ChatGPT/Midjourney/etc.*\n"
        f"Use /start for another prompt!",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def generate_dalle_image(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    """Generate and send DALL-E image"""
    try:
        await update.message.reply_chat_action("upload_photo")
        
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🖼️ **Generated Image**\n\n{prompt[:200]}...\n\nUse /start for more!"
        )
    except Exception as e:
        logger.error(f"DALL-E error: {e}")
        await update.message.reply_text(
            f"⚠️ Image generation failed (check OpenAI credits)\n\n"
            f"**Prompt ready:**\n```\n{prompt}\n```",
            parse_mode='Markdown'
        )

# Prompt generators - highly detailed and professional
def generate_text_prompt(topic: str) -> str:
    return f"""Write a 2000-word {topic} story with cinematic structure:
- ACT 1: Setup world/characters (600 words)
- ACT 2: Rising conflict/climax (800 words)  
- ACT 3: Resolution/twist (600 words)
Professional prose, vivid sensory details, character-driven dialogue, thematic depth."""

def generate_image_prompt(topic: str) -> str:
    return f"""Hyper-detailed {topic}, cinematic lighting, dramatic composition, ultra-realistic, 8K resolution, intricate details, volumetric lighting, atmospheric perspective, professional photography, in the style of [cinematic masterpiece], perfect anatomy, sharp focus, highest quality, trending on ArtStation."""

def generate_code_prompt(topic: str) -> str:
    return f"""Complete, production-ready Python code for {topic}:
- Follow PEP8 standards
- Include error handling, logging, type hints
- Use modern libraries (fastapi/flask/sqlalchemy etc.)
- Add comprehensive docstrings and comments
- Include requirements.txt and example usage
- Make it deployable to Railway/Heroku instantly."""

def generate_social_prompt(topic: str) -> str:
    return f"""Viral {topic} social media post:
- Attention-grabbing hook (first 3 seconds)
- Emotional storytelling arc
- 3-5 punchy bullet points
- Strong CTA (call-to-action)
- Perfect for Instagram Reels/TikTok (15-30s)
- Trending hashtags, emoji optimization, copy-paste ready."""

def generate_cinematic_prompt(topic: str) -> str:
    return f"""Cinematic {topic} scene breakdown:
- Wide establishing shot → medium → extreme closeup
- Dynamic camera movement (dolly/steadicam/orbit)
- Hollywood lighting setup (3-point, practicals, motivated)
- Emotional beats with actor directions
- Sound design notes (foley, score, ambience)
- Ready for film production storyboard."""

def generate_restoration_prompt(topic: str) -> str:
    return f"""4K Restoration timelapse of {topic}:
- Before/after split-screen progression
- Professional tools (Dremel, ultrasonic, chemicals)
- Historical accuracy, period-correct techniques
- Satisfying cleaning sequences, rust removal
- Ambient workshop sounds, detailed closeups
- 60fps smooth motion, perfect for YouTube Shorts."""

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    await update.message.reply_text("❌ Cancelled. Use /start for new prompt!")
    return ConversationHandler.END

def main():
    """Main bot function"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_MODE: [CallbackQueryHandler(mode_selected)],
            ENTERING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_prompt)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    
    # Error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
    
    application.add_error_handler(error_handler)
    
    # Start polling
    print("🤖 Bot started! Press Ctrl+C to stop.")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
