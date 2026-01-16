# Music Manager

A desktop application that manages your music playlist. It downloads songs from YouTube, and maintains metadata like Artist, Genre, and a cover picture.

---

## Prerequisites

Since this application is provided as a standalone binary, most dependencies are included. However, you must have the following installed on your system:

- **FFmpeg**: This is required for audio conversion and metadata tagging. 
  - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to your System PATH.
  - **macOS**: Install via Homebrew: `brew install ffmpeg`.
  - **Linux**: Install via your package manager: `sudo apt install ffmpeg`.

---

## Working

The app doesn't directly sync to a folder, instead, it maintains a `.csv` database of songs, their YouTube URL, and some metadata. This means that you can have an entire list of songs, and download them in any format at any time you wish. You can add all your songs at a go, and then let them download once you have added all your songs. After clicking on the download button, all pending songs are downloaded, and their cover art is fetched and linked automatically.

---

## Usage

1. **Add Songs**: Click on the Action tab in the menubar, and click Add Song. Enter the Title and YouTube URL. Artist and Genre are optional but recommended for better library organization.

2. **Download**: Click **Download All Pending** in the action tab to automatically download all songs in your list that aren't yet on your disk.

3. **Manage Files**:
    - **Edit**: Update song details for a specific entry.
    - **Delete**: Remove entries from the list, delete the local file from your folder, or both.

4. **Update Images**: Click on the Config tab -> open images folder. Edit and save the cover art of any song you wish, all images are stored in that folder. Once you are done editing the images, go to Actions -> Update images. This reapplies cover art to all of your songs.

5. **Delete Songs**: Select the song(s) you want to delete, and then go to Song -> Delete. You will find 3 options:
    - **Delete from list**: This removes the song from the list, but it remains in the folder. You can add it back into the list by the Add new   song action.
    - **Delete from folder**: The song remains in the list with its metadata and cover art, but the downloaded song is deleted. The song is marked as `Pending Download`, so clicking on Download all pending will redownload it. Useful when you want to redownload a song.
    - **Delete from folder and list**: This will completely get rid of the song, both from the list and the downloads. This is what you'd use if you want to compeltely get rid of a song.

---

## Storage & Configuration

- **Music Folder**: By default, songs are saved to your system's default Music directory. You can customize this by clicking on Config -> Change music directory.
- **AppData**: The application stores its database (`Songfile.csv`), configuration, and cached images in a local `MusicManager` folder within your user profile's AppData/Local (Windows) or Application Support (macOS) directory.

---

## Disclaimer

This tool is intended for personal use. Please respect the Terms of Service of content platforms and copyright laws in your jurisdiction.