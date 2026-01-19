import sys
import os
import asyncio
import random
import io
import threading
import time
import zipfile
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import qasync
from telethon import TelegramClient
from telethon.errors import *
from telethon.tl.functions.messages import SetTypingRequest, GetMessagesViewsRequest
from telethon.tl.types import SendMessageTypingAction, SendMessageRecordAudioAction
from telethon import events 
import config
import python_socks
import platform
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas



import json



ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True) 

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

SETTINGS_FILE = ASSETS_DIR / "settings.json"
PROXY_FILE = ASSETS_DIR / "proxies.json"
HISTORY_FILE = ASSETS_DIR / "history.json"
DB_PATH = ASSETS_DIR / "phantom_vault.db"
APP_ICON_PATH = ASSETS_DIR / "icon.png"

DB_CONN = sqlite3.connect(str(DB_PATH), check_same_thread=False)

def init_vault():

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=OFF")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            msg_id INTEGER, chat_id INTEGER, user_id INTEGER, 
            text TEXT, timestamp DATETIME, is_deleted INTEGER DEFAULT 0,
            session_owner TEXT, PRIMARY KEY (msg_id, chat_id)
        )
    ''')
    conn.commit()
    conn.close()

init_vault()
CURRENT_LANG = "EN" 


TRANSLATIONS = {
    "EN": {
        "tab_sessions": "SESSIONS",
        "tab_spam": "SPAM CONTROL",
        "tab_view": "VIEW BOOSTER",
        "tab_dash": "DASHBOARD",
        "tab_scanner": "SCANNER / OSINT",
        "tab_logs": "LOGS TERMINAL",
        "btn_add": "$ ADD_SESSION",
        "btn_del": "$ DEL_SESSION",
        "btn_test": "$ TEST_ALL",
        "btn_check": "$ CHECK_SPAMBLOCK",
        "btn_export": "$ EXPORT",
        "btn_refresh": "$ REFRESH",
        "btn_launch": "$ LAUNCH_ATTACK",
        "btn_stop": "$ ABORT",
        "btn_scanner_start": "$ DEEP_SCAN",
        "btn_db_search": "$ SEARCH_VAULT",
        "lbl_active": "ACTIVE SESSIONS:",
        "lbl_target": "TARGET SPECIFICATION:",
        "lbl_scanner_target": "TARGET CHAT:",
        "lbl_scanner_keys": "KEYWORDS:",
        "lbl_monitor_mode": "MONITORING MODE:",
        "cb_all_sessions": "USE ALL SESSIONS",
        "col_time": "TIME",
        "col_user": "USER ID",
        "col_text": "MESSAGE",
        "msg_restart": "Language changed to Russian!\nPlease restart the application."
    },
    "RU": {
        "tab_sessions": "СЕССИИ",
        "tab_spam": "УПРАВЛЕНИЕ СПАМОМ",
        "tab_view": "НАКРУТКА ПРОСМОТРОВ",
        "tab_dash": "СТАТИСТИКА",
        "tab_scanner": "СКАНЕР / OSINT",
        "tab_logs": "ЛОГИ / ТЕРМИНАЛ",
        "btn_add": "$ ДОБАВИТЬ",
        "btn_del": "$ УДАЛИТЬ",
        "btn_test": "$ ТЕСТ СЕССИЙ",
        "btn_check": "$ ПРОВЕРИТЬ СПАМБЛОК",
        "btn_export": "$ ЭКСПОРТ",
        "btn_refresh": "$ ОБНОВИТЬ",
        "btn_launch": "$ НАЧАТЬ АТАКУ",
        "btn_stop": "$ ОСТАНОВИТЬ",
        "btn_scanner_start": "$ НАЧАТЬ ПОИСК",
        "btn_db_search": "$ ПОИСК В БАЗЕ",
        "lbl_active": "АКТИВНЫЕ СЕССИИ:",
        "lbl_target": "ЦЕЛЬ АТАКИ:",
        "lbl_scanner_target": "ЧАТ ДЛЯ СКАНИРОВАНИЯ:",
        "lbl_scanner_keys": "КЛЮЧЕВЫЕ СЛОВА:",
        "lbl_monitor_mode": "РЕЖИМ СЛЕЖКИ:",
        "cb_all_sessions": "ВСЕ СЕССИИ СРАЗУ",
        "col_time": "ВРЕМЯ",
        "col_user": "ID ЮЗЕРА",
        "col_text": "ТЕКСТ",
        "msg_restart": "Язык изменен на Английский!\nПожалуйста, перезапустите программу."
    }
}

def load_settings():
    global CURRENT_LANG
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                CURRENT_LANG = data.get("language", "EN")
        except:
            pass

def save_settings(lang):
    global CURRENT_LANG
    CURRENT_LANG = lang
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({"language": lang}, f)

def TR(key):
    """Функция получения перевода"""
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["EN"]).get(key, key)


load_settings()

class CyberTheme:
    STYLES = """
    QMainWindow, QWidget {
        background-color: #0a0a0a;
        color: #00ff41;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px; 
    }
    
    QLabel {
        padding: 2px 4px;
        min-height: 18px; 
    }

    QLabel[header="true"] {
        font-size: 15px;
        font-weight: bold;
        color: #00ff9d;
    }

    QLineEdit, QTextEdit {
        background-color: #111111;
        border: 1px solid #333333;
        padding: 6px;
        color: #00ff41;
        min-height: 28px;
    }

    QPushButton {
        border: 1px solid #00ff41;
        padding: 6px 12px;
        background-color: #000;
        font-weight: bold;
    }
    """
    
class TerminalOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            background-color: #000000;
            color: #00ff41;
            font-family: monospace;
            font-size: 10px;
            line-height: 12px;
            border: 1px solid #333333;
            padding: 5px;
        """)
        self.setMinimumHeight(100)
        self.setMaximumHeight(200)
        
    def add_line(self, text, color="#00ff41"):
        if self.document().blockCount() > 200:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{text}</span>'
        self.append(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class ProxyEditor(QDialog):
    def __init__(self, session_name, parent=None):
        super().__init__(parent)
        self.session_name = session_name
        self.setWindowTitle(f"PROXY: {session_name}")
        self.setFixedSize(400, 350)
        self.setup_ui()
        self.load_current_proxy()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        self.setStyleSheet("background: #0a0a0a; color: #00ff41; font-family: 'Consolas';")

        layout.addWidget(QLabel("PROXY CONFIGURATION"))
        
    
        self.type_combo = QComboBox()
        self.type_combo.addItems(["SOCKS5", "HTTP"])
        self.type_combo.setStyleSheet("background: #111; border: 1px solid #333; color: #fff; padding: 5px;")
        layout.addWidget(QLabel("TYPE:"))
        layout.addWidget(self.type_combo)

       
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.1")
        self.ip_input.setStyleSheet("background: #111; border: 1px solid #333; color: #fff; padding: 5px;")
        layout.addWidget(QLabel("HOST (IP):"))
        layout.addWidget(self.ip_input)

      
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("1080")
        self.port_input.setStyleSheet("background: #111; border: 1px solid #333; color: #fff; padding: 5px;")
        layout.addWidget(QLabel("PORT:"))
        layout.addWidget(self.port_input)

       
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username (Optional)")
        self.user_input.setStyleSheet("background: #111; border: 1px solid #333; color: #fff; padding: 5px;")
        layout.addWidget(QLabel("LOGIN:"))
        layout.addWidget(self.user_input)

       
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password (Optional)")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet("background: #111; border: 1px solid #333; color: #fff; padding: 5px;")
        layout.addWidget(QLabel("PASSWORD:"))
        layout.addWidget(self.pass_input)

      
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("SAVE")
        self.btn_save.clicked.connect(self.save_proxy)
        self.btn_save.setStyleSheet("background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 8px;")
        
        self.btn_delete = QPushButton("REMOVE PROXY")
        self.btn_delete.clicked.connect(self.delete_proxy)
        self.btn_delete.setStyleSheet("background: #000; border: 1px solid #ff0033; color: #ff0033; padding: 8px;")
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def load_current_proxy(self):
        import json
        if not PROXY_FILE.exists(): return
        
        try:
            with open(str(PROXY_FILE), "r") as f:
                data = json.load(f)
                proxy_str = data.get(self.session_name)
                
            if proxy_str:
               
                parts = proxy_str.split(":")
                if "http" in parts[0].lower(): self.type_combo.setCurrentText("HTTP")
                else: self.type_combo.setCurrentText("SOCKS5")
                
                if len(parts) > 1: self.ip_input.setText(parts[1])
                if len(parts) > 2: self.port_input.setText(parts[2])
                if len(parts) > 3: self.user_input.setText(parts[3])
                if len(parts) > 4: self.pass_input.setText(parts[4])
        except:
            pass

    def save_proxy(self):
        ptype = self.type_combo.currentText().lower()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        user = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        
        if not ip or not port:
            QMessageBox.warning(self, "Error", "IP and Port are required!")
            return

      
        proxy_str = f"{ptype}:{ip}:{port}"
        if user:
            proxy_str += f":{user}"
            if password:
                proxy_str += f":{password}"
        
        self.update_json(proxy_str)
        QMessageBox.information(self, "Saved", "Proxy settings saved!")
        self.accept()

    def delete_proxy(self):
        self.update_json(None)
        QMessageBox.information(self, "Removed", "Proxy removed for this session.")
        self.accept()

    def update_json(self, value):
        import json
        data = {}
        if PROXY_FILE.exists():
            try:
                with open(str(PROXY_FILE), "r") as f:
                    data = json.load(f)
            except: pass
        
        if value:
            data[self.session_name] = value
        else:
            if self.session_name in data:
                del data[self.session_name]
        
        with open(str(PROXY_FILE), "w") as f:
            json.dump(data, f, indent=4)

class SessionManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        ascii_art = QLabel("""
█▀█ █░█ ▄▀█ █▄░█ ▀█▀ █▀█ █▀▄▀█
█▀▀ █▀█ █▀█ █░▀█ ░█░ █▄█ █░▀░█
█▀ █▄█ █▄░█ █▀▀ ▄█ ░█░ █░▀█ █▄▄
        """)
        ascii_art.setAlignment(Qt.AlignCenter)
        ascii_art.setStyleSheet("color: #00ff41; font-family: monospace; font-size: 8px; line-height: 8px;")
        layout.addWidget(ascii_art)
        
        btn_frame = QFrame()
        btn_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        btn_frame.setLineWidth(1)
        btn_frame.setStyleSheet("border: 1px solid #333333; padding: 10px;")
        
        btn_layout = QGridLayout()
        
        self.btn_add = QPushButton(TR("btn_add"))
        self.btn_add.clicked.connect(self.add_session)
        self.btn_add.setToolTip("Добавить новую сессию")
        btn_layout.addWidget(self.btn_add, 0, 0)
        
        self.btn_delete = QPushButton(TR("btn_del"))
        self.btn_delete.clicked.connect(self.delete_session)
        self.btn_delete.setToolTip("Удалить выбранные сессии")
        btn_layout.addWidget(self.btn_delete, 0, 1)
        
        self.btn_test = QPushButton(TR("btn_test"))
        self.btn_test.clicked.connect(self.test_sessions)
        self.btn_test.setToolTip("Протестировать все сессии")
        btn_layout.addWidget(self.btn_test, 0, 2)
        
        self.btn_spamblock = QPushButton(TR("btn_check"))
        self.btn_spamblock.clicked.connect(self.check_spamblock)
        self.btn_spamblock.setStyleSheet("color: #ff9900; border: 1px solid #ff9900;")
        self.btn_spamblock.setToolTip("Проверить и разблокировать аккаунты")
        btn_layout.addWidget(self.btn_spamblock, 1, 0)
        
        self.btn_export = QPushButton(TR("btn_export"))
        self.btn_export.clicked.connect(self.export_sessions)
        self.btn_export.setToolTip("Экспортировать сессии")
        btn_layout.addWidget(self.btn_export, 1, 1)
        
        self.btn_refresh = QPushButton(TR("btn_refresh"))
        self.btn_refresh.clicked.connect(self.load_sessions)
        self.btn_refresh.setToolTip("Обновить список")
        btn_layout.addWidget(self.btn_refresh, 1, 2)
        
        btn_frame.setLayout(btn_layout)
        layout.addWidget(btn_frame)
        
        list_frame = QFrame()
        list_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        list_frame.setLineWidth(1)
        list_frame.setStyleSheet("border: 1px solid #333333;")
        
        list_layout = QVBoxLayout()
        
        header = QLabel(TR("lbl_active"))
        header.setStyleSheet("color: #00ff9d; font-weight: bold; padding: 5px; background-color: #111111;")
        list_layout.addWidget(header)
        
        self.session_list = QListWidget()
        self.session_list.setSelectionMode(QListWidget.ExtendedSelection)
        
      
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.show_context_menu)
        
        
        list_layout.addWidget(self.session_list)
        
        list_frame.setLayout(list_layout)
        layout.addWidget(list_frame)
        
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        status_frame.setLineWidth(1)
        status_frame.setStyleSheet("border: 1px solid #333333; padding: 5px; background-color: #111111;")
        
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("SESSIONS: 0 | ONLINE: 0 | OFFLINE: 0")
        self.status_label.setStyleSheet("color: #00ff41; font-family: 'Consolas';")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: #ff0033; font-size: 16px;")
        status_layout.addWidget(self.connection_indicator)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        self.setLayout(layout)
        self.load_sessions()
        
    def load_sessions(self):
        self.session_list.clear()
        
        session_files = []
        
        for file in SESSIONS_DIR.glob("*.session"):
            if 'journal' in file.name or '-wal' in file.name or '-shm' in file.name:
                continue
                
            if file.is_file():
                base_name = file.stem
                session_files.append({
                    'path': str(file),
                    'base_name': base_name,
                    'size': file.stat().st_size
                })
        
        online_count = 0
        
        for session_data in session_files:
            session_file = Path(session_data['path'])
            base_name = session_data['base_name']
            
            import re
            numbers = re.findall(r'\d+', base_name)
            phone = f"+{numbers[-1]}" if numbers and len(numbers[-1]) >= 7 else base_name
            
            status_color = "#00ff41"
            online_count += 1
            
          
            item = QListWidgetItem(phone) 
            
    
            item.setForeground(QColor(status_color))
            
           
            item.setData(Qt.UserRole, str(session_file))
            item.setToolTip(f"File: {base_name}\nSize: {session_data['size']} bytes")
            
            self.session_list.addItem(item)
        
        self.status_label.setText(f"SESSIONS: {len(session_files)} | ONLINE: {online_count}")
        
        if online_count > 0:
            self.connection_indicator.setStyleSheet("color: #00ff41; font-size: 16px;")
        else:
            self.connection_indicator.setStyleSheet("color: #ff0033; font-size: 16px;")
            
    def add_session(self):
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log("Opening add session dialog...", "INFO")
            
        dialog = CyberAddSessionDialog(self.parent)
        if dialog.exec_() == QDialog.Accepted:
            self.load_sessions()
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log("Session added successfully", "SUCCESS")
            
    def delete_session(self):
        items = self.session_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "WARNING", "NO SESSIONS SELECTED!")
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log("Delete session failed: no sessions selected", "ERROR")
            return
            
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log(f"Attempting to delete {len(items)} session(s)...", "WARNING")
            
        msg_box = QMessageBox()
        msg_box.setWindowTitle("CONFIRM DELETE")
        msg_box.setText(f"DELETE {len(items)} SESSION(S)?")
        msg_box.setInformativeText("This action cannot be undone!")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #111111;
                color: #00ff41;
            }
            QPushButton {
                border: 1px solid #333333;
                padding: 5px;
                min-width: 70px;
            }
        """)
        
        if msg_box.exec_() == QMessageBox.Yes:
            deleted_count = 0
            for item in items:
                session_file = item.data(Qt.UserRole)
                try:
                    os.remove(session_file)
                    for ext in ['.session', '.session-journal']:
                        if os.path.exists(session_file + ext):
                            os.remove(session_file + ext)
                    deleted_count += 1
                except Exception as e:
                    if hasattr(self.parent, 'logs_panel'):
                        self.parent.logs_panel.add_log(f"Failed to delete {session_file}: {str(e)[:30]}", "ERROR")
            self.load_sessions()
            
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log(f"Successfully deleted {deleted_count} session(s)", "SUCCESS")
            
    def test_sessions(self):
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log("Starting session testing...", "INFO")
        asyncio.create_task(self.parent.test_all_sessions())
        
    def import_sessions(self):
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log("Import sessions requested - feature not implemented", "WARNING")
        QMessageBox.information(self, "INFO", "IMPORT FUNCTION - COMING SOON")
        
    def export_sessions(self):
        items = self.session_list.selectedItems()
        
        if not items:
            reply = QMessageBox.question(
                self, "CONFIRM EXPORT", 
                "No sessions selected. Export ALL active sessions?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                items = [self.session_list.item(i) for i in range(self.session_list.count())]
            else:
                return

        if not items:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"phantom_sessions_{timestamp}.zip"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "SAVE EXPORT ARCHIVE", 
            default_name, 
            "ZIP Archive (*.zip)"
        )

        if not file_path:
            return

        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log(f"Exporting {len(items)} sessions...", "INFO")

        try:
            exported_count = 0
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in items:
                    session_path = Path(item.data(Qt.UserRole))
                    
                    if session_path.exists():
                        zipf.write(session_path, arcname=session_path.name)
                        exported_count += 1
            
            msg = f"Successfully exported {exported_count} sessions to:\n{Path(file_path).name}"
            QMessageBox.information(self, "EXPORT COMPLETE", msg)
            
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log(f"Export success: {file_path}", "SUCCESS")

        except Exception as e:
            err_msg = f"Export failed: {str(e)}"
            QMessageBox.critical(self, "ERROR", err_msg)
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log(err_msg, "ERROR")
        
    def check_spamblock(self):
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log("Starting SpamBlock check & Auto-Fix...", "WARNING")
        asyncio.create_task(self.parent.run_spamblock_checker())

 
    def show_context_menu(self, pos):
        item = self.session_list.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #000; color: #00ff41; border: 1px solid #333; }
            QMenu::item:selected { background-color: #111; }
        """)
        
      
        proxy_action = QAction("⚙️ PROXY SETTINGS", self)
        proxy_action.triggered.connect(lambda: self.open_proxy_settings(item))
        menu.addAction(proxy_action)
        
       
        del_action = QAction("❌ DELETE SESSION", self)
        del_action.triggered.connect(self.delete_session)
        menu.addAction(del_action)
        
        menu.exec_(self.session_list.mapToGlobal(pos))

    def open_proxy_settings(self, item):
        session_file = Path(item.data(Qt.UserRole))
        session_name = session_file.stem 
        
        dialog = ProxyEditor(session_name, self)
        dialog.exec_()

class CyberAddSessionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("$ ADD_SESSION")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.auth_step = "code"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        ascii_header = QLabel("""
┌─────────────────────────────────────┐
│        SESSION INITIALIZATION       │
└─────────────────────────────────────┘
        """)
        ascii_header.setAlignment(Qt.AlignCenter)
        ascii_header.setStyleSheet("color: #00ff41; font-family: 'Consolas'; font-size: 10px;")
        layout.addWidget(ascii_header)
        
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        form_frame.setLineWidth(1)
        form_frame.setStyleSheet("border: 1px solid #333333; padding: 15px;")
        
        form_layout = QVBoxLayout()
        
        phone_label = QLabel("PHONE NUMBER:")
        phone_label.setStyleSheet("color: #00ff9d; font-weight: bold;")
        form_layout.addWidget(phone_label)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+79991234567")
        self.phone_input.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                border: 1px solid #333333;
                padding: 8px;
                color: #00ff41;
            }
        """)
        form_layout.addWidget(self.phone_input)
        
        form_frame.setLayout(form_layout)
        layout.addWidget(form_frame)
        
        btn_frame = QFrame()
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("$ START_AUTH")
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self.start_auth)
        btn_layout.addWidget(self.btn_start)
        
        self.btn_cancel = QPushButton("$ CANCEL")
        self.btn_cancel.setObjectName("danger")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        btn_frame.setLayout(btn_layout)
        layout.addWidget(btn_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.terminal_output = TerminalOutput()
        self.terminal_output.setMaximumHeight(100)
        layout.addWidget(self.terminal_output)
        
        code_frame = QFrame()
        code_frame.setVisible(False)
        code_layout = QVBoxLayout()
        
        self.code_label = QLabel("AUTH CODE:")
        self.code_label.setStyleSheet("color: #00ff9d; font-weight: bold;")
        code_layout.addWidget(self.code_label)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter code from Telegram...")
        code_layout.addWidget(self.code_input)
        
        self.btn_submit = QPushButton("$ SUBMIT_CODE")
        self.btn_submit.clicked.connect(self.submit_code)
        code_layout.addWidget(self.btn_submit)
        
        code_frame.setLayout(code_layout)
        layout.addWidget(code_frame)
        
        self.code_frame = code_frame
        
        layout.addStretch()
        
        self.setLayout(layout)
        
    def start_auth(self):
        phone = self.phone_input.text().strip()
        if not phone:
            self.terminal_output.add_line("ERROR: Phone number required!", "#ff0033")
            return
            
        if not phone.startswith("+"):
            phone = "+" + phone
            
        session_file = SESSIONS_DIR / f"session_{phone[1:]}"
        if session_file.exists():
            self.terminal_output.add_line("ERROR: Session already exists!", "#ff0033")
            return
            
        self.phone = phone
        self.btn_start.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.terminal_output.add_line(f"Initializing session for {phone}...", "#0099ff")
        
        asyncio.create_task(self.authorize_session())
        
    async def authorize_session(self):
        try:
            session_file = SESSIONS_DIR / f"session_{self.phone[1:]}"
            
         
            self.client = TelegramClient(
                session=str(session_file),
                api_id=config.API_ID,
                api_hash=config.API_HASH,
               
                device_model="iPhone 15 Pro Max",
                system_version="17.5",
                app_version="10.8.1",
                lang_code="en",
                system_lang_code="en-US"
            )
          
            
            self.terminal_output.add_line("Connecting to Telegram API...", "#0099ff")
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log("Connecting to Telegram API...", "INFO")
                
            await self.client.connect()
            
            self.terminal_output.add_line("Sending authentication code...", "#0099ff")
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log("Sending authentication code...", "INFO")
                
            self.code = await self.client.send_code_request(self.phone)
            
            self.progress_bar.setVisible(False)
            self.terminal_output.add_line("SUCCESS: Code sent to Telegram!", "#00ff41")
            self.terminal_output.add_line("Enter code below:", "#00ff9d")
            
            self.code_frame.setVisible(True)
            self.code_input.setFocus()
            
        except Exception as e:
            self.terminal_output.add_line(f"ERROR: {str(e)[:50]}", "#ff0033")
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log(f"Authorization error: {str(e)[:50]}", "ERROR")
            self.btn_start.setEnabled(True)
            self.progress_bar.setVisible(False)
            
    def submit_code(self):
        text = self.code_input.text().strip()
        if not text:
            self.terminal_output.add_line("ERROR: Input required!", "#ff0033")
            return
            
        if self.auth_step == "code":
            asyncio.create_task(self.complete_auth(text))
        elif self.auth_step == "password":
            asyncio.create_task(self.submit_password(text))
        
    async def complete_auth(self, code):
        try:
            self.progress_bar.setVisible(True)
            self.terminal_output.add_line("Authenticating...", "#0099ff")
            
            await self.client.sign_in(
                self.phone, 
                code, 
                phone_code_hash=self.code.phone_code_hash
            )
            
            await self.finalize_login()
            
        except SessionPasswordNeededError:
          
            self.terminal_output.add_line("⚠️ 2FA PASSWORD REQUIRED", "#ff9900")
            self.terminal_output.add_line("Enter your 2FA password below:", "#00ff9d")
            
            self.auth_step = "password"
            self.progress_bar.setVisible(False)
            
            self.code_label.setText("2FA PASSWORD:")
            self.code_input.clear()
            self.code_input.setEchoMode(QLineEdit.Password)
            self.code_input.setPlaceholderText("Enter 2FA password...")
            self.btn_submit.setText("$ SUBMIT_PASSWORD")
            self.code_input.setFocus()
            
            if hasattr(self.parent, 'logs_panel'):
                self.parent.logs_panel.add_log("2FA Password required...", "WARNING")
                
        except Exception as e:
            self.handle_error(e)

    async def submit_password(self, password):
        try:
            self.progress_bar.setVisible(True)
            self.terminal_output.add_line("Verifying password...", "#0099ff")
            
            await self.client.sign_in(password=password)
            await self.finalize_login()
            
        except Exception as e:
            self.handle_error(e)

    async def finalize_login(self):
        me = await self.client.get_me()
        await self.client.disconnect()
        
        self.terminal_output.add_line(f"SUCCESS: Authenticated as {me.first_name or 'User'}", "#00ff41")
        self.terminal_output.add_line(f"Phone: +{me.phone}", "#00ff9d")
        
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log(f"SUCCESS: Authenticated as {me.first_name or 'User'}", "SUCCESS")
        
        QTimer.singleShot(1000, self.accept)

    def handle_error(self, e):
        self.terminal_output.add_line(f"AUTH ERROR: {str(e)[:50]}", "#ff0033")
        self.progress_bar.setVisible(False)
        if hasattr(self.parent, 'logs_panel'):
            self.parent.logs_panel.add_log(f"AUTH ERROR: {str(e)[:50]}", "ERROR")
        
        if not isinstance(e, SessionPasswordNeededError):
            try:
                asyncio.create_task(self.client.disconnect())
            except:
                pass

class SpamControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.spam_task = None
        
        self.start_time = None
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats_display)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        target_frame = QFrame()
        target_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        target_frame.setStyleSheet("border: 1px solid #333333; padding: 10px;")
        
        target_layout = QVBoxLayout()
        target_label = QLabel("TARGET SPECIFICATION:")
        target_label.setStyleSheet("color: #ff0033; font-weight: bold;")
        target_layout.addWidget(target_label)
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("@username / +79991234567")
        target_layout.addWidget(self.target_input)
        
        target_frame.setLayout(target_layout)
        layout.addWidget(target_frame)
        
        mode_frame = QFrame()
        mode_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        mode_frame.setStyleSheet("border: 1px solid #333333; padding: 10px;")
        
        mode_layout = QGridLayout()
        
        mode_layout.addWidget(QLabel("ATTACK MODE:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["RANDOM CHAOS", "SPECIFIC TEXT", "GHOST ONLY"])
        self.mode_combo.setStyleSheet("""
            QComboBox { background-color: #000; color: #00ff41; border: 1px solid #333; padding: 5px; }
            QComboBox::drop-down { border: 0px; }
        """)
        self.mode_combo.currentTextChanged.connect(self.toggle_text_input)
        mode_layout.addWidget(self.mode_combo, 0, 1)
        
        self.text_label = QLabel("CUSTOM TEXT:")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter word or sentence to spam...")
        self.text_input.setStyleSheet("color: #00ff9d; border: 1px solid #00ff41;")
        
        mode_layout.addWidget(self.text_label, 1, 0)
        mode_layout.addWidget(self.text_input, 1, 1)
        
        self.text_label.hide()
        self.text_input.hide()
        
        mode_frame.setLayout(mode_layout)
        layout.addWidget(mode_frame)
        
        config_frame = QFrame()
        config_frame.setStyleSheet("border: 1px solid #333333; padding: 10px;")
        config_layout = QGridLayout()
        
        config_layout.addWidget(QLabel("DELAY (sec):"), 0, 0)
        self.delay_input = QSpinBox()
        self.delay_input.setRange(1, 60)
        self.delay_input.setValue(2)
        self.delay_input.setStyleSheet("background-color: #000; color: #00ff41; border: 1px solid #333;")
        config_layout.addWidget(self.delay_input, 0, 1)
        
        config_layout.addWidget(QLabel("MAX ERRORS:"), 1, 0)
        self.max_errors_input = QSpinBox()
        self.max_errors_input.setRange(1, 50)
        self.max_errors_input.setValue(10)
        config_layout.addWidget(self.max_errors_input, 1, 1)
        
        self.random_delay_cb = QCheckBox("RANDOM DELAY")
        self.random_delay_cb.setChecked(True)
        config_layout.addWidget(self.random_delay_cb, 2, 0, 1, 2)
        
        config_frame.setLayout(config_layout)
        layout.addWidget(config_frame)
        
        control_layout = QHBoxLayout()
        self.btn_start = QPushButton("$ LAUNCH_ATTACK")
        self.btn_start.setObjectName("danger")
        self.btn_start.setStyleSheet("font-size: 14px; font-weight: bold; padding: 12px; color: #ff0033; border: 1px solid #ff0033;")
        self.btn_start.clicked.connect(self.toggle_spam)
        control_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("$ ABORT")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_spam)
        control_layout.addWidget(self.btn_stop)
        
        layout.addLayout(control_layout)
        
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        stats_frame.setStyleSheet("border: 1px solid #333333; padding: 5px; background-color: #111111;")
        stats_layout = QHBoxLayout()
        
        self.sent_label = QLabel("SENT: 0")
        self.sent_label.setStyleSheet("color: #00ff41; font-weight: bold;")
        stats_layout.addWidget(self.sent_label)
        
        self.errors_label = QLabel("ERRORS: 0")
        self.errors_label.setStyleSheet("color: #ff0033; font-weight: bold;")
        stats_layout.addWidget(self.errors_label)
        
        self.time_label = QLabel("TIME: 00:00")
        self.time_label.setStyleSheet("color: #0099ff;")
        stats_layout.addWidget(self.time_label)
        
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
       
        self.attack_terminal = TerminalOutput()
        layout.addWidget(self.attack_terminal)
        
        self.setLayout(layout)
        
    def toggle_text_input(self, text):
        if text == "SPECIFIC TEXT":
            self.text_label.show()
            self.text_input.show()
        else:
            self.text_label.hide()
            self.text_input.hide()

    def log(self, message, color="#00ff41"):
        self.attack_terminal.add_line(message, color)
        if hasattr(self.parent, 'logs_panel'):
            type_log = "INFO"
            if "Error" in message or "CRASH" in message: type_log = "ERROR"
            elif "Success" in message: type_log = "SUCCESS"
            self.parent.logs_panel.add_log(message, type_log)
        
    def update_stats_display(self):
        if hasattr(self.parent, 'spam_stats'):
            sent = self.parent.spam_stats.get('sent', 0)
            errors = self.parent.spam_stats.get('errors', 0)
            
            self.sent_label.setText(f"SENT: {sent}")
            self.errors_label.setText(f"ERRORS: {errors}")
            
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                seconds = int(elapsed.total_seconds())
                self.time_label.setText(f"TIME: {seconds // 60:02d}:{seconds % 60:02d}")
        
    def toggle_spam(self):
        target = self.target_input.text().strip()
        if not target:
            self.log("ERROR: Target required!", "#ff0033")
            return
            
        if not self.spam_task or self.spam_task.done():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("CONFIRM LAUNCH")
            msg_box.setText(f"⚠️ ATTACK TARGET: {target}")
            msg_box.setInformativeText(f"Mode: {self.mode_combo.currentText()}\nProceed?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            msg_box.setStyleSheet("QMessageBox { background-color: #111; color: #0f0; } QPushButton { color: red; background: black; border: 1px solid #333; }")
            
            if msg_box.exec_() != QMessageBox.Yes:
                self.log("ABORTED BY USER", "#ff9900")
                return

            self.log("INITIALIZING...", "#0099ff")
            
      
            if hasattr(self.parent, 'history_panel'):
                mode = self.mode_combo.currentText()
                self.parent.history_panel.add_record("SPAM ATTACK", target, f"Mode: {mode}")
            
            
            self.btn_start.setText("$ STOP_ATTACK")
            self.btn_stop.setEnabled(True)
            
        
            self.start_time = datetime.now()
            self.stats_timer.start(1000)
            
            self.spam_task = asyncio.create_task(
                self.parent.start_spam(
                    target=target,
                    delay=self.delay_input.value(),
                    max_errors=self.max_errors_input.value(),
                    random_delay=self.random_delay_cb.isChecked(),
                    mode=self.mode_combo.currentText(),        
                    custom_text=self.text_input.text().strip() 
                )
            )
        else:
          
            self.log("PAUSED", "#ff9900")
        
    def stop_spam(self):
        if self.spam_task:
            self.spam_task.cancel()
        
        self.stats_timer.stop()
        self.parent.is_spamming = False
        self.btn_start.setText("$ LAUNCH_ATTACK")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
class StatsDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
   
        ascii_art = QLabel("") 
        layout.addWidget(ascii_art)
        
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        stats_frame.setStyleSheet("border: 1px solid #333333; padding: 10px;")
        
        stats_layout = QGridLayout()
        
       
        stats_layout.addWidget(QLabel("TOTAL SESSIONS:"), 0, 0)
        self.total_sessions_label = QLabel("0")
        self.total_sessions_label.setStyleSheet("color: #00ff41; font-weight: bold;")
        stats_layout.addWidget(self.total_sessions_label, 0, 1)
        
        stats_layout.addWidget(QLabel("ACTIVE SESSIONS:"), 1, 0)
        self.active_sessions_label = QLabel("0")
        self.active_sessions_label.setStyleSheet("color: #00ff9d; font-weight: bold;")
        stats_layout.addWidget(self.active_sessions_label, 1, 1)
        
        stats_layout.addWidget(QLabel("TOTAL ATTACKS:"), 2, 0)
        self.total_attacks_label = QLabel("0")
        self.total_attacks_label.setStyleSheet("color: #ff9900; font-weight: bold;")
        stats_layout.addWidget(self.total_attacks_label, 2, 1)
        
        stats_layout.addWidget(QLabel("SUCCESSFUL:"), 3, 0)
        self.successful_label = QLabel("0")
        self.successful_label.setStyleSheet("color: #00ff41; font-weight: bold;")
        stats_layout.addWidget(self.successful_label, 3, 1)
        
        stats_layout.addWidget(QLabel("FAILED:"), 4, 0)
        self.failed_label = QLabel("0")
        self.failed_label.setStyleSheet("color: #ff0033; font-weight: bold;")
        stats_layout.addWidget(self.failed_label, 4, 1)

     
        stats_layout.addWidget(QLabel("CPU LOAD:"), 5, 0)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setStyleSheet("color: #0099ff;")
        stats_layout.addWidget(self.cpu_label, 5, 1)

        stats_layout.addWidget(QLabel("RAM USAGE:"), 6, 0)
        self.ram_label = QLabel("0%")
        self.ram_label.setStyleSheet("color: #0099ff;")
        stats_layout.addWidget(self.ram_label, 6, 1)
        
        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)
        
      
        active = 0
        total = 0
        if SESSIONS_DIR.exists():
           
            for session_file in SESSIONS_DIR.glob("*.session"):
                total += 1
                try:
                    if session_file.stat().st_size > 100:
                        active += 1
                except:
                    pass
        
        self.total_sessions_label.setText(str(total))
        self.active_sessions_label.setText(str(active))
        
      
        if hasattr(self.parent, 'spam_stats'):
            stats = self.parent.spam_stats
            self.total_attacks_label.setText(str(stats.get('total_sent', 0)))
            self.successful_label.setText(str(stats.get('successful', 0)))
            self.failed_label.setText(str(stats.get('errors', 0)))
            
     
        import psutil
        try:
            cpu = psutil.cpu_percent()
           
            cpu_bar = '█' * int(cpu/10) + '░' * (10 - int(cpu/10))
            self.cpu_label.setText(f"{cpu_bar} {cpu:.0f}%")
            
            ram = psutil.virtual_memory().percent
            ram_bar = '█' * int(ram/10) + '░' * (10 - int(ram/10))
            self.ram_label.setText(f"{ram_bar} {ram:.0f}%")
        except:
            self.cpu_label.setText("N/A")
            self.ram_label.setText("N/A")

        self.setLayout(layout)

class LogsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.all_logs = []
        self.filtered_logs = []
        self.is_paused = False
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
       
        ascii_header = QLabel("""
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM LOG TERMINAL                             │
│                     ALL EVENTS • DEBUG • ERRORS • SUCCESS                    │
└──────────────────────────────────────────────────────────────────────────────┘
        """)
        ascii_header.setAlignment(Qt.AlignCenter)
        ascii_header.setStyleSheet("color: #00ff41; font-family: 'Consolas'; font-size: 10px; line-height: 10px;")
        layout.addWidget(ascii_header)
        
      
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        control_frame.setLineWidth(1)
        control_frame.setStyleSheet("border: 1px solid #333333; padding: 8px; background-color: #111111;")
        
        control_layout = QHBoxLayout()
        
       
        filters_label = QLabel("FILTERS:")
        filters_label.setStyleSheet("color: #00ff9d; font-weight: bold;")
        control_layout.addWidget(filters_label)
        
        self.show_info_cb = QCheckBox("INFO")
        self.show_info_cb.setChecked(True)
        self.show_info_cb.stateChanged.connect(self.filter_logs)
        control_layout.addWidget(self.show_info_cb)
        
        self.show_success_cb = QCheckBox("SUCCESS")
        self.show_success_cb.setChecked(True)
        self.show_success_cb.stateChanged.connect(self.filter_logs)
        control_layout.addWidget(self.show_success_cb)
        
        self.show_warning_cb = QCheckBox("WARNINGS")
        self.show_warning_cb.setChecked(True)
        self.show_warning_cb.stateChanged.connect(self.filter_logs)
        control_layout.addWidget(self.show_warning_cb)
        
        self.show_error_cb = QCheckBox("ERRORS")
        self.show_error_cb.setChecked(True)
        self.show_error_cb.stateChanged.connect(self.filter_logs)
        control_layout.addWidget(self.show_error_cb)
        
        control_layout.addStretch()
        
     
        self.btn_clear = QPushButton("$ CLEAR_LOGS")
        self.btn_clear.clicked.connect(self.clear_logs)
        control_layout.addWidget(self.btn_clear)
        
        self.btn_export = QPushButton("$ EXPORT_LOGS")
        self.btn_export.clicked.connect(self.export_logs)
        control_layout.addWidget(self.btn_export)
        
        self.btn_pause = QPushButton("$ PAUSE")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.btn_pause)
        
        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)
        
        
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #00ff41;
                font-family: 'JetBrains Mono', monospace;
                font-size: 10px;
                line-height: 12px;
                border: 1px solid #333333;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_terminal, 100)
        
     
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        status_frame.setLineWidth(1)
        status_frame.setStyleSheet("border: 1px solid #333333; padding: 5px; background-color: #111111;")
        
        status_layout = QHBoxLayout()
        
        self.log_count_label = QLabel("LOGS: 0")
        self.log_count_label.setStyleSheet("color: #00ff41;")
        status_layout.addWidget(self.log_count_label)
        
        status_layout.addStretch()
        
        self.autoscroll_label = QLabel("AUTOSCROLL: ON")
        self.autoscroll_label.setStyleSheet("color: #00ff9d;")
        status_layout.addWidget(self.autoscroll_label)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        self.setLayout(layout)
        
    def add_log(self, message, log_type="INFO"):
        if self.is_paused:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type,
            'color': self.get_color_for_type(log_type)
        }
        
        self.all_logs.append(log_entry)
        
        if self.should_show_log(log_type):
            self.filtered_logs.append(log_entry)
            self.append_to_terminal(log_entry)
            
        self.update_status()
        
    def get_color_for_type(self, log_type):
        colors = {
            'INFO': '#0099ff',
            'SUCCESS': '#00ff41',
            'WARNING': '#ff9900',
            'ERROR': '#ff0033',
            'SYSTEM': '#ff00ff'
        }
        return colors.get(log_type, '#00ff41')
        
    def should_show_log(self, log_type):
        if log_type == 'INFO' and not self.show_info_cb.isChecked():
            return False
        if log_type == 'SUCCESS' and not self.show_success_cb.isChecked():
            return False
        if log_type == 'WARNING' and not self.show_warning_cb.isChecked():
            return False
        if log_type == 'ERROR' and not self.show_error_cb.isChecked():
            return False
        return True
        
    def append_to_terminal(self, log_entry):
        html = f'<span style="color: #666666;">[{log_entry["timestamp"]}]</span> '
        html += f'<span style="color: {log_entry["color"]};">{log_entry["message"]}</span>'
        
        cursor = self.log_terminal.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(html + '<br>')
        
        
        if self.autoscroll_label.text() == "AUTOSCROLL: ON":
            scrollbar = self.log_terminal.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def filter_logs(self):
        self.filtered_logs = []
        self.log_terminal.clear()
        
        for log in self.all_logs:
            if self.should_show_log(log['type']):
                self.filtered_logs.append(log)
                self.append_to_terminal(log)
                
    def clear_logs(self):
        self.all_logs = []
        self.filtered_logs = []
        self.log_terminal.clear()
        self.update_status()
        
    def export_logs(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", 
            f"phantom_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                for log in self.all_logs:
                    f.write(f"[{log['timestamp']}] {log['message']}\n")
                    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.setText("$ RESUME")
        else:
            self.btn_pause.setText("$ PAUSE")
            
    def update_status(self):
        self.log_count_label.setText(f"LOGS: {len(self.all_logs)}")

class ViewBooster(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.is_running = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

       
        header = QLabel("👁️ VIEW BOOSTER (НАКРУТКА ПРОСМОТРОВ)")
        header.setStyleSheet("color: #00ff9d; font-weight: bold; font-size: 14px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

       
        input_frame = QFrame()
        input_frame.setStyleSheet("border: 1px solid #333; padding: 10px; background: #0a0a0a;")
        input_layout = QVBoxLayout()
        
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("https://t.me/channelname/1234")
        self.link_input.setStyleSheet("color: #00ff41; padding: 8px; border: 1px solid #00ff41;")
        input_layout.addWidget(QLabel("POST LINK:"))
        input_layout.addWidget(self.link_input)
        
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)

        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #000; color: #00ff9d; font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_area)

      
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("$ START_BOOST")
        self.btn_start.clicked.connect(self.start_boost)
        self.btn_start.setStyleSheet("color: #00ff41; border: 1px solid #00ff41; padding: 10px; font-weight: bold;")
        
        self.btn_stop = QPushButton("$ STOP")
        self.btn_stop.clicked.connect(self.stop_boost)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("color: #ff0033; border: 1px solid #ff0033; padding: 10px;")

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def log(self, text, color="#00ff41"):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f'<span style="color: #666;">[{time_str}]</span> <span style="color: {color};">{text}</span>')
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_boost(self):
        link = self.link_input.text().strip()
        if not link or "t.me/" not in link:
            self.log("ERROR: Invalid Link", "#ff0033")
            return

        try:
          
            parts = link.split('/')
            post_id = int(parts[-1])
            channel = parts[-2]
        except:
            self.log("ERROR: Cannot parse link format", "#ff0033")
            return

        self.is_running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log(f"🚀 STARTING BOOST: {channel}/{post_id}", "#0099ff")
        
        
        if hasattr(self.parent, 'history_panel'):
            self.parent.history_panel.add_record("VIEW BOOST", link, f"ID: {post_id}")
       
        asyncio.create_task(self.run_boost_task(channel, post_id))

    def stop_boost(self):
        self.is_running = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log("🛑 STOPPED BY USER", "#ff9900")

    async def run_boost_task(self, channel, post_id):
        session_files = list(SESSIONS_DIR.glob("*.session"))
        success = 0
        
        for session in session_files:
            if not self.is_running: break
            
            proxy_config = self.parent.get_proxy_for_session(session.stem) if hasattr(self.parent, 'get_proxy_for_session') else None
            
            client = TelegramClient(str(session), config.API_ID, config.API_HASH, proxy=proxy_config)
            
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    await client.disconnect()
                    continue

          
                try:
                 
                    entity = await client.get_entity(channel)
                    
                 
                    await client(GetMessagesViewsRequest(
                        peer=entity,
                        id=[post_id],
                        increment=True
                    ))
                    
                    self.log(f"✅ Viewed by {session.stem}", "#00ff41")
                    success += 1
                except Exception as e:
                    self.log(f"❌ Error {session.stem}: {str(e)[:20]}", "#ff0033")
                
                await client.disconnect()
                
            except Exception as e:
                self.log(f"⚠️ Connection error: {session.stem}", "#ff9900")
            
        
            await asyncio.sleep(random.uniform(1, 3))

        self.log(f"🏁 DONE! Total views added: {success}", "#ffffff")
        self.stop_boost()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SYSTEM SETTINGS")
        self.setFixedSize(300, 200)
        self.setStyleSheet("background: #0a0a0a; color: #00ff41; font-family: 'Consolas'; border: 1px solid #333;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(QLabel("INTERFACE LANGUAGE / ЯЗЫК:"))
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ENGLISH", "RUSSIAN"])
        self.lang_combo.setStyleSheet("background: #111; padding: 5px; border: 1px solid #00ff41;")
        
        
        if CURRENT_LANG == "RU":
            self.lang_combo.setCurrentIndex(1)
        else:
            self.lang_combo.setCurrentIndex(0)
            
        layout.addWidget(self.lang_combo)
        
        btn_save = QPushButton("$ SAVE_SETTINGS")
        btn_save.clicked.connect(self.save_and_exit)
        btn_save.setStyleSheet("background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 10px; margin-top: 15px;")
        layout.addWidget(btn_save)
        
        self.setLayout(layout)

    def save_and_exit(self):
        choice = self.lang_combo.currentIndex()
        new_lang = "RU" if choice == 1 else "EN"
        
        if new_lang != CURRENT_LANG:
            save_settings(new_lang)
            msg = TR("msg_restart") if new_lang == "EN" else "Язык изменен! Перезапустите программу."
            QMessageBox.information(self, "RESTART REQUIRED", msg)
        
        self.accept()

class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.history_file = HISTORY_FILE
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

      
        header = QLabel("📜 ATTACK HISTORY (ИСТОРИЯ ДЕЙСТВИЙ)")
        header.setStyleSheet("color: #00ff9d; font-weight: bold; font-size: 14px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

       
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["TIME", "ACTION", "TARGET / LINK", "DETAILS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #000;
                gridline-color: #333;
                color: #00ff41;
                font-family: 'Consolas';
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #111;
                color: #fff;
                border: 1px solid #333;
                padding: 4px;
            }
        """)
        layout.addWidget(self.table)

    
        btn_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("$ CLEAR_HISTORY")
        self.btn_clear.clicked.connect(self.clear_history)
        self.btn_clear.setStyleSheet("color: #ff0033; border: 1px solid #ff0033; padding: 8px;")
        
        self.btn_refresh = QPushButton("$ RELOAD")
        self.btn_refresh.clicked.connect(self.load_history)
        self.btn_refresh.setStyleSheet("color: #0099ff; border: 1px solid #0099ff; padding: 8px;")

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def add_record(self, action_type, target, details=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
      
        self.insert_row(timestamp, action_type, target, details)
        
        
        self.save_record_to_json({
            "time": timestamp,
            "action": action_type,
            "target": target,
            "details": details
        })

    def insert_row(self, time, action, target, details):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(time))
        self.table.setItem(row, 1, QTableWidgetItem(action))
        self.table.setItem(row, 2, QTableWidgetItem(target))
        self.table.setItem(row, 3, QTableWidgetItem(details))

    def save_record_to_json(self, record):
        data = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except: pass
            
        data.insert(0, record) 
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_history(self):
        self.table.setRowCount(0)
        if not self.history_file.exists(): return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for item in data:
                self.insert_row(item.get("time"), item.get("action"), item.get("target"), item.get("details"))
        except Exception as e:
            print(f"History load error: {e}")

    def clear_history(self):
        reply = QMessageBox.question(self, "CONFIRM", "Delete all history?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table.setRowCount(0)
            with open(self.history_file, 'w') as f:
                json.dump([], f)

class ScannerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        grid = QGridLayout()
        grid.addWidget(QLabel(TR("lbl_scanner_target")), 0, 0)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("@chat_link")
        grid.addWidget(self.target_input, 0, 1)

        self.all_sessions_cb = QCheckBox(TR("cb_all_sessions"))
        self.all_sessions_cb.setChecked(True)
        grid.addWidget(self.all_sessions_cb, 0, 2)

        self.btn_start = QPushButton(TR("btn_scanner_start"))
        self.btn_start.clicked.connect(self.start_global_monitoring)
        grid.addWidget(self.btn_start, 1, 2)
        
        layout.addLayout(grid)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по всей базе сообщений...")
        self.btn_search = QPushButton(TR("btn_db_search"))
        self.btn_search.clicked.connect(self.search_vault)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)

        self.res_table = QTableWidget(0, 3)
        self.res_table.setHorizontalHeaderLabels([TR("col_time"), TR("col_user"), TR("col_text")])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.res_table)

        self.setLayout(layout)

    def start_global_monitoring(self):
        target = self.target_input.text().strip()
        if not target: return
        asyncio.create_task(self.parent.deploy_monitors(target, self.all_sessions_cb.isChecked()))

    def search_vault(self):
        query = self.search_input.text().strip()
        cursor = DB_CONN.cursor()
        sql = "SELECT timestamp, user_id, text FROM messages"
        if query:
            sql += f" WHERE text LIKE '%{query}%'"
        sql += " ORDER BY timestamp DESC LIMIT 100"
        
        df = pd.read_sql_query(sql, DB_CONN)
        
        self.res_table.setRowCount(0)
        for _, row in df.iterrows():
            r = self.res_table.rowCount()
            self.res_table.insertRow(r)
            self.res_table.setItem(r, 0, QTableWidgetItem(str(row['timestamp'])))
            self.res_table.setItem(r, 1, QTableWidgetItem(str(row['user_id'])))
            self.res_table.setItem(r, 2, QTableWidgetItem(str(row['text'])))

class CyberMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_TITLE)
        self.setGeometry(100, 100, 1400, 900)
        
        self.setMinimumSize(1000, 700)
        
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.setStyleSheet(CyberTheme.STYLES)
        
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        else:
            self.setWindowIcon(QIcon.fromTheme("terminal"))
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("READY | ARCH LINUX | ROOT ACCESS GRANTED")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        # header_frame = QFrame()
        # header_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        # header_frame.setLineWidth(2)
        # header_frame.setStyleSheet("""
        #     border: 2px solid #00ff41;
        #     background-color: #000000;
        #     padding: 5px;
        # """)
        # 
        # header_label = QLabel("""
        # █▀█ █░█ ▄▀█ █▄░█ ▀█▀ █▀█ █▀▄▀█
        # █▀▀ █▀█ █▀█ █░▀█ ░█░ █▄█ █░▀░█
        # █▀ █▄█ █▄░█ █▀▀ ▄█ ░█░ █░▀█ █▄▄
        #         """)
        # header_label.setAlignment(Qt.AlignCenter)
        # 
        # header_label.setStyleSheet("""
        #     color: #00ff41; 
        #     font-family: monospace; 
        #     font-size: 8px;    
        #     line-height: 8px;    
        #     letter-spacing: 0px;
        # """)
        # 
        # header_layout = QVBoxLayout()
        # header_layout.addWidget(header_label)
        # header_frame.setLayout(header_layout)
        # main_layout.addWidget(header_frame)
        # =====================================================================
        
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 10, 10, 0) 
        

        toolbar_layout.addStretch()
        self.btn_settings = QPushButton("⚙️") 
        self.btn_settings.setFixedWidth(120)
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #000; 
                color: #666; 
                border: 1px solid #333; 
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #00ff41;
                border: 1px solid #00ff41;
            }
        """)
        toolbar_layout.addWidget(self.btn_settings)
        
        main_layout.addLayout(toolbar_layout)

        self.tabs = QTabWidget()
        
       
        self.session_manager = SessionManager(self)
        self.tabs.addTab(self.session_manager, TR("tab_sessions"))
        
       
        self.spam_control = SpamControl(self)
        self.tabs.addTab(self.spam_control, TR("tab_spam"))
        
        
        self.view_booster = ViewBooster(self)
        self.tabs.addTab(self.view_booster, TR("tab_view"))
        
        
        self.stats_dashboard = StatsDashboard(self)
        self.tabs.addTab(self.stats_dashboard, TR("tab_dash"))
        
      
        self.history_panel = HistoryPanel(self)
        self.tabs.addTab(self.history_panel, "HISTORY") 
        
        self.scanner_panel = ScannerPanel(self)
        self.tabs.addTab(self.scanner_panel, TR("tab_scanner"))
        
        
        self.logs_panel = LogsPanel(self)
        self.tabs.addTab(self.logs_panel, TR("tab_logs"))
        
        main_layout.addWidget(self.tabs)
        
      
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        footer_frame.setLineWidth(1)
        footer_frame.setStyleSheet("""
            border: 1px solid #333333;
            background-color: #111111;
            padding: 5px;
        """)
        
        footer_layout = QHBoxLayout()
        
        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.time_label.setStyleSheet("color: #666666; font-family: 'Consolas';")
        footer_layout.addWidget(self.time_label)
        
        footer_layout.addStretch()
        
        self.user_label = QLabel(f"USER: {os.getlogin()} | HOST: {platform.node()}")
        self.user_label.setStyleSheet("color: #00ff41; font-family: 'Consolas';")
        footer_layout.addWidget(self.user_label)
        
        footer_layout.addStretch()
        
        self.mode_label = QLabel("MODE: NORMAL | PRIVILEGES: ROOT")
        self.mode_label.setStyleSheet("color: #ff9900; font-family: 'Consolas';")
        footer_layout.addWidget(self.mode_label)
        
        footer_frame.setLayout(footer_layout)
        main_layout.addWidget(footer_frame)
        
       
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
    
        self.spam_clients = []
        self.is_spamming = False
        self.spam_stats = {
            'active': 0,
            'sent': 0,
            'errors': 0,
            'total_sent': 0,
            'successful': 0
        }
        
    def update_clock(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()
        
    async def attach_sniffer(self, client, session_name, target_chat=None):
        @client.on(events.NewMessage(chats=target_chat if target_chat else None))
        async def log_handler(event):
            if event.is_group or event.is_channel:
                cursor = DB_CONN.cursor()
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO messages 
                        (msg_id, chat_id, user_id, text, timestamp, session_owner) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (event.id, event.chat_id, event.sender_id, event.text, event.date, session_name))
                    DB_CONN.commit()
                finally:
                    pass
        
        @client.on(events.MessageDeleted())
        async def delete_handler(event):
            cursor = DB_CONN.cursor()
            try:
                for msg_id in event.deleted_ids:
                    cursor.execute("UPDATE messages SET is_deleted = 1 WHERE msg_id = ?", (msg_id,))
                DB_CONN.commit()
            finally:
                pass

    async def deploy_monitors(self, target, all_sessions=True):
        session_files = list(SESSIONS_DIR.glob("*.session"))
        if not session_files: return
        
        targets = [session_files[0]] if not all_sessions else session_files
        
        if hasattr(self, 'logs_panel'):
            self.logs_panel.add_log(f"Starting monitors on {target}...", "INFO")
        
        for s_file in targets:
            try:
                client = TelegramClient(str(s_file), config.API_ID, config.API_HASH)
                await client.connect()
                if await client.is_user_authorized():
                    await self.attach_sniffer(client, s_file.stem, target)
                    if hasattr(self, 'logs_panel'):
                        self.logs_panel.add_log(f"Session {s_file.stem} is now monitoring.", "SUCCESS")
            except Exception as e:
                if hasattr(self, 'logs_panel'):
                    self.logs_panel.add_log(f"Failed to start monitor on {s_file.stem}: {e}", "ERROR")
        
    async def test_all_sessions(self):
        session_files = []
        
       
        for file in SESSIONS_DIR.glob("*.session"):
         
            if 'journal' in file.name or '-wal' in file.name or '-shm' in file.name:
                continue
                
            session_files.append({'path': file})
        
        if not session_files:
            self.spam_control.log("ERROR: No valid .session files found!", "#ff0033")
            return
            
        self.spam_control.log(f"Testing {len(session_files)} session files...", "#0099ff")
        
        success_count = 0
        fail_count = 0
        
        for session_data in session_files:
            session_file = session_data['path']
            try:
                client = TelegramClient(
                    session=str(session_file),
                    api_id=config.API_ID,
                    api_hash=config.API_HASH
                )
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    phone = f"+{me.phone}" if hasattr(me, 'phone') else "No phone"
                    self.spam_control.log(f"✅ OK: {phone}", "#00ff41")
                    success_count += 1
                else:
                    self.spam_control.log(f"❌ FAIL: {session_file.name}", "#ff0033")
                    fail_count += 1
                    
                await client.disconnect()
                
            except Exception as e:
                self.spam_control.log(f"⚠️ ERROR: {session_file.name} -> {str(e)[:30]}", "#ff9900")
                fail_count += 1
                
        self.spam_control.log(f"Test complete! OK: {success_count}, DEAD: {fail_count}", "#00ff41")

    async def run_spamblock_checker(self):
        session_files = list(SESSIONS_DIR.glob("*.session"))
            
        if not session_files:
            self.spam_control.log("No sessions found!", "#ff0033")
            return

        self.spam_control.log(f"🕵️ DETECTING SPAMBLOCK ON {len(session_files)} ACCOUNTS...", "#0099ff")
        
        stats = {"CLEAN": 0, "BLOCKED": 0, "FIXED": 0, "PENDING": 0, "ERROR": 0}
        
        for session_file in session_files:
            client = TelegramClient(str(session_file), config.API_ID, config.API_HASH)
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    await client.disconnect()
                    continue
                    
                me = await client.get_me()
                phone = f"+{me.phone}"
                
                
                status = await self.solve_spambot(client)
                
                if status == "CLEAN":
                    self.spam_control.log(f"[{phone}] ✅ CLEAN", "#00ff41")
                    stats["CLEAN"] += 1
                    
                elif status == "PENDING":
                
                    self.spam_control.log(f"[{phone}] ⏳ ALREADY REVIEWING (Skip)", "#ff9900")
                    stats["PENDING"] += 1
                    
                elif status == "APPEAL_SENT":
                    self.spam_control.log(f"[{phone}] 📨 APPEAL SENT NOW", "#0099ff")
                    stats["FIXED"] += 1
                    
                elif status == "BLOCKED_FOREVER":
                    self.spam_control.log(f"[{phone}] 💀 PERMANENT BAN", "#ff0033")
                    stats["BLOCKED"] += 1
                    
                else: 
                    self.spam_control.log(f"[{phone}] ❌ BLOCKED/ERROR", "#ff0033")
                    stats["BLOCKED"] += 1
                
                await client.disconnect()
                await asyncio.sleep(2) 
                
            except Exception as e:
                self.spam_control.log(f"[{session_file.stem}] Error: {str(e)[:20]}", "#ff0033")
                stats["ERROR"] += 1
                try: await client.disconnect() 
                except: pass
                
        
        self.spam_control.log("-" * 30, "#666666")
        self.spam_control.log(f"DONE! ✅Clean: {stats['CLEAN']} | ⏳Pending: {stats['PENDING']} | 📨Sent: {stats['FIXED']}", "#00ff9d")

    async def solve_spambot(self, client):
        try:
            bot_username = "@SpamBot"
            
            try:
                history = await client.get_messages(bot_username, limit=1)
                if history and history[0].out and "mistake" in history[0].text.lower():
                     return "PENDING"
            except:
                pass

            await client.send_message(bot_username, "/start")
            await asyncio.sleep(2)
            
            history = await client.get_messages(bot_username, limit=1)
            if not history or history[0].out:
                return "SILENT"
            
            last_msg = history[0]
            text = last_msg.text.lower()
            
            clean_phrases = ["good news", "no limits", "свободен", "ограничений нет", "аккаунт не ограничен"]
            
            pending_phrases = [
                "complaint has been received", "жалоба принята", 
                "reviewing", "рассматривают", 
                "check", "проверят", 
                "moderators", "модераторы",
                "wait", "ожидайте"
            ]
            
            for phrase in clean_phrases:
                if phrase in text:
                    return "CLEAN"
                    
            for phrase in pending_phrases:
                if phrase in text:
                    return "PENDING"
            
            if not last_msg.buttons:
                return "BLOCKED_FOREVER"
                
            if not await self.click_btn(client, last_msg, ["mistake", "ошибка"]):
                return "BLOCKED"
            
            await asyncio.sleep(1.5)
            
            history = await client.get_messages(bot_username, limit=1)
            if not await self.click_btn(client, history[0], ["yes", "да"]):
                return "BLOCKED"
            
            await asyncio.sleep(1.5)
            
            history = await client.get_messages(bot_username, limit=1)
            if not await self.click_btn(client, history[0], ["no", "нет"]):
                return "BLOCKED"
            
            await asyncio.sleep(1.5)
            
            appeal_text = "Hello team. I believe my account was limited by mistake. I use Telegram only for personal family chats and work. I have not sent spam. Please review. Thank you."
            await client.send_message(bot_username, appeal_text)
            
            return "APPEAL_SENT"
            
        except Exception as e:
            print(f"Spambot error: {e}")
            return "ERROR"

    async def click_btn(self, client, message, triggers):
        if not message.buttons: return False
        for row in message.buttons:
            for btn in row:
                btn_text = btn.text.lower()
                for trig in triggers:
                    if trig in btn_text:
                        await btn.click()
                        return True
        return False
        
     
        self.session_manager.load_sessions()
        
    async def send_guaranteed_screenshot_notification(self, client, entity, reply_id=None):
        try:
           
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
            except:
                import pyautogui
                screenshot = pyautogui.screenshot()
            
           
            width, height = screenshot.size
            
          
            from PIL import Image, ImageDraw
            mask = Image.new('L', (512, 512), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 512, 512), fill=255)
            
           
            screenshot_resized = screenshot.resize((512, 512), Image.Resampling.LANCZOS)
            screenshot_circle = Image.new('RGBA', (512, 512))
            screenshot_circle.paste(screenshot_resized, (0, 0), mask)
            
           
            output = io.BytesIO()
            screenshot_circle.save(output, format='PNG', quality=95)
            output.seek(0)
            
           
            await client.send_file(
                entity,
                file=output,
                video_note=True, 
                duration=1,
                length=512,
                reply_to=reply_id,
                supports_streaming=False
            )
            
            return True
            
        except Exception as e:
            print(f"Screenshot notification error: {e}")
            return False
        
    async def send_screenshot(self, client, target):
        try:
            from telethon.tl.functions.messages import SendScreenshotNotificationRequest
            from telethon.tl.types import InputReplyToMessage
            import random
            
            entity = await client.get_entity(target)
            
           
            try:
                messages = await client.get_messages(entity, limit=1)
                reply_id = messages[0].id if messages and messages[0].id else 0
            except:
                reply_id = 0
                
            reply_to = InputReplyToMessage(reply_to_msg_id=reply_id)
            
        
            result = await client(SendScreenshotNotificationRequest(
                peer=entity,
                reply_to=reply_to,
                random_id=random.randint(0, 0x7fffffff)
            ))
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            
           
            if "random_id" in error_msg or "Missing" in error_msg:
                try:
                   
                    await client(SendScreenshotNotificationRequest(
                        peer=entity,
                        reply_to=reply_to
                    ))
                    return True
                except Exception as e2:
                    return False
            return False
            
    async def check_premium_status(self, client):
        try:
            me = await client.get_me()
            return getattr(me, 'premium', False)
        except:
            return False
        
    def start_spam_safe(self, target, delay=5, max_errors=5, random_delay=True, stealth_mode=False):
       
        asyncio.create_task(self.start_spam(
            target, delay, max_errors, random_delay, stealth_mode
        ))
            
    async def start_spam(self, target, delay=5, max_errors=5, random_delay=True, mode="RANDOM CHAOS", custom_text=""):
        try:
           
            session_files = []
            for file in SESSIONS_DIR.glob("*.session"):
            
                if 'journal' not in file.name and file.stat().st_size > 500:
                    session_files.append(file)
            
            if not session_files:
                self.spam_control.log("NO VALID SESSIONS FOUND", "#ff0033")
                self.spam_control.btn_stop.click()
                return

            self.spam_clients = []
            self.is_spamming = True
            self.spam_control.log(f"🔥 MODE: {mode}", "#ff9900")
            if mode == "SPECIFIC TEXT":
                 self.spam_control.log(f"📝 TEXT: {custom_text}", "#00ff9d")

           
            load_tasks = [self.load_client(f) for f in session_files]
            results = await asyncio.gather(*load_tasks, return_exceptions=True)
            
            loaded = 0
            for res in results:
                if isinstance(res, dict) and 'client' in res:
                    self.spam_clients.append(res)
                    loaded += 1
            
            if loaded == 0:
                self.spam_control.log("ALL SESSIONS DEAD", "#ff0033")
            tasks = []
            for i, client in enumerate(self.spam_clients):
                tasks.append(asyncio.create_task(
                    self.mass_spam_from_client(client, target, delay, max_errors, random_delay, mode, custom_text, start_delay=i*1.5)
                ))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.spam_control.log(f"CRITICAL: {e}", "#ff0033")
        finally:
            self.is_spamming = False
            for c in self.spam_clients: 
                if c.get('client'): await c['client'].disconnect()
            self.spam_control.stop_spam()
            
    def get_proxy_for_session(self, session_name):
        import json
        import python_socks
        
        if not PROXY_FILE.exists():
            return None
            
        try:
            with open(str(PROXY_FILE), 'r') as f:
                proxies = json.load(f)
                
           
            proxy_str = proxies.get(session_name)
            if not proxy_str:
                return None
                
       
            parts = proxy_str.split(':')
            
            p_type = python_socks.ProxyType.SOCKS5 if 'socks5' in parts[0] else python_socks.ProxyType.HTTP
            p_addr = parts[1]
            p_port = int(parts[2])
            p_user = parts[3] if len(parts) > 3 else None
            p_pass = parts[4] if len(parts) > 4 else None
            
            return (p_type, p_addr, p_port, True, p_user, p_pass)
            
        except Exception as e:
            if hasattr(self, 'logs_panel'):
                self.logs_panel.add_log(f"Proxy Error: {e}", "ERROR")
            return None
            
    async def load_client(self, session_file):
        try:
       
            session_name = session_file.stem 
            
       
            proxy_config = self.get_proxy_for_session(session_name)
            
          
            client = TelegramClient(
                session=str(session_file),
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                proxy=proxy_config  
            )
            
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                phone = f"+{me.phone}" if hasattr(me, 'phone') else session_file.name
                premium = getattr(me, 'premium', False)
                
                await self.attach_sniffer(client, session_name, None)
                
                return {
                    'client': client,
                    'phone': phone,
                    'sent': 0,
                    'errors': 0,
                    'active': True,
                    'premium': premium
                }
            else:
                await client.disconnect()
                return None
                
        except Exception as e:
            try:
                await client.disconnect()
            except:
                pass
            return None
            
    async def mass_spam_from_client(self, client_data, target, base_delay, max_errors, random_delay, mode, custom_text, start_delay):
        client = client_data['client']
        phone = client_data['phone']
        is_premium = client_data.get('premium', False)
        
        await asyncio.sleep(start_delay)
        
        try:
            try:
                if not self.is_spamming: return
                entity = await client.get_entity(target)
            except Exception as e:
                self.spam_control.log(f"[{phone}] ❌ Цель не найдена: {str(e)[:20]}", "#ff0033")
                return

            self.spam_control.log(f"[{phone}] ⚔️ Цель захвачена", "#666666")

            while client_data['errors'] < max_errors and self.is_spamming:
                wait = base_delay if is_premium else base_delay * 1.5
                if random_delay: wait = random.uniform(wait*0.8, wait*1.2)
                await asyncio.sleep(wait)
                
                if not self.is_spamming: break

                try:
                    success = False
                    
                    if mode == "GHOST ONLY":
                        try:
                            action = SendMessageTypingAction() if random.random() > 0.5 else SendMessageRecordAudioAction()
                            await client(SetTypingRequest(entity, action))
                            client_data['errors'] = 0
                            continue 
                        except:
                            pass

                    elif is_premium:
                        success = await self.send_screenshot(client, target)
                        log_msg = "📸 Скриншот"
                        
                    else:
                        if mode == "SPECIFIC TEXT":
                            msg_text = custom_text if custom_text else "."
                            msg_text += f" ‏‏‎ " * random.randint(0, 3) 
                        else:
                            phrases = ["?", "ку", "че молчишь", ".", "ало", "лол", "мда", "что?", "спам", "1337"]
                            msg_text = random.choice(phrases)
                        
                        await client.send_message(entity, msg_text)
                        success = True
                        log_msg = f"💬 {msg_text.strip()[:10]}"

                    if success:
                        client_data['sent'] += 1
                        client_data['errors'] = 0
                        if is_premium or client_data['sent'] % 2 == 0:
                            color = "#00ff41" if is_premium else "#0099ff"
                            self.spam_control.log(f"[{phone}] {log_msg}", color)
                    else:
                        client_data['errors'] += 1

                except Exception as e:
                    err = str(e)
                    
                    if "Too many requests" in err or "FLOOD_WAIT" in err:
                        import re
                        match = re.search(r'(\d+)', err)
                        wait_sec = int(match.group(1)) if match else 60
                        self.spam_control.log(f"[{phone}] ⏳ ФЛУД-ЛИМИТ (Ждем {wait_sec}с)", "#ff9900")
                        
                        end = time.time() + wait_sec
                        while time.time() < end and self.is_spamming:
                            await asyncio.sleep(5)

                    elif "PEER_FLOOD" in err:
                        self.spam_control.log(f"[{phone}] ☠️ СПАМБЛОК (Аккаунт умер)", "#ff0033")
                        return
                        
                    elif "USER_PRIVACY_RESTRICTED" in err:
                        self.spam_control.log(f"[{phone}] ❌ ПРИВАТНОСТЬ (ЛС закрыто)", "#ff0033")
                        client_data['errors'] += 1
                        
                    elif "CHAT_WRITE_FORBIDDEN" in err:
                        self.spam_control.log(f"[{phone}] ❌ ЧАТ ЗАКРЫТ (Нет прав)", "#ff0033")
                        return
                        
                    elif "USER_BANNED_IN_CHANNEL" in err:
                        self.spam_control.log(f"[{phone}] 🔨 ЗАБАНЕН В ЧАТЕ", "#ff0033")
                        return
                        
                    else:
                        clean_err = err.replace("RPCError", "").replace("Request", "")[:40]
                        self.spam_control.log(f"[{phone}] ⚠️ ОШИБКА: {clean_err}", "#ff0033")
                        client_data['errors'] += 1
                        
        except Exception as e:
            self.spam_control.log(f"[{phone}] 💥 КРАШ: {e}", "#ff0033")
            
    async def spam_from_client(self, client_data, target, base_delay, max_errors, random_delay, stealth_mode):
        client = client_data['client']
        phone = client_data['phone']
        
        try:
            while client_data['errors'] < max_errors and self.is_spamming:
                if random_delay:
                    current_delay = random.uniform(base_delay * 0.7, base_delay * 1.3)
                else:
                    current_delay = base_delay
                    
                if stealth_mode and random.random() < 0.1:
                    pause = random.uniform(10, 30)
                    self.spam_control.log(f"[{phone}] Stealth pause: {pause:.1f}s", "#666666")
                    await asyncio.sleep(pause)
                    
                success = await self.send_screenshot(client, target)
                
                if success:
                    client_data['sent'] += 1
                    self.spam_stats['sent'] += 1
                    self.spam_stats['total_sent'] += 1
                    self.spam_stats['successful'] += 1
                    
                    if client_data['sent'] % 10 == 0:
                        self.spam_control.log(f"[{phone}] Sent: {client_data['sent']}", "#00ff41")
                else:
                    client_data['errors'] += 1
                    self.spam_stats['errors'] += 1
                    self.spam_control.log(f"[{phone}] Error #{client_data['errors']}", "#ff9900")
                    
                active = len([c for c in self.spam_clients if c['errors'] < max_errors])
                self.spam_stats['active'] = active
                    
                await asyncio.sleep(current_delay)
                
        except Exception as e:
            client_data['active'] = False
            self.spam_control.log(f"[{phone}] Disconnected: {str(e)[:50]}", "#ff0033")


def main():
    os.environ["QT_QPA_PLATFORM"] = "xcb" 
    
    os.environ["QT_NO_GLIB"] = "1"
    
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1.0"
    
    
    app = QApplication(sys.argv)
    
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app.setStyle('Fusion')

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = CyberMainWindow()
    window.show()
    

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main()