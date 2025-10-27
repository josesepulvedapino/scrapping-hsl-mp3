# Scraper de Streaming a MP3

Este script de Python descarga todos los segmentos de un stream de video (HLS con manifiesto JSON personalizado) y los convierte en un único archivo `audio_final.mp3`.

Está diseñado para el sistema de streaming de `sesiones.senado.cl`, que utiliza parámetros dinámicos y un manifiesto para proteger su contenido.

---

## Qué Hace

1.  **Obtiene un Manifiesto JSON** desde una URL dinámica (que debe ser proporcionada).
2.  **Parsea el JSON** para encontrar la lista de segmentos de video (`.ts`).
3.  **Descarga** todos los segmentos `.ts` individualmente.
4.  **Usa FFMPEG** para concatenar todos los segmentos en un video `video_completo.mp4`.
5.  **Usa FFMPEG** para extraer el audio de ese video a `audio_final.mp3`.
6.  **Limpia** todos los archivos temporales (`.ts`, `.txt`, `.mp4`).

---

## Requisitos

Para ejecutar este script, necesitas:

1.  **Python 3.x**
2.  **Librería `requests`**:
    ```bash
    pip install requests
    ```
3.  **FFMPEG**:
    * Debe estar **instalado** en tu sistema.
    * Debe estar accesible en el **PATH** de tu terminal (puedes probarlo escribiendo `ffmpeg -version`).
    * *En Windows (PowerShell): `winget install -e --id Gyan.FFmpeg`*

---

## Cómo Usarlo

La URL del manifiesto es dinámica y **expira en segundos**.

1.  Abre las **DevTools (F12)** en el navegador en `https://sesiones.senado.cl/`.
2.  Ve a la pestaña **Network** y filtra por `.m3u8`.
3.  Refresca el video para obtener una **URL nueva**.
4.  **INMEDIATAMENTE**, copia la dirección de ese enlace.
5.  Pega la URL en tu terminal **entre comillas**:

```bash
python descargar_limpio.py "URL_COMPLETA_Y_NUEVA_AQUI"
