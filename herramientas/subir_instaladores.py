"""
Empaqueta la carpeta «Programas» del pendrive y la sube al Release «instaladores» del
repositorio PRIVADO Grupo-Depor-TI/programa-depor-instaladores.

- Cada archivo suelto de una categoría va como un archivo.
- Cada subcarpeta va como un .zip (el TPV, un .zip por paso).
- Genera catalogo_instaladores.json (se incluye dentro del .exe al compilar; no va al repo público).
- Se puede volver a ejecutar: lo que ya está subido con el mismo tamaño se salta.

Uso:  python subir_instaladores.py  <carpeta Programas>  <carpeta temporal>
El token se toma de Git Credential Manager (la sesión de GitHub de este PC).
"""
import hashlib
import http.client
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile

OWNER, REPO, TAG = "Grupo-Depor-TI", "programa-depor-instaladores", "instaladores"
EXCLUIR = {  # nunca se suben (rutas relativas a Programas, en minúsculas)
    "02 - office y activacion",                     # activadores de Windows/Office
    "09 - utilidades y limpieza/crack winrar",       # licencia pirata de WinRAR
    "herramientas sellout addon",                    # no lo usa el programa
}
CATALOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "catalogo_instaladores.json")


def token():
    r = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    return next(l.split("=", 1)[1] for l in r.stdout.splitlines() if l.startswith("password="))


TOKEN = token()


def api(metodo, ruta, datos=None):
    req = urllib.request.Request("https://api.github.com" + ruta, method=metodo,
                                 data=json.dumps(datos).encode() if datos is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        txt = r.read()
        return json.loads(txt) if txt else {}


def excluido(rel):
    rel = rel.replace("\\", "/").lower()
    return any(rel == e or rel.startswith(e + "/") for e in EXCLUIR)


def nombre_asset(i, rel, ext):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.splitext(os.path.basename(rel))[0]).strip("_")[:60] or "archivo"
    return f"{i:03d}-{base}{ext}"


def unidades(raiz):
    """(rel_destino, ruta_origen, tipo) — tipo 'archivo' o 'zip' (carpeta)."""
    salida = []
    pv = os.path.join("04 - Punto de Venta (TPV)", "PuntodeVenta")
    for cat in sorted(os.listdir(raiz)):
        pc = os.path.join(raiz, cat)
        if not os.path.isdir(pc) or excluido(cat):
            continue
        for item in sorted(os.listdir(pc)):
            rel = os.path.join(cat, item)
            if excluido(rel):
                continue
            ruta = os.path.join(raiz, rel)
            if os.path.isfile(ruta):
                salida.append((rel, ruta, "archivo"))
            elif rel == pv:
                # TPV: un paquete por paso para no bajar 1,5 GB de una vez
                for sub in sorted(os.listdir(ruta)):
                    rs = os.path.join(rel, sub)
                    if os.path.isfile(os.path.join(raiz, rs)):
                        salida.append((rs, os.path.join(raiz, rs), "archivo"))
                    elif sub.lower().startswith("1."):
                        for paso in sorted(os.listdir(os.path.join(raiz, rs))):
                            rp = os.path.join(rs, paso)
                            salida.append((rp, os.path.join(raiz, rp), "zip" if os.path.isdir(os.path.join(raiz, rp)) else "archivo"))
                    else:
                        salida.append((rs, os.path.join(raiz, rs), "zip"))
            else:
                salida.append((rel, ruta, "zip"))
    return salida


def armar(raiz, temporal):
    os.makedirs(temporal, exist_ok=True)
    catalogo = []
    for i, (rel, ruta, tipo) in enumerate(unidades(raiz), 1):
        rel_web = rel.replace("\\", "/")
        if tipo == "archivo":
            archivos = [rel_web]
            asset = nombre_asset(i, rel, os.path.splitext(rel)[1].lower() or ".bin")
            local = ruta
        else:
            archivos = []
            asset = nombre_asset(i, rel, ".zip")
            local = os.path.join(temporal, asset)
            if not os.path.exists(local):
                print(f"  comprimiendo {rel} ...", flush=True)
                with zipfile.ZipFile(local + ".tmp", "w", zipfile.ZIP_STORED, allowZip64=True) as z:
                    for d, _, fs in os.walk(ruta):
                        for f in fs:
                            p = os.path.join(d, f)
                            z.write(p, os.path.relpath(p, ruta))
                os.replace(local + ".tmp", local)
            for d, _, fs in os.walk(ruta):
                for f in fs:
                    archivos.append(os.path.relpath(os.path.join(d, f), raiz).replace("\\", "/"))
        catalogo.append({"asset": asset, "tipo": tipo, "destino": rel_web, "archivos": archivos,
                         "bytes": os.path.getsize(local), "_local": local})
    return catalogo


def subir(catalogo):
    rel = api("GET", f"/repos/{OWNER}/{REPO}/releases/tags/{TAG}")
    existentes = {a["name"]: a for a in rel["assets"]}
    total = sum(c["bytes"] for c in catalogo)
    hecho = sum(c["bytes"] for c in catalogo if existentes.get(c["asset"], {}).get("size") == c["bytes"])
    for c in catalogo:
        e = existentes.get(c["asset"])
        if e and e["size"] == c["bytes"] and e["state"] == "uploaded":
            continue
        if e:
            api("DELETE", f"/repos/{OWNER}/{REPO}/releases/assets/{e['id']}")
        print(f"  subiendo {c['asset']} ({c['bytes'] / 1e6:,.0f} MB) — llevamos {hecho / 1e9:.2f} de {total / 1e9:.2f} GB", flush=True)
        conn = http.client.HTTPSConnection("uploads.github.com", timeout=3600)
        q = urllib.parse.quote(c["asset"])
        with open(c["_local"], "rb") as f:
            conn.request("POST", f"/repos/{OWNER}/{REPO}/releases/{rel['id']}/assets?name={q}", body=f, headers={
                "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/octet-stream",
                "Content-Length": str(c["bytes"]), "Accept": "application/vnd.github+json"})
            resp = conn.getresponse()
            cuerpo = resp.read()
        if resp.status != 201:
            raise SystemExit(f"Falló {c['asset']}: {resp.status} {cuerpo[:200]}")
        hecho += c["bytes"]
    print(f"LISTO: {len(catalogo)} paquetes, {total / 1e9:.2f} GB", flush=True)


if __name__ == "__main__":
    raiz, temporal = sys.argv[1], sys.argv[2]
    cat = armar(raiz, temporal)
    with open(CATALOGO, "w", encoding="utf-8") as f:
        json.dump({"repo": f"{OWNER}/{REPO}", "tag": TAG,
                   "paquetes": [{k: v for k, v in c.items() if not k.startswith("_")} for c in cat]},
                  f, ensure_ascii=False, indent=1)
    print(f"catálogo: {len(cat)} paquetes -> {os.path.abspath(CATALOGO)}", flush=True)
    if "--solo-catalogo" not in sys.argv:
        subir(cat)
