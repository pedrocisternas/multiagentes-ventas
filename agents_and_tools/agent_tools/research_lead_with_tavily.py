import os
import logging
from typing import Any, Dict
import json
from agents import RunContextWrapper, function_tool
from openai import OpenAI
from dotenv import load_dotenv
from models.sales import SalesContext
from agent_tools.tavily_search import search_tavily

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Inicializar cliente OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


@function_tool
async def research_lead_with_tavily(
    wrapper: RunContextWrapper[SalesContext], name: str, linkedin_url: str = None
) -> Dict[str, Any]:
    """Investigar un lead utilizando la búsqueda web de Tavily y formatear los resultados similar a un perfil de LinkedIn"""
    description = wrapper.context.get("description", "")
    print(f"Iniciando investigación web para lead: {name}")
    logger.info(f"Investigando lead: {name} (LinkedIn URL: {linkedin_url})")
    if description:
        logger.info(f"Descripción del lead: {description}")
    
    # Primero, crear consultas de búsqueda para recopilar información sobre la persona
    search_queries = []
    
    # Si tenemos una descripción, usarla para consultas más precisas
    if description:
        search_queries = [
            f"{name} {description}",
            f"{name} {description} background",
            f"{name} {description} experience",
            f"{name} {description} education"
        ]
    else:
        # Consultas genéricas si no hay descripción
        search_queries = [
            f"{name} professional background",
            f"{name} current job position",
            f"{name} career history",
            f"{name} education background",
            f"{name} professional interests"
        ]
    
    # Extraer dominio de LinkedIn URL si está disponible para contexto adicional
    domain = None
    if linkedin_url:
        parts = linkedin_url.split("/")
        if len(parts) > 2:
            # Extraer nombre de usuario de la URL de LinkedIn
            username = parts[-1] if parts[-1] else parts[-2]
            if username:
                search_queries.append(f"{name} {username} professional background")
    
    # Recopilar resultados de búsqueda
    print(f"Buscando en la web información sobre {name}...")
    combined_results = ""
    for query in search_queries:
        results = await search_tavily(query=query, max_results=3)
        combined_results += f"\n\n{results}"
    
    print("✅ Búsqueda web completada")
    
    # Usar OpenAI para extraer información estructurada de los resultados de búsqueda
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Eres un experto en extraer información profesional sobre personas a partir de resultados de búsqueda web.
                    Extrae información sobre la carrera, educación, intereses y actividades profesionales de la persona.
                    Formatea la información para que coincida con la estructura de un perfil de LinkedIn.
                    Por favor, devuelve la información como un objeto JSON con estos campos exactos en el nivel superior (NO los anides bajo una clave 'profile'):
                    - current_role: su cargo actual
                    - company: su empresa actual
                    - industry: su industria
                    - experience: array de objetos con campos title, company y duration
                    - education: array de strings
                    - interests: array de strings
                    - recent_activity: string
                    
                    Si la información no está disponible, haz una suposición razonable basada en el contexto pero indica incertidumbre."""
                },
                {
                    "role": "user",
                    "content": f"Aquí están los resultados de búsqueda web sobre {name}. Extrae información profesional y devuélvela como un objeto JSON formateado como un perfil de LinkedIn con los campos exactos especificados:\n\n{combined_results}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Analizar los datos estructurados de la respuesta
        structured_data = json.loads(response.choices[0].message.content)
        
        # Comprobar si los datos están anidados bajo una clave 'profile'
        if 'profile' in structured_data and isinstance(structured_data['profile'], dict):
            profile_data = structured_data['profile']
        else:
            profile_data = structured_data
        
        # Asegurar que la respuesta coincida con el formato del esquema de LinkedIn, con el mapeo adecuado
        formatted_profile = {
            "current_role": profile_data.get("current_role") or profile_data.get("headline") or "Unknown",
            "company": profile_data.get("company") or (profile_data.get("experience", [{}])[0].get("company") if profile_data.get("experience") else "Unknown"),
            "industry": profile_data.get("industry", "Unknown"),
            "experience": []
        }
        
        # Manejar la experiencia con el formato adecuado
        if "experience" in profile_data and isinstance(profile_data["experience"], list):
            for exp in profile_data["experience"]:
                if isinstance(exp, dict):
                    formatted_exp = {
                        "title": exp.get("title", "Unknown"),
                        "company": exp.get("company", "Unknown"),
                        "duration": exp.get("duration") or f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
                    }
                    formatted_profile["experience"].append(formatted_exp)
        
        if not formatted_profile["experience"]:
            formatted_profile["experience"] = [{"title": "Unknown", "company": "Unknown", "duration": "Unknown"}]
        
        # Manejar la educación
        if "education" in profile_data and isinstance(profile_data["education"], list):
            formatted_profile["education"] = []
            for edu in profile_data["education"]:
                if isinstance(edu, dict):
                    edu_str = f"{edu.get('degree', 'Degree')} at {edu.get('institution', 'Institution')}"
                    formatted_profile["education"].append(edu_str)
                elif isinstance(edu, str):
                    formatted_profile["education"].append(edu)
        else:
            formatted_profile["education"] = ["Unknown"]
        
        # Manejar intereses
        formatted_profile["interests"] = profile_data.get("interests", ["Unknown"])
        if not isinstance(formatted_profile["interests"], list):
            formatted_profile["interests"] = ["Unknown"]
        
        # Manejar actividad reciente
        formatted_profile["recent_activity"] = profile_data.get("recent_activity") or "No hay información de actividad reciente disponible"
        
        # Imprimir un resumen de la información encontrada
        print("\n📋 Resumen del Perfil del Lead:")
        print(f"  • Rol actual: {formatted_profile['current_role']} en {formatted_profile['company']}")
        print(f"  • Industria: {formatted_profile['industry']}")
        if formatted_profile['education'] and formatted_profile['education'][0] != "Unknown":
            print(f"  • Educación: {formatted_profile['education'][0]}")
        if formatted_profile['interests'] and formatted_profile['interests'][0] != "Unknown":
            print(f"  • Intereses clave: {', '.join(formatted_profile['interests'][:3])}")
        
        # Actualizar el contexto con los datos de perfil estructurados
        wrapper.context["profile_data"] = formatted_profile
        
        print("✅ Investigación del lead completada")
        return formatted_profile
        
    except Exception as e:
        logger.error(f"Error al procesar los resultados de búsqueda web: {str(e)}")
        # Devolver datos de respaldo que coincidan con el esquema requerido
        fallback_data = {
            "current_role": "Unknown",
            "company": "Unknown",
            "industry": "Unknown",
            "experience": [{"title": "Unknown", "company": "Unknown", "duration": "Unknown"}],
            "education": ["Unknown"],
            "interests": ["Unknown"],
            "recent_activity": f"Error al extraer información del perfil. Error: {str(e)}"
        }
        wrapper.context["profile_data"] = fallback_data
        return fallback_data
