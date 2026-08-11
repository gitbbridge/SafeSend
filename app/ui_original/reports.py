import tkinter as tk
from tkinter import ttk

from app.database import db
from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Reports / Logs", "Campaign totals, queue results, SMTP usage, and recent errors.")
    frame.pack(fill="both", expand=True)
    table_frame = ttk.Frame(frame)
    table_frame.grid(row=2, column=0, sticky="nsew")
    columns = ("campaign", "total", "sent", "failed", "skipped", "suppressed", "smtp_accounts_used")
    tree = build_tree(table_frame, columns, height=16)
    rows = [
        dict(row)
        for row in db.fetch_all(
            """
            SELECT
                campaigns.name AS campaign,
                COUNT(send_queue.id) AS total,
                SUM(CASE WHEN send_queue.status = 'Sent' THEN 1 ELSE 0 END) AS sent,
                SUM(CASE WHEN send_queue.status = 'Failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN send_queue.status = 'Skipped' THEN 1 ELSE 0 END) AS skipped,
                SUM(CASE WHEN send_queue.status = 'Suppressed' THEN 1 ELSE 0 END) AS suppressed,
                COUNT(DISTINCT send_queue.smtp_profile_id) AS smtp_accounts_used
            FROM campaigns
            LEFT JOIN send_queue ON send_queue.campaign_id = campaigns.id
            GROUP BY campaigns.id
            ORDER BY campaigns.created_at DESC
            """
        )
    ]
    fill_tree(tree, rows, columns)
    frame.rowconfigure(2, weight=1)
