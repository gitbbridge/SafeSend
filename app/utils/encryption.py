from app.services.credential_service import CredentialService


def encrypt_value(value: str) -> str:
    return CredentialService().protect(value)


def decrypt_value(value: str) -> str:
    return CredentialService().unprotect(value)
