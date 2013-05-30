"""

Drop media on window

Files get added to list



Type

Movie
TV Show





"""

import re
import sys
import os
from pprint import pprint
from functools import partial
import time
import shutil
import traceback

from PyQt4 import uic
from PyQt4.QtGui import (QMainWindow, QIcon, QMessageBox, QTreeWidgetItem,
                         QItemDelegate, QProgressBar, QVBoxLayout, QColor,
                         QTreeWidget)
from PyQt4.QtCore import Qt, QUrl, QThread


from settingsdialog import SettingsDialog
from urllabel import URLLabel
from imdbapi import SearchThread, FilepathSearchThread, find_movie






class MediaManWindow(QMainWindow):

    app_name = 'MediaMan'
    app_version = '0.1'

    invalid_chars_map = {
        ':': '',
    }

    def __init__(self, *args, **kwargs):
        super(MediaManWindow, self).__init__(*args, **kwargs)
        uifile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'mediaman.ui')
        uic.loadUi(uifile, self)
        self._loadStyleSheet()
        self.setWindowTitle('{} v{}'.format(self.app_name, self.app_version))
        self._loadIcon(self, 'Cofee')
        self._loadIcon(self.ui_refresh_btn, 'Repeat')
        self._loadIcon(self.ui_lookup_btn, 'FTP Download')
        self._loadIcon(self.ui_settings_btn, 'Work')
        self._loadIcon(self.ui_rename_btn, 'CD Burning')
        self._loadIcon(self.ui_clear_btn, 'Ccleaner')
        self._loadIcon(self.ui_set_movie_btn, 'FTP Upload')

        self._loadIcon(self.ui_manual_btn, 'FTP Upload')
        self._loadIcon(self.ui_set_episode_btn, 'FTP Upload')





        self.current_media_info = None

        self.uiMoviesTXT.setText(ur'E:\Media\Movies')
        self.uiTVTXT.setText(ur'E:\Media\TV Shows')

        self._file_delegate = TreeDelegate(self)
        self.ui_file_tree.setItemDelegate(self._file_delegate)

        self._search_delegate = TreeDelegate(self)
        self.ui_search_tree.setItemDelegate(self._search_delegate)

        self._episode_delegate = TreeDelegate(self)
        self.ui_episode_tree.setItemDelegate(self._episode_delegate)

        self.ui_poster_lbl = URLLabel(self)
        self.ui_poster_lyt.addWidget(self.ui_poster_lbl)

        self.ui_file_tree.dragMoveEvent = self._ui_file_tree_dragMoveEvent
        self.ui_file_tree.dragEnterEvent = self._ui_file_tree_dragEnterEvent
        self.ui_file_tree.dropEvent = self._ui_file_tree_dropEvent
        self.ui_file_tree.keyPressEvent = self._ui_file_tree_keyPressEvent

        self.ui_about_act.triggered.connect(self._about)
        self.ui_license_act.triggered.connect(self._license)

        self.ui_settings_btn.clicked.connect(self.showSettings)
        self.ui_clear_btn.clicked.connect(self.ui_file_tree.clear)

        self.ui_search_txt.returnPressed.connect(self._user_search)
        self.ui_search_tree.itemSelectionChanged.connect(self.searchSelectionChanged)
        self.ui_file_tree.itemSelectionChanged.connect(self.fileSelectionChanged)

        self.ui_rename_btn.clicked.connect(self.rename)

        self.ui_set_movie_btn.clicked.connect(self.search_set_movie)
        self.ui_manual_btn.clicked.connect(self.manual_set_movie)

        self.ui_set_episode_btn.clicked.connect(self.search_set_episode)



    def manual_set_movie(self):
        title = unicode(self.ui_manual_title_txt.text())
        year = self.ui_manual_year_spin.value()
        media_info = {
            'title': title,
            'year': year,
        }
        for file_item in self.ui_file_tree.selectedItems():
            file_item.media_info = media_info
            file_item.episode_info = None
            file_item.refresh()


    def search_set_movie(self):
        search_items = self.ui_search_tree.selectedItems()
        if not search_items:
            return

        search_item = search_items[0]
        media_info = search_item.media_info

        for file_item in self.ui_file_tree.selectedItems():
            file_item.media_info = media_info
            file_item.episode_info = None
            file_item.refresh()

    def search_set_episode(self):
        episode_items = self.ui_episode_tree.selectedItems()
        if not episode_items:
            return

        episode_item = episode_items[0]
        episode_info = episode_item.episode_info
        media_info = episode_item.media_info

        for file_item in self.ui_file_tree.selectedItems():
            file_item.media_info = media_info
            file_item.episode_info = episode_info
            file_item.refresh()



    def rename(self):
        tree = self.ui_file_tree
        root = tree.invisibleRootItem()
        fileitems = [root.child(i) for i in range(root.childCount())]
        for fileitem in fileitems:
            fp = fileitem.filepath
            rfp = fileitem.renamed_filepath
            print 'PATH', fp, rfp
            if not rfp:
                continue

            if not os.path.isdir(os.path.dirname(rfp)):
                os.makedirs(os.path.dirname(rfp))
            if os.path.exists(rfp):
                if QMessageBox.question(
                        self,
                        'Overwrite File?',
                        'File already exists',
                         QMessageBox.Yes | QMessageBox.No,
                         QMessageBox.No) != QMessageBox.Yes:
                    continue

            try:
                os.rename(fp, rfp)
            except:
                traceback.print_exc()
            else:
                i = root.indexOfChild(fileitem)
                root.takeChild(i)
                del fileitem

    def _ui_file_tree_keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            root = self.ui_file_tree.invisibleRootItem()
            for item in self.ui_file_tree.selectedItems():
                i = root.indexOfChild(item)
                root.takeChild(i)
                del item
        else:
            super(QTreeWidget, self.ui_file_tree).keyPressEvent(event)


    def _ui_file_tree_dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata.hasFormat('text/uri-list'):
            event.accept()
        else:
            event.reject()

    def _ui_file_tree_dragMoveEvent(self, event):
        event.accept()

    def _ui_file_tree_dropEvent(self, event):
        mimedata = event.mimeData()
        filepaths = [os.path.normpath(unicode(s.path()).lstrip('\\/')) for s in mimedata.urls()]
        root = self.ui_file_tree.invisibleRootItem()
        for fp in filepaths:
            if os.path.isfile(fp):
                item = FileItem(root, fp, self)
            elif os.path.isdir(fp):
                for rootdir, dirnames, filenames in os.walk(fp):
                    for fn in filenames:
                        FileItem(root, os.path.join(rootdir, fn), self)

    def fileSelectionChanged(self):
        media_info = None
        items = self.ui_file_tree.selectedItems()
        if items:
            item = items[0]
            media_info = item.media_info
        self.setMediaInfo(media_info)

    def searchSelectionChanged(self):
        media_info = None
        items = self.ui_search_tree.selectedItems()
        if items:
            item = items[0]
            media_info = item.media_info
        self.setMediaInfo(media_info)

    def setMediaInfo(self, media_info):
        self.current_media_info = media_info
        self.ui_poster_lbl.clear()
        if not media_info:
            return

        # Set info on table

        # Set movie poster
        imageurl = media_info.get('poster')
        if imageurl:
            self.ui_poster_lbl.setRemotePixmap(imageurl)

        self.ui_episode_tree.clear()
        if media_info.get('episodes'):
            episodes = media_info.get('episodes')
            episodes.sort(key=lambda x: (x['season'], x['episode']))
            root = self.ui_episode_tree.invisibleRootItem()
            for episode in episodes:
                EpisodeItem(root, episode, media_info)

    def _user_search(self):
        title = unicode(self.ui_search_txt.text()).strip()
        if not title:
            return
        results = find_movie(title)

        self.ui_search_tree.blockSignals(True)
        self.ui_search_tree.clear()
        root = self.ui_search_tree.invisibleRootItem()
        for result_info in results:
            SearchResultItem(root, result_info)
        self.ui_search_tree.blockSignals(False)

    def showSettings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

    def _license(self):
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'license.txt')
        if os.path.isfile(fp):
            os.startfile(fp)

    def _about(self):
        title = 'About {}'.format(self.app_name)
        txt = []
        txt.append('{} v{}'.format(self.app_name, self.app_version))
        txt.append('')
        txt.append('Python: {}'.format(sys.version))
        txt.append('')
        txt.append('Devine Icon Set used with permission from <a href="http://ipapun.deviantart.com/" style="text-decoration:none;color:rgb(50,150,255);">Subrat Nayak</a>')
        txt.append('')
        txt.append(u'Copyright \u00a9 2013 Brendan Abel')
        txt.append('')
        txt = '<br \>\n'.join(txt)

        box = QMessageBox(self)
        icon = self.windowIcon()
        size = sorted(icon.availableSizes(), reverse=True)[0]
        box.setIconPixmap(icon.pixmap(size))
        box.setWindowTitle(title)
        box.setText(txt)
        box.setTextFormat(Qt.RichText)
        box.exec_()

#        QMessageBox.about(self, 'About', txt)

    def _loadIcon(self, widget, name, alt=False):
        iconset = 'White' if not alt else 'Black'
        icondir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon', iconset)
        fp = os.path.join(icondir, '{}.png'.format(name))
        if os.path.isfile(fp):
            icon = QIcon(fp)
            if isinstance(widget, QMainWindow):
                widget.setWindowIcon(icon)
            else:
                widget.setIcon(icon)

    def _loadStyleSheet(self):
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'stylesheet.css')
        try:
            with open(fp, 'r') as f:
                txt = f.read()
            self.setStyleSheet(txt)
        except Exception:
            self.setStyleSheet('')


    def tvdir(self):
        return unicode(self.uiTVTXT.text())

    def moviedir(self):
        return unicode(self.uiMoviesTXT.text())


class FileItem(QTreeWidgetItem):

    cols = ['Filepath', 'Renamed Filepath']

    invalid_char_map = {':': ''}

    re_filename_episodes = [
        re.compile(r'.*[Ss](?P<season>\d{1,2})[\s\-_]*[Ee](?P<episode>\d{1,2}).*', re.I),
        re.compile(r'.*season\s*(?P<season>\d{1,2})[\s\-_]*episode\s*[Ee](?P<episode>\d{1,2}).*', re.I),
    ]

    re_filepath_episodes = [
        re.compile(r'.*season\s*(?P<season>\d{1,2})\\(?:season\s*\d{1,2}[\s\-_]*)?(?:episode|ep\.?|e)\s*(?P<episode>\d{1,2}).*', re.I),
    ]

    def __init__(self, parent, filepath, mediaman):
        super(FileItem, self).__init__(parent)
        self._renamed = False
        self.mediaman = mediaman
        self.filepath = filepath
        self.renamed_filepath = None
        self.media_info = None
        self.episode_info = None
        self.thread = None
        self.pbar = None
        self.setText(0, self.filepath)
        self.send_thread()

    def send_thread(self):
        if self.thread is None:
            self.thread = FilepathSearchThread(self.treeWidget())
            self.thread.finished.connect(self.receive_thread)
        thread_ready = self.thread.wait(10000)
        if thread_ready:
            tree = self.treeWidget()
            self.pbar = QProgressBar(tree)
            self.pbar.setRange(0, 0)
            tree.setItemWidget(self, 1, self.pbar)
            self.thread.filepath = self.filepath
            self.thread.start()

    def receive_thread(self):
        self.media_info = self.thread.result
        self.pbar.reset()
        tree = self.treeWidget()
        tree.removeItemWidget(self, 1)
        self.pbar.deleteLater()
        self.refresh()


    def _replace_invalid_chars(self, text):
        for k, v in FileItem.invalid_char_map.items():
            if k in text:
                text = text.replace(k, v)
        return text

    def refresh(self):
        moviedir = self.mediaman.moviedir()
        tvdir = self.mediaman.tvdir()

        if self.media_info:
            title = self.media_info.get('title')
            title = self._replace_invalid_chars(title)
            year = self.media_info.get('year')

            filename, ext = os.path.splitext(os.path.basename(self.filepath))

            if self.episode_info or self.media_info.get('episodes'):
                if not self.episode_info:
                    episodes = self.media_info['episodes']
                    ep_match = None
                    for reg in FileItem.re_filename_episodes:
                        m = reg.search(filename)
                        if m:
                            ep_match = m.groupdict()
                            break
                    if not ep_match:
                        for reg in FileItem.re_filepath_episodes:
                            m = reg.search(self.filepath)
                            if m:
                                ep_match = m.groupdict()

                    if ep_match:
                        season, episode = int(ep_match['season']), int(ep_match['episode'])
                        for episode_info in episodes:
                            if (episode_info['season'], episode_info['episode']) == (season, episode):
                                self.episode_info = episode_info
                                break

                if self.episode_info:
                    self.renamed_filepath = ur'{tvdir}\{title}\Season{season:02d}\{title}.S{season:02d}E{episode:02d}.{episode_title}{ext}'.format(
                        tvdir=tvdir,
                        title=title,
                        year=year,
                        season=self.episode_info['season']  ,
                        episode=self.episode_info['episode'],
                        episode_title=self._replace_invalid_chars(self.episode_info['title']),
                        ext=ext,
                    )
                else:
                    self.renamed_filepath = ur'{tvdir}\{title}\Season00\{title}.S00E00.XXX{ext}'.format(
                        tvdir=tvdir,
                        title=title,
                        year=year,
                        ext=ext,
                    )


            else:
                self.renamed_filepath = ur'{moviedir}\{title} ({year})\{title}{ext}'.format(
                    moviedir=moviedir,
                    title=title,
                    year=year,
                    ext=ext
                )


            self.setText(1, self.renamed_filepath)
            if os.path.exists(self.renamed_filepath):
                self.setBackgroundColor(FileItem.cols.index('Renamed Filepath'), QColor(0, 255, 0, 100))




class SearchResultItem(QTreeWidgetItem):

    cols = ['Title', 'Year', 'Type']

    type_map = {
        'M': 'Movie',
        'TVS': 'TV Series',
        'TV': 'TV Movie',
        'V': 'Video',
        'VG': 'Video Game',
    }

    def __init__(self, parent, media_info):
        super(SearchResultItem, self).__init__(parent)
        self.media_info = media_info
        self.refresh()

    def refresh(self):
        C = SearchResultItem.cols.index
        self.setText(C('Title'), self.media_info.get('title', ''))
        self.setText(C('Year'), unicode(self.media_info.get('year', '')))
        self.setText(C('Type'), SearchResultItem.type_map.get(self.media_info.get('type', ''), ''))



class EpisodeItem(QTreeWidgetItem):

    cols = ['Season', 'Episode', 'Title']

    def __init__(self, parent, episode_info, media_info):
        super(EpisodeItem, self).__init__(parent)
        self.episode_info = episode_info
        self.media_info = media_info
        self.refresh()

    def refresh(self):
        C = EpisodeItem.cols.index
        self.setText(C('Season'), unicode(self.episode_info.get('season', '')))
        self.setText(C('Episode'), unicode(self.episode_info.get('episode', '')))
        self.setText(C('Title'), unicode(self.episode_info.get('title', '')))



class TreeDelegate(QItemDelegate):

    min_row_height = 20

    def sizeHint(self, option, index):
        size = super(TreeDelegate, self).sizeHint(option, index)
        if size.height() < TreeDelegate.min_row_height:
            size.setHeight(TreeDelegate.min_row_height)
        return size







