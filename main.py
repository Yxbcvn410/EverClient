from Frontend import Terminal, init_gui, SelectorFrame
from LetsEnhance.LetsEnhanceFrontend import LetsEnhanceSelector

terminal = Terminal()

selector_frame = SelectorFrame()
selector_frame.add_selector(LetsEnhanceSelector(selector_frame, terminal))
selector_frame.activate()
init_gui()
