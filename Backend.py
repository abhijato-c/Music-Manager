from pathlib import Path
import platform
import os
import json
import yt_dlp
import subprocess
import pandas as pd

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

default_config = {
    "Music_Directory": str(GetMusicDir()),
}

if not ConfigFile.exists():
    with open(ConfigFile, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4)

if not SongFile.exists():
    SongFile.touch()
    with open(SongFile, 'w', encoding='utf-8') as f:
        f.write("title,URL\n")

with open(ConfigFile, 'r', encoding='utf-8') as f:
    Config = json.load(f)
    
    if Config.get("Music_Directory"):
        MusicDir = Path(Config.get("Music_Directory"))
    else:
        MusicDir = GetMusicDir()

SongDF = pd.read_csv(SongFile)

def DownloadSong(URL, title, encoding = 'mp3'):
    CODEC_MAP = {
        'mp3': 'libmp3lame',
        'flac': 'flac',
        'wav': 'pcm_s16le',   # Standard CD quality
        'aac': 'aac',
        'ogg': 'libvorbis'
    }
    TempFilename = f"{title}.webm" 
    TempPath = AppData / TempFilename
    FinalPath = MusicDir / f"{title}.{encoding}"

    video = yt_dlp.YoutubeDL({
        'format':'251', #Highest quality as far as I've found out
        'paths':{'home':str(AppData)}, #Download the temp song in the appdata directory before converting and moving it to the music folder
        'outtmpl':TempFilename,
        'quiet': True,
        'no_warnings': True
    })
    try:
        video.download([URL])
    except:
        print("Failed to download "+title)
    
    print(f"Converting to {encoding}...")
        
    # Build the ffmpeg command
    # -y: Overwrite output if it exists
    # -i: Input file
    # -metadata title="...": Sets the internal song title tag
    # -c:a: Audio codec
    # -vn: No video
    # -b:a 192k: Bitrate
    cmd = [
        'ffmpeg', '-y', 
        '-i', str(TempPath),
        '-metadata', f'title={title}',
        '-c:a', CODEC_MAP[encoding],
        '-vn',
        str(FinalPath)
    ]

    # For MP3, we might want to specify bitrate or VBR quality
    if encoding == 'mp3':
        cmd.extend(['-q:a', '2']) # VBR quality setting (approx 190-250kbps)

    try:
        # Run ffmpeg - capture_output hides logs
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(TempPath)
        
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e.stderr.decode()}")

def SaveSongfile():
    SongDF.to_csv(SongFile, index=False)

def AddSongToSongfile(title, URL):
    global SongDF
    row = pd.DataFrame([{"title": title, "URL": URL}])
    SongDF = pd.concat([SongDF, row], ignore_index=True)
    SaveSongfile()
