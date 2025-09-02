import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import feedparser
import webbrowser
import threading
import time
import sqlite3
import csv
import requests
from PIL import Image
import pymupdf as fitz  # PyMuPDF
from plyer import notification  # pip install plyer

# Configuration
FEEDS = {
    "Announcements": ("https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml", 300),
    "Annual Reports": ("https://nsearchives.nseindia.com/content/RSS/Annual_Reports.xml", 600),
    "Board Meetings": ("https://nsearchives.nseindia.com/content/RSS/Board_Meetings.xml", 300),
    "Sustainability": ("https://nsearchives.nseindia.com/content/RSS/brsr.xml", 600),
}
USER_AGENT = "Mozilla/5.0"
DB_FILE = "rss_items.db"
ALERT_KEYWORDS = ["dividend", "meeting", "sustainability"]

class RSSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Indian Stock Market RSS Visualizer")
        self.geometry("1000x700")
        self._init_db()
        self.entries = []
        self._create_widgets()
        self._load_entries()
        for feed, (_, interval) in FEEDS.items():
            self._schedule_refresh(feed, interval)

    def _init_db(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                link TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                summary TEXT,
                published TEXT,
                read INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text="Refresh All", command=self._refresh_all).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="Mark All Read", command=self._mark_all_read).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Export CSV", command=self._export_csv).pack(side=tk.RIGHT)
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self._apply_search())

        self.notebook = ttk.Notebook(self)
        self.trees = {}
        for feed in FEEDS:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=feed)
            cols = ("title", "published", "read")
            tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
            for col, hd, w in zip(cols, ["Title", "Published", "Read"], [500, 140, 60]):
                tree.heading(col, text=hd)
                tree.column(col, width=w)
            tree.bind("<<TreeviewSelect>>", self._on_select)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb = ttk.Scrollbar(frame, command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            self.trees[feed] = tree
        self.notebook.pack(fill=tk.BOTH, expand=True)

        preview_frame = ttk.Frame(self, relief=tk.GROOVE)
        preview_frame.pack(fill=tk.X, padx=5, pady=5)
        self.preview = tk.Text(preview_frame, height=8, wrap=tk.WORD)
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.config(state=tk.DISABLED)

        self.status = ttk.Label(self, text="Ready", anchor=tk.W)
        self.status.pack(fill=tk.X)

    def _refresh_all(self):
        for feed in FEEDS:
            self._fetch_feed(feed)

    def _schedule_refresh(self, feed, interval):
        self.after(interval * 1000, lambda f=feed: [self._fetch_feed(f), self._schedule_refresh(f, interval)])

    def _fetch_feed(self, feed):
        def worker():
            self.status.config(text=f"Refreshing {feed}...")
            url, _ = FEEDS[feed]
            data = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for entry in data.entries:
                link = entry.get("link","")
                title = entry.get("title","")
                summary = entry.get("summary","")
                published = entry.get("published","")
                try:
                    c.execute("INSERT INTO items VALUES (?,?,?,?,?,0)",
                              (link, feed, title, summary, published))
                    for kw in ALERT_KEYWORDS:
                        if kw.lower() in title.lower():
                            notification.notify(title=f"{feed} alert", message=title, timeout=5)
                            break
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
            conn.close()
            self.after(0, lambda: [self._load_entries(), self.status.config(text=f"{feed} refreshed")])
        threading.Thread(target=worker, daemon=True).start()

    def _load_entries(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT source,title,published,read,summary,link FROM items ORDER BY published DESC")
        rows = c.fetchall()
        conn.close()
        self.entries = [
            {"source":r[0],"title":r[1],"published":r[2],
             "read":bool(r[3]),"summary":r[4],"link":r[5]}
            for r in rows
        ]
        self._populate_trees(self.entries)

    def _populate_trees(self, entries):
        for feed, tree in self.trees.items():
            for iid in tree.get_children():
                tree.delete(iid)
        for idx, e in enumerate(entries):
            self.trees[e["source"]].insert("", tk.END, iid=idx,
                                           values=(e["title"], e["published"],
                                                   "Yes" if e["read"] else "No"))

    def _apply_search(self):
        term = self.search_var.get().lower()
        filtered = [e for e in self.entries if term in e["title"].lower() or term in e["summary"].lower()]
        self._populate_trees(filtered)
        self.status.config(text=f"Filtered by '{term}'")

    def _on_select(self, event):
        tree = event.widget
        sel = tree.focus()
        if not sel: return
        entry = self.entries[int(sel)]
        threading.Thread(target=self._load_preview, args=(entry,), daemon=True).start()

    def _load_preview(self, entry):
        text = entry["summary"]
        url = entry["link"]
        if url.lower().endswith(".pdf"):
            try:
                resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
                resp.raise_for_status()
                doc = fitz.open(stream=resp.content, filetype="pdf")
                page = doc.load_page(0)
                txt = page.get_text("text")
                text = txt[:500].replace("\n"," ") + "…"
            except Exception as e:
                text = f"[PDF preview error]\n{e}"
        self.after(0, lambda: self._update_preview(text, url))

    def _update_preview(self, text, url):
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, text)
        self.preview.config(state=tk.DISABLED)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE items SET read=1 WHERE link=?", (url,))
        conn.commit()
        conn.close()
        self._load_entries()

    def _mark_all_read(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE items SET read=1")
        conn.commit()
        conn.close()
        self._load_entries()
        self.status.config(text="All marked read")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Source","Title","Published","Read","Link"])
            for e in self.entries:
                writer.writerow([e["source"],e["title"],e["published"],
                                 "Yes" if e["read"] else "No",e["link"]])
        messagebox.showinfo("Export", f"Exported to {path}")

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = RSSApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

