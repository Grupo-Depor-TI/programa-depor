"""
Comportamiento de ventana nativo de Windows para una ventana pywebview sin marco (frameless).

- Maximizar ocupando el área de trabajo (respeta la barra de tareas).
- Arrastrar desde la barra de título propia:
    · soltar arriba del monitor      → maximizar (Aero Snap)
    · soltar en el borde izq./der.   → media pantalla
    · arrastrar estando maximizada   → se restaura bajo el cursor y sigue el arrastre
- Doble clic en la barra de título   → maximizar / restaurar
"""
import ctypes
import os
import threading
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

VK_LBUTTON = 0x01
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
MONITOR_DEFAULTTONEAREST = 2
DRAG_THRESHOLD = 6
EDGE = 2  # píxeles desde el borde del monitor que activan el snap

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
user32.MonitorFromPoint.restype = wintypes.HMONITOR
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromWindow.restype = wintypes.HMONITOR
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]


def _rect_tuple(r):
    return r.left, r.top, r.right - r.left, r.bottom - r.top


class WindowManager:
    def __init__(self, title, on_state=None, min_size=(720, 560)):
        self.title = title
        self.on_state = on_state or (lambda state: None)
        self.min_w, self.min_h = min_size
        self.hwnd = None
        self.state = "normal"          # normal | maximized | snapped
        self.normal_rect = None        # (x, y, w, h) para restaurar
        self._drag_lock = threading.Lock()

    # ─────────── utilidades Win32 ───────────
    def find_hwnd(self):
        if self.hwnd and user32.IsWindow(self.hwnd):
            return self.hwnd
        pid = os.getpid()
        found = []

        def cb(hwnd, _):
            p = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid:
                title = ctypes.create_unicode_buffer(256)
                cls = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, title, 256)
                user32.GetClassNameW(hwnd, cls, 256)
                if title.value == self.title and cls.value.startswith("WindowsForms"):
                    found.append(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(cb), 0)
        self.hwnd = found[0] if found else None
        return self.hwnd

    def rect(self):
        r = wintypes.RECT()
        user32.GetWindowRect(self.find_hwnd(), ctypes.byref(r))
        return _rect_tuple(r)

    @staticmethod
    def cursor():
        p = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(p))
        return p.x, p.y

    @staticmethod
    def _monitor_info(hmon):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
        return _rect_tuple(mi.rcMonitor), _rect_tuple(mi.rcWork)

    def monitor_at(self, x, y):
        return self._monitor_info(user32.MonitorFromPoint(wintypes.POINT(x, y), MONITOR_DEFAULTTONEAREST))

    def monitor_of_window(self):
        return self._monitor_info(user32.MonitorFromWindow(self.find_hwnd(), MONITOR_DEFAULTTONEAREST))

    def set_rect(self, x, y, w, h):
        user32.SetWindowPos(self.find_hwnd(), None, int(x), int(y), int(w), int(h), SWP_NOZORDER | SWP_SHOWWINDOW)

    def _set_state(self, state):
        self.state = state
        self.on_state(state)

    # ─────────── acciones ───────────
    def maximize(self, work=None):
        if not self.find_hwnd():
            return
        if self.state == "normal" and work is None:
            self.normal_rect = self.rect()
        work = work or self.monitor_of_window()[1]
        self.set_rect(*work)
        self._set_state("maximized")

    def restore(self):
        if not self.find_hwnd():
            return
        if self.normal_rect:
            x, y, w, h = self.normal_rect
            work = self.monitor_of_window()[1]
            # si el tamaño normal era casi del área de trabajo, dejar una ventana centrada razonable
            if w >= work[2] - 8 and h >= work[3] - 8:
                w, h = max(self.min_w, int(work[2] * 0.78)), max(self.min_h, int(work[3] * 0.82))
                x, y = work[0] + (work[2] - w) // 2, work[1] + (work[3] - h) // 2
            # mantener la ventana dentro del área de trabajo
            w, h = min(w, work[2]), min(h, work[3])
            x = min(max(x, work[0]), work[0] + work[2] - w)
            y = min(max(y, work[1]), work[1] + work[3] - h)
            self.set_rect(x, y, w, h)
        self._set_state("normal")

    def toggle_maximize(self):
        if self.state == "normal":
            self.maximize()
        else:
            self.restore()

    def snap(self, side, work):
        if self.state == "normal" and self.normal_rect is None:
            self.normal_rect = self.rect()
        half = work[2] // 2
        x = work[0] if side == "left" else work[0] + work[2] - half
        self.set_rect(x, work[1], half, work[3])
        self._set_state("snapped")

    def reapply(self):
        """Vuelve a ajustar la ventana al área de trabajo (tras mostrarla desde la bandeja)."""
        if self.state == "maximized":
            self.set_rect(*self.monitor_of_window()[1])

    # ─────────── arrastre ───────────
    def start_drag(self):
        """Llamar al presionar el botón izquierdo en la barra de título. Sigue al cursor hasta soltar."""
        if not self.find_hwnd() or not self._drag_lock.acquire(blocking=False):
            return
        threading.Thread(target=self._drag_loop, daemon=True).start()

    def _drag_loop(self):
        try:
            sx, sy = self.cursor()
            left, top, w, h = self.rect()
            if self.state == "normal":
                self.normal_rect = (left, top, w, h)  # tamaño/posición a recordar si termina en snap
            moved = False
            while user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000:
                cx, cy = self.cursor()
                if not moved:
                    if abs(cx - sx) + abs(cy - sy) < DRAG_THRESHOLD:
                        time.sleep(0.01)
                        continue
                    moved = True
                    if self.state != "normal" and self.normal_rect:
                        # restaurar bajo el cursor manteniendo la proporción horizontal del agarre
                        _, _, nw, nh = self.normal_rect
                        ratio = (sx - left) / max(1, w)
                        offset_y = sy - top
                        left, top, w, h = cx - int(nw * ratio), cy - offset_y, nw, nh
                        self.set_rect(left, top, w, h)
                        sx, sy = cx, cy
                        self._set_state("normal")
                        continue
                user32.SetWindowPos(self.hwnd, None, left + (cx - sx), top + (cy - sy), 0, 0,
                                    SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
                time.sleep(0.008)

            if moved:
                cx, cy = self.cursor()
                monitor, work = self.monitor_at(cx, cy)
                if cy <= monitor[1] + EDGE:
                    self.maximize(work)
                elif cx <= monitor[0] + EDGE:
                    self.snap("left", work)
                elif cx >= monitor[0] + monitor[2] - 1 - EDGE:
                    self.snap("right", work)
                elif self.state == "normal":
                    self.normal_rect = self.rect()
        finally:
            self._drag_lock.release()
