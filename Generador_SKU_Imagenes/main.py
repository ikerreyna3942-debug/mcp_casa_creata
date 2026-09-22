import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agente_orquestador import AgenteOrquestadorJefe
from agente_generador import AgenteGeneradorCiego

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

CREDENTIALS_PATH = BASE_DIR / "credentials.json"
SPREADSHEET_ID = "1YsqnJNaOYNGVbpLOUQ0_BQzPtLK-JPjPiz3ObP4EtM4"

app = FastAPI(title="Generador SKU Imagenes - Casa Creata")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

orquestador_jefe = AgenteOrquestadorJefe()
generador_ciego = AgenteGeneradorCiego()

class ConfirmRequest(BaseModel):
    productos: Optional[List[Dict[str, Any]]] = []
    archivos_nombres: Optional[List[str]] = []
    sku: Optional[str] = "N/A"
    product_name: Optional[str] = "Varios"
    description: Optional[str] = ""
    style_name: Optional[str] = "Casa Creata"
    aspect_ratio: Optional[str] = "1:1"
    notes: Optional[str] = "Aprobado"
    target_sheet: Optional[str] = "Hoja 1"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template_path = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))

@app.get("/api/productos")
async def get_productos():
    if not CREDENTIALS_PATH.exists():
        raise HTTPException(status_code=500, detail="credentials.json no encontrado")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = service_account.Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=scopes)
        sheets = build("sheets", "v4", credentials=creds)

        resp = sheets.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="'PRODUCTO'!A3:AL"
        ).execute()

        rows = resp.get("values", [])
        productos_validos = []

        for idx, r in enumerate(rows):
            nombre_z = r[25].strip() if len(r) > 25 and r[25] else ""
            nombre_b = r[1].strip() if len(r) > 1 and r[1] else ""
            nombre_final = nombre_z if nombre_z else nombre_b

            foto_link = ""
            for c_idx in [28, 31, 34, 37]:
                if len(r) > c_idx and r[c_idx] and ("http" in r[c_idx] or "drive.google.com" in r[c_idx]):
                    foto_link = r[c_idx].strip()
                    break

            if not foto_link or not nombre_final:
                continue

            sku = r[0].strip() if len(r) > 0 and r[0] else f"SKU-{idx+1:04d}"
            thumb_url = foto_link
            if "drive.google.com/file/d/" in foto_link:
                file_id = foto_link.split("/d/")[1].split("/")[0].split("?")[0]
                thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w300"

            productos_validos.append({
                "id": f"PRD-{idx+1:04d}",
                "sku": sku,
                "nombre": nombre_final,
                "foto_url": thumb_url,
                "link_original": foto_link
            })

        return {"success": True, "total": len(productos_validos), "productos": productos_validos}

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@app.post("/api/confirm-and-save")
async def confirm_and_save_endpoint(req: ConfirmRequest):
    import traceback
    from fastapi.responses import JSONResponse
    try:
        # Paso 1: Orquestación
        lista_arch = [{"nombre": n, "is_image": True, "bytes": None} for n in (req.archivos_nombres or [])]
        resultado_orquestacion = orquestador_jefe.orquestar_flujo(
            lista_productos=req.productos or [],
            lista_archivos=lista_arch,
            observaciones=req.notes or ""
        )

        super_prompt = resultado_orquestacion.get("super_prompt", "")

        # Paso 2: Ejecución de Inpainting en Vertex AI (Agente 4)
        base_img = resultado_orquestacion.get("base_image_b64", "")
        mask_img = resultado_orquestacion.get("mask_b64", "")
        ref_img = resultado_orquestacion.get("reference_image_b64", "")

        resultado_generacion = generador_ciego.ejecutar_generacion(
            super_prompt=super_prompt,
            base_image_b64=base_img,
            mask_b64=mask_img,
            reference_image_b64=ref_img,
            aspect_ratio=req.aspect_ratio or "1:1"
        )

        status = resultado_generacion.get("status", "mock")
        img_b64 = resultado_generacion.get("image_base64")
        mime_type = resultado_generacion.get("mime_type", "image/svg+xml")
        mensaje = resultado_generacion.get("message", "Operación completada")

        # Paso 3: Asentar metadatos en Sheets
        if CREDENTIALS_PATH.exists():
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                from datetime import datetime

                scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                creds = service_account.Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=scopes)
                service_sheets = build("sheets", "v4", credentials=creds)

                sheet_tab = req.target_sheet or "Hoja 1"
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_values = [
                    now_str, req.sku, req.product_name,
                    super_prompt[:300] + "...", f"Generación ({status})",
                    req.aspect_ratio, req.notes, "REGISTRADO_OK"
                ]

                service_sheets.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"'{sheet_tab}'!A:H",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [row_values]}
                ).execute()
            except Exception as e:
                print(f"[GOOGLE SHEETS] Error de registro: {e}")

        # Paso 4: Devolver datos con flag 'status'
        return {
            "success": True,
            "status": status,
            "message": mensaje,
            "image_base64": img_b64,
            "mime_type": mime_type,
            "super_prompt": super_prompt
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "type": "Internal Server Error"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
