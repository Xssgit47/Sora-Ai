import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import quote

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configuration
API_URL = "https://texttovideov2.alphaapi.workers.dev/api/"
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f'Hi {user.mention_html()}! 👋\n\n'
        f'I can create videos from your text prompts! 🎬\n\n'
        f'Just send me a text description and I\'ll generate a video for you.\n\n'
        f'Example: "a girl dancing" or "sunset over mountains"\n\n'
        f'Commands:\n'
        f'/start - Show this message\n'
        f'/help - Get help',
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        '📖 *How to use this bot:*\n\n'
        '1. Send me a text prompt describing the video you want\n'
        '2. Wait while I generate your video (this may take a minute)\n'
        '3. I\'ll send you the video once it\'s ready!\n\n'
        '*Tips for better results:*\n'
        '• Be specific and descriptive\n'
        '• Keep prompts clear and concise\n'
        '• Examples: "a cat playing piano", "fireworks in the sky"\n\n'
        '*Need more help?* Just send me a message!',
        parse_mode='Markdown'
    )

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate video from user's text prompt."""
    user_prompt = update.message.text
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        '⏳ Generating your video...\nThis may take a moment, please wait!'
    )
    
    try:
        # Encode the prompt for URL
        encoded_prompt = quote(user_prompt)
        api_request_url = f"{API_URL}?prompt={encoded_prompt}"
        
        logger.info(f"Requesting video for prompt: {user_prompt}")
        
        # Make API request
        response = requests.get(api_request_url, timeout=120)
        
        if response.status_code == 200:
            # Check if response is JSON (error) or video content
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                # API returned JSON, likely contains video URL
                data = response.json()
                if 'video_url' in data:
                    video_url = data['video_url']
                    await update.message.reply_video(
                        video=video_url,
                        caption=f'🎬 Generated video for: "{user_prompt}"'
                    )
                else:
                    await update.message.reply_text(
                        '❌ Sorry, couldn\'t generate the video. Please try again with a different prompt.'
                    )
            else:
                # Direct video content
                video_file = response.content
                await update.message.reply_video(
                    video=video_file,
                    caption=f'🎬 Generated video for: "{user_prompt}"'
                )
            
            # Delete processing message
            await processing_msg.delete()
            logger.info(f"Video generated successfully for: {user_prompt}")
            
        else:
            await processing_msg.edit_text(
                '❌ Failed to generate video. Please try again later.'
            )
            logger.error(f"API request failed with status: {response.status_code}")
            
    except requests.Timeout:
        await processing_msg.edit_text(
            '⏰ Request timed out. The server might be busy. Please try again.'
        )
        logger.error("API request timed out")
        
    except Exception as e:
        await processing_msg.edit_text(
            '❌ An error occurred while generating the video. Please try again.'
        )
        logger.error(f"Error generating video: {str(e)}")

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_video))
    
    # Start the Bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
