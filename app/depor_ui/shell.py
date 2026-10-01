"""
Ventana común de los programas Depor (pywebview + interfaz Liquid Glass en la carpeta ui/).

    from depor_ui import Shell, ApiBase

    class Api(ApiBase):
        def hola(self): return "hola"

    Shell("Mi Programa", "mi_programa.html", Api).run()

- Ventana sin marco que abre maximizada, con snap de Windows al arrastrar (ventana.py).
- ApiBase ya trae win_minimize / win_toggle_max / win_drag / win_close para la barra de título.
- shell.push_js("onAlgo", {...}) llama a window.onAlgo(...) en la página.
- shell.log(texto, tipo) y shell.progreso(valor, total, texto) alimentan el registro (#log)
  y la barra de progreso (#progreso) del kit.
- ApiBase trae además elegir_carpeta / elegir_archivos / guardar_como / mostrar_en_carpeta / abrir_ruta.
"""
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import unicodedata
import zlib

import webview

from .ventana import WindowManager

# Carpeta «Programas Depor Python» (o la del .exe empaquetado)
CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ui_path(pagina):
    return os.path.join(getattr(sys, "_MEIPASS", CARPETA), "ui", pagina)


def _slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "", t) or "Programa"


def _puerto_libre(preferido):
    """Puerto fijo por programa (así conserva sus preferencias); si está ocupado, uno libre cualquiera."""
    for puerto in (preferido, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", puerto))
                return s.getsockname()[1]
            except OSError:
                continue
    return None


class ApiBase:
    """Métodos de la barra de título. Los atributos que empiezan con «_» no se exponen a JS."""

    def __init__(self, shell):
        self._shell = shell

    def win_minimize(self):
        self._shell.window.minimize()

    def win_toggle_max(self):
        self._shell.wm.toggle_maximize()
        return self._shell.wm.state

    def win_drag(self):
        self._shell.wm.start_drag()

    def win_close(self):
        self._shell.window.destroy()

    # --- diálogos de archivo del sistema (la única pieza nativa que se mantiene) ---
    def elegir_carpeta(self, inicial=""):
        r = self._shell.window.create_file_dialog(
            webview.FileDialog.FOLDER, directory=inicial if inicial and os.path.isdir(inicial) else "")
        return (r[0] if isinstance(r, (list, tuple)) else r) if r else None

    def elegir_archivos(self, tipos=None, multiple=False, inicial=""):
        r = self._shell.window.create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=bool(multiple),
            directory=inicial if inicial and os.path.isdir(inicial) else "",
            file_types=tuple(tipos or ("Todos los archivos (*.*)",)))
        return list(r) if r else []

    def guardar_como(self, nombre="", tipos=None, inicial=""):
        r = self._shell.window.create_file_dialog(
            webview.FileDialog.SAVE, save_filename=nombre or "",
            directory=inicial if inicial and os.path.isdir(inicial) else "",
            file_types=tuple(tipos or ("Todos los archivos (*.*)",)))
        return (r[0] if isinstance(r, (list, tuple)) else r) if r else None

    def mostrar_en_carpeta(self, ruta):
        """Abre el Explorador: con el archivo seleccionado, o la carpeta misma."""
        if not ruta or not os.path.exists(ruta):
            return False
        if os.path.isdir(ruta):
            os.startfile(ruta)
        else:
            subprocess.Popen(["explorer", "/select,", os.path.normpath(ruta)])
        return True

    def abrir_ruta(self, ruta):
        if ruta and os.path.exists(ruta):
            os.startfile(ruta)
            return True
        return False


class Shell:
    def __init__(self, titulo, pagina, api_cls=ApiBase, min_size=(900, 600), on_loaded=None):
        self.titulo = titulo                # debe ser único: WindowManager busca la ventana por él
        self.pagina = pagina
        self.min_size = min_size
        self.window = None
        self.wm = WindowManager(titulo, on_state=lambda st: self.push_js("onWindowState", {"state": st}),
                                min_size=min_size)
        self.api = api_cls(self)
        self._on_loaded = on_loaded

    def push_js(self, fn, payload=None):
        try:
            self.window.evaluate_js(f"window.{fn} && window.{fn}({json.dumps(payload)})")
        except Exception:
            pass

    def log(self, texto, tipo=""):
        """Agrega una línea al registro de la página (#log). tipo: ok | error | aviso | titulo."""
        self.push_js("onLog", {"texto": str(texto), "tipo": tipo})

    def progreso(self, valor, total=100, texto=""):
        self.push_js("onProgreso", {"valor": valor, "total": total, "texto": texto})

    def _maximizar(self):
        def go():
            for _ in range(50):
                if self.wm.find_hwnd():
                    self.wm.maximize()
                    return
                time.sleep(0.1)
        threading.Thread(target=go, daemon=True).start()

    def run(self):
        self.window = webview.create_window(
            self.titulo, url=ui_path(self.pagina), js_api=self.api,
            width=1240, height=840, min_size=self.min_size,
            frameless=True, easy_drag=False, background_color="#EEF2FA")
        self.window.events.shown += self._maximizar
        if self._on_loaded:
            self.window.events.loaded += self._on_loaded
        # carpeta de datos del navegador propia de cada programa (dos programas abiertos no chocan)
        slug = _slug(self.titulo)
        storage = os.path.join(os.environ.get("LOCALAPPDATA") or CARPETA, "DeporProgramas", slug)
        # pywebview usa siempre el puerto 42001 si no se le da uno: con dos programas abiertos
        # el segundo cargaría la página del primero. Cada programa tiene su puerto.
        puerto = _puerto_libre(43000 + zlib.crc32(slug.encode()) % 2000)
        webview.start(private_mode=False, storage_path=storage, http_port=puerto)
