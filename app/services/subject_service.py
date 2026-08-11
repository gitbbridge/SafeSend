import random

from app.database import db


class SubjectService:
    def list_subjects(self, template_id: int | None = None) -> list[dict]:
        if template_id:
            rows = db.fetch_all("SELECT * FROM subjects WHERE template_id = ? ORDER BY is_preferred DESC, updated_at DESC", (template_id,))
        else:
            rows = db.fetch_all("SELECT * FROM subjects ORDER BY updated_at DESC")
        return [dict(row) for row in rows]

    def save_subject(self, subject: str, template_id: int | None = None, label: str = "", ab_group: str = "", preferred: bool = False, subject_id: int | None = None) -> int:
        subject = subject.strip()
        if not subject:
            raise ValueError("Subject line is required.")
        if preferred and template_id:
            db.execute("UPDATE subjects SET is_preferred = 0 WHERE template_id = ?", (template_id,))
        if subject_id:
            db.execute(
                """
                UPDATE subjects
                SET subject = ?, label = ?, ab_group = ?, is_preferred = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (subject, label.strip(), ab_group.strip(), 1 if preferred else 0, subject_id),
            )
            return subject_id
        return db.execute(
            "INSERT INTO subjects (template_id, subject, label, ab_group, is_preferred) VALUES (?, ?, ?, ?, ?)",
            (template_id, subject, label.strip(), ab_group.strip(), 1 if preferred else 0),
        )

    def duplicate_subject(self, subject_id: int) -> int:
        row = db.fetch_one("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        if not row:
            raise ValueError("Subject was not found.")
        return self.save_subject(
            f"{row['subject']} Copy",
            row["template_id"],
            row["label"] or "",
            row["ab_group"] or "",
            False,
        )

    def delete_subject(self, subject_id: int) -> None:
        db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def random_subject(self, template_id: int | None = None) -> str:
        subjects = self.list_subjects(template_id)
        return random.choice(subjects)["subject"] if subjects else ""
