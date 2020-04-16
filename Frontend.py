import os
import sys
import wx

VERSION = '0.4.3'

wx_app = wx.App()


def init_gui():
    wx_app.MainLoop()


def kill_gui():
    wx_app.ExitMainLoop()


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except BaseException:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Selector(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'EverClient session')
        self.SetIcon(wx.Icon(resource_path('Assets' + os.sep + 'favicon.ico'), wx.BITMAP_TYPE_ICO))

        def select_images(event=None):
            with wx.FileDialog(self, 'Select images', wildcard='JPEG images |*.jpg;*.jpeg',
                               style=wx.FD_OPEN | wx.FD_MULTIPLE) as file_dialog:
                if file_dialog.ShowModal() != wx.ID_CANCEL:
                    self.files = file_dialog.GetPaths()
                self.images_label.SetLabel(f'{len(self.files) if self.files else "None"} selected')

        def select_directory(event=None):
            with wx.DirDialog(self, 'Select target directory', defaultPath=self.target_dir,
                              style=wx.DD_DIR_MUST_EXIST | wx.DD_NEW_DIR_BUTTON) as dir_dialog:
                if dir_dialog.ShowModal() != wx.ID_CANCEL:
                    self.target_dir = dir_dialog.GetPath()
                if self.target_dir:
                    self.dir_label.SetLabel('Selected')
                else:
                    self.dir_label.SetLabel('Not selected')

        def show_help(event=None):
            wx.MessageBox(
                f'''
Let's Enhance workaround.

1. Click Select images to select images you want to enhance
2. Click Select target directory to choose the directory where to put enhanced images
3. Click Start
4. Wait

EverClient {VERSION} by Yxbcvn410, inc.
                ''',
                'Help',
                wx.ICON_INFORMATION
            )

        self.files = []
        self.target_dir = ''

        fgs = wx.FlexGridSizer(3, 2, 4, 4)
        self.images_label = wx.StaticText(self, label='None selected')
        self.dir_label = wx.StaticText(self, label='Not selected')
        self.buttons = [
            wx.Button(self, label='Select Images'),
            wx.Button(self, label='Select Folder'),
            wx.Button(self, label='Start'),
            wx.Button(self, label='About...')
        ]

        self.buttons[0].Bind(wx.EVT_BUTTON, select_images)
        self.buttons[1].Bind(wx.EVT_BUTTON, select_directory)
        self.buttons[3].Bind(wx.EVT_BUTTON, show_help)
        self.Bind(wx.EVT_CLOSE, lambda *args: kill_gui())

        ibs = wx.BoxSizer(wx.VERTICAL)
        ibs.AddStretchSpacer()
        ibs.Add(self.images_label, wx.CENTRE)
        ibs.AddStretchSpacer()

        dbs = wx.BoxSizer(wx.VERTICAL)
        dbs.AddStretchSpacer()
        dbs.Add(self.dir_label, wx.CENTER)
        dbs.AddStretchSpacer()

        fgs.AddMany([
            (self.buttons[0], 0, wx.EXPAND),
            (ibs, 1, wx.EXPAND),
            (self.buttons[1], 2, wx.EXPAND),
            (dbs, 3, wx.EXPAND),
            (self.buttons[2], 4, wx.EXPAND),
            (self.buttons[3], 5, wx.EXPAND),
        ])
        fgs.AddGrowableRow(0, 1)
        fgs.AddGrowableRow(1, 1)
        fgs.AddGrowableRow(2, 1)
        fgs.AddGrowableCol(0, 1)
        fgs.AddGrowableCol(1, 1)

        self.SetSizer(fgs)

    def activate(self, select_callback):
        def start(event=None):
            if self.files and self.target_dir:
                self.Show(False)
                select_callback(self.files, self.target_dir)
            elif not self.files:
                wx.MessageBox('No pictures selected', 'Error', wx.ICON_ERROR)
            else:
                wx.MessageBox('No output directory selected', 'Error', wx.ICON_ERROR)

        self.buttons[2].Bind(wx.EVT_BUTTON, start)
        self.Show(True)


class Terminal(wx.Frame):
    def __init__(self):
        super().__init__(None, wx.ID_ANY, 'EverClient session', size=(250, 300))
        self.SetIcon(wx.Icon(resource_path('Assets' + os.sep + 'favicon.ico'), wx.BITMAP_TYPE_ICO))

        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.abort_button = wx.Button(self, label='Abort')
        self.progress_bar = wx.Gauge(self, range=100)

        fgs = wx.FlexGridSizer(3, 0, 4, 4)
        bs = wx.BoxSizer(wx.HORIZONTAL)
        bs.AddStretchSpacer()
        bs.Add(self.abort_button, wx.CENTRE)
        bs.AddStretchSpacer()
        fgs.AddMany([(self.text, 0, wx.EXPAND), (self.progress_bar, 1, wx.EXPAND), (bs, 2, wx.EXPAND)])
        fgs.AddGrowableRow(0, 1)
        fgs.AddGrowableCol(0, 1)
        self.SetSizer(fgs)

    def print(self, line):
        self.text.AppendText(line + '\n')

    def set_progress(self, progress):
        self.progress_bar.SetValue(self.progress_bar.GetRange() * progress)

    def activate(self, abort_callback):
        self.abort_button.Bind(wx.EVT_BUTTON, lambda *args: abort_callback())
        self.Bind(wx.EVT_CLOSE, lambda *args: abort_callback())
        self.Show(True)
