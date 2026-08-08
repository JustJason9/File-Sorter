import os
from pathlib import Path 
import shutil
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget,
                                QVBoxLayout, QHBoxLayout, QGridLayout, 
                                QPushButton, QLineEdit, QSlider, QComboBox, 
                                QProgressBar, QListWidget, QFileDialog)
from PySide6.QtGui import QIcon, QFont

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path

class Main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.selected_folder = ""

        self.setFont(QFont("Segoe UI", 10))
        self.setFixedSize(500, 350)
        self.setWindowIcon(QIcon(str(resource_path("icon.ico"))))
        self.setWindowTitle("File Sorter 1.0")


        container = QWidget()
        self.setCentralWidget(container)

        layout = QVBoxLayout(container)

        self.label = QLabel("No folder selected")

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.browse_btn = QPushButton("Browse")
        self.sort_btn = QPushButton("Sort Files")

        self.browse_btn.clicked.connect(self.select_folder)
        self.sort_btn.clicked.connect(self.sort_selected_folder)

        layout.addWidget(self.label)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.sort_btn)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )

        if folder:
            self.selected_folder = folder
            self.label.setText(folder)

    def sort_files(self, selectedFolder):
        fileFormat = {
	           "Web": [".html5", ".html", ".htm", ".xhtml",".html",
                     ".htm", ".css", ".js", ".jsx", ".ts", ".tsx", 
                     ".php", ".asp", ".aspx", ".jsp",".xml",
                     ".json", ".yaml", ".yml",".svg", ".rss"], 
	
               "Picture": ['.heif', 'svg', '.tif', '.nef', '.dng', '.cr2', '.arw', 
                           '.raw', '.jfif', '.heic', '.psd', '.tiff', '.rw2', '.orf', 
                           '.ico', '.jpg', '.avif', '.bpg', '.gif', 
                           '.bmp', '.png', '.svg', '.webp', '.jpeg'], 
	
               "Video": ['.flv', '.mpeg', '.ts', '.mng', '.f4v', '.3gp', '.mp4', '.m4v', 
                         '.webm', '.wmv', '.avi', '.mov', '.vob', '.qt', '.mpg', 
                         '.rmvb', '.divx', '.asf', '.ogv', '.rm', '.mkv'], 
	
              "Document": ['.dotx', '.fdf', '.dox', '.xlsx', '.rtf', '.numbers', '.pdf', 
                            '.xls', '.rvg', '.xps', '.ods', '.tex', '.rtfd', '.docx', '.odt', 
                            '.csv', '.pwi', '.key', '.wpd', '.mobi', '.docm','.epub', '.ppt', 
                            '.pptx', '.xsn', '.doc', '.oxps', '.pages', '.odp', 'pptx', '.txt'], 
	
               "Compressed": [".a", ".ar", ".cpio", ".iso", ".zip", ".rar", 
                              ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz", ".cab",
                             ".iso", ".lz", ".lzma", ".z", ".tar", 
                             ".gz", ".rz", ".7z", ".dmg", ".rar", ".xar", ".zip"], 
	
               "Audio": ['.aiff', '.mp3', '.aif', '.vox', '.flac', '.m4b', '.raw', 
                         '.m4a', '.ape','.ac3', '.msv', '.dvf', '.m4p', '.oga', '.wma',
                         '.mid', '.aa', '.opus', '.midi', '.ogg', '.ra', '.amr', '.aac', '.wav'],

                "Codes": [".py", ".pyw",".java", ".class",
                        ".c", ".h", ".cpp", ".hpp",
                        ".cs", ".go",".rs",".swift",
                        ".kt", ".kts", ".rb",".pl",
                        ".lua",".r", ".m", ".scala", ".dart",
                        ".sql",".sh", ".bat", ".ps1", ".vbs"] ,

                "Executables": [".exe",".msi",".msix",".msixbundle",".appx",
                                ".appxbundle",".bat",   ".cmd",".com", ".scr",".ps1",
                                ".vbs",   ".js",".jse",".wsf",
                                ".hta",]

              } 

        folder = Path(selectedFolder)

        for file in folder.iterdir():
            if not file.is_file():
                continue

            ext = Path(file.name).suffix.lower()

            category = "Other"


            for name, extensions in fileFormat.items():
                if ext in extensions:
                    category = name
                    break


            destination_folder = folder / category
            destination_folder.mkdir(exist_ok=True)

            shutil.move(
            str(file),
            str(destination_folder / file.name)
            )
                        

    def sort_selected_folder(self):
        if self.selected_folder:
            self.sort_files(self.selected_folder)
            self.label.setText("Sorting complete!")
        else:
            self.label.setText("Please select a folder first.")


app = QApplication()
window = Main()

window.show()
app.exec()
