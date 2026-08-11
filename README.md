# SafeSend

SafeSend is a Windows desktop SMTP sender for controlled, reputation-aware campaign sending.

This first build includes the commercial application shell:

- CustomTkinter desktop shell with an Azure-inspired SafeSend design system.
- Sidebar navigation for Dashboard, Campaigns, Compose, Contacts / Lists, SMTP Servers, Sending Rules, Clustering / Reputation Strategy, Verification, Sending Queue, Reports / Logs, Suppression List, and Settings.
- Local SQLite initialization in `data/safesend.db`.
- Modular services for SMTP profiles, campaign drafts, CSV imports, suppression, verification, clustering, rotation, and queue generation.
- Basic logging in `logs/safesend.log`.
- PyInstaller helper for future `.exe` packaging.

## Run Locally

```powershell
cd C:\Users\inboxblake\development\CAL\SafeSend
python -m pip install -r requirements.txt
python main.py
```

Tkinter ships with most Windows Python installers. If your Python install does not include Tkinter, install a Python distribution that includes Tcl/Tk.

## Package

```powershell
cd C:\Users\inboxblake\development\CAL\SafeSend
python build_exe.py
```

The build script uses PyInstaller and places output in `dist/`. CustomTkinter ships data files, so the script includes the installed `customtkinter` package folder as PyInstaller data.

## Current Milestone

This is the first working milestone, not the complete sending engine. It intentionally focuses on:

- Clean commercial app structure.
- Database schema and persistence.
- SMTP profile management and connection testing.
- CSV contact import with validation and dedupe.
- Campaign draft composition with footer compliance checks.
- Clustering analysis and queue preparation.
- Reports, suppression, settings, and verification configuration.

Full live campaign sending, scheduling workers, bounce processing, attachment handling, and richer HTML editing should be added as later milestones.

## Safety Scope

SafeSend does not include scraping, lead finding, exhibitor research, or list harvesting features. Use permission-based lists and comply with applicable email laws and SMTP provider policies.
