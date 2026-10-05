import asyncio
import base64
import os
from pathlib import Path

from agente_orquestador import AgenteOrquestadorJefe
from agente_generador import AgenteGeneradorCiego
from google.oauth2 import service_account
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = Path(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", BASE_DIR / "credentials.json"))
SPREADSHEET_ID = "1YsqnJNaOYNGVbpLOUQ0_BQzPtLK-JPjPiz3ObP4EtM4"

async def test():
    print("Iniciando prueba rápida de generación...")
    
    # 1. Obtener productos
    if not CREDENTIALS_PATH.exists():
        print("Error: credentials.json no encontrado.")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = service_account.Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=scopes)
    sheets = build("sheets", "v4", credentials=creds)

    print("Obteniendo producto de prueba (Bypass Sheets API por error de credencial)...")
    producto_prueba = {
        "id": "PRD-TEST",
        "sku": "SKU-9999",
        "nombre": "Mueble de Prueba",
        "foto_url": "https://dummyimage.com/600x400/000/fff&text=Mueble+Prueba",
        "cantidad": 1
    }
    
    print(f"Producto seleccionado para la prueba: {producto_prueba['nombre']} (SKU: {producto_prueba['sku']})")
    
    # 2. Orquestar
    orquestador = AgenteOrquestadorJefe()
    generador = AgenteGeneradorCiego()
    
    import urllib.request
    print("Descargando imagen de fondo de prueba...")
    req = urllib.request.Request("https://dummyimage.com/800x600/ccc/000&text=Habitacion+Fondo", headers={'User-Agent': 'Mozilla/5.0'})
    bg_bytes = urllib.request.urlopen(req).read()
    
    print("Iniciando Agente Orquestador...")
    resultado_orquestacion = orquestador.orquestar_flujo(
        lista_productos=[producto_prueba],
        lista_archivos=[{"nombre": "escena_fondo.jpg", "is_image": True, "bytes": bg_bytes}],
        observaciones="Prueba local"
    )
    
    super_prompt = resultado_orquestacion.get("super_prompt", "")
    base_img = resultado_orquestacion.get("base_image_b64", "")
    mask_img = resultado_orquestacion.get("mask_b64", "")
    ref_img = resultado_orquestacion.get("reference_image_b64", "")
    
    print("\n[PROMPT GENERADO]")
    print(super_prompt)
    print("------------------\n")
    
    # 3. Generar
    print("Iniciando Agente Generador (rembg + OpenCV)...")
    resultado_generacion = generador.ejecutar_generacion(
        super_prompt=super_prompt,
        base_image_b64=base_img,
        mask_b64=mask_img,
        reference_image_b64=ref_img,
        aspect_ratio="1:1"
    )
    
    status = resultado_generacion.get("status")
    if status == "error":
        print("Error en generación:", resultado_generacion.get("message"))
        return
        
    img_b64 = resultado_generacion.get("image_base64")
    if img_b64:
        with open("resultado_prueba.jpg", "wb") as f:
            f.write(base64.b64decode(img_b64))
        print("\n¡ÉXITO! La imagen se guardó localmente como 'resultado_prueba.jpg'.")
        print("NOTA: No se guardó en Google Sheets como pediste.")

if __name__ == "__main__":
    asyncio.run(test())
