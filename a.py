import os
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget,
                                QVBoxLayout, QHBoxLayout,
                                QPushButton, QFileDialog,
                                QStackedWidget, QProgressBar,
                                QScrollArea, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QObject
from PySide6.QtGui import QIcon


DB_DIR = Path.home() / ".file_sorter"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DB_DIR / "sort_history.db")

NAV_BUTTON_STYLE = """
    QPushButton {
        color: #cccccc;
        background-color: transparent;
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #2a2a2a;
        color: white;
    }
    QPushButton:checked {
        background-color: #333333;
        color: white;
        border-left: 3px solid #4da6ff;
    }
"""

BROWSE_STYLE = """
    QPushButton {
        background-color: transparent;
        color: white;
        border: 1px solid #555555;
        border-radius: 6px;
        padding: 10px;
        font-size: 14px;
    }
    QPushButton:hover {
        border-color: #888888;
        background-color: #2a2a2a;
    }
"""

SORT_STYLE = """
    QPushButton {
        background-color: #4da6ff;
        color: #0d0d0d;
        border: none;
        border-radius: 6px;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #6ab8ff;
    }
    QPushButton:disabled {
        background-color: #333333;
        color: #777777;
    }
"""
class FileSorterWorker(QObject):
    # Define custom signals to communicate safely with the main UI thread
    progress = Signal(int)       # Sends percentage integers (0 to 100)
    status_message = Signal(str) # Sends text updates
    finished = Signal()          # Alerts the UI that the job is complete
    sorting_summary = Signal(dict)   
        

    def __init__(self, target_folder):
        super().__init__()
        self.target_folder = target_folder

    @Slot()
    def run_sorting(self):
        # 📂 Define your format map right here at the start of the method
        fileFormat = {
            "Web": [".html5", ".html", ".htm", ".xhtml", ".css", ".js", ".jsx", ".ts", ".tsx", 
                    ".php", ".asp", ".aspx", ".jsp", ".xml", ".json", ".yaml", ".yml", ".svg", ".rss"], 
            "Picture": ['.heif', 'svg', '.tif', '.nef', '.dng', '.cr2', '.arw', '.raw', '.jfif', 
                        '.heic', '.psd', '.tiff', '.rw2', '.orf', '.ico', '.jpg', '.avif', '.bpg', 
                        '.gif', '.bmp', '.png', '.webp', '.jpeg'], 
            "Video": ['.flv', '.mpeg', '.ts', '.mng', '.f4v', '.3gp', '.mp4', '.m4v', '.webm', 
                      '.wmv', '.avi', '.mov', '.vob', '.qt', '.mpg', '.rmvb', '.divx', '.asf', 
                      '.ogv', '.rm', '.mkv'], 
            "Document": ['.dotx', '.fdf', '.dox', '.xlsx', '.rtf', '.numbers', '.pdf', '.xls', 
                         '.rvg', '.xps', '.ods', '.tex', '.rtfd', '.docx', '.odt', '.csv', '.pwi', 
                         '.key', '.wpd', '.mobi', '.docm', '.epub', '.ppt', '.pptx', '.xsn', 
                         '.doc', '.oxps', '.pages', '.odp', '.txt'], 
            "Compressed": [".a", ".ar", ".cpio", ".iso", ".zip", ".rar", ".7z", ".tar", ".gz", 
                           ".bz2", ".xz", ".tgz", ".cab", ".lz", ".lzma", ".z", ".rz", ".dmg", ".xar"], 
            "Audio": ['.aiff', '.mp3', '.aif', '.vox', '.flac', '.m4b', '.raw', '.m4a', '.ape', 
                      '.ac3', '.msv', '.dvf', '.m4p', 'oga', '.wma', '.mid', '.aa', '.opus', 
                      '.midi', '.ogg', '.ra', '.amr', '.aac', '.wav'],
            "Codes": [".py", ".pyw", ".java", ".class", ".c", ".h", ".cpp", ".hpp", ".cs", ".go", 
                      ".rs", ".swift", ".kt", ".kts", ".rb", ".pl", ".lua", ".r", ".m", ".scala", 
                      ".dart", ".sql", ".sh", ".bat", ".ps1", ".vbs"],
            "Executables": [".exe", ".msi", ".msix", ".msixbundle", ".appx", ".appxbundle", 
                            ".bat", ".cmd", ".com", ".scr", ".ps1", ".vbs", ".js", ".jse", ".wsf", ".hta"]
        } 

        folder = Path(self.target_folder)
        
    
        files_to_sort = [item for item in folder.iterdir() if item.is_file()]
        total_files = len(files_to_sort)
        category_counts = {}

        if total_files == 0:
            self.sorting_summary.emit(category_counts)
            self.finished.emit()
            return
        
        for i, file in enumerate(files_to_sort, start=1):
            ext = Path(file.name).suffix.lower()
            category = "Other"
        
            # Scan your format dictionary
            for name, extensions in fileFormat.items():
                if ext in extensions:
                    category = name
                    break
        
            destination_folder = folder / category
            destination_folder.mkdir(exist_ok=True)
        
            # Move files securely using absolute path handling strings
            try:
                shutil.move(str(file.resolve()), str(destination_folder / file.name))
                category_counts[category] = category_counts.get(category, 0) + 1

            except FileNotFoundError:
                continue 

            # Send your background metrics smoothly up to the Main UI Thread
            percentage = int((i / total_files) * 100)
            self.progress.emit(percentage)
            self.status_message.emit(f"Sorting file {i} of {total_files}...")

        # 3. Finalize execution and ship the results away
        self.sorting_summary.emit(category_counts)
        self.finished.emit()

      


class HistoryManager:
    """Handles all reading and writing to the sort history database."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create the history table if it doesn't already exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                count INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def log_sort_history(self, category_counts):
        """Insert one row per category for this sort run."""
        if not category_counts:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for category, count in category_counts.items():
            cursor.execute(
                "INSERT INTO history (timestamp, category, count) VALUES (?, ?, ?)",
                (timestamp, category, count)
            )

        conn.commit()
        conn.close()

    def fetch_history(self):
        """Return all history rows, most recent first."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, category, count FROM history ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def fetch_grouped_history(self):
        """Group history rows by sort session (timestamp), most recent first.

        Returns a list of dicts like:
        {"timestamp": "...", "categories": {"Document": 3, "Picture": 2}, "total": 5}
        """
        rows = self.fetch_history()  # already most-recent-first

        sessions = {}
        order = []  # preserves most-recent-first order of timestamps

        for timestamp, category, count in rows:
            if timestamp not in sessions:
                sessions[timestamp] = {}
                order.append(timestamp)
            sessions[timestamp][category] = sessions[timestamp].get(category, 0) + count

        grouped = []
        for timestamp in order:
            categories = sessions[timestamp]
            total = sum(categories.values())
            grouped.append({
                "timestamp": timestamp,
                "categories": categories,
                "total": total
            })

        return grouped


class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sorted = None

        self.history_manager = HistoryManager(DB_PATH)

        self.selected_folder = ""
        self.setWindowTitle("File Sorter 1.0")
        self.resize(700, 480)
        self.setWindowIcon(QIcon("icon.png"))
        self.setStyleSheet("background-color: #1c1c1c;")

        content = QWidget()
        self.setCentralWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top bar (sidebar toggle) ---
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet("background-color: #1a1a1a;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(12, 0, 0, 0)

        self.toggle_btn = QPushButton("\u2630")
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)

        top_bar_layout.addWidget(self.toggle_btn, alignment=Qt.AlignLeft)
        top_bar_layout.addStretch()

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar_width = 180
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)
        self.sidebar.setStyleSheet("""
            background-color: #1c1c1c;
            border-right: 1px solid #333333;
        """)
        self.sidebar.setAttribute(Qt.WA_StyledBackground, True)

        self.dashboard_btn = QPushButton("  \U0001F3E0  Dashboard")
        self.history_btn = QPushButton("  \U0001F553  History")

        nav_buttons = [self.dashboard_btn, self.history_btn]
        for btn in nav_buttons:
            btn.setStyleSheet(NAV_BUTTON_STYLE)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.dashboard_btn.setChecked(True)

        self.sidebar.setMinimumWidth(0)
        self.sidebar.setMaximumWidth(self.sidebar_width)
        self.sidebar_expanded = True

        # --- Pages ---
        self.pages = QStackedWidget()
        self.dashboard_page = self.build_dashboard_page()
        self.history_page = self.build_history_page()

        self.pages.addWidget(self.dashboard_page)  # index 0
        self.pages.addWidget(self.history_page)    # index 1

        self.dashboard_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.history_btn.clicked.connect(self.show_history_page)

        # --- Bottom row: sidebar + pages ---
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0) #
        bottom_layout.setSpacing(0)

        bottom_layout.addWidget(self.sidebar)
        bottom_layout.addWidget(self.pages)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(bottom_row)

    # ---------------- Sidebar toggle ----------------

    def toggle_sidebar(self):
        self.sidebar.setMaximumWidth(0 if self.sidebar_expanded else self.sidebar_width)
        self.sidebar_expanded = not self.sidebar_expanded

    # ---------------- Dashboard page ----------------

    def build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.status_area = QWidget()
        self.status_layout = QVBoxLayout(self.status_area)
        self.status_layout.setAlignment(Qt.AlignCenter)

        self.empty_state = self.build_empty_state()
        self.status_layout.addWidget(self.empty_state)

        layout.addWidget(self.status_area, stretch=1)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet(BROWSE_STYLE)

        self.sort_btn = QPushButton("Sort Files")
        self.sort_btn.setStyleSheet(SORT_STYLE)
        self.sort_btn.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        #self.progress_bar.setTextVisible(False)

        self.browse_btn.clicked.connect(self.select_folder)
        self.sort_btn.clicked.connect(self.sort_selected_folder)

        layout.addWidget(self.browse_btn)
        layout.addWidget(self.sort_btn)
        layout.addWidget(self.progress_bar)
        return page

    def build_empty_state(self):
        empty_state = QWidget()
        empty_layout = QVBoxLayout(empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(6)

        icon_label = QLabel("\U0001F4C1")
        icon_label.setStyleSheet("font-size: 40px;")
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel("No folder selected")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Choose a folder to start sorting your files")
        subtitle_label.setStyleSheet("font-size: 12px; color: #888888;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)

        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(title_label)
        empty_layout.addWidget(subtitle_label)

        return empty_state

    def clear_status_area(self):
        for i in reversed(range(self.status_layout.count())):
            widget = self.status_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def show_status(self, icon, title, subtitle="", color="white"):
        self.clear_status_area()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 40px;")
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        title_label.setAlignment(Qt.AlignCenter)

        self.status_layout.addWidget(icon_label)
        self.status_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 12px; color: #888888;")
            subtitle_label.setAlignment(Qt.AlignCenter)
            subtitle_label.setWordWrap(True)
            self.status_layout.addWidget(subtitle_label)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )

        if folder:
            self.selected_folder = folder
            self.show_status("\U0001F4C2", "Folder selected", folder)
            self.sort_btn.setEnabled(True)

    def bgsort(self, selectedFolder):
        self.thread = QThread()
        self.worker = FileSorterWorker(target_folder=Path(selectedFolder))

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run_sorting)
        self.worker.sorting_summary.connect(self.data)

        self.worker.progress.connect(self.progress_bar.setValue)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        

        self.thread.start()

       

    def sort_selected_folder(self):
        if self.selected_folder:
            # Disable buttons so user cannot click twice during thread activity
            self.sort_btn.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.show_status("⏳", "Sorting files in the background...", "Please wait...")
            
            # Fire background thread
            self.bgsort(self.selected_folder)
        else:
            self.show_status("⚠️", "Please select a folder first.", color="#ffb84d")

    def data(self, data_summary):

        self.sorted = data_summary
            

        self.history_manager.log_sort_history(data_summary)

            # Compile text message display info
        if data_summary:
            summary = ", ".join(f"{cat}: {count}" for cat, count in data_summary.items())
        else:
            summary = "No files needed sorting."

            # Update screen status display safely on the Main UI thread
        self.show_status("✅", "Sorting complete!", summary, color="#4da6ff")
            
            # Restore button controls back to the user
        self.browse_btn.setEnabled(True)

    # ---------------- History page ----------------

    def build_history_page(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Sort History")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Container that will hold the stack of history cards.
        # Cleared and repopulated each time the page is shown.
        self.history_list_container = QWidget()
        self.history_list_layout = QVBoxLayout(self.history_list_container)
        self.history_list_layout.setContentsMargins(0, 0, 0, 0)
        self.history_list_layout.setSpacing(14)

        layout.addWidget(self.history_list_container)
        layout.addStretch()

        # Wrap the whole page in a scroll area so overflow scrolls the page.
        scroll_area = QScrollArea()
        scroll_area.setWidget(content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #1c1c1c; }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        return scroll_area

    def build_history_card(self, session):
        """Build one rounded card for a single sort session."""
        card = QFrame()
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setStyleSheet("""
            QFrame {
                background-color: #222222;
                border: 1px solid #3a3a3a;
                border-radius: 14px;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(4)

        def add_row(label_text, value_text, bold=False):
            row = QLabel(f"{label_text} {value_text}")
            weight = "bold" if bold else "normal"
            row.setStyleSheet(f"color: white; font-size: 13px; font-weight: {weight};")
            card_layout.addWidget(row)

        add_row("Time:", session["timestamp"])

        for category, count in session["categories"].items():
            add_row(f"{category}:", str(count))

        add_row("Total:", str(session["total"]), bold=True)

        return card

    def clear_history_list(self):
        for i in reversed(range(self.history_list_layout.count())):
            widget = self.history_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def show_history_page(self):
        self.pages.setCurrentIndex(1)
        self.refresh_history_list()

    def refresh_history_list(self):
        self.clear_history_list()

        sessions = self.history_manager.fetch_grouped_history()

        if not sessions:
            empty_label = QLabel("No sort history yet")
            empty_label.setStyleSheet("color: #888888; font-size: 13px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.history_list_layout.addWidget(empty_label)
            return

        for session in sessions:
            card = self.build_history_card(session)
            self.history_list_layout.addWidget(card)





app = QApplication()
window = Main()

window.show()
app.exec()
