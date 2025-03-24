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
    - Empresa del Remitente: Gimnasio Inc
    
    CONTEXTO DE LA EMPRESA: Gimnasio Inc es un gimnasio boutique con entrenamientos personalizados para deportistas. Nos enfocamos en ofrecer programas de entrenamiento adaptados a las necesidades individuales de cada cliente, ayudándolos a alcanzar sus objetivos de fitness de manera eficiente y segura. Nos especializamos en:
    
    1. Entrenamiento personalizado
    2. Evaluaciones físicas detalladas
    3. Programas de nutrición y bienestar
    4. Clases grupales exclusivas para mejorar el rendimiento

    
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
