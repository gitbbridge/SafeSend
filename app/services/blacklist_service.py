import socket
from datetime import datetime
from typing import Callable

from app.database import db

BLACKLIST_ZONES = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "b.barracudacentral.org",
    "dnsbl.sorbs.net",
    "psbl.surriel.com",
    "cbl.abuseat.org",
    "dnsbl-1.uceprotect.net",
]


class BlacklistService:
    def check_profile(self, profile_id: int, progress_callback: Callable[[int, int, str], None] | None = None) -> dict:
        profile = db.fetch_one("SELECT id, host, resolved_ip FROM smtp_profiles WHERE id = ?", (profile_id,))
        if not profile:
            raise ValueError("SMTP profile was not found.")
        resolved = self.resolve_host(profile["host"])
        ip = resolved.get("resolved_ip") or profile["resolved_ip"] or ""
        if not ip:
            raise ValueError("Could not resolve SMTP host to an IP address.")
        results = self.check_ip(ip, progress_callback=progress_callback)
        self.store_results(profile_id, results)
        db.execute(
            """
            UPDATE smtp_profiles
            SET resolved_ip = ?, resolved_hostname = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ip, resolved.get("resolved_hostname", ""), profile_id),
        )
        listed_count = sum(1 for item in results if item["listed"])
        return {
            "ip": ip,
            "hostname": resolved.get("resolved_hostname", ""),
            "listed_count": listed_count,
            "clean_count": len(results) - listed_count,
            "results": results,
        }

    def resolve_host(self, host: str) -> dict:
        result = {"resolved_ip": "", "resolved_hostname": ""}
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
            if infos:
                result["resolved_ip"] = infos[0][4][0]
        except OSError:
            return result
        if result["resolved_ip"]:
            try:
                result["resolved_hostname"] = socket.gethostbyaddr(result["resolved_ip"])[0]
            except OSError:
                result["resolved_hostname"] = socket.getfqdn(host)
        return result

    def check_ip(self, ip: str, progress_callback: Callable[[int, int, str], None] | None = None) -> list[dict]:
        reversed_ip = self.reverse_ip(ip)
        checked_at = datetime.now().isoformat(timespec="seconds")
        results = []
        total = len(BLACKLIST_ZONES)
        for index, zone in enumerate(BLACKLIST_ZONES, start=1):
            if progress_callback:
                progress_callback(index, total, zone)
            query = f"{reversed_ip}.{zone}"
            result = {
                "zone": zone,
                "query": query,
                "listed": False,
                "response": "",
                "error_message": "",
                "checked_at": checked_at,
            }
            try:
                result["response"] = socket.gethostbyname(query)
                result["listed"] = True
            except socket.gaierror:
                result["listed"] = False
            except OSError as exc:
                result["error_message"] = str(exc) or exc.__class__.__name__
            results.append(result)
        return results

    def reverse_ip(self, ip: str) -> str:
        parts = ip.split(".")
        if len(parts) != 4 or not all(part.isdigit() for part in parts):
            raise ValueError("DNSBL checks currently require an IPv4 address.")
        return ".".join(reversed(parts))

    def store_results(self, profile_id: int, results: list[dict]) -> None:
        db.execute("DELETE FROM smtp_blacklist_checks WHERE smtp_profile_id = ?", (profile_id,))
        for item in results:
            db.execute(
                """
                INSERT INTO smtp_blacklist_checks (
                    smtp_profile_id, zone, query, listed, response, error_message, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    item["zone"],
                    item["query"],
                    1 if item["listed"] else 0,
                    item.get("response", ""),
                    item.get("error_message", ""),
                    item["checked_at"],
                ),
            )
