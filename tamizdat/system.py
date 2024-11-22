import threading

from telegram.ext.updater import Updater


def shutdown(updater: Updater):
    updater.stop()
    updater.is_idle = False


def stop_bot(updater: Updater):
    threading.Thread(target=shutdown, args=(updater, )).start()
