# 👻 PHANTOM SYNC
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?style=for-the-badge&logo=qt)
![Telethon](https://img.shields.io/badge/Telethon-Async-orange?style=for-the-badge)

**Phantom Sync** is a powerful, asynchronous Telegram session management and automation tool designed for marketing professionals. Built with Python and PyQt5, it features a modern "Cyberpunk" interface and supports multi-threaded operations.

---

## 🖥️ Interface
![Dashboard Preview](https://via.placeholder.com/800x400.png?text=Preview+Coming+Soon)

## 🔥 Key Features

* **Advanced Session Management**: Import, validate, and manage unlimited Telegram sessions (`.session`).
* **Asynchronous Architecture**: Built on `asyncio` and `Telethon` for non-blocking high-performance tasks.
* **Smart Proxy Support**: Individual proxy configuration (SOCKS5/HTTP) for each account to ensure safety.
* **Interactive Dashboard**: Real-time statistics (CPU/RAM usage, active sessions, success rates).
* **Modern GUI**: Custom-styled dark theme interface using PyQt5.
* **Safe-Mode Automation**: Imitates real user behavior (typing status, scrolling, random delays) to avoid detection.
* **Detailed Logging**: Built-in terminal for real-time operation logs and history tracking.

## 🛠️ Tech Stack

* **Core**: Python 3.10+
* **GUI Framework**: PyQt5
* **Telegram API**: Telethon (MTProto)
* **Concurrency**: asyncio, qasync
* **Utilities**: psutil, Pillow, python-socks

## 🚀 Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Phantom-Sync.git](https://github.com/YOUR_USERNAME/Phantom-Sync.git)
    cd Phantom-Sync
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(Or run `install.bat` on Windows)*

3.  **Configuration**
    Open `config.py` and add your Telegram API credentials:
    ```python
    API_ID = 123456
    API_HASH = "your_hash_here"
    ```

4.  **Run**
    ```bash
    python main.py
    ```

## ⚙️ Usage

1.  Launch the application.
2.  Go to **Sessions** tab and add accounts (via phone login).
3.  (Optional) Configure proxies via Right-Click menu context.
4.  Use **Spam Control** or **View Booster** tabs for automation tasks.

---

## ⚠️ Disclaimer

This tool is developed for **educational purposes and internal marketing testing only**. The developer is not responsible for any misuse of this software. Please respect Telegram's Terms of Service.

---
*Developed by apvcode*