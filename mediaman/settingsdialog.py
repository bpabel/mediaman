

import sys
import os

from PyQt4 import uic
from PyQt4.QtGui import QDialog, QIcon, QMessageBox


class SettingsDialog(QDialog):

    app_name = 'MediaMan Settings'

    def __init__(self, parent, *args, **kwargs):
        super(SettingsDialog, self).__init__(parent, *args, **kwargs)
        uifile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'settingsdialog.ui')
        uic.loadUi(uifile, self)
        self.setWindowTitle(self.app_name)


        self.ui_save_btn.clicked.connect(self.saveSettings)
        self.ui_cancel_btn.clicked.connect(self.reject)

    def saveSettings(self):
        self.accept()
