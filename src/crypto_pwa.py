"""
Módulo de Criptografia AES-256-GCM para o PWA Mobile
Criptografa data/consolidado_2026_2027.json gerando web/payload.enc.json.
Compatível 100% com a WebCrypto API do navegador (PBKDF2 + AES-GCM).
"""

import os
import sys
import json
import base64
from datetime import datetime
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_regras as regras

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_JSON = os.path.join(BASE_DIR, "data", "consolidado_2026_2027.json")
OUTPUT_ENC = os.path.join(BASE_DIR, "web", "payload.enc.json")


def derivar_chave(pin: str, salt: bytes) -> bytes:
    """Deriva chave AES de 256 bits a partir do PIN usando PBKDF2-HMAC-SHA256 (100.000 iterações)."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(pin.encode("utf-8"))


def criptografar_payload(pin: str = None) -> dict:
    """Lê o consolidado JSON, criptografa com AES-256-GCM e salva em web/payload.enc.json."""
    pin = pin or regras.CASA_PIN
    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError(f"Arquivo {INPUT_JSON} não encontrado. Execute o extrator_unificado.py primeiro.")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data_str = f.read()

    data_bytes = data_str.encode("utf-8")
    salt = os.urandom(16)
    iv = os.urandom(12)  # 96 bits recomendado para AES-GCM

    key = derivar_chave(pin, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data_bytes, None)

    payload = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "updated_at": datetime.now().isoformat(),
        "size_bytes": len(data_bytes),
    }

    os.makedirs(os.path.dirname(OUTPUT_ENC), exist_ok=True)
    with open(OUTPUT_ENC, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Criptografia AES-256-GCM concluída com sucesso!")
    print(f"Salvo em: {OUTPUT_ENC} ({os.path.getsize(OUTPUT_ENC)} bytes)")
    return payload


def descriptografar_payload(payload_dict: dict, pin: str = None) -> dict:
    """Descriptografa o payload (para testes e validações automatizadas)."""
    pin = pin or regras.CASA_PIN
    salt = base64.b64decode(payload_dict["salt"])
    iv = base64.b64decode(payload_dict["iv"])
    ciphertext = base64.b64decode(payload_dict["ciphertext"])

    key = derivar_chave(pin, salt)
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(iv, ciphertext, None)
    return json.loads(decrypted_bytes.decode("utf-8"))


if __name__ == "__main__":
    payload = criptografar_payload()
    # Teste de integridade imediato
    dec = descriptografar_payload(payload)
    print(f"Validação de decifragem com PIN: OK! Meses: {dec['metadata']['meses_analisados']}")
