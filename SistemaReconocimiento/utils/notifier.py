import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("sistema_reconocimiento.utils.notifier")


class Notifier(ABC):
    @abstractmethod
    def send_message(self, phone: str, message: str) -> bool:
        ...


class WhatsAppAutoNotifier(Notifier):
    def send_message(self, phone: str, message: str) -> bool:
        if not phone:
            logger.warning("WhatsApp phone not configured")
            return False
        try:
            import pywhatkit as kit
            kit.sendwhatmsg_instantly(
                phone_no=phone,
                message=message,
                wait_time=15,
                tab_close=True,
            )
            logger.info(f"WhatsApp message sent to {phone}")
            return True
        except ImportError:
            logger.warning("pywhatkit not installed. Install with: pip install pywhatkit")
            return False
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False


class LogNotifier(Notifier):
    def send_message(self, phone: str, message: str) -> bool:
        logger.info(f"[NOTIFICATION] To: {phone} | {message}")
        return True
