import base64
import ctypes
import os
from ctypes import wintypes


DPAPI_PREFIX = "dpapi:"
LEGACY_PREFIX = "legacy:"


class CredentialProtectionError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


class CredentialService:
    """Protects local secrets before they are stored in SQLite."""

    def protect(self, value: str) -> str:
        if not value:
            return ""
        if os.name == "nt":
            return f"{DPAPI_PREFIX}{self._protect_windows(value)}"
        return f"{LEGACY_PREFIX}{base64.urlsafe_b64encode(value.encode('utf-8')).decode('ascii')}"

    def unprotect(self, stored_value: str) -> str:
        if not stored_value:
            return ""
        if stored_value.startswith(DPAPI_PREFIX):
            return self._unprotect_windows(stored_value[len(DPAPI_PREFIX) :])
        if stored_value.startswith(LEGACY_PREFIX):
            return base64.urlsafe_b64decode(stored_value[len(LEGACY_PREFIX) :].encode("ascii")).decode("utf-8")
        return self._decode_legacy_base64(stored_value)

    def is_protected(self, stored_value: str) -> bool:
        return bool(stored_value and stored_value.startswith(DPAPI_PREFIX))

    def _protect_windows(self, value: str) -> str:
        data = value.encode("utf-8")
        in_blob = _DataBlob(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char)))
        out_blob = _DataBlob()
        crypt32 = ctypes.windll.crypt32
        if not crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            raise CredentialProtectionError("Windows DPAPI failed to protect the credential.")
        try:
            encrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return base64.urlsafe_b64encode(encrypted).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _unprotect_windows(self, value: str) -> str:
        encrypted = base64.urlsafe_b64decode(value.encode("ascii"))
        in_blob = _DataBlob(
            len(encrypted),
            ctypes.cast(ctypes.create_string_buffer(encrypted), ctypes.POINTER(ctypes.c_char)),
        )
        out_blob = _DataBlob()
        crypt32 = ctypes.windll.crypt32
        if not crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            raise CredentialProtectionError("Windows DPAPI failed to read the credential.")
        try:
            decrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return decrypted.decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _decode_legacy_base64(self, value: str) -> str:
        try:
            return base64.urlsafe_b64decode(value.encode("ascii")).decode("utf-8")
        except Exception:
            return value
