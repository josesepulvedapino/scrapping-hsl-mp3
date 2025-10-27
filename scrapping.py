import requests
import sys
import subprocess
import os

# -----------------------------------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------------------------------

# Simula ser un navegador. El 'Referer' es crucial para que el servidor
# acepte la petición, como descubrimos en el análisis.
HEADERS = {
    'Referer': 'https://sesiones.senado.cl/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36'
}

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------

def parsear_manifiesto(texto_manifiesto):
    """
    Parsea el manifiesto JSON personalizado.
    Busca la llave 'files:' y extrae todas las URLs .ts siguientes.
    """
    urls_ts = []
    encontrado_files = False
    for linea in texto_manifiesto.splitlines():
        if 'files:' in linea:
            encontrado_files = True
            continue  # Salta la línea "files:" y procesa las siguientes
        
        # Si estamos en la sección "files" y la línea es una URL
        if encontrado_files and linea.strip().startswith('https://'):
            urls_ts.append(linea.strip())
            
    return urls_ts

def ejecutar_comando_ffmpeg(comando):
    """
    Ejecuta un comando de FFMPEG (subprocess).
    Maneja errores y oculta la salida estándar para una consola limpia.
    """
    try:
        # stdout=subprocess.DEVNULL oculta la salida exitosa (limpia)
        # stderr=subprocess.PIPE captura los errores para mostrarlos
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        # Si FFMPEG falla, muestra el error
        print("\n--- Error de FFMPEG ---")
        print(e.stderr.decode())
        print("------------------------")
        return False
    except FileNotFoundError:
        # Si FFMPEG no está instalado
        print("\nError: 'ffmpeg' no encontrado.")
        print("Asegúrese de que FFMPEG esté instalado y en el PATH del sistema.")
        return False
    return True

def limpiar_archivos(archivos):
    """Elimina una lista de archivos temporales, ignorando errores."""
    for archivo in archivos:
        try:
            os.remove(archivo)
        except OSError:
            pass # No importa si el archivo no existe

# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------------------------------------------------------

def main(manifest_url):
    
    archivos_temporales = []
    
    try:
        # --- PASO 1: Obtener y Parsear el Manifiesto JSON ---
        print(f"[Paso 1] Obteniendo manifiesto... (usando {manifest_url[:50]}...)")
        r = requests.get(manifest_url, headers=HEADERS, timeout=10)
        r.raise_for_status() # Lanza error si la petición falla (ej: 403)
        
        urls_ts = parsear_manifiesto(r.text)
        if not urls_ts:
            print("Error: No se pudo parsear el manifiesto o no se encontró 'files:'.")
            return
            
        print(f"Manifiesto parseado. {len(urls_ts)} segmentos encontrados.")

        # --- PASO 2: Descargar todos los segmentos .ts ---
        print(f"[Paso 2] Descargando {len(urls_ts)} segmentos .ts...")
        nombres_archivos_ts = []
        for i, url in enumerate(urls_ts):
            nombre_archivo = f"seg_{i:05d}.ts"
            nombres_archivos_ts.append(nombre_archivo)
            
            r_seg = requests.get(url, headers=HEADERS, timeout=10)
            r_seg.raise_for_status()
            with open(nombre_archivo, 'wb') as f:
                f.write(r_seg.content)
            print(f"Descargado {nombre_archivo}", end='\r')
        
        archivos_temporales.extend(nombres_archivos_ts)
        print("\nDescarga de segmentos completa.")

        # --- PASO 3: Crear lista.txt para FFMPEG ---
        print("[Paso 3] Creando 'lista.txt' para FFMPEG...")
        nombre_lista = 'lista.txt'
        archivos_temporales.append(nombre_lista)
        with open(nombre_lista, 'w') as f:
            for nombre in nombres_archivos_ts:
                f.write(f"file '{nombre}'\n")

        # --- PASO 4: Unir segmentos (FFMPEG Concat) ---
        print("[Paso 4] Uniendo segmentos en 'video_completo.mp4'...")
        output_mp4 = 'video_completo.mp4'
        archivos_temporales.append(output_mp4)
        cmd_concat = [
            'ffmpeg',
            '-f', 'concat',    # Formato de entrada: concatenar
            '-safe', '0',      # Permite rutas de archivo
            '-i', nombre_lista,
            '-c', 'copy',      # Copia streams (rápido), no re-codifica
            output_mp4
        ]
        if not ejecutar_comando_ffmpeg(cmd_concat):
            raise Exception("Fallo al concatenar video.")

        # --- PASO 5: Convertir a MP3 (FFMPEG Extract) ---
        print("[Paso 5] Extrayendo audio a 'audio_final.mp3'...")
        output_mp3 = 'audio_final.mp3'
        cmd_mp3 = [
            'ffmpeg',
            '-i', output_mp4,
            '-vn',             # 'No Video' - ignora el stream de video
            '-q:a', '0',       # Máxima calidad de audio VBR
            output_mp3
        ]
        if not ejecutar_comando_ffmpeg(cmd_mp3):
            raise Exception("Fallo al convertir a MP3.")
        
        print("\n--- ¡PROCESO COMPLETADO! ---")
        print(f"Archivo '{output_mp3}' generado exitosamente.")

    except requests.RequestException as e:
        print(f"\nError de red: {e}")
        print("Verifique su conexión o la URL (puede haber expirado).")
    except Exception as e:
        print(f"\nOcurrió un error: {e}")
    finally:
        # --- PASO 6: Limpieza ---
        print(f"[Paso 6] Limpiando {len(archivos_temporales)} archivos temporales...")
        limpiar_archivos(archivos_temporales)
        print("Limpieza finalizada.")

# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Debe pasar la URL completa del manifiesto como argumento.")
        print("Uso: python descargar_limpio.py \"<URL_COMPLETA_CON_PARAMETROS>\"")
        print("(Recuerde poner la URL entre comillas)")
    else:
        url_manifiesto_dinamica = sys.argv[1]
        main(url_manifiesto_dinamica)
