import Backend as bk
from PyQt6.QtCore import QThread, pyqtSignal

# Download Thread
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) 
    RefreshList = pyqtSignal()       
    Finished = pyqtSignal(int, int)      

    def __init__(self, titles):
        super().__init__()
        self.rows = bk.SongDF[bk.SongDF['Title'].isin(titles)]

    def run(self):
        successes = 0
        fails = 0
        for _, row in self.rows.iterrows():
            title = row['Title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            success = bk.DownloadSong(row['VideoID'], title, artist=row['Artist'], genre=row['Genre'], encoding=bk.Config.get("Encoding"))
            if success: successes+=1
            else: fails+=1
            self.RefreshList.emit()

        self.ProgressUpdate.emit("Ready")
        self.Finished.emit(successes, fails)

# Update Images Thread
class ImageWorker(QThread):
    Finished = pyqtSignal()

    def __init__(self, titles, redownload):
        super().__init__()
        self.titles = titles
        self.redownload = redownload

    def run(self):
        for title in self.titles:
            ImagePath = bk.AppData / "Images" / f"{title}.jpg"
            # Download cover if not exists or redownload is True
            if self.redownload or not ImagePath.exists():
                id = bk.SongDF.loc[bk.SongDF['Title'] == title, 'VideoID'].item()
                bk.DownloadCover(id, title)
            
            # Add cover art
            for ext in ['mp3', 'flac', 'm4a']:
                SongPath = bk.MusicDir / f"{title}.{ext}"
                if SongPath.exists() and ImagePath.exists():
                    bk.AddCoverArt(SongPath, ImagePath, ext)
                    break
        self.Finished.emit()

# Init backend & download ffmpeg
class InitWorker(QThread):
    finished = pyqtSignal(bool)
    status = pyqtSignal(str)

    def run(self):
        bk.Init()
        try:
            if not bk.IsFfmpegInstalled():
                self.status.emit("Downloading FFmpeg (this may take a minute)...")
                bk.LocalFFMPEG()
            
            # Final check
            success = bk.IsFfmpegInstalled()
            self.finished.emit(success)
        except Exception as e:
            print(f"Worker Error: {e}")
            self.finished.emit(False)