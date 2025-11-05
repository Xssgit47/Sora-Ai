import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import quote
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configuration
API_URL = "https://socialdownloder2.anshapi.workers.dev/"
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Supported platforms
SUPPORTED_PLATFORMS = [
    "Instagram", "TikTok", "YouTube", "Facebook", 
    "Twitter", "Reddit", "Pinterest", "Threads"
]

def is_valid_url(url):
    """Check if the text contains a valid URL."""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return bool(url_pattern.search(url))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    platforms = "\n".join([f"• {platform}" for platform in SUPPORTED_PLATFORMS])
    
    await update.message.reply_text(
        f'Hi —<b>DANGER</b> 💥! 👋\n\n'
        f'I can download videos and photos from social media! 📥\n\n'
        f'<b>Supported Platforms:</b>\n{platforms}\n\n'
        f'<b>How to use:</b>\n'
        f'Just send me a link from any supported platform!\n\n'
        f'<b>Examples:</b>\n'
        f'• Instagram: https://www.instagram.com/reel/...\n'
        f'• TikTok: https://www.tiktok.com/@user/video/...\n'
        f'• YouTube: https://www.youtube.com/shorts/...\n\n'
        f'<b>Commands:</b>\n'
        f'/start - Show this message\n'
        f'/help - Get help',
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    platforms = "\n".join([f"• {platform}" for platform in SUPPORTED_PLATFORMS])
    
    await update.message.reply_text(
        f'📖 *Social Media Downloader Bot*\n\n'
        f'*How to use:*\n'
        f'1. Copy a video or photo link from any supported platform\n'
        f'2. Send the link to me\n'
        f'3. I\'ll download and send you the media!\n\n'
        f'*Supported Platforms:*\n{platforms}\n\n'
        f'*Tips:*\n'
        f'• Send the direct link (URL)\n'
        f'• Works with posts, reels, videos, and shorts\n'
        f'• No watermarks on most platforms\n\n'
        f'*Need more help?* Just send me a link!',
        parse_mode='Markdown'
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download media from social media URL."""
    user_input = update.message.text.strip()
    
    # Check if input contains a URL
    if not is_valid_url(user_input):
        await update.message.reply_text(
            '❌ Please send a valid social media link.\n\n'
            'Example: https://www.instagram.com/reel/...'
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        '⏳ Downloading your media...\nPlease wait!'
    )
    
    try:
        # Encode the URL for API request
        encoded_url = quote(user_input)
        api_request_url = f"{API_URL}?url={encoded_url}"
        
        logger.info(f"Downloading from URL: {user_input}")
        logger.info(f"API Request URL: {api_request_url}")
        
        # Make API request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(api_request_url, headers=headers, timeout=120)
        
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Log response preview
            try:
                if len(response.content) < 10000:
                    logger.info(f"API Response Preview: {response.text[:500]}")
                else:
                    logger.info(f"API Response is large data, size: {len(response.content)} bytes")
            except:
                logger.info(f"API Response is binary, size: {len(response.content)} bytes")
            
            # Check if response is JSON
            if 'application/json' in content_type or (len(response.content) < 10000 and response.text.strip().startswith('{')):
                try:
                    data = response.json()
                    logger.info(f"API JSON Response: {data}")
                    
                    # Check for error
                    if 'error' in data:
                        error_msg = data.get('error', 'Unknown error')
                        await processing_msg.edit_text(
                            f'❌ Error: {error_msg}\n\n'
                            'Please check the link and try again.'
                        )
                        logger.error(f"API error: {error_msg}")
                        return
                    
                    # Extract media URL (various possible formats)
                    media_url = None
                    media_type = 'video'  # default
                    
                    # Try different response formats
                    if 'url' in data:
                        media_url = data['url']
                    elif 'video_url' in data:
                        media_url = data['video_url']
                    elif 'videoUrl' in data:
                        media_url = data['videoUrl']
                    elif 'download_url' in data:
                        media_url = data['download_url']
                    elif 'media' in data:
                        if isinstance(data['media'], str):
                            media_url = data['media']
                        elif isinstance(data['media'], dict):
                            media_url = data['media'].get('url')
                    elif 'data' in data:
                        if isinstance(data['data'], str):
                            media_url = data['data']
                        elif isinstance(data['data'], dict):
                            media_url = data['data'].get('url') or data['data'].get('video_url')
                    
                    # Check for media type
                    if 'type' in data:
                        media_type = data['type'].lower()
                    elif 'media_type' in data:
                        media_type = data['media_type'].lower()
                    
                    if media_url:
                        logger.info(f"Media URL found: {media_url}, Type: {media_type}")
                        
                        await processing_msg.edit_text(
                            '⏳ Downloading media...'
                        )
                        
                        # Download the media
                        media_response = requests.get(media_url, headers=headers, timeout=120)
                        
                        if media_response.status_code == 200:
                            logger.info(f"Media downloaded, size: {len(media_response.content)} bytes")
                            
                            # Send based on media type
                            if 'image' in media_type or 'photo' in media_type:
                                await update.message.reply_photo(
                                    photo=media_response.content,
                                    caption='📸 Downloaded by —DANGER Bot'
                                )
                            else:
                                # Default to video
                                await update.message.reply_video(
                                    video=media_response.content,
                                    caption='🎬 Downloaded by —DANGER Bot'
                                )
                            
                            await processing_msg.delete()
                            logger.info(f"Media sent successfully")
                        else:
                            raise Exception(f"Failed to download media: {media_response.status_code}")
                    else:
                        await processing_msg.edit_text(
                            '❌ Could not extract media URL from API response.\n\n'
                            f'Response keys: {", ".join(data.keys())}\n\n'
                            'Please try again or use a different link.'
                        )
                        logger.error(f"No media URL found in response: {data}")
                
                except ValueError as e:
                    await processing_msg.edit_text(
                        '❌ Invalid API response format.'
                    )
                    logger.error(f"JSON parse error: {str(e)}")
            
            # Check if response is direct media content
            elif 'video' in content_type or 'image' in content_type or len(response.content) > 10000:
                logger.info(f"Direct media content received, size: {len(response.content)} bytes")
                
                try:
                    if 'image' in content_type:
                        await update.message.reply_photo(
                            photo=response.content,
                            caption='📸 Downloaded by —DANGER Bot'
                        )
                    else:
                        await update.message.reply_video(
                            video=response.content,
                            caption='🎬 Downloaded by —DANGER Bot'
                        )
                    
                    await processing_msg.delete()
                    logger.info(f"Direct media sent successfully")
                except Exception as e:
                    await processing_msg.edit_text(
                        f'❌ Failed to send media: {str(e)[:100]}'
                    )
                    logger.error(f"Failed to send media: {str(e)}")
            
            else:
                await processing_msg.edit_text(
                    f'❌ Unexpected response format.\n\n'
                    f'Content-Type: {content_type}\n'
                    f'Size: {len(response.content)} bytes\n\n'
                    'Please try a different link.'
                )
                logger.error(f"Unknown format: {content_type}")
                logger.error(f"Response: {response.text[:500]}")
        
        else:
            await processing_msg.edit_text(
                f'❌ Download failed (Status: {response.status_code})\n\n'
                'Possible reasons:\n'
                '• Link is invalid or expired\n'
                '• Platform not supported\n'
                '• Media is private or deleted\n\n'
                'Please try another link.'
            )
            logger.error(f"API failed: {response.status_code} - {response.text[:500]}")
    
    except requests.Timeout:
        await processing_msg.edit_text(
            '⏰ Request timed out.\n\n'
            'The download is taking too long. Please try again.'
        )
        logger.error("Request timed out")
    
    except Exception as e:
        await processing_msg.edit_text(
            f'❌ An error occurred: {str(e)[:100]}\n\n'
            'Please try again with a different link.'
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    
    # Start the Bot
    logger.info("Social Media Downloader Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
