#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
"""
Access-Aide GUI with optional AI-assisted ALT autofill
"""
import sys
import os
import base64
import json
import urllib.request
import urllib.error

from plugin_utils import QtCore, QtGui, QtWidgets, QtSvg
from quickparser import QuickXHTMLParser

_THUMBNAIL_SIZE_INCREMENT = 50
_COL_ALTTEXT = 2

# --- SVG Rendering Helpers ---
def FixupSvgForRendering(data):
    svgdata = []
    qp = QuickXHTMLParser()
    qp.setContent(data)
    skip = False
    for (text, tpath, tname, ttype, tattr) in qp.parse_iter():
        if tname and tname.lower() in ['desc', 'title', 'flowroot', 'flowRoot']:
            if ttype == 'single':
                continue
            skip = (ttype == 'begin')
            if ttype == 'end':
                skip = False
            continue
        if not skip:
            svgdata.append(text or qp.tag_info_to_xml(tname, ttype, tattr))
    return ''.join(svgdata)


def RenderSvgToImage(fpath):
    with open(fpath, 'rb') as f:
        svgdat = f.read().decode('utf-8', errors='replace')
    svgdata = FixupSvgForRendering(svgdat)
    renderer = QtSvg.QSvgRenderer()
    renderer.load(svgdata.encode('utf-8'))
    sz = renderer.defaultSize()
    image = QtGui.QImage(sz, QtGui.QImage.Format_ARGB32)
    image.fill(QtGui.QColor('white'))
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    return image


class AltTextDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == _COL_ALTTEXT:
            return QtWidgets.QTextEdit(parent)
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == _COL_ALTTEXT:
            editor.setPlainText(index.data(QtCore.Qt.EditRole))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == _COL_ALTTEXT:
            model.setData(index, editor.toPlainText(), QtCore.Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


class AltTextEditor(QtWidgets.QDialog):
    def __init__(self, resources, thumbnail_size):
        super().__init__(None, QtCore.Qt.Window)
        self.resources = resources
        self.ThumbnailSize = thumbnail_size
        self.altdata = {}
        self.said_ok = False
        self.setWindowTitle('Update Alt for Each Image')

        # Model & Delegate
        self.editModel = QtGui.QStandardItemModel(self)
        self.editModel.itemChanged.connect(self.UpdateAltTextForItem)
        self.altDelegate = AltTextDelegate(self)

        # Tree View
        self.imageTree = QtWidgets.QTreeView(self)
        self.imageTree.setItemDelegateForColumn(_COL_ALTTEXT, self.altDelegate)
        self.imageTree.setModel(self.editModel)
        self.imageTree.setWordWrap(True)
        self.imageTree.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)

        # Buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.btnOk = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.btnCancel = self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)
        self.btnAIfill = QtWidgets.QPushButton('Autofill with AI')
        self.buttonBox.addButton(self.btnAIfill, QtWidgets.QDialogButtonBox.ActionRole)

        self.btnOk.clicked.connect(self.AcceptChanges)
        self.btnCancel.clicked.connect(self.reject)
        self.btnAIfill.clicked.connect(self.onAIFillAll)

        # Thumbnail Size Controls
        lbl = QtWidgets.QLabel('Thumbnail Size')
        dec = QtWidgets.QToolButton(self)
        dec.setText('-')
        dec.clicked.connect(self.DecreaseThumbnailSize)
        inc = QtWidgets.QToolButton(self)
        inc.setText('+')
        inc.clicked.connect(self.IncreaseThumbnailSize)
        sizeLayout = QtWidgets.QHBoxLayout()
        sizeLayout.addWidget(lbl)
        sizeLayout.addWidget(dec)
        sizeLayout.addWidget(inc)
        sizeLayout.addStretch()

        # Main Layout
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.imageTree)
        mainLayout.addLayout(sizeLayout)
        mainLayout.addWidget(self.buttonBox)

        self.SetImages()

    def sizeHint(self):
        return QtCore.QSize(1000, 800)

    def SetImages(self):
        self.editModel.clear()
        self.editModel.setHorizontalHeaderLabels(['Path', 'Thumbnail', 'Alt Text'])
        for (apath, bkpath, mime, key, atext) in self.resources:
            self.altdata[key] = atext
            # Path item
            name = QtGui.QStandardItem(bkpath)
            name.setData(apath, QtCore.Qt.UserRole + 1)
            name.setData(mime, QtCore.Qt.UserRole + 2)
            name.setData(key, QtCore.Qt.UserRole + 3)
            name.setEditable(False)
            # Thumbnail item
            if mime == 'image/svg+xml':
                img = RenderSvgToImage(apath)
            else:
                img = QtGui.QImage(apath)
            pix = QtGui.QPixmap.fromImage(img).scaled(
                self.ThumbnailSize, self.ThumbnailSize,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            icon = QtGui.QStandardItem()
            icon.setData(pix, QtCore.Qt.DecorationRole)
            icon.setEditable(False)
            # Alt Text item
            alt = QtGui.QStandardItem(atext)
            alt.setEditable(True)
            self.editModel.appendRow([name, icon, alt])
        header = self.imageTree.header()
        header.setStretchLastSection(True)
        for i in range(header.count()):
            self.imageTree.resizeColumnToContents(i)

    def DecreaseThumbnailSize(self):
        self.ThumbnailSize = max(0, self.ThumbnailSize - _THUMBNAIL_SIZE_INCREMENT)
        self.UpdateThumbnails()

    def IncreaseThumbnailSize(self):
        self.ThumbnailSize += _THUMBNAIL_SIZE_INCREMENT
        self.UpdateThumbnails()

    def UpdateThumbnails(self):
        for r in range(self.editModel.rowCount()):
            item = self.editModel.item(r, 0)
            apath = item.data(QtCore.Qt.UserRole + 1)
            mime = item.data(QtCore.Qt.UserRole + 2)
            if mime == 'image/svg+xml':
                img = RenderSvgToImage(apath)
            else:
                img = QtGui.QImage(apath)
            pix = QtGui.QPixmap.fromImage(img).scaled(
                self.ThumbnailSize, self.ThumbnailSize,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            self.editModel.item(r, 1).setData(pix, QtCore.Qt.DecorationRole)

    def UpdateAltTextForItem(self, item):
        idx = self.editModel.indexFromItem(item)
        if idx.column() == _COL_ALTTEXT:
            key = self.editModel.item(idx.row(), 0).data(QtCore.Qt.UserRole + 3)
            self.altdata[key] = item.text()

    def onAIFillAll(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            QtWidgets.QMessageBox.critical(
                self, 'API Key Mancante', 'Imposta OPENAI_API_KEY per usare l IA.'
            )
            return
        missing = [r for r in range(self.editModel.rowCount())
                   if not self.editModel.item(r, 2).text().strip()]
        if not missing:
            QtWidgets.QMessageBox.information(
                self, 'Autofill IA', 'Nessuna immagine da processare.'
            )
            return
        # UI Feedback
        self.btnAIfill.setEnabled(False)
        self.btnAIfill.setText('Processing...')
        QtWidgets.QApplication.processEvents()
        dlg = QtWidgets.QProgressDialog(
            'Autofill ALT con IA...', None, 0, len(missing), self
        )
        dlg.setWindowModality(QtCore.Qt.WindowModal)
        count = 0
        for r in missing:
            apath = self.editModel.item(r, 0).data(QtCore.Qt.UserRole + 1)
            print(f"[Access-Aide] Requesting ALT for: {apath}")
            alt = self._generate_alt(apath, api_key)
            print(f"[Access-Aide] Received ALT: {alt}")
            if alt:
                self.editModel.item(r, 2).setText(alt)
                key = self.editModel.item(r, 0).data(QtCore.Qt.UserRole + 3)
                self.altdata[key] = alt
                count += 1
            dlg.setValue(count)
            QtWidgets.QApplication.processEvents()
        dlg.close()
        self.btnAIfill.setText('Autofill with IA')
        self.btnAIfill.setEnabled(True)
        QtWidgets.QApplication.processEvents()
        QtWidgets.QMessageBox.information(
            self, 'Autofill IA', f'Aggiornati {count} ALT su {len(missing)}'
        )

    def _generate_alt(self, src, api_key):
        try:
            with open(src, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"[Access-Aide] Failed to read image {src}: {e}")
            return ''
        payload = {
            'model': 'gpt-4o-mini',
            'input': [
                {
                    'role': 'user',
                    'content': [
                         {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{b64}"
                        },
                        {
                        "type": "input_text",
                        "text": "descrivi l'immagine per compilare l'attributo ALT html"
                        }
                    ]
                }
            ]
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        print(f"[Access-Aide] Payload: {json.dumps(payload)[:200]}...")
        print(f"[Access-Aide] Headers: {headers}")
        req = urllib.request.Request(
            'https://api.openai.com/v1/responses',
            data=json.dumps(payload).encode(),
            headers=headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.getcode()
                print(f"[Access-Aide] Response status: {status}")
                resp_data = resp.read().decode()
                print(f"[Access-Aide] Response body: {resp_data[:1000]}...")
                data = json.loads(resp_data)
                desc = data['output'][0]['content'][0]['text'].strip()
                return desc if len(desc) <= 400 else desc[:397] + '...'
        except urllib.error.HTTPError as e:
            print(f"[Access-Aide] HTTPError {e.code}: {e.reason}")
            return f"ERROR_API_{e.code}"
        except Exception as e:
            print(f"[Access-Aide] Unexpected error: {e}")
            return ''

    def AcceptChanges(self):
        self.said_ok = True
        self.accept()

    def GetResults(self):
        return self.altdata if self.said_ok else {}


def GUIUpdateFromList(resources, basewidth):
    app = QtWidgets.QApplication(sys.argv)
    dlg = AltTextEditor(resources, basewidth)
    dlg.exec()
    return dlg.GetResults()
