#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROGRAMA DEPOR - INSTALADOR AUTOMÁTICO
============================================================
Versión: 4.0.0 (interfaz Liquid Glass con pywebview, carpeta ui/)

Lo que instala y configura cada botón (clase ProgramManager) es el mismo
código de la versión 3.6; solo cambió la interfaz.
"""

import sys
import os
import ctypes
import winsound
import rarfile
import subprocess
import threading
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime
import socket
import time
import inspect
import json
import traceback

# Los mensajes de depuracion llevan emojis. Compilado (--windowed) la salida usa cp1252 y un
# print("🔐 ...") botaba el programa al abrirlo. Ningun print puede cerrar el programa:
import builtins
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(errors="replace")
    except Exception:
        pass
_print_original = builtins.print


def _print_seguro(*args, **kwargs):
    try:
        _print_original(*args, **kwargs)
    except Exception:
        pass


builtins.print = _print_seguro


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def carpeta_raiz_proyecto():
    """Devolver la carpeta que contiene "Programas" (la raiz del proyecto).

    Compilado: es la carpeta del .exe.
    Como script: se SUBE nivel a nivel desde el .pyw hasta encontrar una
    carpeta que contenga "Programas". Antes se subian dos niveles fijos, lo
    que se rompio al mover el fuente a "_Desarrollo\\Archivos Python": el
    programa buscaba "_Desarrollo\\Programas" y acababa pidiendo la carpeta a
    mano. Buscando hacia arriba funciona este de donde este el archivo.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)

    actual = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):                       # tope de seguridad
        if os.path.isdir(os.path.join(actual, "Programas")):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:                  # se llego a la raiz del disco
            break
        actual = padre

    # Si no se encontro, se devuelve el comportamiento historico
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))




# ===============================================
# 💻 GESTOR PRINCIPAL DE FUNCIONES - CORREGIDO
# ===============================================

# ===============================================
# 🌐 MODO SIN PENDRIVE (el .exe descargado desde la web)
# ===============================================
# Sin la carpeta "Programas" al lado, el programa guarda su log, su config y lo
# que descarga en ProgramData, y solo funcionan los botones que bajan el
# instalador del sitio oficial del fabricante.
CARPETA_DATOS_WEB = os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "DeporInstalador")

# nombre que busca el programa -> (URL oficial, nombre con que se guarda)
DESCARGAS_OFICIALES = {
    "chromesetup.exe": ("https://dl.google.com/chrome/install/latest/chrome_installer.exe", "ChromeSetup.exe"),
    "anydesk.exe": ("https://download.anydesk.com/AnyDesk.exe", "AnyDesk.exe"),
    "teamviewer.exe": ("https://download.teamviewer.com/download/TeamViewer_Setup_x64.exe", "TeamViewer.exe"),
    "googledrivesetup.exe": ("https://dl.google.com/drive-file-stream/GoogleDriveSetup.exe", "GoogleDriveSetup.exe"),
    "7zip.exe": ("https://www.7-zip.org/a/7z2409-x64.exe", "7zip.exe"),
    "winrar.exe": ("https://www.rarlab.com/rar/winrar-x64-711es.exe", "winrar.exe"),
    "forticlientvpninstaller.exe": ("https://links.fortinet.com/forticlient/win/vpnagent", "FortiClientVPNInstaller.exe"),
}


def hay_pendrive():
    """¿Está la carpeta "Programas" junto al programa?"""
    return os.path.isdir(os.path.join(carpeta_raiz_proyecto(), "Programas"))


def carpeta_datos():
    """Dónde van instalaciones.log y config.json: junto al exe, o en ProgramData si no hay pendrive."""
    if hay_pendrive():
        return carpeta_raiz_proyecto()
    os.makedirs(CARPETA_DATOS_WEB, exist_ok=True)
    return CARPETA_DATOS_WEB


def descargar_oficial(nombre, avisar=None):
    """Bajar un instalador gratuito desde el sitio oficial. Devuelve la ruta, o None si no es de los que se descargan."""
    entrada = DESCARGAS_OFICIALES.get(os.path.basename(nombre).lower())
    if not entrada:
        return None
    url, archivo = entrada
    carpeta = os.path.join(CARPETA_DATOS_WEB, "Descargas")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, archivo)
    temporal = destino + ".parcial"
    avisar = avisar or (lambda m: None)
    avisar(f"Descargando {archivo} del sitio oficial...")
    peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProgramaDepor"})
    try:
        with urllib.request.urlopen(peticion, timeout=60) as r, open(temporal, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            bajado, ultimo = 0, -1
            while True:
                bloque = r.read(1024 * 256)
                if not bloque:
                    break
                f.write(bloque)
                bajado += len(bloque)
                if total:
                    pct = bajado * 100 // total
                    if pct // 5 != ultimo:
                        ultimo = pct // 5
                        avisar(f"Descargando {archivo}... {pct}%")
        os.replace(temporal, destino)
    except Exception as e:
        try:
            os.remove(temporal)
        except OSError:
            pass
        raise Exception(f"No se pudo descargar {archivo}: {e}. Revisa la conexión a internet.")
    print(f"🌐 [DESCARGA] {url} -> {destino}")
    return destino


def registrar_instalacion(nombre, resultado, ruta_log=None):
    """Escribir en instalaciones.log cada programa ejecutado con fecha y hora"""
    try:
        if ruta_log is None:
            # Junto al exe (pendrive) o en ProgramData si se usa el exe descargado de la web
            ruta_log = os.path.join(carpeta_datos(), "instalaciones.log")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pc_name = os.environ.get("COMPUTERNAME", "PC desconocido")
        usuario = os.environ.get("USERNAME", "usuario desconocido")
        linea = f"[{timestamp}] [{pc_name}] [{usuario}] {nombre} → {resultado}\n"

        with open(ruta_log, "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"📋 [LOG] {linea.strip()}")
    except Exception as e:
        print(f"⚠️ [LOG] No se pudo escribir en el log: {e}")


class ProgramManager:
    def __init__(self, ruta_programas):
        self.ruta_programas = ruta_programas
        self._cache_rutas = {}
        self.ruta_tpv = self.resolver_ruta(os.path.join("PuntodeVenta", "1.- Instalar"))
        self.configurar_unrar()

    # ===============================================
    # 📦 HERRAMIENTA PARA DESCOMPRIMIR .RAR
    # ===============================================

    def configurar_unrar(self):
        """Localizar UnRAR/WinRAR y dejarlo configurado en rarfile.

        Antes se fijaba a mano "C:\\Program Files\\WinRAR\\UnRAR.exe". En un PC
        recien formateado (que es el caso de uso normal de esta herramienta)
        WinRAR NO esta instalado todavia, y el boton de Office fallaba con un
        "Cannot find working tool" en ingles que no le dice nada al usuario.
        Aqui se busca en varios sitios y se recuerda si no se encontro, para
        poder dar un mensaje claro en castellano.
        """
        candidatos = []

        # 1) Instalaciones normales (64 y 32 bits)
        for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
            base = os.environ.get(var)
            if base:
                candidatos.append(os.path.join(base, "WinRAR", "UnRAR.exe"))
                candidatos.append(os.path.join(base, "WinRAR", "WinRAR.exe"))

        # 2) Donde diga el registro (por si se instalo en otra unidad)
        try:
            import winreg
            for hive, clave in (
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WinRAR"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\WinRAR"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WinRAR"),
            ):
                try:
                    with winreg.OpenKey(hive, clave) as k:
                        exe, _ = winreg.QueryValueEx(k, "exe64")
                        candidatos.append(os.path.join(os.path.dirname(exe), "UnRAR.exe"))
                except OSError:
                    continue
        except Exception as e:
            print(f"⚠️ [RAR] No se pudo consultar el registro: {e}")

        # 3) Un UnRAR.exe portable junto a los programas
        candidatos.append(self.resolver_ruta("UnRAR.exe"))

        # 4) Lo que haya en el PATH
        for nombre in ("UnRAR.exe", "WinRAR.exe"):
            encontrado = shutil.which(nombre)
            if encontrado:
                candidatos.append(encontrado)

        for c in candidatos:
            if c and os.path.exists(c):
                rarfile.UNRAR_TOOL = c
                # rarfile CACHEA el resultado de buscar la herramienta. Si el
                # usuario instala WinRAR con el boton "Compresores" mientras el
                # programa esta abierto, sin este force=True seguiria fallando
                # con el resultado viejo hasta reiniciar el programa.
                try:
                    rarfile.tool_setup(force=True)
                except Exception as e:
                    print(f"⚠️ [RAR] {c} existe pero no sirve: {e}")
                    continue
                self.unrar_disponible = True
                print(f"📦 [RAR] Herramienta de descompresion: {c}")
                return c

        self.unrar_disponible = False
        print("⚠️ [RAR] No se encontró WinRAR/UnRAR en este equipo")
        return None

    def exigir_unrar(self):
        """Comprobar que se puede descomprimir, con un mensaje util si no."""
        # Se reintenta la busqueda: el usuario pudo instalar WinRAR con el
        # boton "Compresores" despues de abrir el programa.
        if not getattr(self, "unrar_disponible", False):
            self.configurar_unrar()

        if not getattr(self, "unrar_disponible", False):
            raise Exception(
                "Falta WinRAR, que es lo que descomprime los archivos .rar.\n\n"
                "Instálalo primero con el botón «Compresores» y vuelve a "
                "intentarlo."
            )

    # ===============================================
    # 🔎 RESOLUCION DE RUTAS DENTRO DE "Programas"
    # ===============================================
    # La carpeta "Programas" esta organizada en subcarpetas por categoria
    # (01 - Navegadores..., 03 - Impresoras, etc.). Estas funciones buscan
    # primero en la raiz (compatibilidad con la estructura plana anterior) y
    # si no lo encuentran hacen una busqueda recursiva por nombre.

    def resolver_ruta(self, nombre, carpeta_base=None):
        """Devolver la ruta real de un archivo/carpeta dentro de la carpeta de programas.

        Acepta nombres simples ("AnyDesk.exe") o relativos ("office 19/OInstall.exe").
        Si no existe en la raiz, busca recursivamente en las subcarpetas de categoria.
        Si no se encuentra, devuelve la ruta plana original (para que el llamador
        genere su propio mensaje de error).
        """
        base = carpeta_base or self.ruta_programas
        nombre = nombre.replace("/", os.sep).replace("\\", os.sep)
        ruta_plana = os.path.join(base, nombre)

        # 1) Estructura plana (comportamiento historico)
        if os.path.exists(ruta_plana):
            return ruta_plana

        clave = (base.lower(), nombre.lower())
        if clave in self._cache_rutas:
            return self._cache_rutas[clave]

        # 2) Busqueda recursiva: el primer segmento del nombre es lo que se busca,
        #    el resto se vuelve a unir despues de encontrarlo.
        partes = [p for p in nombre.split(os.sep) if p]
        objetivo = partes[0].lower()
        resto = os.sep.join(partes[1:])

        encontrada = None
        try:
            for dirpath, dirnames, filenames in os.walk(base):
                for item in dirnames + filenames:
                    if item.lower() == objetivo:
                        candidata = os.path.join(dirpath, item)
                        if resto:
                            candidata = os.path.join(candidata, resto)
                        if os.path.exists(candidata):
                            encontrada = candidata
                            break
                if encontrada:
                    break
        except Exception as e:
            print(f"⚠️ [RUTA] Error buscando '{nombre}': {e}")

        # ⚠️SOLO se cachea cuando se ENCONTRO. Cachear el fallo rompia los
        #   procesos que primero descomprimen y despues buscan el ejecutable
        #   (Office, FortiClient): la primera busqueda fallaba, se guardaba la
        #   ruta plana incorrecta, y despues de descomprimir se seguia
        #   devolviendo esa ruta vieja -> "OInstall.exe no encontrado".
        if encontrada:
            print(f"🔎 [RUTA] '{nombre}' resuelto en: {encontrada}")
            self._cache_rutas[clave] = encontrada
            return encontrada

        return ruta_plana


    def ejecutar_comando_admin(self, comando):
        """Ejecutar comando como administrador"""
        try:
            subprocess.run(['powershell', '-Command', f'Start-Process PowerShell -ArgumentList "{comando}" -Verb RunAs'], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "Comando ejecutado exitosamente"
        except subprocess.CalledProcessError as error:
            mensaje_error = error.stderr.decode() if error.stderr else str(error)
            raise Exception(f"Error al ejecutar comando: {mensaje_error}")
    
    def abrir_archivo(self, nombre_archivo, admin=False, carpeta_base=None, consola=False):
        """Abrir archivo ejecutable"""
        try:
            ruta_archivo = self.resolver_ruta(nombre_archivo, carpeta_base)

            if not os.path.exists(ruta_archivo):
                # Sin pendrive: los gratuitos se bajan del sitio oficial del fabricante
                descargado = descargar_oficial(nombre_archivo, getattr(self, "avisar", None))
                if descargado:
                    ruta_archivo = descargado
                elif not hay_pendrive():
                    raise FileNotFoundError(f"Archivo {nombre_archivo} no encontrado. Este programa solo está "
                                            "en el pendrive: abre el instalador desde ahí.")
                else:
                    raise FileNotFoundError(f"Archivo {nombre_archivo} no encontrado.")
            
            if admin:
                abs_path = os.path.abspath(ruta_archivo)
                subprocess.Popen(
                    ["powershell", "-Command",
                     f"Start-Process -FilePath '{abs_path}' -Verb RunAs"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif consola:
                # Para apps de consola (CMD): abrir con su propia ventana CMD
                subprocess.Popen(
                    [ruta_archivo],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Apps normales con interfaz gráfica: sin ventana CMD
                subprocess.Popen(
                    [ruta_archivo],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return f"Archivo {nombre_archivo} ejecutado correctamente"
        except Exception as e:
            raise Exception(f"No se pudo abrir {nombre_archivo}: {str(e)}")
    
    # ==================== FUNCIONES GENERALES ====================
    
    # ✅SOLUCIÓN DEFINITIVA PARA DEFENDER: Usar ejecutables directos
    # DefenderApps.exe - Excluir C:/apps automáticamente  
    # DefenderSeleccion.exe - Herramienta para selección personalizada
    # Esto elimina completamente el problema de cuelgue con QFileDialog
    
    def ejecutar_exclusion_apps(self):
        """✅DEFINITIVO: Usar ejecutable directo DefenderApps.exe"""
        print("🛡️[DEBUG] Ejecutando DefenderApps.exe para excluir C:/apps")
        return self.abrir_archivo("DefenderApps.exe")
    
    def exclusion_seleccion(self):
        """✅DEFINITIVO: Usar ejecutable directo DefenderSeleccion.exe - Sin cuelgues"""
        print("🛡️[DEBUG] Ejecutando DefenderSeleccion.exe para selección personalizada")
        return self.abrir_archivo("DefenderSeleccion.exe")

    def exclusion_seleccion_completa(self):
        """✅Excluye carpeta raíz + UAC silencioso + abre Defender para que el usuario apague el toggle"""

        # Detectar carpeta raíz del programa (padre de la carpeta "Programas")
        raiz = os.path.dirname(self.ruta_programas)

        # Salvaguarda: si "Programas" quedara en la raiz de una unidad
        # (E:\Programas, por ejemplo, al copiarlo mal a un pendrive), el padre
        # seria "E:\" y se excluiria el DISCO ENTERO de Windows Defender.
        # En ese caso se excluye solo la carpeta "Programas".
        if os.path.dirname(raiz) == raiz:      # llegamos a la raiz del disco
            print(f"⚠️ [DEFENDER] '{raiz}' es la raíz del disco: se excluye "
                  f"solo la carpeta de programas, no la unidad completa")
            raiz = self.ruta_programas
        print(f"🛡️[DEBUG] Carpeta raíz detectada: {raiz}")

        # Carpeta temporal del usuario (donde el activador descarga archivos)
        temp_activador = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "Activador")
        temp_raiz = os.environ.get("TEMP", "C:\\Temp")

        # 1. Agregar TODAS las rutas relevantes a exclusiones de Defender:
        #    - Carpeta raíz del programa
        #    - Carpeta Programas (subcarpeta)
        #    - Carpeta TEMP\Activador (donde el .bat descarga el script)
        exclusiones_cmd = (
            f"Add-MpPreference -ExclusionPath '{raiz}' -ErrorAction SilentlyContinue; "
            f"Add-MpPreference -ExclusionPath '{self.ruta_programas}' -ErrorAction SilentlyContinue; "
            f"Add-MpPreference -ExclusionPath '{temp_activador}' -ErrorAction SilentlyContinue"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", exclusiones_cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # 2. UAC: No notificarme nunca
        uac_cmd = (
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
            "-Name 'ConsentPromptBehaviorAdmin' -Value 0; "
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
            "-Name 'PromptOnSecureDesktop' -Value 0"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", uac_cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # 3. Abrir directamente la página de configuración de Defender
        #    (el usuario solo tiene que hacer click en el toggle de "Protección en tiempo real")
        subprocess.Popen(
            ["powershell", "-Command",
             "Start-Process 'windowsdefender://threatsettings/'"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        nombre_raiz = os.path.basename(raiz)
        print(f"✅[DEBUG] Exclusión agregada, UAC configurado, Defender abierto.")
        return f"Exclusión: {nombre_raiz} | UAC silencioso | Apaga el toggle en Defender"
    
    def abrir_pc_admin(self):
        subprocess.Popen('start netplwiz', shell=True)
        return "Configuración de administradores abierta"
    
    def abrir_chrome(self):
        return self.abrir_archivo("ChromeSetup.exe")
    
    def abrir_winrar(self):
        return self.abrir_archivo("winrar.exe")
    
    def copiar_crack_winrar(self):
        """Copiar archivo de licencia (crack) de WinRAR con permisos de administrador"""
        try:
            origen_crack = self.resolver_ruta(os.path.join("crack winrar", "rarreg.key"))
            destino_crack = r"C:\Program Files\WinRAR\rarreg.key"
            
            print(f"🔑 [DEBUG] Copiando crack WinRAR desde: {origen_crack}")
            print(f"🔑 [DEBUG] Destino: {destino_crack}")
            
            # Verificar que existe el archivo de origen
            if not os.path.exists(origen_crack):
                raise FileNotFoundError(f"Archivo rarreg.key no encontrado en la carpeta 'crack winrar'")
            
            # Verificar que existe la carpeta de WinRAR
            if not os.path.exists(r"C:\Program Files\WinRAR"):
                raise FileNotFoundError("WinRAR no está instalado. Instálalo primero antes de copiar el crack.")
            
            # ✅CREAR ARCHIVO .BAT TEMPORAL PARA COPIAR CON ADMIN
            bat_temporal = os.path.join(os.environ['TEMP'], 'copiar_crack_winrar.bat')
            
            with open(bat_temporal, 'w', encoding='utf-8') as bat:
                bat.write('@echo off\n')
                bat.write(f'copy /Y "{origen_crack}" "{destino_crack}"\n')
                bat.write('if %errorlevel% equ 0 (echo EXITO) else (echo ERROR)\n')
                bat.write('timeout /t 2 >nul\n')
            
            print(f"🔑 [DEBUG] Ejecutando BAT temporal con permisos admin...")
            
            # Ejecutar BAT con permisos de administrador
            subprocess.run(
                ['powershell', '-Command', f'Start-Process "{bat_temporal}" -Verb RunAs -Wait'],
                check=False,
                timeout=30
            )
            
            # Esperar un momento
            time.sleep(1)
            
            # Limpiar archivo temporal
            try:
                if os.path.exists(bat_temporal):
                    os.remove(bat_temporal)
            except:
                pass
            
            # Verificar que se copió correctamente
            if os.path.exists(destino_crack):
                size = os.path.getsize(destino_crack)
                print(f"✅[DEBUG] Crack de WinRAR copiado exitosamente: {size} bytes")
                return "Licencia de WinRAR copiada correctamente"
            else:
                raise Exception("El archivo no se copió. Verifica que diste permisos de administrador.")
                
        except subprocess.TimeoutExpired:
            raise Exception("Tiempo de espera agotado al copiar crack.")
        except FileNotFoundError as e:
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"Error al copiar crack de WinRAR: {str(e)}")
    
    def abrir_7zip(self):
        return self.abrir_archivo("7zip.exe")
    
    def abrir_anydesk(self):
        return self.abrir_archivo("AnyDesk.exe")
    
    def abrir_teamviewer(self):
        return self.abrir_archivo("TeamViewer.exe")
    
    def abrir_google_drive(self):
        return self.abrir_archivo("GoogleDriveSetup.exe")
    
    
    def abrir_inventario(self):
        return self.abrir_archivo("AgenteInventarioDepor.exe", consola=True)

    def abrir_agente_zabbix(self):
        """Instalador unico de agentes (Zabbix + GLPI) - el "Paquete Tiendas".

        Es el mismo .exe que se envia a las tiendas por AnyDesk: se
        autodescomprime en C:\\Depor\\Agentes, instala los dos agentes
        apuntando a adm.cdepor.cl y verifica que queden corriendo.
        Reemplaza al antiguo "Permisos Agente ZABBIX.bat" + los dos MSI sueltos.
        """
        return self.abrir_archivo("InstalarAgentesDepor.exe", consola=True)

    def instalar_sql_backup_master(self, progreso=None):
        """Instalar SQL Backup Master en silencio.

        Misma logica que la PARTE 3 de InstalarAgentes.bat: si ya esta
        instalado no lo reinstala, y usa /exenoui /qn. A diferencia del resto
        de instaladores, aca SI se espera a que termine, por eso el mensaje
        final puede decir "instalado" con propiedad.
        """
        def avisar(mensaje, icono="🔄"):
            print(f"💾 [SBM] {mensaje}")
            if progreso:
                progreso(mensaje, icono)

        # ---- ¿Ya esta instalado? (mismo chequeo del .bat)
        avisar("Comprobando si SQL Backup Master ya está instalado...")
        consulta = (
            "$k=@('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
            "'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*');"
            "$z=$null; foreach ($x in (Get-ItemProperty $k -EA SilentlyContinue))"
            "{ if ($x.DisplayName -like '*SQL Backup Master*') { $z=$x } };"
            "if ($z) { if ($z.DisplayVersion) { $z.DisplayVersion } else { 'INSTALADO' } } else { 'NO' }"
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", consulta],
                capture_output=True, text=True, timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW)
            version = (r.stdout or "").strip()
        except Exception as e:
            print(f"⚠️ [SBM] No se pudo consultar el registro: {e}")
            version = "NO"

        if version and version != "NO":
            avisar(f"Ya estaba instalado (versión {version})", "✅")
            return f"SQL Backup Master ya estaba instalado (versión {version})"

        # ---- Instalar en silencio
        ruta = self.resolver_ruta("sbm-setup.exe")
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                "sbm-setup.exe no encontrado en la carpeta de programas")

        avisar("Instalando SQL Backup Master en silencio (puede tardar)...")
        try:
            r = subprocess.run([ruta, "/exenoui", "/qn"], timeout=900,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            codigo = r.returncode
        except subprocess.TimeoutExpired:
            raise Exception("El instalador de SQL Backup Master no terminó en 15 minutos")

        if codigo != 0:
            raise Exception(f"El instalador terminó con código {codigo}")

        avisar("Instalado correctamente", "✅")
        return "SQL Backup Master instalado correctamente"

    def crear_tarea_reinicio_nocturno(self, progreso=None):
        """Crear la tarea programada que reinicia el equipo a las 23:00.

        Misma tarea que crea la PARTE 4 de InstalarAgentes.bat
        ('ReinicioNocturnoDepor'), para los puntos de venta.
        """
        def avisar(mensaje, icono="🔄"):
            print(f"🕚 [REINICIO] {mensaje}")
            if progreso:
                progreso(mensaje, icono)

        avisar("Programando el reinicio diario a las 23:00...")

        # El aviso al usuario lleva comillas; se arman con [char]34 para no
        # anidar comillas dentro del -Command (rompe el parseo).
        # -ErrorAction Stop es imprescindible: sin el, Register-ScheduledTask
        # lanza un error NO terminante que el try/catch no atrapa y se
        # reportaria exito sin haber creado la tarea.
        crear = (
            "try { $q = [char]34; "
            "$arg = '/r /f /t 120 /c ' + $q + 'Reinicio programado nocturno. Guarde su trabajo.' + $q; "
            "$a = New-ScheduledTaskAction -Execute 'shutdown.exe' -Argument $arg; "
            "$d = New-ScheduledTaskTrigger -Daily -At '23:00'; "
            "$p = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest; "
            "Register-ScheduledTask -TaskName 'ReinicioNocturnoDepor' -Action $a "
            "-Trigger $d -Principal $p -Force -ErrorAction Stop | Out-Null; "
            "exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", crear],
            capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW)

        if r.returncode != 0:
            detalle = (r.stdout or r.stderr or "").strip()[:120]
            raise Exception(f"No se pudo crear la tarea programada. {detalle}")

        # No basta con que no diera error: se comprueba que exista de verdad
        avisar("Verificando que la tarea quedó creada...")
        v = subprocess.run(["schtasks", "/query", "/tn", "ReinicioNocturnoDepor"],
                           capture_output=True, text=True, timeout=60,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if v.returncode != 0:
            raise Exception("La tarea no aparece en el Programador de tareas")

        avisar("Tarea creada y verificada", "✅")
        return "Reinicio nocturno programado a las 23:00 (tarea ReinicioNocturnoDepor)"

    def exportar_csv_inventario(self):
        """Ejecuta PowerShell que recopila datos del equipo y exporta CSV al escritorio"""
        comando_ps = (
            "$cs=Get-CimInstance Win32_ComputerSystem;"
            "$bios=Get-CimInstance Win32_BIOS;"
            "$csp=Get-CimInstance Win32_ComputerSystemProduct;"
            "$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1;"
            "$os=Get-CimInstance Win32_OperatingSystem;"
            "$disk=Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\";"
            "$ip=(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter \"IPEnabled=True\" "
            "| Select-Object -First 1 -ExpandProperty IPAddress "
            "| Where-Object {$_ -match \'^\\d{1,3}(\\.\\d{1,3}){3}$\'});"
            "[pscustomobject]@{"
            "Fecha=(Get-Date -Format \"yyyy-MM-dd HH:mm\");"
            "PC=$env:COMPUTERNAME;"
            "Usuario=$env:USERNAME;"
            "Fabricante=$cs.Manufacturer;"
            "Modelo=$cs.Model;"
            "SerialBIOS=$bios.SerialNumber;"
            "UUID=$csp.UUID;"
            "CPU=$cpu.Name;"
            "RAM_GB=[math]::Round($cs.TotalPhysicalMemory/1GB,2).ToString([System.Globalization.CultureInfo]::InvariantCulture);"
            "DiscoC_GB=[math]::Round($disk.Size/1GB,2).ToString([System.Globalization.CultureInfo]::InvariantCulture);"
            "Win=$os.Caption;"
            "WinBuild=$os.BuildNumber;"
            "IP=$ip"
            "} | Export-Csv -NoTypeInformation -Encoding UTF8 -Delimiter \",\" "
            "\"$env:USERPROFILE\\Desktop\\InventarioPC.csv\""
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando_ps],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Exportando datos del equipo al escritorio..."

    def abrir_numero_serie(self):
        return self.abrir_archivo("NumeroSerie.bat", consola=True)
    
    def descomprimir_office_rar(self):
        """✅MEJORADO: Descomprimir Office con reporte de progreso detallado"""
        try:
            self.exigir_unrar()
            ruta_archivo_rar = self.resolver_ruta("office.rar")

            if os.path.exists(ruta_archivo_rar):
                # Extraer en la misma carpeta donde vive el .rar (categoria de Office)
                destino_rar = os.path.dirname(ruta_archivo_rar)
                print("📦 [DEBUG] Iniciando descompresión de office.rar...")
                print(f"📦 [DEBUG] Archivo RAR: {ruta_archivo_rar}")
                print(f"📦 [DEBUG] Destino: {destino_rar}")

                with rarfile.RarFile(ruta_archivo_rar) as archivo_rar:
                    # Obtener información del archivo
                    archivos_en_rar = archivo_rar.namelist()
                    print(f"📦 [DEBUG] Archivos a extraer: {len(archivos_en_rar)}")

                    # Extraer todos los archivos
                    print("📦 [DEBUG] Extrayendo archivos de Microsoft Office...")
                    archivo_rar.extractall(destino_rar)
                    print("📦 [DEBUG] Todos los archivos extraídos correctamente")

                # Verificar que se creó la carpeta office 19
                carpeta_office = os.path.join(destino_rar, "office 19")
                if os.path.exists(carpeta_office):
                    print("✅[DEBUG] Carpeta 'office 19' creada correctamente")
                else:
                    print("⚠️ [DEBUG] Advertencia: No se encontró carpeta 'office 19'")
                
                print("✅[DEBUG] Descompresión de Office completada exitosamente")
                return "Archivos de Office descomprimidos completamente"
                
            else:
                raise Exception("Archivo office.rar no encontrado en la carpeta de programas")
                
        except Exception as e:
            print(f"❌[DEBUG] Error en descompresión de Office: {e}")
            raise Exception(f"Error al descomprimir office.rar: {str(e)}")
    
    def _tamano_carpeta(self, carpeta):
        """Bytes ocupados por una carpeta (para calcular el % de avance)"""
        total = 0
        try:
            for dirpath, _, filenames in os.walk(carpeta):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except OSError:
                        pass
        except Exception:
            pass
        return total

    def instalar_office_completo(self, progreso=None):
        """✅Descomprimir Office y abrir el instalador en un solo paso.

        Informa cada etapa en tiempo real a través de 'progreso' (mensaje, icono):
        busca el .rar, descomprime mostrando el porcentaje y abre OInstall.exe.
        Si Office ya estaba descomprimido, salta la extracción y lo dice.
        """
        def avisar(mensaje, icono="🔄"):
            print(f"📄 [OFFICE] {mensaje}")
            if progreso:
                progreso(mensaje, icono)

        ruta_instalador = self.resolver_ruta(os.path.join("office 19", "OInstall.exe"))

        # ---------- 1) Descomprimir si hace falta ----------
        if os.path.exists(ruta_instalador):
            avisar("Office ya descomprimido, abriendo instalador...", "📦")
        else:
            ruta_rar = self.resolver_ruta("office.rar")
            if not os.path.exists(ruta_rar):
                raise Exception(
                    "No se encontró office.rar ni la carpeta 'office 19' ya descomprimida")

            # En un PC recien formateado WinRAR todavia no esta instalado
            self.exigir_unrar()

            destino = os.path.dirname(ruta_rar)
            carpeta_office = os.path.join(destino, "office 19")
            avisar("Abriendo office.rar...", "📦")

            with rarfile.RarFile(ruta_rar) as archivo_rar:
                total_bytes = sum(i.file_size for i in archivo_rar.infolist()) or 1
                n_archivos = len(archivo_rar.namelist())
                avisar(f"Descomprimiendo Office ({n_archivos} archivos)...", "📦")

                # Extraer en segundo plano para poder reportar el avance real
                error_extraccion = []

                def extraer():
                    try:
                        archivo_rar.extractall(destino)
                    except Exception as e:
                        error_extraccion.append(e)

                hilo = threading.Thread(target=extraer, daemon=True)
                hilo.start()
                while hilo.is_alive():
                    hilo.join(1.0)
                    if hilo.is_alive():
                        avanzado = self._tamano_carpeta(carpeta_office)
                        pct = min(99, int(avanzado * 100 / total_bytes))
                        avisar(f"Descomprimiendo Office... {pct}%", "📦")

                if error_extraccion:
                    raise Exception(f"Error al descomprimir office.rar: {error_extraccion[0]}")

            avisar("Office descomprimido 100%, abriendo instalador...", "📦")
            # Se arma la ruta directamente desde donde se descomprimio, sin
            # volver a buscar: sabemos exactamente donde quedo.
            ruta_instalador = os.path.join(carpeta_office, "OInstall.exe")
            if not os.path.exists(ruta_instalador):
                # Respaldo por si el .rar trae otra estructura de carpetas
                encontrado = next(
                    (os.path.join(d, f)
                     for d, _, archivos in os.walk(destino)
                     for f in archivos if f.lower() == "oinstall.exe"),
                    None)
                if encontrado:
                    ruta_instalador = encontrado

        # ---------- 2) Abrir el instalador ----------
        if not os.path.exists(ruta_instalador):
            raise Exception("OInstall.exe no encontrado dentro de la carpeta 'office 19'")

        cmd_args = f'/c "{ruta_instalador}"'
        subprocess.Popen(
            ["powershell", "-Command",
             f"Start-Process -FilePath 'cmd.exe' -ArgumentList '{cmd_args}' -Verb RunAs"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        avisar("Instalador de Office abierto", "✅")
        return "Office descomprimido e instalador abierto correctamente"

    def abrir_office(self):
        """✅MEJORADO: Abrir instalador de Office con reporte claro"""
        ruta = self.resolver_ruta(os.path.join("office 19", "OInstall.exe"))

        if os.path.exists(ruta):
            print("📄 [DEBUG] Ejecutando instalador de Office...")
            cmd_args = f'/c "{ruta}"'
            subprocess.Popen(
                ["powershell", "-Command",
                 f"Start-Process -FilePath 'cmd.exe' -ArgumentList '{cmd_args}' -Verb RunAs"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("✅[DEBUG] Instalador de Office abierto exitosamente")
            return "Instalador de Office ejecutado correctamente"  # ✅Mensaje mejorado
        else:
            raise Exception("OInstall.exe no encontrado en la carpeta office 19")
    
    def abrir_quitar_basura(self, progreso=None):
        """Descargar y ejecutar el script de limpieza (necesita internet).

        Antes se lanzaba sin mirar el resultado y SIEMPRE devolvia
        "Script de limpieza ejecutado": en un PC sin internet el tecnico veia
        el tick verde aunque no se hubiera ejecutado absolutamente nada.
        """
        def avisar(mensaje, icono="🔄"):
            print(f"🧹 [LIMPIEZA] {mensaje}")
            if progreso:
                progreso(mensaje, icono)

        avisar("Comprobando conexión a internet...")
        try:
            with urllib.request.urlopen("https://git.io/debloat", timeout=15) as r:
                if r.status >= 400:
                    raise Exception(f"el servidor respondió {r.status}")
        except Exception as e:
            raise Exception(
                "No se pudo descargar el script de limpieza.\n\n"
                f"Detalle: {str(e)[:120]}\n\n"
                "Este botón necesita conexión a internet. Comprueba la red y "
                "vuelve a intentarlo."
            )

        avisar("Descargando y ejecutando el script de limpieza...")
        comando = 'iwr -useb https://git.io/debloat | iex'
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True, text=True, timeout=1800,
            creationflags=subprocess.CREATE_NO_WINDOW)

        if r.returncode != 0:
            detalle = (r.stderr or r.stdout or "").strip()[:200]
            raise Exception(f"El script de limpieza falló (código {r.returncode}). {detalle}")

        avisar("Limpieza terminada", "✅")
        return "Script de limpieza ejecutado correctamente"
    
    def verifica_activacion_windows(self):
        subprocess.run('start ms-settings:activation', shell=True)
        return "Configuración de activación abierta"
    
    def win_office(self):
        """Ejecuta WIN-OFFICE.bat con privilegios de administrador mediante PowerShell RunAs"""
        ruta_bat = self.resolver_ruta("WIN-OFFICE.bat")
        if not os.path.exists(ruta_bat):
            raise Exception(f"Archivo WIN-OFFICE.bat no encontrado en:\n{self.ruta_programas}")
        cmd_args = f'/c "{ruta_bat}"'
        subprocess.Popen(
            ["powershell", "-Command",
             f"Start-Process -FilePath 'cmd.exe' -ArgumentList '{cmd_args}' -Verb RunAs"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Script de activación iniciado"
    
    def abrir_excel(self):
        ruta = self.resolver_ruta("PERSONAL.xlsb")
        if os.path.exists(ruta):
            subprocess.run(["start", "excel", ruta], shell=True)
            return "Excel con macros abierto"
        else:
            raise Exception("PERSONAL.xlsb no encontrado")
    
    def ejecutar_excel(self):
        # consola=True es OBLIGATORIO: InstalarMacroFotos.bat termina con
        # "pause". Sin ventana, esa pausa espera una tecla que nunca puede
        # llegar y el cmd.exe queda colgado, invisible, para siempre (uno
        # nuevo por cada click). Comprobado.
        self.abrir_archivo("InstalarMacroFotos.bat", consola=True)
        return "Instalador de la macro de Excel abierto"
    
    def abrir_impresoras_oficina_cd(self):
        print("🖨️[DEBUG] Ejecutando programa único de impresoras...")
        return self.abrir_archivo("Impresoras.exe")
    
    def abrir_impresoras_hp(self):
        """Instalador de impresoras HP DeskJet USB (2774 / 2874 / 2975).

        Es un SFX de WinRAR (mismo esquema que InstalarAgentesDepor.exe): se
        autodescomprime en C:\\Depor\\ImpresorasHP y abre un menu de consola.
        Toma los instaladores oficiales de "03 - Impresoras\\Paquetes HP" (o los
        descarga de HP). Reemplaza a HPEasyStart.exe, que dejaba la impresora
        con el driver IPP generico y HP Scan sin encontrar el escaner.
        consola=True: el menu espera teclas; sin ventana quedaria colgado.
        """
        return self.abrir_archivo("InstalarImpresorasHP.exe", consola=True)
    
    def abrir_epson_boletas(self):
        return self.abrir_archivo("EpsonBoletas.exe")
    
    def abrir_transbank(self):
        return self.abrir_archivo("transbank.exe")
    
    def abrir_fotos_microsoft(self):
        """✅NUEVO: Ejecutar instalador de Fotos de Microsoft"""
        print("📸 [DEBUG] Ejecutando instalador de Fotos de Microsoft...")
        if not os.path.exists(self.resolver_ruta("Fotos de Microsoft Installer.exe")):
            # Sin pendrive: abrir la ficha de Fotos en Microsoft Store
            os.startfile("ms-windows-store://pdp/?productid=9WZDNCRFJBH4")
            return "Microsoft Store abierta en la aplicación Fotos"
        return self.abrir_archivo("Fotos de Microsoft Installer.exe")
    
    def abrir_desinstalador(self):
        """✅NUEVO: Ejecutar herramienta de desinstalación avanzada"""
        print("🗑️[DEBUG] Ejecutando Des-instalador.exe...")
        return self.abrir_archivo("Des-instalador.exe")
    
    def ejecutar_tls_smtp(self):
        """Ejecutar script TLS 1.2 + SMTP 587"""
        print("🔐 [DEBUG] Ejecutando configuración TLS 1.2 + SMTP 587...")
        return self.abrir_archivo("TLS1.2-SMTP.587.bat", admin=True)
    
    def abrir_staff(self):
        """Ejecutar programa Staff"""
        print("👥 [DEBUG] Ejecutando Staff.exe...")
        return self.abrir_archivo("staff.exe")

    # ==================== AYUDANTES .PS1 Y .REG ====================

    def ejecutar_ps1_admin(self, nombre_ps1):
        """Ejecutar un script .ps1 como administrador.

        No se puede usar abrir_archivo() porque Popen sobre un .ps1 no lo
        ejecuta: Windows lo abriria con el editor asociado.
        """
        ruta = self.resolver_ruta(nombre_ps1)
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Archivo {nombre_ps1} no encontrado.")

        abs_path = os.path.abspath(ruta)
        print(f"⚡ [DEBUG] Ejecutando script PowerShell como admin: {abs_path}")
        # ⚠️La ruta DEBE ir entre comillas dobles literales dentro del argumento:
        #   Start-Process une los elementos de -ArgumentList con espacios y NO
        #   los entrecomilla, así que sin esto una ruta con espacios (como
        #   "D:\Programa para Instalar PC nuevo\...") se parte y el .ps1 nunca corre.
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command",
             "Start-Process powershell -Verb RunAs -ArgumentList "
             f"'-NoProfile','-ExecutionPolicy','Bypass','-File','\"{abs_path}\"'"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Script {nombre_ps1} ejecutado como administrador"

    def importar_reg_admin(self, nombre_reg):
        """Importar un archivo .reg al registro de Windows (pide UAC)."""
        ruta = self.resolver_ruta(nombre_reg)
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Archivo {nombre_reg} no encontrado.")

        abs_path = os.path.abspath(ruta)
        print(f"📝 [DEBUG] Importando al registro: {abs_path}")
        # Mismo motivo que en ejecutar_ps1_admin: la ruta va entrecomillada
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command",
             f"Start-Process regedit -Verb RunAs -ArgumentList '/s','\"{abs_path}\"'"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Archivo {nombre_reg} importado al registro"

    def abrir_carpeta(self, nombre_carpeta):
        """Abrir una carpeta en el Explorador de Windows."""
        ruta = self.resolver_ruta(nombre_carpeta)
        if not os.path.isdir(ruta):
            raise Exception(f"No se encontro la carpeta '{nombre_carpeta}'")

        print(f"📂 [DEBUG] Abriendo carpeta: {ruta}")
        os.startfile(ruta)
        return f"Carpeta '{nombre_carpeta}' abierta"

    # ==================== DRIVERS Y HARDWARE ====================

    def abrir_drivers_intel(self):
        """Instalador de drivers Intel para equipos de 7a a 10a generacion"""
        print("🔌 [DEBUG] Ejecutando Drivers Intel 7-10 GEN...")
        return self.abrir_archivo("Drivers Intel 7-10 GEN.exe")

    def abrir_reiniciar_bios(self):
        """Script para reiniciar la configuracion de BIOS"""
        print("🔄 [DEBUG] Ejecutando ReiniciarBIOS.bat...")
        return self.abrir_archivo("ReiniciarBIOS.bat", admin=True)

    def abrir_antena_wifi(self):
        """Abrir la carpeta del driver de antena WiFi (trae instalador y manual)"""
        print("📶 [DEBUG] Abriendo carpeta de antena WiFi...")
        return self.abrir_carpeta("Antena WIFi Nuevos PC")

    # ==================== CONFIGURACION WINDOWS ====================

    def abrir_activar_powershell(self):
        """Habilitar la ejecucion de scripts de PowerShell"""
        print("⚡ [DEBUG] Ejecutando Activar_Powershell.ps1...")
        return self.ejecutar_ps1_admin("Activar_Powershell.ps1")

    def abrir_compartir_ltsc(self):
        """Aplicar ajustes de registro para compartir carpetas en Windows LTSC"""
        print("🔗 [DEBUG] Importando CompartirLtsc.reg...")
        return self.importar_reg_admin("CompartirLtsc.reg")

    def abrir_habilitar_tcp_smb(self):
        """Habilitar protocolos TCP/IP y SMB para red"""
        print("🌐 [DEBUG] Ejecutando HabilitarTCP_SMB.bat...")
        return self.abrir_archivo("HabilitarTCP_SMB.bat", admin=True)

    def abrir_net_framework_windows(self):
        """Instalar .NET Framework (version de la carpeta Configuracion Windows)"""
        print("🧩 [DEBUG] Ejecutando NetFramework.bat...")
        return self.abrir_archivo("NetFramework.bat", admin=True)

    # ==================== VPN ====================

    def instalar_forticlient_vpn(self):
        """Extraer FortiClient VPN del .rar y lanzar su instalador."""
        try:
            ruta_rar = self.resolver_ruta("FortiClientVPNInstaller_7.4.3.rar")
            if not os.path.exists(ruta_rar):
                # Sin pendrive: instalador oficial de Fortinet (descarga la última versión de FortiClient VPN)
                return self.abrir_archivo("FortiClientVPNInstaller.exe")

            destino = os.path.dirname(ruta_rar)
            instalador = os.path.join(destino, "FortiClientVPNInstaller_7.4.3.exe")

            # Solo extraer si el .exe todavia no esta (evita esperar de mas)
            if not os.path.exists(instalador):
                self.exigir_unrar()   # en un PC nuevo WinRAR aun no esta
                print("📦 [DEBUG] Extrayendo FortiClient VPN del .rar...")
                with rarfile.RarFile(ruta_rar) as archivo_rar:
                    archivo_rar.extractall(destino)
                print("📦 [DEBUG] Extraccion completada")
            else:
                print("📦 [DEBUG] El instalador ya estaba extraido")

            if not os.path.exists(instalador):
                raise Exception("El .rar se extrajo pero no aparecio el instalador .exe")

            return self.abrir_archivo("FortiClientVPNInstaller_7.4.3.exe")

        except Exception as e:
            print(f"❌[DEBUG] Error con FortiClient VPN: {e}")
            raise Exception(f"Error al instalar FortiClient VPN: {str(e)}")

    def crear_conexion_vpn(self):
        """Crear la conexion VPN corporativa (VPN.CDEPOR.CL)"""
        print("🔐 [DEBUG] Creando conexion VPN corporativa...")
        return self.ejecutar_ps1_admin("vpn.ps1")

    # ==================== FUNCIONES IMPRESORAS BIXOLON ====================
    
    def abrir_bixolon_srp_330ii(self):
        """Ejecutar instalador Bixolon SRP 330II"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP 330II...")
        return self.abrir_archivo("BIXOLON_SRP_330II.exe")
    
    def abrir_bixolon_srp_350iii(self):
        """Ejecutar instalador Bixolon SRP 350III"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP 350III...")
        return self.abrir_archivo("BIXOLON_SRP_350III.exe")
    
    def abrir_bixolon_srp_350plusiii(self):
        """Ejecutar instalador Bixolon SRP 350plus III"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP 350plus III...")
        return self.abrir_archivo("BIXOLON_SRP_350plusIII.exe")
    
    def abrir_bixolon_srp_e300(self):
        """Ejecutar instalador Bixolon SRP E300"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP E300...")
        return self.abrir_archivo("BIXOLON_SRP_E300.exe")
    
    def abrir_bixolon_srp_f310(self):
        """Ejecutar instalador Bixolon SRP F310"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP F310...")
        return self.abrir_archivo("BIXOLON_SRP_F310.exe")
    
    def abrir_bixolon_srp_f310ii(self):
        """Ejecutar instalador Bixolon SRP F310II"""
        print("🖨️[DEBUG] Ejecutando instalador Bixolon SRP F310II...")
        return self.abrir_archivo("BIXOLON_SRP_F310II.exe")
    
    def abrir_txpos_tx_30ii(self):
        """Ejecutar instalador TXPos TX-30-II"""
        print("🖨️[DEBUG] Ejecutando instalador TXPos TX-30-II...")
        return self.abrir_archivo("TX-30-II.exe")
        
    def abrir_barpos_t8300(self):
        """Ejecutar instalador BarposT8300"""
        print("🖨️[DEBUG] Ejecutando instalador BarposT8300...")
        return self.abrir_archivo("BarposT8300.exe")    
    # ==================== FUNCIONES TPV ====================
    
    def abrir_hana_client_32bits(self):
        ruta = os.path.join(self.ruta_tpv, "1.- Hana Client", "nt_i386", "hdbsetup.exe")
        return self.abrir_archivo("hdbsetup.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def abrir_hana_client_64bits(self):
        ruta = os.path.join(self.ruta_tpv, "1.- Hana Client", "nt_x64", "hdbsetup.exe")
        return self.abrir_archivo("hdbsetup.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def abrir_fuentes_pdf(self):
        ruta = os.path.join(self.ruta_tpv, "2.- Fuentes PDF", "IDAutomation_PDF417WindowsFontEncoder.exe")
        return self.abrir_archivo("IDAutomation_PDF417WindowsFontEncoder.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def net_frame(self):
        ruta = os.path.join(self.ruta_tpv, "3.- DotNetFX40", "InstalarNetFramework.bat")        
        return self.abrir_archivo("InstalarNetFramework.bat", admin=True, carpeta_base=os.path.dirname(ruta))
        
    
    def abrir_vcredist_x86(self):
        ruta = os.path.join(self.ruta_tpv, "4.- vcredist_x86_x64", "vcredist_x86.exe")
        return self.abrir_archivo("vcredist_x86.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def abrir_vcredist_x64(self):
        ruta = os.path.join(self.ruta_tpv, "4.- vcredist_x86_x64", "vcredist_x64.exe")
        return self.abrir_archivo("vcredist_x64.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def ejecutar_firewall(self):
        ruta = os.path.join(self.ruta_tpv, "5.- Reglas Firewall", "ReglasFirewallTPV.bat")
        if os.path.exists(ruta):
            cmd_args = f'/c "{ruta}"'
            subprocess.Popen(
                ["powershell", "-Command",
                 f"Start-Process -FilePath 'cmd.exe' -ArgumentList '{cmd_args}' -Verb RunAs"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "Reglas de firewall aplicadas"
        else:
            raise Exception("ReglasFirewallTPV.bat no encontrado")
    
    def abrir_sql_express(self):
        ruta = os.path.join(self.ruta_tpv, "5.1- SqlExpress_2017_x64", "SETUP.exe")
        return self.abrir_archivo("SETUP.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def abrir_tpv(self):
        ruta = os.path.join(self.ruta_tpv, "6.- TPV", "Install.msi")
        if os.path.exists(ruta):
            msi_path = os.path.abspath(ruta)
            subprocess.Popen(
                ["msiexec", "/i", msi_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return "Instalador TPV ejecutado"
        else:
            raise Exception("Install.msi (TPV) no encontrado")
    
    def copiar_actualizacion(self):
        try:
            origen = os.path.join(self.ruta_tpv, "7.- Actualizacion", "Actualizacion")
            destino = "C:\\sapgsp"
            if not os.path.exists(destino):
                os.makedirs(destino)
            shutil.copytree(origen, os.path.join(destino, "Actualizacion"), dirs_exist_ok=True)
            return "Actualización copiada a C:\\sapgsp"
        except Exception as e:
            raise Exception(f"Error al copiar actualización: {str(e)}")
    
    def abrir_sql_management(self):
        ruta = os.path.join(self.ruta_tpv, "8.- SQL Management", "SSMS-Setup-ENU.exe")
        return self.abrir_archivo("SSMS-Setup-ENU.exe", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def abrir_crystal_reports(self):
        ruta = os.path.join(self.ruta_tpv, "9.- Crystal Reports", "install.bat")
        return self.abrir_archivo("install.bat", admin=True, carpeta_base=os.path.dirname(ruta))
    
    def copiar_contenido_tienda(self, tienda):
        """✅SUPER CORREGIDO: Copiar reportes con verificación paso a paso de rutas"""
        try:
            # Construir ruta paso a paso para debug
            print(f"📋 [DEBUG] === COPIANDO REPORTES DE TIENDA: {tienda} ===")
            print(f"📋 [DEBUG] Ruta base programas: {self.ruta_programas}")
            
            # Paso 1: Verificar "2.- Despues de Instalado"
            carpeta_despues = self.resolver_ruta(os.path.join("PuntodeVenta", "2.- Despues de Instalado"))
            print(f"📋 [DEBUG] Paso 1 - Carpeta despues: {carpeta_despues}")
            print(f"📋 [DEBUG] Paso 1 - Existe: {os.path.exists(carpeta_despues)}")
            
            if not os.path.exists(carpeta_despues):
                # Buscar carpetas similares
                print("🔍 [DEBUG] Buscando carpetas similares...")
                contenido_base = os.listdir(self.ruta_programas)
                carpetas_candidatas = []
                for item in contenido_base:
                    if ("despues" in item.lower() or "instalado" in item.lower() or 
                        "after" in item.lower() or "post" in item.lower()):
                        carpetas_candidatas.append(item)
                        print(f"📁 [DEBUG] Candidato encontrado: {item}")
                
                if carpetas_candidatas:
                    carpeta_despues = os.path.join(self.ruta_programas, carpetas_candidatas[0])
                    print(f"📋 [DEBUG] Usando carpeta alternativa: {carpeta_despues}")
                else:
                    raise Exception(f"No se encontró carpeta 'Después de Instalado' ni similares en: {self.ruta_programas}")
            
            # Paso 2: Verificar "ReportesTiendas"
            carpeta_reportes = os.path.join(carpeta_despues, "ReportesTiendas")
            print(f"📋 [DEBUG] Paso 2 - Carpeta reportes: {carpeta_reportes}")
            print(f"📋 [DEBUG] Paso 2 - Existe: {os.path.exists(carpeta_reportes)}")
            
            if not os.path.exists(carpeta_reportes):
                # Buscar carpetas similares
                print("🔍 [DEBUG] Buscando carpetas de reportes similares...")
                contenido_despues = os.listdir(carpeta_despues)
                carpetas_reportes_candidatas = []
                for item in contenido_despues:
                    if ("reporte" in item.lower() or "tienda" in item.lower() or 
                        "report" in item.lower() or "store" in item.lower()):
                        carpetas_reportes_candidatas.append(item)
                        print(f"📁 [DEBUG] Candidato reportes: {item}")
                
                if carpetas_reportes_candidatas:
                    carpeta_reportes = os.path.join(carpeta_despues, carpetas_reportes_candidatas[0])
                    print(f"📋 [DEBUG] Usando carpeta reportes alternativa: {carpeta_reportes}")
                else:
                    raise Exception(f"No se encontró carpeta 'ReportesTiendas' ni similares en: {carpeta_despues}")
            
            # Paso 3: Verificar carpeta de tienda específica
            origen = os.path.join(carpeta_reportes, tienda)
            print(f"📋 [DEBUG] Paso 3 - Origen final: {origen}")
            print(f"📋 [DEBUG] Paso 3 - Existe: {os.path.exists(origen)}")
            
            if not os.path.exists(origen):
                # Buscar tiendas disponibles
                print("🔍 [DEBUG] Buscando tiendas disponibles...")
                tiendas_disponibles = os.listdir(carpeta_reportes)
                print(f"📋 [DEBUG] Tiendas encontradas: {tiendas_disponibles}")
                
                # Buscar nombre similar
                tienda_encontrada = None
                for tienda_disponible in tiendas_disponibles:
                    if tienda.lower() in tienda_disponible.lower() or tienda_disponible.lower() in tienda.lower():
                        tienda_encontrada = tienda_disponible
                        break
                
                if tienda_encontrada:
                    origen = os.path.join(carpeta_reportes, tienda_encontrada)
                    print(f"📋 [DEBUG] Usando tienda alternativa: {tienda_encontrada}")
                    print(f"📋 [DEBUG] Nueva ruta origen: {origen}")
                else:
                    raise Exception(f"Tienda '{tienda}' no encontrada. Tiendas disponibles: {tiendas_disponibles}")
            
            # Destino
            destino = "C:\\sapgsp\\tpv\\reports"
            print(f"📋 [DEBUG] Ruta destino: {destino}")
            
            # Verificar contenido en origen
            try:
                contenido_origen = os.listdir(origen)
                print(f"📋 [DEBUG] Archivos/carpetas en origen: {len(contenido_origen)}")
                for item in contenido_origen[:3]:
                    item_path = os.path.join(origen, item)
                    size = "DIR" if os.path.isdir(item_path) else f"{os.path.getsize(item_path)} bytes"
                    print(f"📋 [DEBUG] - {item} ({size})")
                if len(contenido_origen) > 3:
                    print(f"📋 [DEBUG] - ... y {len(contenido_origen) - 3} elementos más")
                    
                if len(contenido_origen) == 0:
                    raise Exception(f"La carpeta origen está vacía: {origen}")
                    
            except Exception as e:
                raise Exception(f"Error al acceder al contenido de origen: {str(e)}")
            
            # Crear carpeta destino si no existe
            if not os.path.exists(destino):
                print(f"📋 [DEBUG] Creando carpeta destino: {destino}")
                os.makedirs(destino)
            else:
                print(f"✅[DEBUG] Carpeta destino ya existe: {destino}")
            
            # Copiar archivos y carpetas
            archivos_copiados = 0
            carpetas_copiadas = 0
            errores = []
            
            for item in contenido_origen:
                origen_item = os.path.join(origen, item)
                destino_item = os.path.join(destino, item)
                
                try:
                    if os.path.isdir(origen_item):
                        # Es una carpeta
                        print(f"📁 [DEBUG] Copiando carpeta: {item}")
                        if os.path.exists(destino_item):
                            print(f"📁 [DEBUG] Eliminando carpeta existente: {item}")
                            shutil.rmtree(destino_item)
                        shutil.copytree(origen_item, destino_item)
                        carpetas_copiadas += 1
                        print(f"✅[DEBUG] Carpeta copiada exitosamente: {item}")
                    else:
                        # Es un archivo
                        size = os.path.getsize(origen_item)
                        print(f"📄 [DEBUG] Copiando archivo: {item} ({size} bytes)")
                        shutil.copy2(origen_item, destino_item)
                        archivos_copiados += 1
                        
                        # Verificar que se copió correctamente
                        if os.path.exists(destino_item):
                            size_copiado = os.path.getsize(destino_item)
                            print(f"✅[DEBUG] Archivo copiado: {item} ({size_copiado} bytes)")
                            if size != size_copiado:
                                print(f"⚠️ [DEBUG] Tamaño diferente: original {size} vs copiado {size_copiado}")
                        else:
                            raise Exception(f"Archivo no se copió correctamente: {item}")
                        
                except Exception as e:
                    error_msg = f"Error copiando {item}: {str(e)}"
                    print(f"❌[DEBUG] {error_msg}")
                    errores.append(error_msg)
            
            # Verificar resultados
            total_copiado = archivos_copiados + carpetas_copiadas
            print(f"📋 [DEBUG] === RESUMEN DE COPIA ===")
            print(f"✅[DEBUG] Archivos copiados: {archivos_copiados}")
            print(f"✅[DEBUG] Carpetas copiadas: {carpetas_copiadas}")
            print(f"✅[DEBUG] Total elementos: {total_copiado}")
            print(f"❌[DEBUG] Errores: {len(errores)}")
            
            if errores:
                for error in errores:
                    print(f"❌[DEBUG] - {error}")
            
            # Verificar contenido final
            try:
                contenido_destino = os.listdir(destino)
                print(f"✅[DEBUG] Elementos en destino final: {len(contenido_destino)}")
                for item in contenido_destino[:5]:
                    print(f"✅[DEBUG] - {item}")
            except Exception as e:
                print(f"⚠️ [DEBUG] No se pudo verificar contenido final: {e}")
            
            if total_copiado == 0:
                raise Exception("No se copiaron elementos. Verifique la estructura y permisos.")

            # ⚠️Si fallo aunque sea UN archivo hay que avisar en rojo. Antes se
            #   devolvia "copiados exitosamente ... (con N errores)" y la
            #   interfaz mostraba el tick verde: el tecnico se iba pensando que
            #   los reportes estaban al dia cuando faltaban varios. Es tipico
            #   que fallen si el TPV esta abierto y tiene los .rpt bloqueados.
            if errores:
                detalle = errores[0] if errores else ""
                raise Exception(
                    f"Se copiaron {total_copiado} elementos pero FALLARON {len(errores)}.\n\n"
                    f"Primero: {str(detalle)[:150]}\n\n"
                    "Suele pasar si el TPV está abierto y tiene los reportes en uso. "
                    "Ciérralo y vuelve a ejecutar este paso."
                )

            return (f"Reportes de {tienda} copiados: "
                    f"{archivos_copiados} archivos, {carpetas_copiadas} carpetas")
            
        except Exception as e:
            print(f"❌[DEBUG] === ERROR COMPLETO ===")
            print(f"❌[DEBUG] {str(e)}")
            raise Exception(f"Error al copiar reportes de {tienda}: {str(e)}")
    
    def verificar_estructura_reportes(self):
        """🔍 MEJORADA: Función de diagnóstico con verificación paso a paso"""
        print("🔍 [DIAGNÓSTICO] Verificando estructura de reportes...")
        
        # Verificar cada nivel de la ruta paso a paso
        ruta_base = self.ruta_programas
        print(f"🔍 [DIAGNÓSTICO] Ruta base programas: {ruta_base}")
        
        # Verificar "2.- Despues de Instalado"
        carpeta_despues = self.resolver_ruta(os.path.join("PuntodeVenta", "2.- Despues de Instalado"))
        print(f"🔍 [DIAGNÓSTICO] Buscando carpeta: {carpeta_despues}")
        
        if not os.path.exists(carpeta_despues):
            print("❌[DIAGNÓSTICO] La carpeta '2.- Despues de Instalado' NO EXISTE")
            
            # Buscar carpetas similares
            print("🔍 [DIAGNÓSTICO] Contenido de la carpeta de programas:")
            try:
                contenido_base = os.listdir(ruta_base)
                for item in contenido_base:
                    if "despues" in item.lower() or "instalado" in item.lower():
                        print(f"📁 [DIAGNÓSTICO] Encontrado similar: {item}")
                    else:
                        print(f"📄 [DIAGNÓSTICO] - {item}")
            except Exception as e:
                print(f"❌[DIAGNÓSTICO] Error listando contenido base: {e}")
                
            return "Carpeta '2.- Despues de Instalado' no encontrada"
        
        print("✅[DIAGNÓSTICO] Carpeta '2.- Despues de Instalado' existe")
        
        # Verificar "ReportesTiendas"
        ruta_reportes = os.path.join(carpeta_despues, "ReportesTiendas")
        print(f"🔍 [DIAGNÓSTICO] Buscando carpeta reportes: {ruta_reportes}")
        
        if not os.path.exists(ruta_reportes):
            print("❌[DIAGNÓSTICO] La carpeta 'ReportesTiendas' NO EXISTE")
            
            # Buscar carpetas similares
            print("🔍 [DIAGNÓSTICO] Contenido de '2.- Despues de Instalado':")
            try:
                contenido_despues = os.listdir(carpeta_despues)
                for item in contenido_despues:
                    if "reporte" in item.lower() or "tienda" in item.lower():
                        print(f"📁 [DIAGNÓSTICO] Encontrado similar: {item}")
                    else:
                        print(f"📄 [DIAGNÓSTICO] - {item}")
            except Exception as e:
                print(f"❌[DIAGNÓSTICO] Error listando '2.- Despues de Instalado': {e}")
                
            return "Carpeta 'ReportesTiendas' no encontrada"
        
        print("✅[DIAGNÓSTICO] Carpeta 'ReportesTiendas' existe")
        
        # Verificar tiendas disponibles
        try:
            tiendas_disponibles = os.listdir(ruta_reportes)
            print(f"🔍 [DIAGNÓSTICO] Tiendas disponibles: {tiendas_disponibles}")
            
            for tienda in tiendas_disponibles:
                ruta_tienda = os.path.join(ruta_reportes, tienda)
                if os.path.isdir(ruta_tienda):
                    try:
                        contenido = os.listdir(ruta_tienda)
                        print(f"🔍 [DIAGNÓSTICO] {tienda}: {len(contenido)} elementos")
                        for item in contenido[:5]:  # Mostrar primeros 5
                            ruta_item = os.path.join(ruta_tienda, item)
                            size = "DIR" if os.path.isdir(ruta_item) else f"{os.path.getsize(ruta_item)} bytes"
                            print(f"  📄 {item} ({size})")
                        if len(contenido) > 5:
                            print(f"  📄 ... y {len(contenido) - 5} más")
                    except Exception as e:
                        print(f"❌[DIAGNÓSTICO] {tienda}: Error accediendo - {e}")
                else:
                    print(f"📄 [DIAGNÓSTICO] {tienda}: Es archivo, no carpeta")
            
            return f"Verificación completa - {len(tiendas_disponibles)} elementos encontrados"
            
        except Exception as e:
            print(f"❌[DIAGNÓSTICO] Error listando tiendas: {e}")
            return f"Error en verificación: {str(e)}"
    
    def permisos_sapgsp(self):
        ruta_bat = self.resolver_ruta("ConfigurarPermisosSapgsp.bat")
        cmd_args = f'/c "{ruta_bat}"'
        subprocess.Popen(
            ["powershell", "-Command",
             f"Start-Process -FilePath 'cmd.exe' -ArgumentList '{cmd_args}' -Verb RunAs"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Configurador abierto como administrador"


# ===============================================
# CATÁLOGO DE BOTONES (antes eran las tarjetas Qt)
# ===============================================
# (titulo, descripcion, icono, color, id)
GENERALES = [
    ("Exclusión Windows Defender", "Excluir carpeta + desactivar Defender + UAC", "shield", "#e63946", "defender"),
    ("PC en Administradores", "Configurar usuarios administradores", "user", "#00a6c8", "admin"),
    ("Activar Windows/Office", "Herramientas de activación", "unlock", "#1f9d4c", "activacion"),
    ("Limpiar Sistema", "Script de limpieza automática", "broom", "#e67e00", "limpieza"),
    ("Google Chrome", "Instalar navegador Chrome", "globe", "#4285f4", "chrome"),
    ("Compresores", "WinRAR y 7-Zip", "archive", "#3a5a8c", "compresores"),
    ("Microsoft Office", "Descomprimir e instalar Office", "doc", "#d35400", "office"),
    ("Control Remoto", "AnyDesk y TeamViewer", "monitor", "#6c5ce7", "control_remoto"),
    ("Google Drive", "Sincronización en la nube", "cloud", "#34a853", "google_drive"),
    ("Excel Macro", "Herramientas de Excel con macros", "sheet", "#217346", "excel_macro"),
    ("Inventario", "Sistema de inventario", "clipboard", "#0f6fa8", "inventario"),
    ("Impresoras", "Configuración de impresoras", "printer", "#4b5563", "impresoras"),
    ("Fotos de Microsoft", "Instalar aplicación Fotos", "camera", "#e74c3c", "fotos_microsoft"),
    ("Des-instalador", "Eliminar programas y archivos basura", "trash", "#0891b2", "desinstalador"),
    ("VPN", "FortiClient y conexión corporativa", "lock", "#8e44ad", "vpn"),
    ("Drivers y Hardware", "Intel, antena WiFi y BIOS", "plug", "#16a085", "drivers"),
    ("Configuración Windows", "Red, PowerShell y compartir", "gear", "#5d6d7e", "config_windows"),
]

PASOS_TPV = [
    ("Hana Client", "Cliente de base de datos SAP HANA", "database", "#0891b2", "hana_client"),
    ("Fuentes PDF", "Fuentes para códigos de barras", "font", "#e67e00", "fuentes_pdf"),
    ("Net Framework", "Framework .NET requerido", "gear", "#3a5a8c", "net_framework"),
    ("Microsoft Visual C++", "Redistribuibles de Visual C++", "wrench", "#e63946", "vcredist"),
    ("Reglas Firewall", "Configurar firewall para TPV", "flame", "#1f9d4c", "firewall_direct"),
    ("SQL Express 2017", "Base de datos SQL Server Express", "database", "#34495e", "sql_express_direct"),
    ("TPV Principal", "Instalador principal del TPV", "store", "#e67e00", "tpv_direct"),
    ("Actualización", "Copiar archivos de actualización", "refresh", "#0f6fa8", "actualizacion_direct"),
    ("SQL Management", "Herramientas de gestión SQL", "tool", "#6c5ce7", "sql_management_direct"),
    ("Crystal Reports", "Motor de reportes", "chart", "#d35400", "crystal_reports_direct"),
    ("Reportes Tiendas", "Reportes específicos por tienda", "building", "#1f9d4c", "reportes_tiendas"),
    ("Permisos Carpeta", "Configurar permisos de sapgsp", "lock", "#4b5563", "permisos_direct"),
    ("Transbank (Final)", "Integración con sistema de pagos", "card", "#e63946", "transbank_direct"),
    ("TLS 1.2 + Puerto 587", "Habilitar TLS 1.2 y puerto SMTP 587", "mail", "#0891b2", "tls_smtp_direct"),
    ("Staff", "Sistema de gestión de personal", "users", "#1f9d4c", "staff_direct"),
]

# Submenús: id -> (titulo, [(texto, descripcion, id_destino)])
# Un id_destino que también está acá abre otro submenú (WinRAR, Bixolon).
SUBMENUS = {
    "compresores": ("Compresores", [
        ("WinRAR", "Opciones de WinRAR", "winrar_menu"),
        ("7-Zip", "Instalar 7-Zip", "7zip")]),
    "winrar_menu": ("WinRAR", [
        ("Instalar WinRAR", "Ejecutar instalador de WinRAR", "winrar_install"),
        ("Copiar Crack", "Copiar archivo de licencia rarreg.key", "winrar_crack")]),
    "control_remoto": ("Control Remoto", [
        ("AnyDesk", "Instalar AnyDesk", "anydesk"),
        ("TeamViewer", "Instalar TeamViewer", "teamviewer")]),
    "activacion": ("Activación", [
        ("Verificar Activación", "Ver estado de Windows", "verificar_activacion"),
        ("Activar Windows/Office", "Script de activación", "activar_windows_office")]),
    "excel_macro": ("Excel Macro", [
        ("Abrir Excel Macro", "Abrir archivo con macros", "excel_abrir"),
        ("Copiar Excel Macro", "Instalar macros", "excel_copiar")]),
    "impresoras": ("Impresoras", [
        ("Impresoras Oficina y CD", "Configurar todas las impresoras", "impresoras_oficina_cd"),
        ("Impresoras HP", "DeskJet 2774 / 2874 / 2975 por USB + escáner", "impresoras_hp"),
        ("Impresoras Epson", "Impresora de boletas", "impresoras_epson"),
        ("Impresoras Bixolon para tiendas", "Impresoras de Boletas", "impresoras_bixolon"),
        ("TXPos TX-30-II", "Impresora de Boletas", "txpos_tx30ii"),
        ("BarposT8300", "Impresora de Boletas", "barpos_t8300")]),
    "impresoras_bixolon": ("Impresoras Bixolon para Tiendas", [
        ("SRP 330II", "Instalador Bixolon SRP 330II", "bixolon_330ii"),
        ("SRP 350III", "Instalador Bixolon SRP 350III", "bixolon_350iii"),
        ("SRP 350plus III", "Instalador Bixolon SRP 350plus III", "bixolon_350plus"),
        ("SRP E300", "Instalador Bixolon SRP E300", "bixolon_e300"),
        ("SRP F310", "Instalador Bixolon SRP F310", "bixolon_f310"),
        ("SRP F310II", "Instalador Bixolon SRP F310II", "bixolon_f310ii")]),
    "inventario": ("Inventario TI", [
        ("Agente Inventario", "Sincronizar equipo al servidor", "inventario_agente"),
        ("Agentes Zabbix + GLPI", "Paquete de tiendas: instala y configura ambos agentes", "inventario_zabbix"),
        ("SQL Backup Master", "Instalar el backup de la base SQL (solo puntos de venta)", "inventario_backup"),
        ("Reinicio nocturno", "Programar el reinicio diario a las 23:00", "inventario_reinicio"),
        ("Exportar CSV", "Guardar datos del equipo en el escritorio", "inventario_csv"),
        ("Número de Serie", "Ver número de serie del equipo", "inventario_serie")]),
    "vpn": ("VPN", [
        ("Instalar FortiClient", "Extraer e instalar el cliente VPN", "vpn_forticlient"),
        ("Crear conexión VPN", "Configurar VPN.CDEPOR.CL en el equipo", "vpn_conexion")]),
    "drivers": ("Drivers y Hardware", [
        ("Drivers Intel 7-10 GEN", "Controladores para equipos Intel", "drivers_intel"),
        ("Antena WiFi", "Abrir carpeta con driver y manual", "drivers_antena_wifi"),
        ("Reiniciar BIOS", "Restablecer configuración de BIOS", "drivers_bios")]),
    "config_windows": ("Configuración Windows", [
        ("Activar PowerShell", "Permitir ejecución de scripts", "cfgwin_powershell"),
        ("Habilitar TCP/SMB", "Activar protocolos de red", "cfgwin_tcp_smb"),
        ("Compartir en LTSC", "Ajustes de registro para compartir", "cfgwin_ltsc"),
        (".NET Framework", "Instalar .NET Framework", "cfgwin_netframework"),
        ("TLS 1.2 + SMTP 587", "Configurar correo saliente", "cfgwin_tls_smtp")]),
    # Punto de venta
    "hana_client": ("Hana Client", [
        ("32 bits", "Cliente Hana para sistemas 32 bits", "hana_32"),
        ("64 bits", "Cliente Hana para sistemas 64 bits", "hana_64")]),
    "net_framework": ("Net Framework", [
        ("NetFramework 3.5 (2.0_3.0)", "Framework versiones anteriores", "net_frame_old")]),
    "vcredist": ("Microsoft Visual C++", [
        ("vcredist x86", "Redistribuible 32 bits", "vcredist_x86"),
        ("vcredist x64", "Redistribuible 64 bits", "vcredist_x64")]),
    "reportes_tiendas": ("Reportes por Tienda", [
        ("Coliseum", "Reportes específicos Coliseum", "reportes_coliseum"),
        ("Converse", "Reportes específicos Converse", "reportes_converse"),
        ("Outlet", "Reportes específicos Outlet", "reportes_outlet"),
        ("SM", "Reportes específicos SM", "reportes_sm")]),
}

# Botones de un solo clic que cambian algo importante del equipo: se confirman antes.
# Acciones que funcionan sin pendrive: bajan el instalador del sitio oficial o no necesitan archivos.
EN_LINEA = {
    "chrome", "anydesk", "teamviewer", "google_drive", "7zip", "winrar_install", "vpn_forticlient",
    "fotos_microsoft", "limpieza", "admin", "verificar_activacion", "inventario_csv", "inventario_reinicio",
    "defender_custom",
}

CONFIRMAR = {
    "defender_custom": "Excluye la carpeta del programa de Windows Defender, deja el UAC en «No notificarme nunca» "
                       "y abre Defender para que apagues la protección en tiempo real.",
    "limpieza": "Descarga de internet y ejecuta el script de limpieza (debloat) de Windows. Puede quitar aplicaciones "
                "preinstaladas y tarda varios minutos.",
    "drivers_bios": "Ejecuta el script que restablece la configuración de la BIOS.",
    "inventario_reinicio": "Crea la tarea ReinicioNocturnoDepor, que reinicia este equipo todos los días a las 23:00.",
}


def mapa_acciones(pm):
    """id -> (nombre del proceso, función, pestaña). Mismos nombres que la versión 3.6 (van al log)."""
    g, t = "generales", "tpv"
    return {
        "defender_apps": ("Exclusión Defender", pm.ejecutar_exclusion_apps, g),
        "defender_custom": ("Exclusión Defender", pm.exclusion_seleccion_completa, g),
        "admin": ("Administradores", pm.abrir_pc_admin, g),
        "limpieza": ("Limpieza Sistema", pm.abrir_quitar_basura, g),
        "chrome": ("Google Chrome", pm.abrir_chrome, g),
        "winrar_install": ("WinRAR", pm.abrir_winrar, g),
        "winrar_crack": ("Crack WinRAR", pm.copiar_crack_winrar, g),
        "7zip": ("7-Zip", pm.abrir_7zip, g),
        "office": ("Office", pm.instalar_office_completo, g),
        "anydesk": ("AnyDesk", pm.abrir_anydesk, g),
        "teamviewer": ("TeamViewer", pm.abrir_teamviewer, g),
        "google_drive": ("Google Drive", pm.abrir_google_drive, g),
        "excel_abrir": ("Excel Macro", pm.abrir_excel, g),
        "excel_copiar": ("Excel Macro", pm.ejecutar_excel, g),
        "inventario_agente": ("Agente Inventario", pm.abrir_inventario, g),
        "inventario_zabbix": ("Agentes Zabbix + GLPI", pm.abrir_agente_zabbix, g),
        "inventario_backup": ("SQL Backup Master", pm.instalar_sql_backup_master, g),
        "inventario_reinicio": ("Reinicio nocturno", pm.crear_tarea_reinicio_nocturno, g),
        "inventario_csv": ("Exportar CSV", pm.exportar_csv_inventario, g),
        "inventario_serie": ("Número de Serie", pm.abrir_numero_serie, g),
        "fotos_microsoft": ("Fotos de Microsoft", pm.abrir_fotos_microsoft, g),
        "vpn_forticlient": ("FortiClient VPN", pm.instalar_forticlient_vpn, g),
        "vpn_conexion": ("Conexión VPN", pm.crear_conexion_vpn, g),
        "drivers_intel": ("Drivers Intel", pm.abrir_drivers_intel, g),
        "drivers_antena_wifi": ("Antena WiFi", pm.abrir_antena_wifi, g),
        "drivers_bios": ("Reiniciar BIOS", pm.abrir_reiniciar_bios, g),
        "cfgwin_powershell": ("Activar PowerShell", pm.abrir_activar_powershell, g),
        "cfgwin_tcp_smb": ("TCP/SMB", pm.abrir_habilitar_tcp_smb, g),
        "cfgwin_ltsc": ("Compartir LTSC", pm.abrir_compartir_ltsc, g),
        "cfgwin_netframework": (".NET Framework", pm.abrir_net_framework_windows, g),
        "cfgwin_tls_smtp": ("TLS 1.2 + SMTP", pm.ejecutar_tls_smtp, g),
        "desinstalador": ("Des-instalador", pm.abrir_desinstalador, g),
        "verificar_activacion": ("Verificar Activación", pm.verifica_activacion_windows, g),
        "activar_windows_office": ("Activar Windows", pm.win_office, g),
        "impresoras_oficina_cd": ("Impresoras Oficina y CD", pm.abrir_impresoras_oficina_cd, g),
        "impresoras_hp": ("Impresoras HP", pm.abrir_impresoras_hp, g),
        "impresoras_epson": ("Impresoras Epson", pm.abrir_epson_boletas, g),
        "txpos_tx30ii": ("TXPos TX-30-II", pm.abrir_txpos_tx_30ii, g),
        "barpos_t8300": ("BarposT8300", pm.abrir_barpos_t8300, g),
        "bixolon_330ii": ("Bixolon SRP 330II", pm.abrir_bixolon_srp_330ii, g),
        "bixolon_350iii": ("Bixolon SRP 350III", pm.abrir_bixolon_srp_350iii, g),
        "bixolon_350plus": ("Bixolon SRP 350plus III", pm.abrir_bixolon_srp_350plusiii, g),
        "bixolon_e300": ("Bixolon SRP E300", pm.abrir_bixolon_srp_e300, g),
        "bixolon_f310": ("Bixolon SRP F310", pm.abrir_bixolon_srp_f310, g),
        "bixolon_f310ii": ("Bixolon SRP F310II", pm.abrir_bixolon_srp_f310ii, g),
        # Punto de venta
        "hana_32": ("Hana Client 32-bit", pm.abrir_hana_client_32bits, t),
        "hana_64": ("Hana Client 64-bit", pm.abrir_hana_client_64bits, t),
        "fuentes_pdf": ("Fuentes PDF", pm.abrir_fuentes_pdf, t),
        "net_frame_old": ("Net Framework 2.0/3.0", pm.net_frame, t),
        "vcredist_x86": ("Visual C++ x86", pm.abrir_vcredist_x86, t),
        "vcredist_x64": ("Visual C++ x64", pm.abrir_vcredist_x64, t),
        "firewall_direct": ("Reglas Firewall", pm.ejecutar_firewall, t),
        "sql_express_direct": ("SQL Express 2017", pm.abrir_sql_express, t),
        "tpv_direct": ("TPV Principal", pm.abrir_tpv, t),
        "actualizacion_direct": ("Actualización TPV", pm.copiar_actualizacion, t),
        "sql_management_direct": ("SQL Management", pm.abrir_sql_management, t),
        "crystal_reports_direct": ("Crystal Reports", pm.abrir_crystal_reports, t),
        "reportes_coliseum": ("Reportes Coliseum", lambda: pm.copiar_contenido_tienda("Coliseum"), t),
        "reportes_converse": ("Reportes Converse", lambda: pm.copiar_contenido_tienda("Converse"), t),
        "reportes_outlet": ("Reportes Outlet", lambda: pm.copiar_contenido_tienda("Outlet"), t),
        "reportes_sm": ("Reportes SM", lambda: pm.copiar_contenido_tienda("SM"), t),
        "permisos_direct": ("Permisos Carpeta", pm.permisos_sapgsp, t),
        "transbank_direct": ("Transbank", pm.abrir_transbank, t),
        "tls_smtp_direct": ("TLS 1.2 + SMTP", pm.ejecutar_tls_smtp, t),
        "staff_direct": ("Staff", pm.abrir_staff, t),
    }


# ===============================================
# MENSAJES CORTOS DE INICIO / FIN (mismos textos que la 3.6)
# ===============================================
def msg_inicio(nombre, pestana, fid):
    n = nombre
    if pestana == "tpv":
        for clave, texto in (("Hana", "Instalando Hana Client..."), ("Fuentes", "Instalando Fuentes PDF..."),
                             ("Framework", "Instalando .NET Framework..."), ("Visual C++", "Instalando Visual C++..."),
                             ("Firewall", "Config. Firewall..."), ("Management", "Abriendo SQL Management..."),
                             ("SQL", "Instalando SQL Express..."), ("Actualización", "Copiando actualización..."),
                             ("TPV", "Abriendo instalador TPV..."), ("Crystal", "Instalando Crystal Reports..."),
                             ("Reportes", "Copiando reportes..."), ("Permisos", "Config. permisos carpeta..."),
                             ("Transbank", "Instalando Transbank..."), ("TLS", "Configurando TLS + SMTP..."),
                             ("Staff", "Abriendo Staff...")):
            if clave in n:
                return texto
        return f"Abriendo {n}..."
    if "Office" in n:
        return "Preparando Office..."
    if "Defender" in n:
        return "Ejecutando DefenderApps..." if fid == "defender_apps" else "Aplicando exclusión + abriendo Defender..."
    for clave, texto in (("Chrome", "Instalando Chrome..."), ("Crack WinRAR", "Copiando crack..."),
                         ("WinRAR", "Instalando WinRAR..."), ("AnyDesk", "Instalando AnyDesk..."),
                         ("TeamViewer", "Instalando TeamViewer..."), ("7-Zip", "Instalando 7-Zip..."),
                         ("Google Drive", "Instalando Drive..."), ("Excel", "Configurando Excel..."),
                         ("SQL Backup", "Instalando SQL Backup Master..."), ("Reinicio", "Programando reinicio nocturno..."),
                         ("Agente Inventario", "Abriendo agente de inventario..."), ("Inventario", "Abriendo Inventario..."),
                         ("Fotos", "Instalando Fotos de Microsoft..."), ("Administradores", "Abriendo administradores..."),
                         ("Limpieza", "Limpiando sistema..."), ("Activar", "Activando..."),
                         ("Impresoras", "Config. impresoras..."), ("Des-instalador", "Abriendo des-instalador..."),
                         ("Verificar", "Verificando activación..."), ("Exportar CSV", "Exportando CSV inventario..."),
                         ("Número de Serie", "Abriendo N° de serie..."), ("TXPos", "Instalando TXPos TX-30-II..."),
                         ("Bixolon", f"Instalando {n}..."), ("BarposT8300", "Instalando BarposT8300...")):
        if clave in n:
            return texto
    return f"Abriendo {n}..."


def msg_fin(nombre, pestana, mensaje):
    """Ojo: abrir_archivo() solo LANZA el instalador (no espera), por eso dice «abierto» y no «instalado»."""
    n = nombre
    if pestana == "tpv":
        if "Reportes" in n:
            if "archivos" in mensaje.lower() and "carpetas" in mensaje.lower():
                return "Reportes copiados"
            return "Reportes procesados"
        for clave, texto in (("Hana", "Instalador de Hana Client abierto"), ("Fuentes", "Instalador de Fuentes PDF abierto"),
                             ("Framework", "Instalador de .NET Framework abierto"), ("Visual C++", "Instalador de Visual C++ abierto"),
                             ("Firewall", "Reglas de firewall aplicadas"), ("Management", "Instalador de SQL Management abierto"),
                             ("SQL", "Instalador de SQL Express abierto"), ("Actualización", "Carpeta Actualización copiada"),
                             ("TPV", "Instalador TPV abierto"), ("Permisos", "Permisos configurados"),
                             ("TLS", "TLS + SMTP OK"), ("Crystal", "Instalador de Crystal Reports abierto"),
                             ("Transbank", "Instalador de Transbank abierto"), ("Staff", "Staff abierto")):
            if clave in n:
                return texto
        return f"{n} abierto"
    for clave, texto in (("Office", "Office listo · instalador abierto"),
                         ("Defender", "Exclusión OK · Apaga el toggle en Defender"),
                         ("Crack WinRAR", "Crack copiado"), ("WinRAR", "Instalador de WinRAR abierto"),
                         ("Chrome", "Instalador de Chrome abierto"), ("AnyDesk", "Instalador de AnyDesk abierto"),
                         ("TeamViewer", "Instalador de TeamViewer abierto"), ("7-Zip", "Instalador de 7-Zip abierto"),
                         ("Google Drive", "Instalador de Drive abierto"), ("Excel", "Excel configurado"),
                         ("SQL Backup", "SQL Backup Master instalado"), ("Reinicio", "Reinicio nocturno programado (23:00)"),
                         ("Agente Inventario", "Agente de inventario abierto"), ("Agentes Zabbix", "Instalador de agentes abierto"),
                         ("Inventario", "Inventario abierto"), ("Fotos", "Instalador de Fotos abierto"),
                         ("Administradores", "Administradores abierto"), ("Limpieza", "Herramienta de limpieza abierta"),
                         ("Des-instalador", "Des-instalador abierto"), ("Activar", "Activador abierto"),
                         ("Impresoras", "Instalador de impresoras abierto"), ("Verificar", "Verificación abierta"),
                         ("Exportar CSV", "CSV exportado al escritorio"), ("Número de Serie", "N° de serie abierto"),
                         ("TXPos", "TXPos TX-30-II abierto"), ("Bixolon", f"{n} abierto"), ("BarposT8300", "BarposT8300 abierto")):
        if clave in n:
            return texto
    return f"{n} abierto"


def msg_error(nombre, pestana, error):
    if pestana == "generales":
        if "no encontrado" in error.lower():
            return f"{nombre} - No encontrado"
        if "permiso" in error.lower():
            return f"{nombre} - Sin permisos"
    return f"{nombre} - Error"


# ===============================================
# PUENTE CON LA INTERFAZ (ui/instalador.html)
# ===============================================
from depor_ui import ApiBase, Shell  # noqa: E402


def leer_config():
    try:
        ruta = os.path.join(carpeta_datos(), "config.json")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except Exception as e:
        print(f"⚠️ [CONFIG] No se pudo leer config.json: {e}")
    return {}


def guardar_config(cambios):
    try:
        ruta = os.path.join(carpeta_datos(), "config.json")
        datos = leer_config()
        datos.update(cambios)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ [CONFIG] No se pudo guardar config.json: {e}")


class Api(ApiBase):
    def __init__(self, shell):
        super().__init__(shell)
        self._pm = None
        self._acciones = {}
        self._contador = 0
        self._lock = threading.Lock()
        self._local = threading.local()      # qué proceso corre en cada hilo (para avisar descargas)
        ruta = os.path.join(carpeta_raiz_proyecto(), "Programas")
        if os.path.isdir(ruta):
            self._usar(ruta)
        else:
            # Exe descargado desde la web: sin pendrive, solo los instaladores de internet
            descargas = os.path.join(CARPETA_DATOS_WEB, "Descargas")
            os.makedirs(descargas, exist_ok=True)
            self._usar(descargas)

    def _usar(self, ruta):
        print(f"📁 [DEBUG] Carpeta de programas: {ruta}")
        self._pm = ProgramManager(ruta)
        self._pm.avisar = self._avisar_hilo
        self._acciones = mapa_acciones(self._pm)

    def _avisar_hilo(self, texto):
        pid = getattr(self._local, "pid", None)
        if pid is not None:
            self._push("onProceso", {"id": pid, "estado": "avance", "texto": texto})

    def _push(self, fn, payload):
        self._shell.push_js(fn, payload)

    def inicio(self):
        lista = lambda filas: [{"titulo": a, "desc": b, "icono": c, "color": d, "id": e} for a, b, c, d, e in filas]  # noqa: E731
        return {
            "ruta": self._pm.ruta_programas if self._pm else None,
            "generales": lista(GENERALES), "tpv": lista(PASOS_TPV),
            "submenus": {k: {"titulo": t, "opciones": [{"titulo": a, "desc": b, "id": c} for a, b, c in o]}
                         for k, (t, o) in SUBMENUS.items()},
            "confirmar": CONFIRMAR,
            "ultima_tab": int(leer_config().get("last_tab", 0) or 0),
            "pc": os.environ.get("COMPUTERNAME", ""),
            "pendrive": self._pm is not None and os.path.normcase(self._pm.ruta_programas) != os.path.normcase(
                os.path.join(CARPETA_DATOS_WEB, "Descargas")),
            "en_linea": sorted(EN_LINEA),
        }

    def guardar_tab(self, indice):
        guardar_config({"last_tab": int(indice)})

    def elegir_carpeta_programas(self):
        ruta = self.elegir_carpeta(carpeta_raiz_proyecto())
        if not ruta:
            return None
        self._usar(ruta)
        return self.inicio()

    def abrir_carpeta_programas(self):
        if self._pm:
            os.startfile(self._pm.ruta_programas)

    def historial(self):
        ruta = os.path.join(carpeta_datos(), "instalaciones.log")
        filas = []
        try:
            with open(ruta, encoding="utf-8", errors="replace") as f:
                lineas = f.read().splitlines()
        except OSError:
            lineas = []
        for linea in reversed(lineas[-300:]):
            partes = linea.split("] ", 3)
            if len(partes) == 4 and " → " in partes[3]:
                nombre, resultado = partes[3].split(" → ", 1)
                filas.append({"fecha": partes[0].lstrip("["), "pc": partes[1].lstrip("["), "usuario": partes[2].lstrip("["),
                              "nombre": nombre, "ok": resultado.startswith("OK"),
                              "resultado": resultado.split(" - ", 1)[-1]})
        return {"filas": filas, "ruta": ruta}

    def ejecutar(self, fid):
        """Lanza la acción en un hilo y avisa a la página con onProceso (inicio, avance y fin)."""
        if fid not in self._acciones:
            return {"ok": False, "error": "Acción desconocida"}
        nombre, funcion, pestana = self._acciones[fid]
        with self._lock:
            self._contador += 1
            pid = self._contador
        self._push("onProceso", {"id": pid, "estado": "inicio", "texto": msg_inicio(nombre, pestana, fid)})
        etiqueta_log = ("TPV - " + nombre) if pestana == "tpv" else nombre

        def correr():
            self._local.pid = pid
            try:
                try:
                    acepta = "progreso" in inspect.signature(funcion).parameters
                except (TypeError, ValueError):
                    acepta = False
                if acepta:
                    resultado = funcion(progreso=lambda m, i="🔄": self._push(
                        "onProceso", {"id": pid, "estado": "avance", "texto": m}))
                else:
                    resultado = funcion()
                mensaje = str(resultado) if resultado else "Operación completada"
                registrar_instalacion(etiqueta_log, "OK - " + mensaje[:80])
                try:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
                except Exception:
                    pass
                cancelado = "cancelada" in mensaje.lower() or "cancelado" in mensaje.lower()
                self._push("onProceso", {"id": pid, "estado": "aviso" if cancelado else "ok",
                                         "texto": "Cancelado" if cancelado else msg_fin(nombre, pestana, mensaje),
                                         "detalle": mensaje})
            except Exception as e:
                error = str(e)
                print(f"❌[DEBUG] Error en proceso {nombre}: {error}")
                registrar_instalacion(etiqueta_log, "ERROR - " + error[:80])
                if pestana == "generales":
                    try:
                        winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
                    except Exception:
                        pass
                self._push("onProceso", {"id": pid, "estado": "error", "texto": msg_error(nombre, pestana, error),
                                         "detalle": error})
        threading.Thread(target=correr, daemon=True).start()
        return {"ok": True, "id": pid}


# ===============================================
# ARRANQUE: permisos de administrador y WebView2
# ===============================================
def aviso_windows(titulo, texto, preguntar=False):
    """Cuadro de mensaje nativo (se usa antes de que exista la ventana). Devuelve True si se eligió «Sí»."""
    estilo = (0x04 | 0x20) if preguntar else 0x10     # MB_YESNO|MB_ICONQUESTION  o  MB_ICONERROR
    return ctypes.windll.user32.MessageBoxW(None, texto, titulo, estilo | 0x00010000) == 6


def is_admin():
    """Verificar si el programa corre con permisos de administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def elevar_admin():
    """Relanzar el programa como administrador si no tiene permisos.

    Es importante que esto NUNCA falle en silencio: todo lo que lanza el
    programa (instaladores, .bat, .ps1) hereda el token del proceso, así que
    si la ventana principal no está elevada, TODO se ejecuta sin permisos y
    los instaladores fallan de formas raras y difíciles de diagnosticar.
    """
    if is_admin():
        print("🔐 [DEBUG] El programa ya corre como administrador")
        return

    print("🔐 [DEBUG] Sin permisos admin, solicitando elevación...")
    try:
        if getattr(sys, 'frozen', False):
            resultado = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
        else:
            script = os.path.abspath(sys.argv[0])
            resultado = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
        # ShellExecuteW devuelve > 32 si logró lanzar el proceso elevado. 5 = se canceló el UAC.
        if int(resultado) > 32:
            sys.exit(0)
        motivo = ("Se canceló la ventana de permisos de Windows (UAC)."
                  if int(resultado) == 5 else f"Windows no pudo elevar el programa (código {resultado}).")
    except Exception as e:
        motivo = f"No se pudo solicitar la elevación: {e}"

    aviso_windows("Se necesitan permisos de administrador",
                  f"{motivo}\n\nEste programa instala y configura Windows, así que necesita ejecutarse como "
                  "administrador.\n\nVuelve a abrirlo y acepta la ventana de permisos, o haz clic derecho sobre el "
                  "programa y elige «Ejecutar como administrador».")
    sys.exit(1)


WEBVIEW2_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_INSTALADORES = ("MicrosoftEdgeWebView2RuntimeInstallerX64.exe", "MicrosoftEdgeWebView2RuntimeInstallerX86.exe",
                         "MicrosoftEdgeWebview2Setup.exe")


def webview2_instalado():
    """La interfaz necesita Microsoft Edge WebView2 (viene en Windows 11; en Windows 10 LTSC puede faltar)."""
    import winreg
    for hive, clave in ((winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_ID}"),
                        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_ID}"),
                        (winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_ID}")):
        try:
            with winreg.OpenKey(hive, clave) as k:
                version, _ = winreg.QueryValueEx(k, "pv")
                if version and version != "0.0.0.0":
                    return True
        except OSError:
            continue
    return False


def asegurar_webview2():
    """Si falta WebView2 se instala desde la carpeta Programas; si no está el instalador, se ofrece la versión clásica."""
    if webview2_instalado():
        return True
    raiz = carpeta_raiz_proyecto()
    instalador = None
    for dirpath, _, archivos in os.walk(os.path.join(raiz, "Programas")):
        for nombre in WEBVIEW2_INSTALADORES:
            if nombre in archivos:
                instalador = os.path.join(dirpath, nombre)
                break
        if instalador:
            break
    if instalador:
        aviso_windows("Programa Depor", "Este equipo no tiene Microsoft Edge WebView2, que necesita la interfaz.\n\n"
                      "Se instalará ahora en silencio (1 o 2 minutos). Presiona Aceptar para continuar.")
        try:
            subprocess.run([instalador, "/silent", "/install"], timeout=900)
        except Exception as e:
            print(f"⚠️ [WEBVIEW2] {e}")
        if webview2_instalado():
            return True
    clasico = os.path.join(raiz, "_Desarrollo", "Otros programas", "ProgramasV3_clasico.exe")
    texto = ("Este equipo no tiene Microsoft Edge WebView2, que necesita la interfaz del programa.\n\n"
             "Para instalarlo sin internet, deja «MicrosoftEdgeWebView2RuntimeInstallerX64.exe» dentro de la carpeta "
             "Programas (por ejemplo en «08 - Configuracion Windows») y vuelve a abrir el programa.")
    if os.path.exists(clasico):
        if aviso_windows("Programa Depor", texto + "\n\n¿Abrir ahora la versión clásica del instalador?", preguntar=True):
            subprocess.Popen([clasico])
    else:
        aviso_windows("Programa Depor", texto)
    return False


def main():
    elevar_admin()
    if not asegurar_webview2():
        sys.exit(1)
    print("🚀 Programa Depor v4.0 - interfaz Liquid Glass")
    Shell("Programa Depor - Instalador de Programas", "instalador.html", Api, min_size=(860, 580)).run()


if __name__ == "__main__":
    main()
