import json
import logging
import os
from openai import OpenAI
from schemas.linkedin_schema import LINKEDIN_PROFILE_SCHEMA

# Inicializar cliente OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


def parse_linkedin_profile(markdown_content: str):
    """Extraer datos estructurados del contenido HTML del perfil de LinkedIn utilizando la API de OpenAI"""
    logging.info("Iniciando extracción de datos estructurados del perfil de LinkedIn")
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Eres un experto en examinar la página de LinkedIn de una persona y extraer información relevante.",
                    }
                ],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": markdown_content}],
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "linkedin_profile",
                "strict": True,
                "schema": LINKEDIN_PROFILE_SCHEMA,
            }
        },
        reasoning={},
        tools=[],
        temperature=0.5,
        top_p=1,
    )

    return json.loads(response.output_text)
