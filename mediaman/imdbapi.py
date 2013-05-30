
from pprint import pprint
import copy
import os
import re
import xml.sax.saxutils as saxutils

import requests
from PyQt4.QtCore import Qt, QThread, pyqtSignal


def find_movie(title, limit=10):
    """ Uses the imdbapi site to find movie information. """
    payload = {'q': title, 'limit': limit}
    url = 'http://imdbapi.org'
    r = requests.get(url, params=payload)
    try:
        response = r.json()
    except:
        print r
        raise
    if isinstance(response, list):
        for d in response:
            d['title'] = saxutils.unescape(d['title'])
        pprint(response)
        return response
    return []


class SearchThread(QThread):

    def __init__(self, parent):
        super(SearchThread, self).__init__(parent)
        self.search_words = None
        self.result = None

    def run(self):
        search_words = self.search_words
        while search_words:
            search_title = ' '.join(search_words)
            results = find_movie(search_title, limit=1)
            if results:
                self.result = results[0]
                break
            else:
                search_words.pop()


class FilepathSearchThread(QThread):

    def __init__(self, parent):
        super(FilepathSearchThread, self).__init__(parent)
        self.filepath = None
        self.result = None

    def run(self):
        fp = self.filepath
        if not fp:
            return

        # Check the filename and the folder name if necessary
        dirname = os.path.basename(os.path.dirname(fp))
        filename, ext = os.path.splitext(os.path.basename(fp))

        if re.match(r'^S(?:eason)?\s*\d{1,2}.*', dirname):
            search_txt = os.path.basename(os.path.dirname(os.path.dirname(fp)))
        else:
            search_txt = filename

        for c in '.-_':
            search_txt = search_txt.replace(c, ' ')
        words = search_txt.split(' ')

        search_words = []
        break_ = False
        for i, word in enumerate(words):
            if i > 0:
                for pattern in [ur'\d{4}', '1080', '720']:
                    if re.search(pattern, word):
                        break_ = True
                        break
                if break_:
                    break
            search_words.append(word)

        while search_words:
            search_title = ' '.join(search_words)
            results = find_movie(search_title, limit=1)
            if results:
                self.result = results[0]
                break
            else:
                search_words.pop()




