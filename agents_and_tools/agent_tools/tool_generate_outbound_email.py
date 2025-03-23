import os
from agents import RunContextWrapper, function_tool
from dotenv import load_dotenv
from openai import OpenAI

from models.sales import SalesContext

load_dotenv()

openai_api_key = os.environ.get("OPENAI_API_KEY")


client = OpenAI(api_key=openai_api_key)


@function_tool
def generate_email(
    wrapper: RunContextWrapper[SalesContext],
) -> str:
    """Generar un correo electrónico de ventas personalizado basado en los datos del perfil de LinkedIn"""

    if not wrapper.context.get("profile_data"):
        return "Error: No hay datos de perfil de LinkedIn disponibles. Por favor, extraiga los datos del perfil primero."

    system_prompt = "Eres un experto en escribir correos electrónicos de ventas personalizados. Escribe un correo electrónico conciso y persuasivo que conecte con los antecedentes e intereses del prospecto."

    prompt_details = f"""
    INFORMACIÓN DEL DESTINATARIO:

    {wrapper.context["name"]}
    
    {wrapper.context["profile_data"]}
    
    
    DETALLES DEL CORREO ELECTRÓNICO:
    - Nombre del Remitente: Pedro Cisternas
    - Empresa del Remitente: Ficticia Inc
    
    CONTEXTO DE LA EMPRESA: Ficticia Inc es una empresa líder en soluciones de inteligencia artificial que está revolucionando la forma en que las empresas analizan y utilizan sus datos. Nuestra tecnología avanzada permite a las organizaciones automatizar procesos complejos, mejorar la toma de decisiones y descubrir nuevas oportunidades de negocio. Nos especializamos en:
    
    1. Análisis predictivo impulsado por IA
    2. Automatización de procesos empresariales
    3. Integración de IA en sistemas existentes para optimizar operaciones
    4. Creación de sistemas multi-agente para automatizar procesos de ventas y marketing

    
    Directrices:
    - Mantén el correo electrónico conciso (1 párrafo)
    - Escribe como Josh Braun (ilumina un problema que el prospecto podría no conocer)
    - Sin jergas, sin pitch duro, solo despierta interés
    - Personaliza según los antecedentes del destinatario, pero sin ser invasivo
    - Concéntrate en despertar curiosidad en lugar de vender
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt_details}],
            },
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[],
        temperature=0.7,
        max_output_tokens=2048,
        top_p=1,
        store=True,
    )

    generated_email = response.output_text

    # Actualiza el contexto con el correo electrónico generado
    wrapper.context["email_draft"] = generated_email

    return generated_email
