import os
import io
import base64
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from typing import Dict, Any, Optional
from pathlib import Path

class AgenteGeneradorCiego:
    def __init__(self, credentials_path: Optional[Path] = None):
        print(f"[AGENTE 4: COMPOSICION LOCAL] Motor de Inpainting Local (Pillow + Rembg) Iniciado.")
        print(f"[AGENTE 4] Bypass API de Google Activado - Procesamiento On-Premise 100%")

    def ejecutar_generacion(
        self,
        super_prompt: str,
        base_image_b64: str = "",
        mask_b64: str = "",
        reference_image_b64: str = "",
        aspect_ratio: str = "1:1"
    ) -> Dict[str, Any]:
        """
        Fase 8 Pivot: Ejecuta 'Photoshop Automático' mediante código.
        Sin llamadas a API externas (adiós error 429).
        """
        try:
            from rembg import remove

            print("[AGENTE 4] Iniciando flujo de 'Photoshop Automático' Local...")

            # 1. Decodificar imágenes base
            base_bytes = base64.b64decode(base_image_b64)
            base_img = Image.open(io.BytesIO(base_bytes)).convert("RGBA")

            ref_bytes = base64.b64decode(reference_image_b64)
            ref_img = Image.open(io.BytesIO(ref_bytes)).convert("RGBA")

            mask_bytes = base64.b64decode(mask_b64)
            mask_np = np.frombuffer(mask_bytes, np.uint8)
            mask_cv = cv2.imdecode(mask_np, cv2.IMREAD_GRAYSCALE)

            # Extraer Bounding Box original de la máscara (Generada por Agente 1)
            x, y, w, h = cv2.boundingRect(mask_cv)
            if w == 0 or h == 0:
                # Fallback lógico si la máscara falla
                x, y, w, h = int(base_img.width*0.50), int(base_img.height*0.55), int(base_img.width*0.35), int(base_img.height*0.35)

            # Paso A: Extracción estricta con rembg
            print("[AGENTE 4] Paso A: Extrayendo mueble con rembg...")
            subject_no_bg = remove(ref_img)

            # Paso B: Escalado al Bounding Box
            print("[AGENTE 4] Paso B: Escalando mueble a las coordenadas espaciales...")
            subj_ratio = subject_no_bg.width / subject_no_bg.height
            bbox_ratio = w / h
            if subj_ratio > bbox_ratio:
                new_w = w
                new_h = int(w / subj_ratio)
            else:
                new_h = h
                new_w = int(h * subj_ratio)
            
            subject_resized = subject_no_bg.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Paso E: Ajuste de Color (Filtro cálido)
            print("[AGENTE 4] Paso E: Aplicando filtro cálido al mueble...")
            r, g, b, a = subject_resized.split()
            # Aumentar rojos (15%) y verdes (5%) levemente para calidez ambiental
            r = r.point(lambda i: min(int(i * 1.15), 255))
            g = g.point(lambda i: min(int(i * 1.05), 255))
            subject_warm = Image.merge("RGBA", (r, g, b, a))

            # Paso C: Generación de Sombras de contacto artificial
            print("[AGENTE 4] Paso C: Generando sombras de contacto artificiales...")
            pad = 100
            shadow = Image.new("RGBA", (new_w + pad*2, new_h + pad*2), (0, 0, 0, 0))
            draw = ImageDraw.Draw(shadow)
            
            # Elipse negra sólida en la base (ambient occlusion directo bajo patas)
            shadow_rect = [pad, new_h + pad - 30, new_w + pad, new_h + pad + 10]
            draw.ellipse(shadow_rect, fill=(0, 0, 0, 180))
            
            # Sombra direccional hacia la derecha (imitando luz de la izquierda)
            shadow_dir_rect = [pad + 40, new_h + pad - 20, new_w + pad + 120, new_h + pad + 40]
            draw.ellipse(shadow_dir_rect, fill=(0, 0, 0, 110))
            
            # Desenfoque gaussiano profundo para naturalidad
            shadow_blurred = shadow.filter(ImageFilter.GaussianBlur(15))

            # Paso D: Fusión de capas
            print("[AGENTE 4] Paso D: Fusionando sombra y mueble sobre fondo...")
            offset_x = x + (w - new_w) // 2
            offset_y = y + (h - new_h) // 2

            # Pegar sombra respetando su padding
            base_img.paste(shadow_blurred, (offset_x - pad, offset_y - pad), shadow_blurred)
            # Pegar mueble usando su propio canal alpha como máscara
            base_img.paste(subject_warm, (offset_x, offset_y), subject_warm)

            # 3. Salida al Frontend
            print("[AGENTE 4] Convirtiendo render local a Base64 para el frontend...")
            final_img = base_img.convert("RGB")
            buffer = io.BytesIO()
            final_img.save(buffer, format="JPEG", quality=90)
            final_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            print("[AGENTE 4] ¡Renderización local completada!")
            return {
                "success": True,
                "status": "local_composition_success",
                "mime_type": "image/jpeg",
                "image_base64": final_b64,
                "super_prompt": super_prompt,
                "payload_structure": "LOCAL_PROCESSING_BYPASS_API"
            }

        except Exception as e:
            err_msg = str(e)
            print(f"[AGENTE 4 - ERROR LOCAL] {err_msg}")
            
            return {
                "success": False,
                "error_type": "LOCAL_RENDER_EXCEPTION",
                "status": "error",
                "message": f"Fallo en Composición Local: {err_msg}",
                "payload_structure": "ERROR"
            }
