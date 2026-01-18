import Backend as bk
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QDialog, QLabel, QLineEdit,
)

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
        
        if title in bk.SongDF['Title'].tolist():
            self.StatusLabel.setStyleSheet("color: #f44336;")
            self.StatusLabel.setText("Error: Title already exists!")
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
        
        if NewTitle != self.OriginalTitle and NewTitle in bk.SongDF['Title'].tolist():
            QMessageBox.critical(self, "Error", "This title already exists, please select a new one!")
            return

        bk.UpdateSongDetails(self.OriginalTitle, NewTitle, NewArtist, NewGenre, NewURL)
        self.accept()