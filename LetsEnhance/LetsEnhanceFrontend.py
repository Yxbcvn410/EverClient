import wx
from threading import Thread
from Frontend import AbstractSelector, kill_gui, EmptyFunction
from LetsEnhance.LetsEnhanceBackend import LetsEnhanceComplexSession

session = LetsEnhanceComplexSession()


class LetsEnhanceSelector(AbstractSelector):
    def __init__(self, parent, terminal):
        super().__init__(parent, terminal)

        def select_images(_event=None):
            with wx.FileDialog(self, 'Select images', wildcard='JPEG images |*.jpg;*.jpeg',
                               style=wx.FD_OPEN | wx.FD_MULTIPLE) as file_dialog:
                if file_dialog.ShowModal() != wx.ID_CANCEL:
                    self.files = file_dialog.GetPaths()
                self.images_label.SetLabel(f'{len(self.files) if self.files else "None"} selected')

        def select_directory(_event=None):
            with wx.DirDialog(self, 'Select target directory', defaultPath=self.target_dir,
                              style=wx.DD_DIR_MUST_EXIST | wx.DD_NEW_DIR_BUTTON) as dir_dialog:
                if dir_dialog.ShowModal() != wx.ID_CANCEL:
                    self.target_dir = dir_dialog.GetPath()
                if self.target_dir:
                    self.dir_label.SetLabel('Selected')
                else:
                    self.dir_label.SetLabel('Not selected')

        self.files = []
        self.target_dir = ''

        fgs = wx.FlexGridSizer(2, 2, 4, 4)
        self.images_label = wx.StaticText(self, label='None selected')
        self.dir_label = wx.StaticText(self, label='Not selected')
        self.button_select_images = wx.Button(self, label='Select Images')
        self.button_select_dir = wx.Button(self, label='Select Folder')

        self.button_select_images.Bind(wx.EVT_BUTTON, select_images)
        self.button_select_dir.Bind(wx.EVT_BUTTON, select_directory)
        self.Bind(wx.EVT_CLOSE, lambda *args: kill_gui())

        fgs.AddMany([
            (self.button_select_images, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND),
            (self.images_label, 1, wx.ALIGN_CENTER),
            (self.button_select_dir, 2, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND),
            (self.dir_label, 3, wx.ALIGN_CENTER),
        ])
        fgs.AddGrowableCol(1, 1)

        self.SetSizer(fgs)

    NAME = "Let's Enhance"

    HELP_STR = """
1. Click Select images to select images you want to enhance
2. Click Select target directory to choose the directory where to put enhanced images
3. Click Start
4. Wait
"""

    def get_callback_on_selected(self):
        if self.files and self.target_dir:
            # This callback is linked to the Terminal's Abort button click
            def abort_callback():
                try:
                    session.abort()
                except ValueError:
                    pass
                kill_gui()

            # This callback is linked to the SelectorFrame Start button click
            def lets_enhance_start_callback(files, target_dir):
                self.terminal.activate(abort_callback)
                session_thread = Thread(target=session.perform, args=(files, target_dir),
                                        kwargs={'print_callback': self.terminal.print,
                                                'progress_callback': self.terminal.set_progress,
                                                'finalize_callback': self.terminal.finalize})
                session_thread.daemon = True
                session_thread.start()

            return lambda: lets_enhance_start_callback(self.files, self.target_dir)
        elif not self.files:
            wx.MessageBox('No pictures selected', 'Error', wx.ICON_ERROR)
        else:
            wx.MessageBox('No output directory selected', 'Error', wx.ICON_ERROR)
        return EmptyFunction()
