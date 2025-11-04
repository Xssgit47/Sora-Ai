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
API_BASE_URL = "https://texttovideoapi.anshapi.workers.dev"
GENERATE_ENDPOINT = f"{API_BASE_URL}/generate"
VIDEO_ENDPOINT = f"{API_BASE_URL}/video"
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f'Hi —<b>DANGER</b> 💥! 👋\n\n'
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
        '2. Wait while I generate your video (this may take 1-2 minutes)\n'
        '3. I\'ll send you the video once it\'s ready!\n\n'
        '*Tips for better results:*\n'
        '• Be specific and descriptive\n'
        '• Keep prompts clear and concise\n'
        '• Examples: "a cat playing piano", "fireworks in the sky"\n\n'
        '*Need more help?* Just send me a message!',
        parse_mode='Markdown'
    )

async def generate_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate video from user's text prompt using AnshAPI."""
    user_prompt = update.message.text
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        '⏳ Generating your video...\nThis may take 1-2 minutes, please wait!'
    )
    
    try:
        # Step 1: Generate video using /generate endpoint
        encoded_prompt = quote(user_prompt)
        generate_url = f"{GENERATE_ENDPOINT}?prompt={encoded_prompt}"
        
        logger.info(f"Requesting video for prompt: {user_prompt}")
        logger.info(f"Generate URL: {generate_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Call the /generate endpoint
        response = requests.get(generate_url, headers=headers, timeout=150)
        
        logger.info(f"Generate Response Status: {response.status_code}")
        logger.info(f"Generate Response Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Log response for debugging
            try:
                if len(response.content) < 10000:
                    logger.info(f"Generate Response Preview: {response.text[:500]}")
                else:
                    logger.info(f"Generate Response is large data, size: {len(response.content)} bytes")
            except:
                logger.info(f"Generate Response is binary, size: {len(response.content)} bytes")
            
            # Check if response is JSON with video ID
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    logger.info(f"Generate JSON Response: {data}")
                    
                    # Check for error
                    if 'error' in data:
                        error_msg = data.get('error', 'Unknown error')
                        await processing_msg.edit_text(
                            f'❌ API Error: {error_msg}\n\nPlease try again with a different prompt.'
                        )
                        logger.error(f"API error: {error_msg}")
                        return
                    
                    # Extract video ID or URL
                    video_id = data.get('id') or data.get('video_id') or data.get('videoId')
                    video_url = data.get('url') or data.get('video_url') or data.get('videoUrl')
                    
                    if video_id:
                        # Step 2: Fetch video using /video endpoint with ID
                        logger.info(f"Video ID received: {video_id}")
                        video_fetch_url = f"{VIDEO_ENDPOINT}?id={video_id}"
                        logger.info(f"Fetching video from: {video_fetch_url}")
                        
                        await processing_msg.edit_text(
                            '⏳ Video generated! Downloading...'
                        )
                        
                        video_response = requests.get(video_fetch_url, headers=headers, timeout=120)
                        
                        if video_response.status_code == 200:
                            logger.info(f"Video downloaded, size: {len(video_response.content)} bytes")
                            await update.message.reply_video(
                                video=video_response.content,
                                caption=f'🎬 Generated video for: "{user_prompt}"'
                            )
                            await processing_msg.delete()
                            logger.info(f"Video sent successfully")
                        else:
                            raise Exception(f"Failed to fetch video: {video_response.status_code}")
                    
                    elif video_url:
                        # Direct video URL provided
                        logger.info(f"Video URL received: {video_url}")
                        await update.message.reply_video(
                            video=video_url,
                            caption=f'🎬 Generated video for: "{user_prompt}"',
                            read_timeout=120,
                            write_timeout=120
                        )
                        await processing_msg.delete()
                        logger.info(f"Video sent successfully from URL")
                    
                    else:
                        await processing_msg.edit_text(
                            '❌ No video ID or URL in API response.\n\n'
                            f'Response: {str(data)[:200]}'
                        )
                        logger.error(f"No video ID/URL found: {data}")
                
                except ValueError as e:
                    await processing_msg.edit_text(
                        '❌ Invalid JSON response from API.'
                    )
                    logger.error(f"JSON parse error: {str(e)}")
            
            # Check if response is direct video content
            elif 'video' in content_type or len(response.content) > 10000:
                logger.info(f"Direct video content received, size: {len(response.content)} bytes")
                try:
                    await update.message.reply_video(
                        video=response.content,
                        caption=f'🎬 Generated video for: "{user_prompt}"'
                    )
                    await processing_msg.delete()
                    logger.info(f"Direct video sent successfully")
                except Exception as e:
                    await processing_msg.edit_text(
                        f'❌ Failed to send video: {str(e)[:100]}'
                    )
                    logger.error(f"Failed to send video: {str(e)}")
            
            else:
                await processing_msg.edit_text(
                    f'❌ Unexpected response format.\n\n'
                    f'Content-Type: {content_type}\n'
                    f'Size: {len(response.content)} bytes'
                )
                logger.error(f"Unknown format: {content_type}")
                logger.error(f"Response: {response.text[:500]}")
        
        else:
            await processing_msg.edit_text(
                f'❌ API request failed with status: {response.status_code}\n\n'
                'Please try again later.'
            )
            logger.error(f"API failed: {response.status_code} - {response.text[:500]}")
    
    except requests.Timeout:
        await processing_msg.edit_text(
            '⏰ Request timed out. Video generation takes time.\n\nPlease try again.'
        )
        logger.error("Request timed out")
    
    except Exception as e:
        await processing_msg.edit_text(
            f'❌ An error occurred: {str(e)[:100]}\n\nPlease try again.'
        )
        logger.error(f"Error: {str(e)}", exc_info=True)

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
