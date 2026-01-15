import sys
import Backend as bk
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, 
    QGroupBox, QMessageBox, QDialog, QLabel, QLineEdit, 
    QTextEdit, QAbstractItemView, QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor

# Worker Thread for Downloads
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) # Update status bar text
    RefreshList = pyqtSignal()       # Trigger table refresh
    Finished = pyqtSignal()          # All downloads done

    def run(self):
        to_download = bk.SongDF[bk.SongDF['status'] != 'Downloaded']
        if to_download.empty:
            self.ProgressUpdate.emit("All songs are already downloaded.")
            self.Finished.emit()
            return

        for _, row in to_download.iterrows():
            title = row['title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            
            # Call backend download
            bk.DownloadSong(row['VideoID'], title, artist=row['artist'], genre=row['genre'])
            
            # Refresh list to show status change
            self.RefreshList.emit()

        self.ProgressUpdate.emit("Ready")
        self.Finished.emit()

# Worker Thread for Update Images
class ImageWorker(QThread):
    Finished = pyqtSignal()

    def run(self):
        for _, row in bk.SongDF.iterrows():
            img_path = bk.AppData / "Images" / f"{row['title']}.jpg"
            for ext in ['mp3', 'flac', 'm4a']:
                song_path = bk.MusicDir / f"{row['title']}.{ext}"
                if song_path.exists() and img_path.exists():
                    bk.AddCoverArt(song_path, img_path, ext)
                    break
        self.Finished.emit()

# Add Song popup
class AddSongDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Song")
        self.setFixedSize(400, 250)
        self.layout = QVBoxLayout(self)

        # Form Layout
        FormLayout = QVBoxLayout()
        
        self.TitleInput = self.create_input("Title (Required):", FormLayout)
        self.URLInput = self.create_input("YouTube URL (Required):", FormLayout)
        self.ArtistInput = self.create_input("Artist (Optional):", FormLayout)
        self.GenreInput = self.create_input("Genre (Optional):", FormLayout)
        
        self.layout.addLayout(FormLayout)

        # Buttons
        btn_box = QHBoxLayout()
        SaveBtn = QPushButton("Add Song")
        SaveBtn.clicked.connect(self.save_song)
        SaveBtn.setProperty("class", "success") # For styling

        CancelBtn = QPushButton("Cancel")
        CancelBtn.clicked.connect(self.reject)
        
        btn_box.addWidget(SaveBtn)
        btn_box.addWidget(CancelBtn)
        self.layout.addLayout(btn_box)

    def create_input(self, label_text, layout):
        lbl = QLabel(label_text)
        inp = QLineEdit()
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp

    def save_song(self):
        title = self.TitleInput.text().strip()
        url = self.URLInput.text().strip()
        artist = self.ArtistInput.text().strip()
        genre = self.GenreInput.text().strip()

        if not title or not url:
            QMessageBox.warning(self, "Missing Data", "Title and URL are required.")
            return

        bk.AddSongToSongfile(title, url, artist, genre)
        self.accept()

# Edit Song Popup
class EditSongDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit: {title}")
        self.setFixedSize(400, 350)
        self.original_title = title
        self.layout = QVBoxLayout(self)

        # Fetch data
        row = bk.SongDF.loc[bk.SongDF['title'] == title].iloc[0]
        
        self.title_input = self.create_field("Title:", row['title'])
        current_url = f"https://www.youtube.com/watch?v={row['VideoID']}"
        self.url_input = self.create_field("YouTube URL:", current_url)
        self.artist_input = self.create_field("Artist:", row['artist'])
        self.genre_input = self.create_field("Genre:", row['genre'])

        save_btn = QPushButton("Save Changes")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

    def create_field(self, label, value):
        self.layout.addWidget(QLabel(label))
        txt = QTextEdit()
        txt.setPlainText(str(value))
        txt.setFixedHeight(30) # Simulate single line but allow multiline view if needed
        self.layout.addWidget(txt)
        return txt

    def save(self):
        new_title = self.title_input.toPlainText().strip()
        new_url = self.url_input.toPlainText().strip()
        new_artist = self.artist_input.toPlainText().strip()
        new_genre = self.genre_input.toPlainText().strip()

        if not new_title:
            QMessageBox.critical(self, "Error", "Title cannot be empty")
            return

        bk.UpdateSongDetails(self.original_title, new_title, new_artist, new_genre, URL=new_url)
        self.accept()

# Main Window
class MusicManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Manager")
        self.setGeometry(100, 100, 1100, 700)
        
        # Setup Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Setup UI Components
        self.setup_table()
        self.setup_controls()
        self.setup_statusbar()
        
        # Apply Styles
        self.apply_styles()

        # Load Data
        self.refresh_list()

    def setup_table(self):
        # Group Box for List
        gb = QGroupBox("Library Status")
        gb_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["S.No", "Title", "Artist", "Genre", "Status"])
        
        # Table Properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Title stretches
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        # Events
        self.table.itemSelectionChanged.connect(self.on_selection_change)

        gb_layout.addWidget(self.table)
        gb.setLayout(gb_layout)
        self.main_layout.addWidget(gb)

    def setup_controls(self):
        controls_layout = QHBoxLayout()

        # Global Actions
        global_gb = QGroupBox("Global Actions")
        global_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add New Song")
        self.btn_add.clicked.connect(self.open_add_song)
        
        self.btn_download = QPushButton("Download Pending")
        self.btn_download.setProperty("class", "success")
        self.btn_download.clicked.connect(self.start_download)

        self.btn_update_img = QPushButton("Update Images")
        self.btn_update_img.clicked.connect(self.start_image_update)

        global_layout.addWidget(self.btn_add)
        global_layout.addWidget(self.btn_download)
        global_layout.addWidget(self.btn_update_img)
        global_gb.setLayout(global_layout)

        # Selected Actions
        selected_gb = QGroupBox("Selected Song Options")
        selected_layout = QHBoxLayout()

        self.btn_edit = QPushButton("Edit Details")
        self.btn_edit.clicked.connect(self.edit_song)
        
        self.btn_del_list = QPushButton("Del from List")
        self.btn_del_list.setProperty("class", "danger")
        self.btn_del_list.clicked.connect(lambda: self.delete_song("list"))

        self.btn_del_folder = QPushButton("Del from Disk")
        self.btn_del_folder.setProperty("class", "danger")
        self.btn_del_folder.clicked.connect(lambda: self.delete_song("folder"))
        
        self.btn_del_both = QPushButton("Del Both")
        self.btn_del_both.setProperty("class", "danger_dark")
        self.btn_del_both.clicked.connect(lambda: self.delete_song("both"))

        selected_layout.addWidget(self.btn_edit)
        selected_layout.addWidget(self.btn_del_list)
        selected_layout.addWidget(self.btn_del_folder)
        selected_layout.addWidget(self.btn_del_both)
        selected_gb.setLayout(selected_layout)

        # Disable selection buttons initially
        for btn in [self.btn_edit, self.btn_del_list, self.btn_del_folder, self.btn_del_both]:
            btn.setEnabled(False)

        controls_layout.addWidget(global_gb, 1)
        controls_layout.addWidget(selected_gb, 1)
        self.main_layout.addLayout(controls_layout)

    def setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def refresh_list(self):
        self.table.setRowCount(0)
        for index, row in bk.SongDF.iterrows():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # Helper to create item centered
            def make_item(text, center=False):
                item = QTableWidgetItem(str(text))
                if center: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item

            self.table.setItem(row_idx, 0, make_item(index + 1, True))
            self.table.setItem(row_idx, 1, make_item(row['title']))
            self.table.setItem(row_idx, 2, make_item(row['artist']))
            self.table.setItem(row_idx, 3, make_item(row['genre']))
            self.table.setItem(row_idx, 4, make_item(row['status'], True))
        
        self.on_selection_change() # Update button states

    def on_selection_change(self):
        selected = self.table.selectionModel().selectedRows()
        count = len(selected)
        
        self.btn_edit.setEnabled(count == 1)
        self.btn_del_list.setEnabled(count > 0)
        self.btn_del_folder.setEnabled(count > 0)
        self.btn_del_both.setEnabled(count > 0)

    # --- Actions ---
    def open_add_song(self):
        dlg = AddSongDialog(self)
        if dlg.exec():
            self.refresh_list()

    def edit_song(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        title = self.table.item(rows[0].row(), 1).text()
        
        dlg = EditSongDialog(title, self)
        if dlg.exec():
            self.refresh_list()

    def delete_song(self, mode):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                   f"Are you sure you want to delete {len(rows)} item(s)?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No: return

        titles = [self.table.item(row.row(), 1).text() for row in rows]
        
        for title in titles:
            if mode in ["folder", "both"]:
                bk.DeleteSongFromDisk(title)
            
            if mode in ["list", "both"]:
                bk.SongDF = bk.SongDF[bk.SongDF.title != title]
        
        if mode in ["list", "both"]:
            bk.SaveSongfile()
            
        self.refresh_list()
        self.status.showMessage(f"Deleted {len(titles)} songs ({mode}).")

    def start_download(self):
        self.btn_download.setEnabled(False)
        self.worker = DownloadWorker()
        self.worker.progress_update.connect(lambda s: self.status.showMessage(s))
        self.worker.list_refresh.connect(self.refresh_list)
        self.worker.finished_all.connect(self.on_download_finished)
        self.worker.start()

    def on_download_finished(self):
        self.btn_download.setEnabled(True)
        QMessageBox.information(self, "Success", "Downloads Complete!")
        self.refresh_list()

    def start_image_update(self):
        self.status.showMessage("Updating images in background...")
        self.img_worker = ImageWorker()
        self.img_worker.finished_update.connect(lambda: QMessageBox.information(self, "Done", "Images Updated"))
        self.img_worker.start()

    def closeEvent(self, event):
        bk.SaveSongfile()
        event.accept()

    def apply_styles(self):
        # A simple modern Dark/Fusion stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { color: #ffffff; font-size: 14px; }
            QGroupBox { 
                font-weight: bold; border: 1px solid #555; 
                margin-top: 10px; padding-top: 10px; border-radius: 5px; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QTableWidget { 
                background-color: #333; gridline-color: #444; 
                selection-background-color: #0078d7; 
            }
            QHeaderView::section { background-color: #444; padding: 4px; border: 1px solid #555; }
            QLineEdit, QTextEdit { 
                background-color: #444; border: 1px solid #555; 
                border-radius: 4px; padding: 4px; color: white;
            }
            QPushButton { 
                background-color: #555; border: 1px solid #666; 
                border-radius: 4px; padding: 6px 12px; min-width: 80px;
            }
            QPushButton:hover { background-color: #666; }
            QPushButton:pressed { background-color: #444; }
            QPushButton:disabled { background-color: #333; color: #777; border: 1px solid #444; }
            
            QPushButton[class="success"] { background-color: #2e7d32; border-color: #1b5e20; }
            QPushButton[class="success"]:hover { background-color: #388e3c; }
            
            QPushButton[class="danger"] { background-color: #c62828; border-color: #b71c1c; }
            QPushButton[class="danger"]:hover { background-color: #d32f2f; }

            QPushButton[class="danger_dark"] { background-color: #8a0000; border-color: #500; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Helps cross-platform look
    window = MusicManagerWindow()
    window.show()
    sys.exit(app.exec())