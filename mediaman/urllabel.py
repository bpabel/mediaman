
from PyQt4.QtGui import QLabel, QPixmap, QPainter
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt4.QtCore import QUrl, Qt


class URLLabel(QLabel):
    """ QLabel subclass to support the display of images via URL.
    
    """

    def __init__(self, parent):
        super(URLLabel, self).__init__(parent)
        self.connection = None
        self._original_pixmap = None
        self.connection = None

    def clear(self):
        self._original_pixmap = None
        super(URLLabel, self).clear()

    def setRemotePixmap(self, url):
        # Lazy creation of QNetworkManager, image download is asynchronous.
        # When the image download is complete (ie the "finished" signal),
        # the image data is read and drawn.
        if self.connection is None:
            self.connection = QNetworkAccessManager(self)
            self.connection.finished.connect(self.pixmapReceived)
        self.connection.get(QNetworkRequest(QUrl(url)))

    def pixmapReceived(self, reply):
        """ Slot for handling the return of the asynchronous image download. """
        if reply.error() != QNetworkReply.NoError:
            reply.deleteLater()
            return

        data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        # The original image is stored as an attribute and drawn manually
        # using an overridden paintEvent.  This is preferable to using the
        # setPixmap() functionality of QLabels because it allows more control
        # over the scaling of the pixmap and allows the size of the QLabel
        # to dictate the pixmap size, and not the other way around.
        self._original_pixmap = pixmap
        reply.deleteLater()
        self.update()

    def paintEvent(self, paintevent):
        super(URLLabel, self).paintEvent(paintevent)
        # Manually draw the downloaded pixmap, scaled to fit the size of the label.
        if self._original_pixmap:
            size = self.size()
            sized_pixmap = self._original_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter = QPainter(self)
            point = self.geometry().topLeft()
            painter.drawPixmap(point, sized_pixmap)
