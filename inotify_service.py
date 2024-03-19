import logging
import os
from asyncinotify import Inotify, Mask


class InotifyMonitoring:
    """
    Сервис для мониторинга локальных файлов
    """
    def __init__(self):
        self.notify_dir = os.getenv("NOTIFY_DIR", ".")

    async def detection(self, rabbit):
        with Inotify() as inotify:
            watch_flags = Mask.CREATE | Mask.MODIFY
            inotify.add_watch(self.notify_dir, mask=watch_flags)
            logging.info("INOTIFY ------- Notify monitoring started.")
            async for event in inotify:
                if event.mask & Mask.CREATE or event.mask & Mask.MODIFY:
                    file_name = f"{self.notify_dir}/{str(event.name)}"
                    logging.info("INOTIFY ------- Event detected.")
                    await rabbit.send_message(event.name, file_name)
