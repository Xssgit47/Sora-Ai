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
API_URL = "https://texttovideoapi.anshapi.workers.dev/"
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
        logger.info(f"API URL: {api_request_url}")
        
        # Make API request with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(api_request_url, headers=headers, timeout=120)
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Log response preview for debugging
            try:
                if len(response.content) < 10000:  # If small, probably JSON or error
                    logger.info(f"API Response Preview: {response.text[:500]}")
                else:
                    logger.info(f"API Response is large binary data, size: {len(response.content)} bytes")
            except:
                logger.info(f"API Response is binary data, size: {len(response.content)} bytes")
            
            # Check if it's JSON response
            if 'application/json' in content_type or (len(response.content) < 10000 and response.text.strip().startswith('{')):
                try:
                    data = response.json()
                    logger.info(f"API JSON Response: {data}")
                    
                    # Check for various response formats
                    video_url = None
                    if 'video_url' in data:
                        video_url = data['video_url']
                    elif 'url' in data:
                        video_url = data['url']
                    elif 'video' in data:
                        video_url = data['video']
                    elif 'result' in data:
                        video_url = data['result']
                    elif 'videoUrl' in data:
                        video_url = data['videoUrl']
                    elif 'data' in data:
                        if isinstance(data['data'], dict):
                            video_url = data['data'].get('url') or data['data'].get('video_url') or data['data'].get('videoUrl')
                        elif isinstance(data['data'], str):
                            video_url = data['data']
                    
                    # Check for error in JSON
                    if 'error' in data:
                        error_msg = data.get('error', 'Unknown error')
                        await processing_msg.edit_text(
                            f'❌ API Error: {error_msg}\n\nPlease try again with a different prompt.'
                        )
                        logger.error(f"API returned error: {error_msg}")
                        return
                    
                    if 'message' in data and not video_url:
                        error_msg = data.get('message', 'Unknown error')
                        await processing_msg.edit_text(
                            f'❌ API Message: {error_msg}\n\nPlease try again.'
                        )
                        logger.error(f"API returned message: {error_msg}")
                        return
                    
                    if video_url:
                        logger.info(f"Video URL found: {video_url}")
                        # Try to send video from URL
                        try:
                            await update.message.reply_video(
                                video=video_url,
                                caption=f'🎬 Generated video for: "{user_prompt}"',
                                read_timeout=120,
                                write_timeout=120
                            )
                            await processing_msg.delete()
                            logger.info(f"Video sent successfully from URL: {video_url}")
                        except Exception as e:
                            logger.error(f"Failed to send video from URL: {str(e)}")
                            # Try downloading and sending
                            try:
                                logger.info(f"Attempting to download video from: {video_url}")
                                video_response = requests.get(video_url, timeout=120, headers=headers)
                                if video_response.status_code == 200:
                                    await update.message.reply_video(
                                        video=video_response.content,
                                        caption=f'🎬 Generated video for: "{user_prompt}"'
                                    )
                                    await processing_msg.delete()
                                    logger.info(f"Video downloaded and sent successfully")
                                else:
                                    raise Exception(f"Failed to download video: {video_response.status_code}")
                            except Exception as e2:
                                await processing_msg.edit_text(
                                    f'❌ Could not send video.\n\nError: {str(e2)[:100]}'
                                )
                                logger.error(f"Failed to download/send video: {str(e2)}")
                    else:
                        await processing_msg.edit_text(
                            '❌ API response does not contain a video URL.\n\n'
                            f'Response keys: {", ".join(data.keys())}\n\n'
                            'Please try again or contact support.'
                        )
                        logger.error(f"No video URL found in JSON response: {data}")
                        
                except ValueError as e:
                    await processing_msg.edit_text(
                        '❌ Invalid API response format. Please try again.'
                    )
                    logger.error(f"Failed to parse JSON: {str(e)}")
                    logger.error(f"Response text: {response.text[:500]}")
                    
            # Check if it's direct video content
            elif 'video' in content_type or len(response.content) > 10000:
                try:
                    logger.info(f"Attempting to send direct video content, size: {len(response.content)} bytes")
                    await update.message.reply_video(
                        video=response.content,
                        caption=f'🎬 Generated video for: "{user_prompt}"'
                    )
                    await processing_msg.delete()
                    logger.info(f"Direct video content sent successfully")
                except Exception as e:
                    await processing_msg.edit_text(
                        f'❌ Failed to send video: {str(e)[:100]}'
                    )
                    logger.error(f"Failed to send video content: {str(e)}")
            else:
                # Unknown response format
                await processing_msg.edit_text(
                    f'❌ Unexpected API response format.\n\n'
                    f'Content-Type: {content_type}\n'
                    f'Size: {len(response.content)} bytes\n\n'
                    'Please check the logs or try again.'
                )
                logger.error(f"Unknown response format. Content-Type: {content_type}")
                logger.error(f"Response preview: {response.text[:500]}")
                
        else:
            await processing_msg.edit_text(
                f'❌ API request failed with status code: {response.status_code}\n\nPlease try again later.'
            )
            logger.error(f"API request failed: {response.status_code}")
            try:
                logger.error(f"Response: {response.text[:500]}")
            except:
                logger.error(f"Could not decode response")
            
    except requests.Timeout:
        await processing_msg.edit_text(
            '⏰ Request timed out. The server might be busy. Please try again.'
        )
        logger.error("API request timed out")
        
    except Exception as e:
        await processing_msg.edit_text(
            f'❌ An error occurred: {str(e)[:100]}\n\nPlease try again.'
        )
        logger.error(f"Error generating video: {str(e)}", exc_info=True)

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
