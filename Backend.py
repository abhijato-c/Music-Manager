from yt_dlp import YoutubeDL
import pandas as pd
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
import os
import json
from pathlib import Path
import subprocess
import platform

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
TempFolder = (AppData / "Temp")
TempFolder.mkdir(exist_ok=True)
SongFile = AppData / "Songfile.csv"
ConfigFile = AppData / "config.json"
Config = {
    "Music_Directory": str(GetMusicDir()),
    "Encoding": "mp3"
}

# Clear Temp Files
for file in os.listdir(TempFolder):
    Path.unlink(TempFolder / file)

# Create default config
if not ConfigFile.exists():
    with open(ConfigFile, 'w', encoding='utf-8') as f:
        json.dump(Config, f, indent=4)

# Create Songfile
if not SongFile.exists():
    SongFile.touch()
    with open(SongFile, 'w', encoding='utf-8') as f:
        f.write("title,artist,genre,VideoID,status\n")

# Load Config
with open(ConfigFile, 'r', encoding='utf-8') as f:
    Config = json.load(f)
    
    if Config.get("Music_Directory"):
        MusicDir = Path(Config.get("Music_Directory"))
    else:
        MusicDir = GetMusicDir()

SongDF = pd.read_csv(SongFile).fillna("").sort_values(by='Title').reset_index(drop=True)

def URLtoID(URL):
    return URL.split('&')[0].split('watch?v=')[-1]

def DownloadCover(id, title):
    ImagePath = AppData/"Images"/ (title+'.jpg')
    url = f'https://img.youtube.com/vi/{id}/hqdefault.jpg'
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

def DownloadSong(id, title, encoding = 'mp3', artist = '', genre = ''):
    CODEC_MAP = {
        'mp3': 'libmp3lame',
        'flac': 'flac',
        'm4a': 'aac',
    }
    TempFilename = f"{title}.webm" 
    TempPath = TempFolder / TempFilename
    FinalPath = MusicDir / f"{title}.{encoding}"

    try:
        video = YoutubeDL({
            'format':'251', #Highest quality as far as I've found out
            'paths':{'home':str(TempFolder)}, #Download the temp song before converting
            'outtmpl':TempFilename,
            'quiet': True,
            'no_warnings': True
        })
        video.download(['https://www.youtube.com/watch?v='+id])
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

    # Convert to desired format
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(TempPath)
        
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e.stderr.decode()}")
        return 0
    
    # Set status to Downloaded
    SongDF.loc[SongDF['Title'] == title, 'Status'] = 'Downloaded'
    SaveSongfile()

    try:
        DownloadCover(id, title)
        AddCoverArt(FinalPath, AppData/"Images"/ (title+'.jpg'), encoding)
        return 2
    except:
        return 1

def AddSongToSongfile(title, URL, artist = '', genre = ''):
    global SongDF
    id = URLtoID(URL)
    row = pd.DataFrame([{"Title": title, "VideoID": id, 'Artist': artist, 'Genre': genre, 'Status': 'Pending Download'}])
    SongDF = pd.concat([SongDF, row], ignore_index=True)
    SaveSongfile()

def DeleteSongFromDisk(title):
    SongDF.loc[SongDF['Title'] == title, 'Status'] = 'Pending Download'
    for ext in ['.mp3', '.flac', '.m4a']:
        fpath = MusicDir / f"{title}{ext}"
        if fpath.exists():
            try: os.remove(fpath)
            except Exception as e: print(f"Error deleting file: {e}")

def UpdateSongDetails(title, NewTitle = None, artist = None, genre = None, URL = None):
    global SongDF
    idx = SongDF.index[SongDF['Title'] == title].tolist()[0]

    if NewTitle != None: SongDF.at[idx, 'Title'] = NewTitle
    if artist != None: SongDF.at[idx, 'Artist'] = artist
    if genre != None: SongDF.at[idx, 'Genre'] = genre

    # Update metadata
    for ext in ['mp3', 'flac', 'm4a']:
        InpPath = MusicDir / f"{title}.{ext}"
        if not InpPath.exists():
            continue
        TempPath = TempFolder / f"{title}.{ext}"
        OutPath = MusicDir / f"{NewTitle}.{ext}" if NewTitle else InpPath
        
        cmd = [
            'ffmpeg', '-y', '-i', str(InpPath),
            '-metadata', f'title={SongDF.loc[SongDF['Title'] == NewTitle, 'Title'].item()}',
            '-metadata', f'artist={SongDF.loc[SongDF['Title'] == NewTitle, 'Artist'].item()}',
            '-metadata', f'genre={SongDF.loc[SongDF['Title'] == NewTitle, 'Genre'].item()}',
            '-c', 'copy', str(TempPath)
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(InpPath)
        os.replace(TempPath, OutPath)
    
    # Update VideoID if changed
    id = URLtoID(URL) if URL else None
    OldID = SongDF.loc[SongDF['Title'] == NewTitle, 'VideoID'].item()
    if id and id!=OldID:
        SongDF.at[idx, 'VideoID'] = id
        SongDF.at[idx, 'Status'] = 'Pending Download'
        DeleteSongFromDisk(NewTitle if NewTitle else title)

    SaveSongfile()

def UpdateSongStatuses():
    Downloaded = [x.rsplit('.', 1)[0] for x in os.listdir(MusicDir)]
    for i, row in SongDF.iterrows():
        if row['Title'] in Downloaded:
            SongDF.at[i, 'Status'] = 'Downloaded'
        else:
            SongDF.at[i, 'Status'] = 'Pending Download'
    SaveSongfile()

def GetSongMetadata(id):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"
    resp = requests.get(url, timeout=2)
    data = resp.json()
    return [data.get("title"), data.get("author_name")]

def ChangeMusicDir(NewDir):
    global MusicDir
    global Config

    MusicDir = Path(NewDir)
    Config['Music_Directory'] = str(MusicDir)
    UpdateSongStatuses()
    with open(ConfigFile, 'w', encoding='utf-8') as f:
        json.dump(Config, f, indent=4)

def UpdateDefaultFormat(fmt):
    global Config
    Config["Encoding"] = fmt
    with open(ConfigFile, "w") as f:
        json.dump(Config, f, indent=4)

def SaveSongfile():
    SongDF.sort_values(by='Title').reset_index(drop=True).to_csv(SongFile, index=False)