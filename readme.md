# BytBeat

A desktop application that manages your music playlist. It downloads songs from YouTube, and maintains metadata like Artist, Genre, and a cover picture.

---

## Prerequisites

Ffmpeg is the only external dependency. If it is not already installed and added to path, BytBeat will try to install it on startup. This installation will be in BytBeat's AppData folder, thus, it won't be a global installation. If you want to install Ffmpeg globally -

- **FFmpeg**: This is required for audio conversion and metadata tagging. 
  - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to your System PATH.
  - **macOS**: Install via Homebrew: `brew install ffmpeg`.
  - **Linux**: Install via your package manager: `sudo apt install ffmpeg`.

---

## Working

BytBeat doesn't directly sync to a folder, instead, it maintains a `.csv` database of songs, their YouTube URL, and some metadata. This means that you can have an entire list of songs, and download them in any format at any time you wish. You can add all your songs at a go, and then let them download once you have added all your songs. After clicking on the download button, all pending songs are downloaded, and their cover art is fetched and linked automatically.

---

## Usage

1. **Add Songs**: Click on the Action tab in the menubar, and click Add Song. Enter the Title and YouTube URL. Artist and Genre are optional but recommended for better library organization.

2. **Download**: Click **Download All Pending** in the action tab to automatically download all songs in your list that aren't yet on your disk. Or, yoy could select specific song(s), right click -> **Download song(s)**

3. **Manage Files**:
    - **Edit**: Update song details for a specific entry.
    - **Delete**: Remove entries from the list, delete the local file from your folder, or both.

4. **Update Images**: Click on the Config tab -> open images folder. Edit and save the cover art of any song you wish, all images are stored in that folder. Once you are done editing the images, go to Actions -> Update images. This reapplies cover art to all of your songs.

5. **Delete Songs**: Select the song(s) you want to delete, and then go to Song -> Delete. You can choose to delete it from disk as well.

---

## Storage & Configuration

- **Music Folder**: By default, songs are saved to your system's default Music directory. You can customize this by clicking on Config -> Change music directory.
- **AppData**: The application stores its database (`Songfile.csv`), configuration, and cached images in a local `BytBeat` folder within your user profile's AppData/Local (Windows) or Application Support (macOS) directory.

---

## Disclaimer

This tool is intended for personal use. Please respect the Terms of Service of content platforms and copyright laws in your jurisdiction.