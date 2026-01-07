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

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        self.setup_ui()
        self.refresh_list()
    
    def on_closing(self):
        bk.SaveSongfile()
        self.root.destroy()

    def setup_ui(self):
        # Add new song
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
        
        for col in cols:
            self.tree.heading(col, text=col)
        
        self.tree.column("S.No", width=50, anchor="center")
        self.tree.column("Title", width=250)
        self.tree.column("Status", width=120, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        # Action buttons
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        global_actions = tk.LabelFrame(bottom_frame, text="Global Actions")
        global_actions.pack(side="left", fill="y")

        tk.Button(global_actions, text="Download All Pending", command=self.start_download_thread, bg="#4CAF50", fg="white").pack(side="left", padx=5, pady=5)
        tk.Button(global_actions, text="Update Images", command=self.ActionUpdateImages).pack(side="left", padx=5, pady=5)

        self.item_actions = tk.LabelFrame(bottom_frame, text="Selected Song Options")
        self.item_actions.pack(side="right", fill="y")

        self.btn_edit = tk.Button(self.item_actions, text="Edit Details", command=self.btn_edit_click, state="disabled")
        self.btn_edit.pack(side="left", padx=5, pady=5)

        self.btn_del_list = tk.Button(self.item_actions, text="Delete from List", command=lambda: self.DeleteClick("list"), state="disabled", fg="red")
        self.btn_del_list.pack(side="left", padx=5, pady=5)

        self.btn_del_folder = tk.Button(self.item_actions, text="Delete from Folder", command=lambda: self.DeleteClick("folder"), state="disabled", fg="red")
        self.btn_del_folder.pack(side="left", padx=5, pady=5)

        self.btn_del_both = tk.Button(self.item_actions, text="Delete Both", command=lambda: self.DeleteClick("both"), state="disabled", bg="#ffcccc", fg="red")
        self.btn_del_both.pack(side="left", padx=5, pady=5)

        tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(side="bottom", fill="x")

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for index, row in bk.SongDF.iterrows():
            self.tree.insert("", "end", values=(index + 1, row['title'], row['artist'], row['genre'], row['status']))
        self.on_selection_change(None)

    def on_selection_change(self, event):
        selected = self.tree.selection()
        state = "normal" if selected else "disabled"
        
        self.btn_edit.config(state="normal" if len(selected) == 1 else "disabled")
        self.btn_del_list.config(state=state)
        self.btn_del_folder.config(state=state)
        self.btn_del_both.config(state=state)

    def btn_edit_click(self):
        selected = self.tree.selection()
        title = self.tree.item(selected[0])['values'][1]
        self.EditWindowPopup(title)

    def DeleteClick(self, mode):
        selected = self.tree.selection()
        if not selected: return
        
        if not messagebox.askyesno("Confirm", f"Delete {len(selected)} item(s)?"): return

        titles = [self.tree.item(x)['values'][1] for x in selected]
        for title in titles:
            if mode in ["folder", "both"]:
                bk.DeleteSongFromDisk(title)
            
            if mode in ["list", "both"]:
                bk.SongDF = bk.SongDF[bk.SongDF.title != title]
                bk.SaveSongfile()
        self.refresh_list()

    def EditWindowPopup(self, title):
        row = bk.SongDF.loc[bk.SongDF['title'] == title].iloc[0]
        popup = tk.Toplevel(self.root)
        popup.title("Edit Song Details")
        popup.geometry("450x550")

        def create_field(label_text, default_value):
            tk.Label(popup, text=label_text).pack(pady=(10, 0))
            # Textboxes are now taller and pre-filled
            txt = tk.Text(popup, width=35, height=2)
            txt.insert("1.0", default_value)
            txt.pack(pady=5)
            return txt

        e_title = create_field("Title:", row['title'])
        # Reconstruct URL from VideoID
        current_url = f"https://www.youtube.com/watch?v={row['VideoID']}"
        e_url = create_field("YouTube URL:", current_url)
        e_artist = create_field("Artist:", row['artist'])
        e_genre = create_field("Genre:", row['genre'])

        def save():
            new_title = e_title.get("1.0", "end-1c").strip()
            new_url = e_url.get("1.0", "end-1c").strip()
            if new_title:
                bk.UpdateSongDetails(title, new_title, e_artist.get("1.0", "end-1c").strip(), 
                                    e_genre.get("1.0", "end-1c").strip(), URL=new_url)
                self.refresh_list()
                popup.destroy()
            else:
                messagebox.showerror("Error", "Title is required")

        tk.Button(popup, text="Save Changes", command=save, bg="#4CAF50", fg="white", width=20).pack(pady=20)

    def action_add_song(self):
        t, u = self.title_entry.get().strip(), self.url_entry.get().strip()
        if t and u:
            bk.AddSongToSongfile(t, u, self.artist_entry.get(), self.genre_entry.get())
            for e in [self.title_entry, self.url_entry, self.artist_entry, self.genre_entry]: e.delete(0, tk.END)
            self.refresh_list()
        else:
            messagebox.showwarning("Input Error", "Title and URL are required.")

    def start_download_thread(self):
        thread = threading.Thread(target=self.action_download_all, daemon=True)
        self.active_threads.append(thread)
        thread.start()

    def action_download_all(self):
        to_download = bk.SongDF[bk.SongDF['status'] != 'Downloaded']
        if to_download.empty:
            messagebox.showinfo("Done", "All songs are downloaded.")
            return

        for _, row in to_download.iterrows():
            self.status_var.set(f"Downloading: {row['title']}...")
            bk.DownloadSong(row['VideoID'], row['title'], artist=row['artist'], genre=row['genre'])
            self.root.after(0, self.refresh_list)
        
        self.status_var.set("Ready")
        messagebox.showinfo("Success", "Downloads complete!")

    def ActionUpdateImages(self):
        threading.Thread(target=self._UpdateImages, daemon=True).start()

    def _UpdateImages(self):
        for _, row in bk.SongDF.iterrows():
            img_path = bk.AppData / "Images" / f"{row['title']}.jpg"
            for ext in ['mp3', 'flac', 'm4a']:
                song_path = bk.MusicDir / f"{row['title']}.{ext}"
                if song_path.exists() and img_path.exists():
                    bk.AddCoverArt(song_path, img_path, ext)
                    break
        self.root.after(0, lambda: messagebox.showinfo("Update", "Images updated."))

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicManagerGUI(root)
    root.mainloop()