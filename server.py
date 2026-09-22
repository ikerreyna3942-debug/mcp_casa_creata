from mcp.server.fastmcp import FastMCP

# Inicializar el servidor
mcp = FastMCP("MiServidorMCP")

# Definir una herramienta (tool) que el LLM podrá ejecutar
@mcp.tool()
def calcular_volumen(alto: float, ancho: float, fondo: float) -> str:
    """Calcula el volumen en metros cúbicos recibiendo medidas en centímetros."""
    volumen_m3 = (alto / 100) * (ancho / 100) * (fondo / 100)
    return f"El volumen calculado es {volumen_m3:.4f} m³"

if __name__ == "__main__":
    # Ejecutar el servidor
    mcp.run_stdio()