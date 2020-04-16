from threading import Thread
from Frontend import Selector, Terminal, init_gui, kill_gui
from LetsEnhance import LetsEnhanceComplexSession

terminal = Terminal()
session = LetsEnhanceComplexSession()


def abort_callback():
    try:
        session.abort()
    except ValueError:
        pass
    kill_gui()


def start_callback(files, target_dir):
    terminal.activate(abort_callback)
    session_thread = Thread(target=session.perform, args=(files, target_dir),
                            kwargs={'print_callback': terminal.print, 'progress_callback': terminal.set_progress})
    session_thread.daemon = True
    session_thread.start()


Selector().activate(start_callback)
init_gui()
