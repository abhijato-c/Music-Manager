from pathlib import Path
import platform
import os
import json
import yt_dlp
import subprocess
import pandas as pd
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover

def GetAppDataFolder():
    home = Path.home()
    system = platform.system()

    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / 'MusicManager'
    elif system == "Darwin":  # macOS
        return home / "Library/Application Support" / 'MusicManager'
    else:  # Linux / Others
        return home / ".local/share" / 'MusicManager'

def GetMusicDir():
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        return home / "Music"
    elif system == "Darwin":
        return home / "Music"
    elif system == "Linux":
        xdg_music = os.environ.get("XDG_MUSIC_DIR")
        if xdg_music:
            return Path(xdg_music)
        # Fallback for Linux if XDG is not set
        return home / "Music"
    return home / "Music" # Universal fallback

AppData = GetAppDataFolder()
AppData.mkdir(parents=True, exist_ok=True)
(AppData / "Images").mkdir(exist_ok=True)
SongFile = AppData / "Songfile.csv"
ConfigFile = AppData / "config.json"

for file in os.listdir(AppData):
    if file.endswith('.webm'):
        Path.unlink(AppData / file)

default_config = {
    "Music_Directory": str(GetMusicDir()),
}

if not ConfigFile.exists():
    with open(ConfigFile, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)

if not SongFile.exists():
    SongFile.touch()
    with open(SongFile, 'w', encoding='utf-8') as f:
        f.write("title,URL,artist,genre\n")

with open(ConfigFile, 'r', encoding='utf-8') as f:
    Config = json.load(f)
    
    if Config.get("Music_Directory"):
        MusicDir = Path(Config.get("Music_Directory"))
    else:
        MusicDir = GetMusicDir()

SongDF = pd.read_csv(SongFile).fillna("")

def DownloadCover(URL, title):
    ImagePath = AppData/"Images"/ (title+'.jpg')
    url = f'https://img.youtube.com/vi/{URL[32:43]}/hqdefault.jpg'
    with open(ImagePath, 'wb') as fil:
        fil.write(requests.get(url).content)


def AddCoverArt(SongPath, ImgPath, ext):
    with open(ImgPath, 'rb') as ImgFil:
        Img = ImgFil.read()

    # ID3 Tags
    if ext == 'mp3':
        try:
            audio = MP3(SongPath, ID3=ID3)
            # Add ID3 tag if it doesn't exist
            try:
                audio.add_tags()
            except error:
                pass
            
            audio.tags.add(APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',
                type=3,      # 3 is for album front cover
                desc='Cover',
                data=Img
            ))
            audio.save()
        except Exception as e:
            print(f"Failed to tag MP3: {e}")

    elif ext == 'flac':
        audio = FLAC(SongPath)
        image = Picture()
        image.type = 3
        image.mime = "image/jpeg"
        image.desc = "front cover"
        image.data = Img
        audio.add_picture(image)
        audio.save()

    # MP4 Container
    elif ext == 'm4a':
        audio = MP4(SongPath)
        audio["covr"] = [MP4Cover(Img, imageformat=MP4Cover.FORMAT_JPEG)]
        audio.save()

    else:
        print("Unsupported file extension")
        return

def DownloadSong(URL, title, encoding = 'mp3', artist = '', genre = ''):
    CODEC_MAP = {
        'mp3': 'libmp3lame',
        'flac': 'flac',
        'm4a': 'aac',
    }
    TempFilename = f"{title}.webm" 
    TempPath = AppData / TempFilename
    FinalPath = MusicDir / f"{title}.{encoding}"

    try:
        video = yt_dlp.YoutubeDL({
            'format':'251', #Highest quality as far as I've found out
            'paths':{'home':str(AppData)}, #Download the temp song before converting
            'outtmpl':TempFilename,
            'quiet': True,
            'no_warnings': True
        })
        video.download([URL])
    except:
        print("Failed to download "+title)
        return 0
        
    # Build the ffmpeg command
    cmd = [
        'ffmpeg', '-y', 
        '-i', str(TempPath),
        '-metadata', f'title={title}',
        '-metadata', f'artist={artist}',
        '-metadata', f'genre={genre}',
        '-c:a', CODEC_MAP[encoding],
        '-vn',
        str(FinalPath)
    ]

    if encoding == 'mp3':
        cmd.extend(['-q:a', '2'])

    try:
        # Run ffmpeg - capture_output hides logs
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(TempPath)
        
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e.stderr.decode()}")
        return 0
    
    try:
        DownloadCover(URL, title)
        AddCoverArt(FinalPath, AppData/"Images"/ (title+'.jpg'), encoding)
        return 2
    except:
        return 1

def SaveSongfile():
    SongDF.to_csv(SongFile, index=False)

def AddSongToSongfile(title, URL, artist = '', genre = ''):
    global SongDF
    URL = URL.split('&')[0]
    row = pd.DataFrame([{"title": title, "URL": URL, 'artist': artist, 'genre': genre}])
    SongDF = pd.concat([SongDF, row], ignore_index=True)
    SaveSongfile()

def GetUndownloadedSongs():
    songs = SongDF['title'].tolist()
    downloaded = [x.split('.')[0] for x in os.listdir(MusicDir)]
    return [x for x in songs if x not in downloaded]

def DeleteSongFromDisk(title):
    for ext in ['.mp3', '.flac', '.m4a']:
        fpath = MusicDir / f"{title}{ext}"
        if fpath.exists():
            try: os.remove(fpath)
            except Exception as e: print(f"Error deleting file: {e}")

def UpdateSongDetails(OldTitle, NewTitle = None, artist = None, genre = None):
    global SongDF
    idx = SongDF.index[SongDF['title'] == OldTitle].tolist()
    if not idx: return

    if NewTitle != None: SongDF.at[idx[0], 'title'] = NewTitle
    if artist != None: SongDF.at[idx[0], 'artist'] = artist
    if genre != None: SongDF.at[idx[0], 'genre'] = genre
    SaveSongfile()