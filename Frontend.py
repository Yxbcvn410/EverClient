import os
import sys
from abc import abstractmethod

import wx

VERSION = 'v0.5.4'

__wx_app = wx.App()


def init_gui():
    __wx_app.MainLoop()


def kill_gui():
    __wx_app.ExitMainLoop()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class EmptyFunction:
    def __init__(self, return_val=None):
        self.return_val = return_val

    def __call__(self, *args, **kwargs):
        return self.return_val

    def __bool__(self):
        return False


class AbstractSelector(wx.Panel):
    @abstractmethod
    def __init__(self, parent, terminal):
        wx.Panel.__init__(self, parent)
        self.terminal = terminal

    NAME = 'Abstract'

    HELP_STR = """
    No help available"""

    @abstractmethod
    def get_callback_on_selected(self):
        """
        :return: Function with no parameters to be called on Start button click
         Return EmptyFunction if selection is invalid (in this case this function should inform user about it)
        """
        return EmptyFunction


class SelectorFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'EverClient')
        self.SetIcon(wx.Icon(resource_path('Assets' + os.sep + 'favicon.ico'), wx.BITMAP_TYPE_ICO))
        self.Bind(wx.EVT_CLOSE, lambda event=None: kill_gui())
        self.selectors: [AbstractSelector] = []

        self.button_start = wx.Button(self, label='Start')
        self.button_help = wx.Button(self, label='About...')

        def provide_help(_event=None):
            wx.MessageBox(f'EverClient {VERSION} by Yxbcvn410, inc.'
                          f'\n\n{self.selector_panel.NAME} workaround information:\n{self.selector_panel.HELP_STR}',
                          'About')

        self.button_help.Bind(wx.EVT_BUTTON, provide_help)

        self.selector_cb = wx.Choice(self, choices=[])
        self.selector_cb.Bind(wx.EVT_CHOICE, self._change_selector)
        self.selector_panel = None  # AbstractSelector(self, lambda: None)

        self.panel_box = wx.BoxSizer(wx.VERTICAL)

        self.sizer = wx.GridBagSizer(4, 4)
        self.sizer.Add(self.selector_cb, (0, 0), (1, 2), wx.EXPAND, border=5)
        self.sizer.Add(self.panel_box, (1, 0), (1, 2), wx.EXPAND, border=5)
        self.sizer.Add(self.button_start, (2, 0), (1, 1), wx.EXPAND, border=5)
        self.sizer.Add(self.button_help, (2, 1), (1, 1), wx.EXPAND, border=5)
        self.sizer.AddGrowableRow(1, 1)
        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 1)
        self.SetSizer(self.sizer)
        self.Show(True)

    def _change_selector(self, _event=None):
        idx = self.selector_cb.GetSelection()
        if idx != wx.NOT_FOUND:
            self.sizer.Remove(self.panel_box)
            self.panel_box = wx.BoxSizer()
            if self.selector_panel:
                self.selector_panel.Hide()
            self.selector_panel = self.selectors[idx]
            self.selector_panel.Show(True)
            self.panel_box.Add(self.selector_panel, 1, wx.EXPAND)
            self.sizer.Add(self.panel_box, (1, 0), (1, 2), wx.EXPAND, border=5)
            self.Layout()
            self.sizer.Layout()
            self.panel_box.Layout()

    def add_selector(self, selector: AbstractSelector):
        selector.Hide()
        self.selectors.append(selector)
        self.selector_cb.Destroy()
        self.selector_cb = wx.Choice(self, choices=[sel.NAME for sel in self.selectors])
        self.selector_cb.Bind(wx.EVT_CHOICE, self._change_selector)
        self.sizer.Add(self.selector_cb, (0, 0), (1, 2), wx.EXPAND, border=5)
        if len(self.selectors) < 2:
            self.selector_cb.Hide()
        else:
            self.selector_cb.Show(True)

    def activate(self):
        def start(_event=None):
            try:
                start_callback = self.selector_panel.get_callback_on_selected()
                if start_callback:
                    self.Show(False)
                    start_callback()
            except AttributeError:
                wx.MessageBox('No selector chosen!', 'Error', wx.ICON_ERROR)

        self.selector_cb.SetSelection(0)
        self._change_selector()
        self.button_start.Bind(wx.EVT_BUTTON, start)
        self.Show(True)


class Terminal(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'EverClient session', size=(450, 300))
        self.SetIcon(wx.Icon(resource_path('Assets' + os.sep + 'favicon.ico'), wx.BITMAP_TYPE_ICO))

        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.abort_button = wx.Button(self, label='Abort')
        self.progress_bar = wx.Gauge(self, range=100)

        fgs = wx.FlexGridSizer(3, 1, 4, 4)
        fgs.AddMany([(self.text, 0, wx.EXPAND, 5), (self.progress_bar, 1, wx.EXPAND, 5),
                     (self.abort_button, 2, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)])
        fgs.AddGrowableRow(0, 1)
        fgs.AddGrowableCol(0, 1)
        self.SetSizer(fgs)

    def print(self, line):
        self.text.AppendText(line + '\n')

    def set_progress(self, progress):
        self.progress_bar.SetValue(self.progress_bar.GetRange() * progress)

    def finalize(self):
        self.set_progress(0)
        self.abort_button.SetLabel('Quit')
        self.abort_button.Unbind(wx.EVT_BUTTON)
        self.abort_button.Bind(wx.EVT_BUTTON, lambda event=None: kill_gui())

    def activate(self, abort_callback):
        self.abort_button.Bind(wx.EVT_BUTTON, lambda event=None: (
            self.print('Aborting...'), abort_callback()))
        self.Bind(wx.EVT_CLOSE, lambda event=None: (
            self.print('Aborting...'), abort_callback()))
        self.Bind(wx.EVT_CLOSE, lambda *args: abort_callback())
        self.Show(True)
