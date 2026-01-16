import sys
import Backend as bk
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QGroupBox, QMessageBox, QDialog, QLabel, QLineEdit, QAbstractItemView, QStatusBar, QFileDialog,QWidgetAction, QWidget
)
#from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Download Thread
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) 
    RefreshList = pyqtSignal()       
    Finished = pyqtSignal()          

    def run(self):
        PendingDownload = bk.SongDF[bk.SongDF['Status'] != 'Downloaded']
        if PendingDownload.empty:
            self.ProgressUpdate.emit("All songs are already downloaded.")
            self.Finished.emit()
            return

        for _, row in PendingDownload.iterrows():
            title = row['Title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            bk.DownloadSong(row['VideoID'], title, artist=row['Artist'], genre=row['Genre'], encoding=bk.Config.get("Encoding"))
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

        self.StatusLabel = QLabel("")
        self.StatusLabel.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.StatusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.StatusLabel)

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

        ButtonBox = QHBoxLayout()
        SaveBtn = QPushButton("Add Song")
        SaveBtn.clicked.connect(self.SaveSong)
        SaveBtn.setProperty("class", "success")

        CloseBtn = QPushButton("Close")
        CloseBtn.clicked.connect(self.reject) 

        ButtonBox.addWidget(SaveBtn)
        ButtonBox.addWidget(CloseBtn)
        self.layout.addLayout(ButtonBox)

    def CreateInput(self, label_text, layout):
        lbl = QLabel(label_text)
        inp = QLineEdit()
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp
    
    def Autofill(self):
        url = self.URLInput.text().strip()

        if not url:
            self.StatusLabel.setStyleSheet("color: #f44336;")
            self.StatusLabel.setText("Error: URL required for autofill!")
            return

        id = bk.URLtoID(url)
        try:
            title, author = bk.GetSongMetadata(id)
        except Exception as e:
            self.StatusLabel.setStyleSheet("color: #f44336;")
            self.StatusLabel.setText(f"Error fetching metadata")
            return
        
        self.TitleInput.setText(title)
        self.ArtistInput.setText(author)
        self.StatusLabel.setStyleSheet("color: #4CAF50;")
        self.StatusLabel.setText("Autofill successful!")

    def SaveSong(self):
        title = self.TitleInput.text().strip()
        url = self.URLInput.text().strip()
        artist = self.ArtistInput.text().strip()
        genre = self.GenreInput.text().strip()

        if not title or not url:
            self.StatusLabel.setStyleSheet("color: #f44336;")
            self.StatusLabel.setText("Error: Title and URL are required!")
            return

        bk.AddSongToSongfile(title, url, artist, genre)
        
        self.StatusLabel.setStyleSheet("color: #4CAF50;")
        self.StatusLabel.setText(f"Song '{title}' has been added.")
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
        self.setFixedSize(400, 300)
        self.layout = QVBoxLayout(self)

        row = bk.SongDF.loc[bk.SongDF['Title'] == title].iloc[0]
        self.OriginalTitle = title
        current_url = f"https://www.youtube.com/watch?v={row['VideoID']}"
        
        self.TitleInput = self.create_field("Title:", row['Title'])
        self.URLInput = self.create_field("YouTube URL:", current_url)
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
        NewURL = self.URLInput.text().strip()

        if not NewTitle:
            QMessageBox.critical(self, "Error", "Title cannot be empty")
            return

        bk.UpdateSongDetails(self.OriginalTitle, NewTitle, NewArtist, NewGenre, NewURL)
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
        self.SortOrder = True  

        bk.UpdateSongStatuses()

        self.SetupMenu()
        self.SetupTable()
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

    def SetupMenu(self):
        def CreateMenuWidget(menu, text, color_class, callback):
            action = QWidgetAction(menu)
            
            # Container widget to handle padding/margins inside the menu
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(4, 2, 4, 2) # Button spacing inside dropdown
            
            btn = QPushButton(text)
            btn.setProperty("class", color_class)
            btn.clicked.connect(callback)
            btn.clicked.connect(menu.close)
            
            layout.addWidget(btn)
            action.setDefaultWidget(container)
            menu.addAction(action)
            return btn
        
        # Action Menu
        ActionMenu = self.menuBar().addMenu("Actions")

        self.AddSongBtn = CreateMenuWidget(ActionMenu, "Add New Song", "standard", self.OpenAddSongDialog)
        self.DownloadBtn = CreateMenuWidget(ActionMenu, "Download Pending", "success", self.StartDownload)
        self.ActionUpdateImg = CreateMenuWidget(ActionMenu, "Update Images", "standard", self.StartImageUpdate)
        self.ActionChangeDir = CreateMenuWidget(ActionMenu, "Change Folder", "standard", self.ChangeDownloadDir)

        # Song Menu
        SongMenu = self.menuBar().addMenu("Song")

        self.EditSongBtn = CreateMenuWidget(SongMenu, "Edit Details", "standard", self.EditSong)
        self.DelListBtn = CreateMenuWidget(SongMenu, "Delete from List", "danger", lambda: self.DeleteSong("list"))
        self.DelFolderBtn = CreateMenuWidget(SongMenu, "Delete from Folder", "danger", lambda: self.DeleteSong("folder"))
        self.DelBothBtn = CreateMenuWidget(SongMenu, "Delete Both", "danger_dark", lambda: self.DeleteSong("both"))
        
        # Set all buttons to disabled initially
        for b in [self.EditSongBtn, self.DelListBtn, self.DelFolderBtn, self.DelBothBtn]: b.setEnabled(False)

    def SelectionChanged(self):
        selected = self.table.selectionModel().selectedRows()
        count = len(selected)
        
        # Update Menu Actions instead of Buttons
        self.EditSongBtn.setEnabled(count == 1)
        self.DelListBtn.setEnabled(count > 0)
        self.DelFolderBtn.setEnabled(count > 0)
        self.DelBothBtn.setEnabled(count > 0)

    def StartDownload(self):
        def DownloadDone():
            QMessageBox.information(self, "Download Complete", "All pending songs have been downloaded.")
            self.DownloadBtn.setEnabled(True) # Re-enable menu action
            self.RefreshList()
            self.status.showMessage("Ready")
        
        self.status.showMessage("Starting download...")
        self.DownloadBtn.setEnabled(False) # Disable menu action
        self.worker = DownloadWorker()
        self.worker.ProgressUpdate.connect(lambda s: self.status.showMessage(s))
        self.worker.RefreshList.connect(self.RefreshList)
        self.worker.Finished.connect(DownloadDone)
        self.worker.start()

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