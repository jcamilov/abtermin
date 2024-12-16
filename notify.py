import os
from dotenv import load_dotenv
from telegram import Bot, InputFile
from telegram.error import TelegramError
import asyncio
import logging

# Load environment variables from .env file
load_dotenv()

# These should be stored in environment variables or a config file
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or BOT_TOKEN
        self.chat_id = chat_id or CHAT_ID
        
        if not self.token:
            raise ValueError("Telegram Bot Token is required")
        if not self.chat_id:
            raise ValueError("Telegram Chat ID is required")
            
        self.bot = Bot(token=self.token)

    async def send_message(self, message: str) -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            # logger.info(f"Message sent successfully: {message[:50]}...")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False

    async def send_photo(self, photo_path: str, caption: str = None) -> bool:
        """
        Send a photo via Telegram.
        
        Args:
            photo_path (str): Path to the photo file
            caption (str): Optional caption for the photo
            
        Returns:
            bool: True if photo was sent successfully, False otherwise
        """
        try:
            with open(photo_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=InputFile(photo),
                    caption=caption
                )
            # logger.info(f"Photo sent successfully: {photo_path}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send photo: {str(e)}")
            return False
        except FileNotFoundError:
            logger.error(f"Photo file not found: {photo_path}")
            return False

def send_notification(message: str) -> bool:
    """
    Synchronous wrapper for sending notifications.
    
    Args:
        message (str): The message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        notifier = TelegramNotifier()
        return asyncio.run(notifier.send_message(message))
    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}")
        return False

def send_photo_notification(photo_path: str, caption: str = None) -> bool:
    """
    Synchronous wrapper for sending photo notifications.
    
    Args:
        photo_path (str): Path to the photo file
        caption (str): Optional caption for the photo
        
    Returns:
        bool: True if photo was sent successfully, False otherwise
    """
    try:
        notifier = TelegramNotifier()
        return asyncio.run(notifier.send_photo(photo_path, caption))
    except Exception as e:
        logger.error(f"Error in send_photo_notification: {str(e)}")
        return False

# Example usage
if __name__ == "__main__":
    # Example of how to use the notification system
    success = send_notification("🔔 Test notification from Python!")
    print(f"Notification {'sent successfully' if success else 'failed'}")
