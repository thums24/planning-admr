<p align="center">
  <img src="assets/logo.png" width="160" alt="Planning ADMR logo">
</p>

<h1 align="center">Planning ADMR</h1>

<p align="center">
  One button. Next week's care schedule as a large-print PDF.<br>
  Designed for elderly people who just want to click and read.
</p>

> **Disclaimer:** unofficial community tool, not affiliated with ADMR.
> Your credentials stay on your computer (OS keychain) and are only sent
> to the official site `monadmr.org` to download your own schedule.

## Download

Go to **[Releases](../../releases)** and get:

| System | File | Install |
|---|---|---|
| Windows | `Setup-Planning-ADMR-1.0.0.exe` | Double-click, Next → Install → Finish |
| macOS | `Planning-ADMR-1.0.0.dmg` | Open, drag the app to Applications |

No admin rights needed. No Python needed.

## How it works (for the end user)

1. Open **Planning ADMR**.
2. First time only: enter your ADMR login (9-character username + 6-digit code) and click **"Voir mon planning"**.
3. Every week after that: open the app, it logs in by itself, downloads **next week's** schedule and opens the big-letter PDF.

If next week's schedule isn't published yet (usually online on Saturday),
the app says so instead of failing silently.

## Features

- 🔑 One-time login, securely stored in the OS keychain (macOS Keychain / Windows Credential Locker)
- 📅 Always fetches the **upcoming week** (Mon → Sun)
- 🔤 Large-print PDF: boxed day headers, bold times, lined space for handwritten notes
- 🖥️ Big-font, single-window interface, French throughout
- 📴 Offline fallback: reuses the last downloaded schedule file if the network is down

## For developers

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python admr.py
```

Build installers locally:

```bash
pip install -r requirements-build.txt
pyinstaller planning-admr.spec          # macOS -> dist/"Planning ADMR.app"
iscc installer.iss                      # Windows -> Setup-Planning-ADMR-1.0.0.exe
```

Windows `.exe` and the installer are built automatically by
[GitHub Actions](.github/workflows/build.yml) on every `v*` tag and
attached to the GitHub Release.

```
admr.py                 # the whole app: login, download, PDF, GUI
assets/                 # logo (svg/png), icons (ico/icns), logo generator
planning-admr.spec      # PyInstaller build definition
installer.iss           # Inno Setup installer definition (Windows)
```

## License

MIT — see [LICENSE](LICENSE).
