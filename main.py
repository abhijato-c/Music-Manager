import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import Backend as bk
import subprocess

class MusicManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Manager")
        self.root.geometry("1000x650")
        self.active_threads = []
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Status Variable
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        self.setup_ui()
        self.refresh_list()
    
    def on_closing(self):
        # Safely exit app
        if any(t.is_alive() for t in self.active_threads):
            if messagebox.askyesno("Exit", "Downloads are in progress. Exit anyway?"):
                self.root.destroy()
        else:
            self.root.destroy()

    def setup_ui(self):
        # Add Song
        add_frame = tk.LabelFrame(self.root, text="Add New Song")
        add_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(add_frame, text="Title (Req):").grid(row=0, column=0, padx=5, pady=2, sticky='e')
        self.title_entry = tk.Entry(add_frame, width=25)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="URL (Req):").grid(row=0, column=2, padx=5, pady=2, sticky='e')
        self.url_entry = tk.Entry(add_frame, width=25)
        self.url_entry.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(add_frame, text="Artist (Opt):").grid(row=1, column=0, padx=5, pady=2, sticky='e')
        self.artist_entry = tk.Entry(add_frame, width=25)
        self.artist_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="Genre (Opt):").grid(row=1, column=2, padx=5, pady=2, sticky='e')
        self.genre_entry = tk.Entry(add_frame, width=25)
        self.genre_entry.grid(row=1, column=3, padx=5, pady=2)

        tk.Button(add_frame, text="Add to List", command=self.action_add_song, bg="#dddddd").grid(row=0, column=4, rowspan=2, padx=15, sticky="ns")

        # Song list
        list_frame = tk.LabelFrame(self.root, text="Library Status")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.configure("Treeview", rowheight=35)
        
        cols = ("S.No", "Title", "Artist", "Genre", "Status")
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', style='Treeview')
        
        self.tree.heading("S.No", text="S.No")
        self.tree.heading("Title", text="Song Title")
        self.tree.heading("Artist", text="Artist")
        self.tree.heading("Genre", text="Genre")
        self.tree.heading("Status", text="Status")

        self.tree.column("S.No", width=1, anchor="center")
        self.tree.column("Title", width=250)
        self.tree.column("Artist", width=150)
        self.tree.column("Genre", width=100)
        self.tree.column("Status", width=100, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        # Global actions
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        global_actions = tk.LabelFrame(bottom_frame, text="Global Actions")
        global_actions.pack(side="left", fill="y")

        tk.Button(global_actions, text="Download All Pending", command=self.start_download_thread, bg="#4CAF50", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(global_actions, text="Update Images", command=self.ActionUpdateImages).pack(side="left", padx=5, pady=5)
        tk.Button(global_actions, text="Open Image Folder", command=self.action_open_images).pack(side="left", padx=5, pady=5)

        # Song actions
        self.item_actions = tk.LabelFrame(bottom_frame, text="Selected Song Options")
        self.item_actions.pack(side="right", fill="y")

        self.btn_edit = tk.Button(self.item_actions, text="Edit Details", command=self.btn_edit_click, state="disabled")
        self.btn_edit.pack(side="left", padx=5, pady=5)

        self.btn_del_list = tk.Button(self.item_actions, text="Delete from List", command=lambda: self.btn_delete_click("list"), state="disabled", fg="red")
        self.btn_del_list.pack(side="left", padx=5, pady=5)

        self.btn_del_folder = tk.Button(self.item_actions, text="Delete from Folder", command=lambda: self.btn_delete_click("folder"), state="disabled", fg="red")
        self.btn_del_folder.pack(side="left", padx=5, pady=5)

        self.btn_del_both = tk.Button(self.item_actions, text="Delete Both", command=lambda: self.btn_delete_click("both"), state="disabled", bg="#ffcccc", fg="red")
        self.btn_del_both.pack(side="left", padx=5, pady=5)

        # status bar
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w", padx=10, bg="#f0f0f0")
        status_bar.pack(side="bottom", fill="x")

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        undownloaded = bk.GetUndownloadedSongs()
        
        for index, row in bk.SongDF.iterrows():
            status = "Pending" if row['title'] in undownloaded else "Downloaded"
            self.tree.insert("", "end", values=(index, row['title'], row['artist'], row['genre'], status))
        
        self.on_selection_change(None)

    def on_selection_change(self, event):
        selected = self.tree.selection()
        
        self.btn_edit.config(state="disabled")
        self.btn_del_list.config(state="disabled")
        self.btn_del_folder.config(state="disabled")
        self.btn_del_both.config(state="disabled")

        if not selected: return

        if len(selected) == 1:
            self.btn_edit.config(state="normal")
        
        self.btn_del_list.config(state="normal")

        item = self.tree.item(selected[0])
        status = item['values'][4]

        if "Downloaded" in status:
            self.btn_del_folder.config(state="normal")
            self.btn_del_both.config(state="normal")

    def btn_edit_click(self):
        selected = self.tree.selection()
        if not selected: return
        title = self.tree.item(selected[0])['values'][1]
        self.EditWindowPopup(title)

    def btn_delete_click(self, mode):
        selected = self.tree.selection()
        if not selected: return

        title = self.tree.item(selected[0])['values'][1]
        
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete '{title}'?")
        if not confirm: return

        if mode == "folder" or mode == "both":
            bk.DeleteSongFromDisk(title)
        
        if mode == "list" or mode == "both":
            bk.SongDF = bk.SongDF[bk.SongDF.title != title]
            bk.SaveSongfile()

        self.refresh_list()

    def action_add_song(self):
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        artist = self.artist_entry.get().strip()
        genre = self.genre_entry.get().strip()

        if title and url:
            bk.AddSongToSongfile(title, url, artist, genre)
            self.title_entry.delete(0, tk.END)
            self.url_entry.delete(0, tk.END)
            self.artist_entry.delete(0, tk.END)
            self.genre_entry.delete(0, tk.END)
            self.refresh_list()
        else:
            messagebox.showwarning("Input Error", "Title and URL are compulsory.")

    def start_download_thread(self):
        thread = threading.Thread(target=self.action_download_all, daemon=True)
        self.active_threads.append(thread)
        thread.start()

    def update_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))

    def action_download_all(self):
        undownloaded_titles = bk.GetUndownloadedSongs()
        if not undownloaded_titles:
            messagebox.showinfo("Done", "All songs are already downloaded!")
            return

        for title in undownloaded_titles:
            # Update Status Bar
            self.update_status(f"Downloading: {title}...")
            
            row = bk.SongDF.loc[bk.SongDF['title'] == title].iloc[0]
            print(f"Starting download for: {title}")
            bk.DownloadSong(row['URL'], title, artist=row['artist'], genre=row['genre'])
            
            # Refresh list immediately after each song checks out
            self.root.after(0, self.refresh_list)
        
        self.update_status("Ready")
        messagebox.showinfo("Success", "Download process completed!")

    def EditWindowPopup(self, title):
        row = bk.SongDF.loc[bk.SongDF['title'] == title].iloc[0]
        
        popup = tk.Toplevel(self.root)
        popup.title("Edit Song Details")
        popup.geometry("600x400")

        tk.Label(popup, text="Title:").pack(pady=5)
        e_title = tk.Entry(popup, width=30)
        e_title.insert(0, row['title'])
        e_title.pack()

        tk.Label(popup, text="Artist:").pack(pady=5)
        e_artist = tk.Entry(popup, width=30)
        e_artist.insert(0, row['artist'])
        e_artist.pack()

        tk.Label(popup, text="Genre:").pack(pady=5)
        e_genre = tk.Entry(popup, width=30)
        e_genre.insert(0, row['genre'])
        e_genre.pack()

        def save_changes():
            new_title = e_title.get().strip()
            new_artist = e_artist.get().strip()
            new_genre = e_genre.get().strip()
            
            if new_title:
                bk.UpdateSongDetails(title, new_title, new_artist, new_genre)
                self.refresh_list()
                popup.destroy()
            else:
                messagebox.showerror("Error", "Title cannot be empty")

        tk.Button(popup, text="Save Changes", command=save_changes, bg="#4CAF50", fg="white").pack(pady=20)

    def ActionUpdateImages(self):
        thread = threading.Thread(target=self._UpdateImages, daemon=True)
        self.active_threads.append(thread)
        thread.start()

    def _UpdateImages(self):
        self.update_status("Starting Image Updates...")
        for index, row in bk.SongDF.iterrows():
            title = row['title']
            self.update_status(f"Updating image for: {title}")
            
            image_path = bk.AppData / "Images" / f"{title}.jpg"
            for ext in ['mp3', 'flac', 'm4a']:
                song_path = bk.MusicDir / f"{title}.{ext}"
                if song_path.exists() and image_path.exists():
                    bk.AddCoverArt(song_path, image_path, ext)
                    break
        
        self.update_status("Ready")
        self.root.after(0, lambda: messagebox.showinfo("Update Complete", f"Updated all images."))

    def action_open_images(self):
        path = bk.AppData / "Images"
        if os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix':
            subprocess.Popen(['open' if bk.platform.system() == 'Darwin' else 'xdg-open', path])

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicManagerGUI(root)
    root.mainloop()