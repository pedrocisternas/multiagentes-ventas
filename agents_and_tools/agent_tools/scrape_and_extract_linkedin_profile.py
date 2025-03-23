import os
from typing import Any, Dict
from agents import RunContextWrapper, function_tool
from dotenv import load_dotenv
import requests
from agent_tools.utils.linkedin import parse_linkedin_profile
from models.sales import SalesContext

load_dotenv()

scraper_api_key = os.environ.get("SCRAPER_API_KEY")


@function_tool
def extract_linkedin_profile(
    wrapper: RunContextWrapper[SalesContext], linkedin_url: str
) -> Dict[str, Any]:
    """Extraer datos de perfil de una URL de LinkedIn"""
    print("Iniciando raspado y extracción de LinkedIn")

    payload = {
        "api_key": scraper_api_key,
        "url": linkedin_url,
        "output_format": "markdown",
    }
    response = requests.get(
        "https://api.scraperapi.com/",
        params=payload,
    )

    page_markdown = response.text

    # Extraer el perfil del usuario de la respuesta
    profile_data = parse_linkedin_profile(page_markdown)

    # Actualizar el contexto con los datos del perfil extraído
    wrapper.context["profile_data"] = profile_data

    print("Extracción de LinkedIn finalizada.")

    return profile_data
