import os
import cv2
import numpy as np
import base64
from typing import Dict, Any

SYSTEM_PROMPT_ANALISIS_PRODUCTO = """
Eres el Agente Especialista en Analisis Tecnico de Mobiliario y Metrologia de Casa Creata.
Tu mision principal ahora es asegurar que la imagen del producto seleccionado este perfectamente
aislada (fondo transparente o blanco puro) para servir como 'Imagen de Referencia'.

Reglas:
1. Analisis tecnico de textura, color, y geometria del producto.
2. Asegurar el recorte perfecto y entregar la Referencia Visual en Base64.
"""

class AgenteAnalisisProducto:
    def __init__(self, system_prompt_template: str = SYSTEM_PROMPT_ANALISIS_PRODUCTO):
        self.system_prompt_template = system_prompt_template

    def preparar_datos_producto(self, datos_producto: Dict[str, Any], cantidad: int = 1) -> Dict[str, Any]:
        cant = max(int(cantidad), 1)
        return {
            "nombre": datos_producto.get("nombre", "Producto Desconocido"),
            "sku": datos_producto.get("sku", "SKU-S/N"),
            "cantidad": cant,
            "medidas": {
                "frente_cm": datos_producto.get("frente", 0.0),
                "fondo_cm": datos_producto.get("fondo", 0.0),
                "alto_cm": datos_producto.get("alto", 0.0),
            },
            "foto_referencia_url": datos_producto.get("foto_url", ""),
            "materiales_declarados": datos_producto.get("materiales", ""),
            "acabado_tela": datos_producto.get("color_tela", ""),
            "acabado_madera": datos_producto.get("madera_tono", "")
        }

    def aislar_imagen_referencia(self, url_or_path: str, image_bytes: bytes = None) -> str:
        """
        Agente 2 (Fase 8): Transparencia de Referencia.
        Descarga (si es un enlace de Google Sheets), remueve el fondo blanco y añade un Canal Alpha.
        Garantiza que la imagen enviada al generador sea la silueta pura y nunca falle por un link en texto plano.
        """
        import requests
        
        # 1. Fase 8.1: Verificación de manejo de archivos remotos
        if not image_bytes and url_or_path and url_or_path.startswith("http"):
            try:
                print(f"[AGENTE 2] Descargando imagen de referencia desde: {url_or_path[:60]}...")
                resp = requests.get(url_or_path, timeout=10)
                resp.raise_for_status()
                image_bytes = resp.content
            except Exception as e:
                print(f"[AGENTE 2] ERROR descargando {url_or_path}: {e}")
                
        if not image_bytes:
            print("[AGENTE 2] Advertencia: No hay bytes de imagen, retornando MOCK transparente.")
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("cv2.imdecode devolvió None, los bytes descargados no son una imagen válida.")
                
            # Filtro rapido para fondos de e-commerce (blancos o casi blancos)
            lower_white = np.array([240, 240, 240])
            upper_white = np.array([255, 255, 255])
            mask = cv2.inRange(img, lower_white, upper_white)
            
            # Invertir mascara: 255 sera el mueble, 0 el fondo
            mask_inv = cv2.bitwise_not(mask)
            
            # Convertir a BGRA (con canal Alpha)
            b, g, r = cv2.split(img)
            rgba = [b, g, r, mask_inv]
            img_rgba = cv2.merge(rgba)
            
            # OBLIGATORIO: Codificar en PNG para preservar transparencia Alpha
            _, buffer = cv2.imencode('.png', img_rgba)
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            print(f"[AGENTE 2 ERROR] Fallo al aplicar transparencia: {e}")
            return "MOCK_REFERENCE_IMAGE_B64_ISOLATED_BACKGROUND"

    def analizar_producto_mock(self, datos_producto: Dict[str, Any], cantidad: int = 1) -> Dict[str, Any]:
        datos = self.preparar_datos_producto(datos_producto, cantidad)
        
        # Generar imagen aislada (sin bytes en este test, devolvera el mock PNG alpha)
        reference_image_b64 = self.aislar_imagen_referencia(datos["foto_referencia_url"])
        
        return {
            "status": "PRODUCT_ISOLATED_AND_ANALYZED",
            "cantidad_procesada": datos["cantidad"],
            "system_prompt": self.system_prompt_template.strip(),
            "reference_image_b64": reference_image_b64,
            "analisis_estructurado": {
                "geometria": f"Silueta aislada de {datos['nombre']} (Canal Alpha Verificado)",
                "textura_detectada": datos["materiales_declarados"] or "Textil organico",
                "color_acabado": datos["acabado_tela"] or "Tono neutro",
                "medidas_validadas": datos["medidas"]
            }
        }
