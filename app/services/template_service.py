import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from app.database import db


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


class TemplateService:
    def list_templates(self, search: str = "", include_archived: bool = False, sort_by: str = "updated_at DESC") -> list[dict]:
        clauses = []
        params: list[object] = []
        if not include_archived:
            clauses.append("archived = 0")
        if search.strip():
            clauses.append("(name LIKE ? OR subject LIKE ? OR category LIKE ? OR tags LIKE ? OR html_body LIKE ? OR plain_text_body LIKE ?)")
            like = f"%{search.strip()}%"
            params.extend([like, like, like, like, like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_sort = sort_by if sort_by in {
            "name ASC",
            "name DESC",
            "updated_at DESC",
            "updated_at ASC",
            "created_at DESC",
            "favorite DESC",
            "times_used DESC",
            "last_used_at DESC",
        } else "updated_at DESC"
        rows = db.fetch_all(f"SELECT * FROM templates {where} ORDER BY {safe_sort}", params)
        return [dict(row) for row in rows]

    def filtered_templates(
        self,
        search: str = "",
        category: str = "All",
        status: str = "All",
        include_archived: bool = False,
        sort_by: str = "updated_at DESC",
    ) -> list[dict]:
        rows = self.list_templates(search, include_archived=True, sort_by=sort_by)
        filtered: list[dict] = []
        for row in rows:
            row_archived = bool(row.get("archived"))
            if not include_archived and row_archived:
                continue
            if category not in {"", "All"} and (row.get("category") or "General") != category:
                continue
            row_status = "Archived" if row_archived else (row.get("status") or "Draft")
            if status not in {"", "All"} and row_status != status:
                continue
            filtered.append(row)
        return filtered

    def get_template(self, template_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM templates WHERE id = ?", (template_id,))
        return dict(row) if row else None

    def create_template(self, name: str = "Untitled Template") -> int:
        unique = self._unique_name(name)
        return db.execute(
            """
            INSERT INTO templates (name, subject, html_body, plain_text_body)
            VALUES (?, '', '<p></p>', '')
            """,
            (unique,),
        )

    def save_template(self, values: dict, template_id: int | None = None, create_version: bool = True) -> int:
        name = (values.get("name") or "Untitled Template").strip()
        if not name:
            raise ValueError("Template name is required.")
        if template_id and create_version:
            self.create_version(template_id)
        html_body = values.get("html_body") or ""
        plain_text = values.get("plain_text_body") or self.html_to_text(html_body)
        params = (
            name,
            values.get("subject", "").strip(),
            values.get("preheader", "").strip(),
            values.get("from_name", "").strip(),
            values.get("from_email", "").strip(),
            values.get("reply_to_email", "").strip(),
            html_body,
            plain_text,
            values.get("category", "General").strip() or "General",
            values.get("status", "Draft").strip() or "Draft",
            values.get("tags", "").strip(),
            1 if values.get("favorite") else 0,
            values.get("created_by", "Local User").strip() or "Local User",
            values.get("notes", "").strip(),
        )
        if template_id:
            existing = db.fetch_one("SELECT id FROM templates WHERE name = ? AND id <> ?", (name, template_id))
            if existing:
                raise ValueError("Another template already uses that name.")
            db.execute(
                """
                UPDATE templates
                SET name = ?, subject = ?, preheader = ?, from_name = ?, from_email = ?,
                    reply_to_email = ?, html_body = ?, plain_text_body = ?, category = ?,
                    status = ?, tags = ?, favorite = ?, created_by = ?,
                    notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*params, template_id),
            )
            return template_id
        existing = db.fetch_one("SELECT id FROM templates WHERE name = ?", (name,))
        if existing:
            raise ValueError("A template with that name already exists.")
        return db.execute(
            """
            INSERT INTO templates (
                name, subject, preheader, from_name, from_email, reply_to_email,
                html_body, plain_text_body, category, status, tags, favorite, created_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            params,
        )

    def duplicate_template(self, template_id: int) -> int:
        template = self.get_template(template_id)
        if not template:
            raise ValueError("Template was not found.")
        template["name"] = self._unique_name(f"{template['name']} Copy")
        template["favorite"] = 0
        return self.save_template(template, None, False)

    def rename_template(self, template_id: int, name: str) -> None:
        template = self.get_template(template_id)
        if not template:
            raise ValueError("Template was not found.")
        template["name"] = name
        self.save_template(template, template_id)

    def archive_template(self, template_id: int, archived: bool = True) -> None:
        db.execute("UPDATE templates SET archived = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (1 if archived else 0, template_id))

    def delete_template(self, template_id: int) -> None:
        db.execute("DELETE FROM templates WHERE id = ?", (template_id,))

    def toggle_favorite(self, template_id: int) -> None:
        db.execute(
            """
            UPDATE templates
            SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (template_id,),
        )

    def create_version(self, template_id: int) -> int:
        template = self.get_template(template_id)
        if not template:
            raise ValueError("Template was not found.")
        row = db.fetch_one("SELECT COALESCE(MAX(version_number), 0) + 1 AS version FROM template_versions WHERE template_id = ?", (template_id,))
        version = int(row["version"]) if row else 1
        return db.execute(
            """
            INSERT INTO template_versions (
                template_id, version_number, name, subject, preheader, html_body, plain_text_body
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                version,
                template.get("name", ""),
                template.get("subject", ""),
                template.get("preheader", ""),
                template.get("html_body", ""),
                template.get("plain_text_body", ""),
            ),
        )

    def versions(self, template_id: int) -> list[dict]:
        rows = db.fetch_all(
            "SELECT * FROM template_versions WHERE template_id = ? ORDER BY version_number DESC",
            (template_id,),
        )
        return [dict(row) for row in rows]

    def restore_version(self, version_id: int) -> int:
        version = db.fetch_one("SELECT * FROM template_versions WHERE id = ?", (version_id,))
        if not version:
            raise ValueError("Version was not found.")
        template_id = int(version["template_id"])
        self.create_version(template_id)
        db.execute(
            """
            UPDATE templates
            SET name = ?, subject = ?, preheader = ?, html_body = ?, plain_text_body = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                version["name"],
                version["subject"],
                version["preheader"],
                version["html_body"],
                version["plain_text_body"],
                template_id,
            ),
        )
        return template_id

    def increment_used(self, template_id: int) -> None:
        db.execute(
            "UPDATE templates SET times_used = times_used + 1, last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
            (template_id,),
        )

    def categories(self) -> list[str]:
        rows = db.fetch_all("SELECT DISTINCT category FROM templates WHERE COALESCE(category, '') <> '' ORDER BY category ASC")
        default = ["General", "Sales", "Follow Up", "Events", "Introductions", "Re-engagement", "Custom"]
        existing = [row["category"] for row in rows]
        return sorted(set(default + existing))

    def summary(self) -> dict[str, int]:
        rows = db.fetch_all(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN favorite = 1 THEN 1 ELSE 0 END) AS favorites,
                SUM(CASE WHEN COALESCE(status, 'Draft') = 'Draft' AND archived = 0 THEN 1 ELSE 0 END) AS drafts,
                SUM(CASE WHEN archived = 1 THEN 1 ELSE 0 END) AS archived,
                COUNT(DISTINCT COALESCE(category, 'General')) AS categories,
                SUM(CASE WHEN last_used_at IS NOT NULL THEN 1 ELSE 0 END) AS recently_used
            FROM templates
            """
        )
        row = dict(rows[0]) if rows else {}
        return {key: int(row.get(key) or 0) for key in ["total", "favorites", "drafts", "archived", "categories", "recently_used"]}

    def export_template(self, template_id: int, path: str | Path) -> None:
        template = self.get_template(template_id)
        if not template:
            raise ValueError("Template was not found.")
        payload = {
            "type": "safesend_template",
            "version": 1,
            "template": {key: template.get(key) for key in [
                "name", "subject", "preheader", "from_name", "from_email", "reply_to_email",
                "html_body", "plain_text_body", "category", "status", "tags", "favorite", "notes"
            ]},
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_template(self, path: str | Path) -> int:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        template = payload.get("template") if isinstance(payload, dict) else None
        if not isinstance(template, dict):
            raise ValueError("This file is not a SafeSend template export.")
        template["name"] = self._unique_name(template.get("name") or "Imported Template")
        return self.save_template(template, None, False)

    def html_to_text(self, html: str) -> str:
        parser = _TextExtractor()
        parser.feed(html or "")
        return parser.text()

    def text_to_html(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(f"<p>{escape(line) or '<br>'}</p>" for line in lines) or "<p></p>"

    def _unique_name(self, name: str) -> str:
        base = (name or "Untitled Template").strip()
        candidate = base
        idx = 2
        while db.fetch_one("SELECT id FROM templates WHERE name = ?", (candidate,)):
            candidate = f"{base} {idx}"
            idx += 1
        return candidate
