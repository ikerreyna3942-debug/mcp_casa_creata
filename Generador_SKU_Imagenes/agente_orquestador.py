from typing import Dict, Any, List
from agente_medicion import AgenteMedicionHibrido
from agente_analisis import AgenteAnalisisProducto

SYSTEM_PROMPT_ORQUESTADOR = """
Eres el Orquestador de Edicion CGI (Inpainting) de Casa Creata.
Tu System Prompt ha cambiado. Ya no describes la habitación entera. 
Tu prompt debe enfocarse exclusivamente en cómo fusionar los bordes:
'Inserta la imagen de referencia dentro del área de la máscara. Genera únicamente 
las sombras de contacto direccionales (ambient occlusion) para anclar el objeto 
al suelo, respetando la iluminación global. No modifiques ni un solo píxel fuera 
de la máscara. Mantén la geometría y textura del mueble exactamente igual a la referencia'.
"""

class AgenteOrquestadorJefe:
    def __init__(self, system_prompt: str = SYSTEM_PROMPT_ORQUESTADOR):
        self.system_prompt = system_prompt
        self.agente_medicion = AgenteMedicionHibrido()
        self.agente_analisis = AgenteAnalisisProducto()

    def sintetizar_prompt_edicion(self) -> str:
        """
        Fase 8: Prompt de CGI Orquestador. Obliga realismo extremo en Inpainting.
        """
        super_prompt = (
            "Insert the reference product into the masked area. Preserve the exact physical geometry, "
            "wood texture, and fabric material of the reference image. "
            "CRITICAL ILLUMINATION: The background room has warm ambient light with a primary light source "
            "coming from the left window. You MUST color-grade the chair to match this warm environment. "
            "Apply realistic highlights on the left side of the chair and cast soft directional shadows to the right. "
            "CRITICAL SHADOWS: Eliminate the floating effect. Generate deep contact shadows (ambient occlusion) "
            "exactly under the four wooden legs touching the rug. You are allowed to slightly adapt the perspective "
            "of the chair to perfectly match the vanishing point of the floor."
        )
        return super_prompt

    def orquestar_flujo(
        self,
        lista_productos: List[Dict[str, Any]],
        lista_archivos: List[Dict[str, Any]],
        observaciones: str = ""
    ) -> Dict[str, Any]:
        """
        Controlador Maestro del Flujo Multi-Agente para Inpainting:
        Recolecta Base Image, Mask (Agente 1) y Reference Image (Agente 2).
        """
        # 1. Agente 1 (Enmascarado y Medición)
        reporte_medicion = self.agente_medicion.analizar_archivos_adjuntos_memoria(lista_archivos)
        
        base_image_b64 = ""
        mask_b64 = ""
        if reporte_medicion.get("imagenes_detectadas"):
            img_data = reporte_medicion["imagenes_detectadas"][0]
            base_image_b64 = img_data.get("base_image_b64", "")
            mask_b64 = img_data.get("mask_b64", "")

        # 2. Agente 2 (Análisis y Aislamiento de Producto)
        reportes_productos = []
        for prod in lista_productos:
            cant = prod.get("cantidad", 1)
            analisis = self.agente_analisis.analizar_producto_mock(prod, cantidad=cant)
            reportes_productos.append(analisis)

        prod_principal = reportes_productos[0] if reportes_productos else {}
        reference_image_b64 = prod_principal.get("reference_image_b64", "")

        # 3. Agente 3 (Orquestador - Síntesis de Inpainting)
        super_prompt = self.sintetizar_prompt_edicion()

        print("\n" + "="*70)
        print(" [AGENTE 3: ORQUESTADOR] - EDICIÓN POR MÁSCARA (INPAINTING) LISTA")
        print("="*70)
        print(" -> Base Image recolectada (Agente 1)")
        print(" -> Máscara [B/N] generada en posición (Agente 1)")
        print(" -> Imagen de Referencia [Aislada] recolectada (Agente 2)")
        print("-" * 70)
        print(f" PROMPT FUSIÓN:\n '{super_prompt}'")
        print("="*70 + "\n")

        return {
            "status": "INPAINTING_READY",
            "super_prompt": super_prompt,
            "base_image_b64": base_image_b64,
            "mask_b64": mask_b64,
            "reference_image_b64": reference_image_b64,
            "observaciones": observaciones
        }
