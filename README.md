# Programa Depor · Instalador

Instalador de programas para dejar listo un PC nuevo o un TPV de tienda (Windows 10/11).

- **Web:** https://grupo-depor-ti.github.io/programa-depor/ (con clave de acceso)
- **Descarga:** sección *Releases* → `ProgramasV3.exe`

## Cómo funciona

- **Con el pendrive** (carpeta `Programas` junto al .exe): todos los botones usan los instaladores de esa carpeta.
- **Sin pendrive** (el .exe descargado desde la web): funcionan los programas que se descargan de su sitio oficial
  (Chrome, AnyDesk, TeamViewer, Google Drive, 7-Zip, WinRAR, FortiClient VPN), Fotos desde Microsoft Store y las
  herramientas de Windows. El resto queda marcado como «Necesita el pendrive».

Los instaladores no se guardan en este repositorio.

## Estructura

| Carpeta | Contenido |
|---|---|
| `app/` | Programa (Python + pywebview, interfaz en `app/ui/`) |
| `docs/` | Página web publicada con GitHub Pages |

## Compilar

Requisitos: Python 3.12+, `pip install pywebview rarfile pyinstaller`.

Ejecutar `app\COMPILAR_ProgramasV3.bat`. El .exe pide permisos de administrador al abrirse y necesita
Microsoft Edge WebView2 (incluido en Windows 11).
