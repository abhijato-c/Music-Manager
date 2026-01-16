import sys
import Backend as bk
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QPushButton, QGroupBox, QMessageBox, QDialog, QLabel, QLineEdit, QAbstractItemView, QStatusBar, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Download Thread
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) 
    RefreshList = pyqtSignal()       
    Finished = pyqtSignal()          

    def run(self):
        to_download = bk.SongDF[bk.SongDF['Status'] != 'Downloaded']
        if to_download.empty:
            self.ProgressUpdate.emit("All songs are already downloaded.")
            self.Finished.emit()
            return

        for _, row in to_download.iterrows():
            title = row['Title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            bk.DownloadSong(row['VideoID'], title, artist=row['Artist'], genre=row['Genre'])
            self.RefreshList.emit()

        self.ProgressUpdate.emit("Ready")
        self.Finished.emit()

# Update Images Thread
class ImageWorker(QThread):
    Finished = pyqtSignal()

    def run(self):
        for _, row in bk.SongDF.iterrows():
            img_path = bk.AppData / "Images" / f"{row['Title']}.jpg"
            for ext in ['mp3', 'flac', 'm4a']:
                song_path = bk.MusicDir / f"{row['Title']}.{ext}"
                if song_path.exists() and img_path.exists():
                    bk.AddCoverArt(song_path, img_path, ext)
                    break
        self.Finished.emit()

# Add Song popup
class AddSongDialog(QDialog):
    song_added = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Song")
        self.setFixedSize(400, 300)
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        FormLayout = QVBoxLayout()
        self.URLInput = self.CreateInput("YouTube URL (Required):", FormLayout)

        TitleHeader = QHBoxLayout()
        TitleHeader.addWidget(QLabel("Title (Required):"))
        TitleHeader.addStretch() 

        self.AutofillBtn = QPushButton("Autofill")
        self.AutofillBtn.setFixedWidth(80)
        self.AutofillBtn.clicked.connect(self.Autofill)
        TitleHeader.addWidget(self.AutofillBtn)

        FormLayout.addLayout(TitleHeader)
        self.TitleInput = QLineEdit()
        FormLayout.addWidget(self.TitleInput)

        self.ArtistInput = self.CreateInput("Artist (Optional):", FormLayout)
        self.GenreInput = self.CreateInput("Genre (Optional):", FormLayout)
        self.layout.addLayout(FormLayout)

        btn_box = QHBoxLayout()
        SaveBtn = QPushButton("Add Song")
        SaveBtn.clicked.connect(self.SaveSong)
        SaveBtn.setProperty("class", "success")

        CloseBtn = QPushButton("Close")
        CloseBtn.clicked.connect(self.reject) 
        
        btn_box.addWidget(SaveBtn)
        btn_box.addWidget(CloseBtn)
        self.layout.addLayout(btn_box)

    def CreateInput(self, label_text, layout):
        lbl = QLabel(label_text)
        inp = QLineEdit()
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp
    
    def Autofill(self):
        url = self.URLInput.text().strip()

        if not url:
            self.status_label.setStyleSheet("color: #f44336;")
            self.status_label.setText("Error: URL required for autofill!")
            return

        id = bk.URLtoID(url)
        try:
            title, author = bk.GetSongMetadata(id)
        except Exception as e:
            self.status_label.setStyleSheet("color: #f44336;")
            self.status_label.setText(f"Error fetching metadata")
            return
        
        self.TitleInput.setText(title)
        self.ArtistInput.setText(author)
        self.status_label.setStyleSheet("color: #4CAF50;")
        self.status_label.setText("Autofill successful!")

    def SaveSong(self):
        title = self.TitleInput.text().strip()
        url = self.URLInput.text().strip()
        artist = self.ArtistInput.text().strip()
        genre = self.GenreInput.text().strip()

        if not title or not url:
            self.status_label.setStyleSheet("color: #f44336;")
            self.status_label.setText("Error: Title and URL are required!")
            return

        bk.AddSongToSongfile(title, url, artist, genre)
        
        self.status_label.setStyleSheet("color: #4CAF50;")
        self.status_label.setText(f"Song '{title}' has been added.")
        self.TitleInput.clear()
        self.URLInput.clear()
        self.ArtistInput.clear()
        self.GenreInput.clear()
        self.TitleInput.setFocus()
        
        self.song_added.emit()

# Edit Song Popup
class EditSongDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit: {title}")
        self.setFixedSize(400, 260)
        self.layout = QVBoxLayout(self)
        self.OriginalTitle = title

        row = bk.SongDF.loc[bk.SongDF['Title'] == title].iloc[0]
        
        self.TitleInput = self.create_field("Title:", row['Title'])
        self.ArtistInput = self.create_field("Artist:", row['Artist'])
        self.GenreInput = self.create_field("Genre:", row['Genre'])

        SaveBtn = QPushButton("Save Changes")
        SaveBtn.setProperty("class", "success")
        SaveBtn.clicked.connect(self.save)
        self.layout.addWidget(SaveBtn)

    def create_field(self, label, value):
        self.layout.addWidget(QLabel(label))
        txt = QLineEdit()
        txt.setText(str(value))
        self.layout.addWidget(txt)
        return txt

    def save(self):
        NewTitle = self.TitleInput.text().strip()
        NewArtist = self.ArtistInput.text().strip()
        NewGenre = self.GenreInput.text().strip()

        if not NewTitle:
            QMessageBox.critical(self, "Error", "Title cannot be empty")
            return

        bk.UpdateSongDetails(self.OriginalTitle, NewTitle, NewArtist, NewGenre)
        self.accept()

# Main Window
class MusicManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Manager")
        self.setGeometry(100, 100, 1100, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.Columns = ['Title', 'Artist', 'Genre', 'Status']

        self.SortBy = 'Title'
        self.SortOrder = True  # True for Ascending, False for Descending

        self.SetupTable()
        self.SetupControls()
        self.SetupStatusbar()
        self.ApplyStyles()
        self.RefreshList()

    def SetupTable(self):
        gb = QGroupBox("Library Status")
        gb_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4) 
        self.table.setHorizontalHeaderLabels(self.Columns)
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        self.table.horizontalHeader().sectionClicked.connect(self.HeaderClicked)
        self.table.horizontalHeader().setSortIndicatorShown(True)

        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(40)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        self.table.itemSelectionChanged.connect(self.SelectionChanged)

        gb_layout.addWidget(self.table)
        gb.setLayout(gb_layout)
        self.main_layout.addWidget(gb)

    def SetupControls(self):
        controls_layout = QHBoxLayout()

        global_gb = QGroupBox("Global Actions")
        global_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add New Song")
        self.btn_add.clicked.connect(self.OpenAddSongDialog)
        
        self.btn_download = QPushButton("Download Pending")
        self.btn_download.setProperty("class", "success")
        self.btn_download.clicked.connect(self.StartDownload)

        self.btn_update_img = QPushButton("Update Images")
        self.btn_update_img.clicked.connect(self.StartImageUpdate)

        self.btn_change_dir = QPushButton("Change Folder")
        self.btn_change_dir.clicked.connect(self.ChangeDownloadDir)

        global_layout.addWidget(self.btn_add)
        global_layout.addWidget(self.btn_download)
        global_layout.addWidget(self.btn_update_img)
        global_layout.addWidget(self.btn_change_dir)
        global_gb.setLayout(global_layout)

        selected_gb = QGroupBox("Selected Song Options")
        selected_layout = QHBoxLayout()

        self.btn_edit = QPushButton("Edit Details")
        self.btn_edit.clicked.connect(self.EditSong)
        
        self.btn_del_list = QPushButton("Delete from List")
        self.btn_del_list.setProperty("class", "danger")
        self.btn_del_list.clicked.connect(lambda: self.DeleteSong("list"))

        self.btn_del_folder = QPushButton("Delete from Folder")
        self.btn_del_folder.setProperty("class", "danger")
        self.btn_del_folder.clicked.connect(lambda: self.DeleteSong("folder"))
        
        self.btn_del_both = QPushButton("Delete Both")
        self.btn_del_both.setProperty("class", "danger_dark")
        self.btn_del_both.clicked.connect(lambda: self.DeleteSong("both"))

        selected_layout.addWidget(self.btn_edit)
        selected_layout.addWidget(self.btn_del_list)
        selected_layout.addWidget(self.btn_del_folder)
        selected_layout.addWidget(self.btn_del_both)
        selected_gb.setLayout(selected_layout)

        for btn in [self.btn_edit, self.btn_del_list, self.btn_del_folder, self.btn_del_both]:
            btn.setEnabled(False)

        controls_layout.addWidget(global_gb, 1)
        controls_layout.addWidget(selected_gb, 1)
        self.main_layout.addLayout(controls_layout)

    def SetupStatusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def RefreshList(self):
        # Sort list
        bk.SongDF.sort_values(by=self.SortBy, ascending=self.SortOrder, inplace=True)
        bk.SongDF.reset_index(drop=True, inplace=True)
        self.table.horizontalHeader().setSortIndicator(self.Columns.index(self.SortBy), Qt.SortOrder.AscendingOrder if self.SortOrder else Qt.SortOrder.DescendingOrder)

        # Clear table and repopulate
        self.table.setRowCount(0)
        for index, row in bk.SongDF.iterrows():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(index + 1)))
            
            def make_item(text, center=False):
                item = QTableWidgetItem(str(text))
                if center: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item

            self.table.setItem(row_idx, 0, make_item(row['Title']))
            self.table.setItem(row_idx, 1, make_item(row['Artist']))
            self.table.setItem(row_idx, 2, make_item(row['Genre']))
            self.table.setItem(row_idx, 3, make_item(row['Status'], True))
        
        self.SelectionChanged()
    
    def HeaderClicked(self, index):
        ClickedCol = self.Columns[index]

        if self.SortBy == ClickedCol:
            self.SortOrder = not self.SortOrder  
        else:
            self.SortBy = ClickedCol
            self.SortOrder = True  

        self.RefreshList()

    def SelectionChanged(self):
        selected = self.table.selectionModel().selectedRows()
        count = len(selected)
        self.btn_edit.setEnabled(count == 1)
        self.btn_del_list.setEnabled(count > 0)
        self.btn_del_folder.setEnabled(count > 0)
        self.btn_del_both.setEnabled(count > 0)

    def OpenAddSongDialog(self):
        dlg = AddSongDialog(self)
        dlg.song_added.connect(self.RefreshList) 
        dlg.exec()
        self.RefreshList() 

    def EditSong(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        title = self.table.item(rows[0].row(), 0).text()
        dlg = EditSongDialog(title, self)
        if dlg.exec():
            self.RefreshList()

    def DeleteSong(self, mode):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                   f"Are you sure you want to delete {len(rows)} item(s)?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        titles = [self.table.item(row.row(), 0).text() for row in rows]
        for title in titles:
            if mode in ["folder", "both"]: bk.DeleteSongFromDisk(title)
            if mode in ["list", "both"]: bk.SongDF = bk.SongDF[bk.SongDF['Title'] != title]
        if mode in ["list", "both"]: bk.SaveSongfile()
        self.RefreshList()
        self.status.showMessage(f"Deleted {len(titles)} songs ({mode}).")

    def StartDownload(self):
        def DownloadDone():
            QMessageBox.information(self, "Download Complete", "All pending songs have been downloaded.")
            self.btn_download.setEnabled(True)
            self.RefreshList()
            self.status.showMessage("Ready")
        
        self.status.showMessage("Starting download...")
        self.btn_download.setEnabled(False)
        self.worker = DownloadWorker()
        self.worker.ProgressUpdate.connect(lambda s: self.status.showMessage(s))
        self.worker.RefreshList.connect(self.RefreshList)
        self.worker.Finished.connect(DownloadDone)
        self.worker.start()

    def StartImageUpdate(self):
        def UpdateDone():
            QMessageBox.information(self, "Done", "Images Updated")
            self.status.showMessage("Ready")
        
        self.status.showMessage("Updating images")
        self.img_worker = ImageWorker()
        self.img_worker.Finished.connect(UpdateDone)
        self.img_worker.start()

    def ChangeDownloadDir(self):
        NewDir = QFileDialog.getExistingDirectory(self, "Select Music Download Folder", str(bk.MusicDir))
        if NewDir:
            bk.ChangeMusicDir(NewDir)
            self.status.showMessage(f"Download folder changed to: {NewDir}")
        self.RefreshList()

    def closeEvent(self, event):
        bk.SaveSongfile()
        event.accept()

    def ApplyStyles(self):
        with open('style.css', "r") as f:
            stylesheet = f.read()
        self.setStyleSheet(stylesheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MusicManagerWindow()
    window.show()
    sys.exit(app.exec())