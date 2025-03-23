"""
Herramienta de búsqueda personalizada utilizando la API de Tavily para capacidades de búsqueda web más potentes.
"""

import os
import asyncio
from typing import Optional
from dotenv import load_dotenv
import logging

from agents import function_tool, RunContextWrapper

# Configurar logging
logger = logging.getLogger("tavily_search")

# Cargar variables de entorno para obtener la clave API de Tavily
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Intentar importar el cliente Tavily, manejar el caso donde podría no estar instalado
try:
    from tavily import TavilyClient

    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning(
        "SDK de Python Tavily no encontrado. Ejecuta 'pip install tavily-python' para usar la búsqueda Tavily."
    )
except Exception as e:
    TAVILY_AVAILABLE = False
    logger.warning(f"Error al inicializar el cliente Tavily: {str(e)}")


async def search_tavily(query: str, max_results: int = 5) -> str:
    """
    Función interna para buscar utilizando la API de Tavily.
    """
    from tavily import TavilyClient

    # Inicializar cliente Tavily desde variable de entorno
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        return "Error: Variable de entorno TAVILY_API_KEY no encontrada."

    # Crear instancia del cliente
    tavily_client = TavilyClient(api_key=tavily_api_key)

    try:
        # Llamar a la API de Tavily utilizando el cliente
        response = tavily_client.search(
            query=query, search_depth="basic", max_results=max_results
        )

        if not response or "results" not in response:
            return f"No se encontraron resultados para la consulta: {query}"

        # Formatear los resultados
        results_text = f"Resultados de búsqueda web para '{query}':\n\n"

        for i, result in enumerate(response["results"]):
            results_text += f"{i + 1}. {result.get('title', 'Sin título')}\n"
            results_text += f"   URL: {result.get('url', 'Sin URL')}\n"
            results_text += f"   {result.get('content', 'No hay contenido disponible')}\n\n"

        return results_text

    except Exception as e:
        return f"Error al buscar en la web: {str(e)}"


@function_tool
async def tavily_search(
    ctx: RunContextWrapper,
    query: str,
    max_results: Optional[int] = None,
) -> str:
    """
    Buscar información en la web utilizando el motor de búsqueda Tavily.

    Args:
        query: La consulta de búsqueda para encontrar información en la web
        max_results: Número de resultados a devolver (entre 1 y 10)
        search_depth: Profundidad de búsqueda, ya sea "basic" para resultados más rápidos o "comprehensive" para una búsqueda más exhaustiva

    Returns:
        Información encontrada en la web relacionada con la consulta
    """
    # Establecer el nombre de la herramienta en el contexto
    ctx.context.set_last_tool("tavily_search")

    # Aplicar valores predeterminados dentro de la función
    if max_results is None:
        max_results = 5

    return await search_tavily(query=query, max_results=max_results)
