"""
Cifra el permiso de lectura (token de GitHub de solo lectura del repositorio privado de
instaladores) con la clave de la página web, y lo deja en app/acceso_instaladores.json.

Ese archivo va DENTRO del .exe al compilar, pero NO al repositorio público (.gitignore).
El programa lo descifra cuando el técnico escribe la clave la primera vez en cada PC.

Uso:  python crear_acceso.py <archivo con el token> [--borrar-token]
      (pide la clave de la web sin mostrarla)
"""
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys

ITERACIONES = 600_000
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "acceso_instaladores.json")


def flujo(clave, nonce, largo):
    salida, i = b"", 0
    while len(salida) < largo:
        salida += hashlib.sha256(clave + nonce + i.to_bytes(4, "big")).digest()
        i += 1
    return salida[:largo]


def cifrar(token, clave_web):
    sal, nonce = secrets.token_bytes(16), secrets.token_bytes(16)
    llave = hashlib.pbkdf2_hmac("sha256", clave_web.encode("utf-8"), sal, ITERACIONES, 64)
    datos = token.encode("utf-8")
    cifrado = bytes(a ^ b for a, b in zip(datos, flujo(llave[:32], nonce, len(datos))))
    return {"version": 1, "sal": sal.hex(), "iter": ITERACIONES, "nonce": nonce.hex(), "cifrado": cifrado.hex(),
            "firma": hmac.new(llave[32:], nonce + cifrado, "sha256").hexdigest()}


if __name__ == "__main__":
    archivo_token = sys.argv[1]
    token = open(archivo_token, encoding="utf-8").read().strip()
    if not token.startswith(("github_pat_", "ghp_")):
        raise SystemExit("El archivo no parece tener un token de GitHub.")
    clave = os.environ.get("CLAVE_WEB") or getpass.getpass("Clave de la página web: ")
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump(cifrar(token, clave), f, indent=1)
    print("Permiso cifrado en", os.path.abspath(DESTINO))
    if "--borrar-token" in sys.argv:
        os.remove(archivo_token)
        print("Archivo del token borrado.")
