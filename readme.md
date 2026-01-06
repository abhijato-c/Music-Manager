# Music Manager

An extremely basic desktop application for managing and downloading a local music library. This tool allows you to track your favorite songs, download them from YouTube with high-quality audio extraction, and automatically manage metadata and cover art.

---

## Features

- **Library Tracking**: Maintain a persistent list of songs with details for Title, Artist, and Genre.
- **High-Quality Downloads**: Downloads audio at high bitrates and converts them to your preferred format (MP3, FLAC, or M4A).
- **Automatic Tagging**: Automatically fetches YouTube thumbnails and embeds them along with Artist and Genre tags directly into the audio files.
- **Real-Time Status**: A dedicated action bar at the bottom of the interface displays current tasks, such as active downloads or image updates.
- **Background Processing**: Operations like downloading and updating tags run in background threads to ensure the UI remains responsive.
- **Safe Exit**: Includes a protection layer that prevents the application from closing abruptly during an active download to avoid file corruption.

---

## Prerequisites

Since this application is provided as a standalone binary, most dependencies are included. However, you must have the following installed on your system:

- **FFmpeg**: This is required for audio conversion and metadata tagging. 
  - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder to your System PATH.
  - **macOS**: Install via Homebrew: `brew install ffmpeg`.
  - **Linux**: Install via your package manager: `sudo apt install ffmpeg`.

---

## Usage

1. **Add Songs**: Enter the Title and YouTube URL. Artist and Genre are optional but recommended for better library organization.
2. **Download**: Click **Download All Pending** to process all songs in your list that aren't yet on your disk.
3. **Manage Files**:
    - **Edit**: Update song details for a specific entry.
    - **Delete**: Remove entries from the list, delete the local file from your folder, or both.
4. **Update Images**: Use this feature to re-apply cover art to your local music files if they were downloaded without tags.

---

## Storage & Configuration

- **Music Folder**: By default, songs are saved to your system's default Music directory. You can customize this in the `config.json` file located in the application's AppData folder.
- **AppData**: The application stores its database (`Songfile.csv`), configuration, and cached images in a local `MusicManager` folder within your user profile's AppData/Local (Windows) or Application Support (macOS) directory.

---

## Disclaimer

This tool is intended for personal use. Please respect the Terms of Service of content platforms and copyright laws in your jurisdiction.