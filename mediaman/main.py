
import sys

from PyQt4.QtGui import QApplication

from mediamanwindow import MediaManWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('plastique')
    window = MediaManWindow()
    window.show()
    sys.exit(app.exec_())
