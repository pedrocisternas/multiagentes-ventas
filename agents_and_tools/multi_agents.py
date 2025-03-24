import os
import asyncio
import json
from datetime import datetime

from models.sales import SalesContext
from prompts.sales import (
    COLD_EMAIL_SPECIALIST_INSTRUCTIONS,
    SALES_DEVELOPMENT_REP_INSTRUCTIONS,
    SALES_DEVELOPMENT_REP_TAVILY_INSTRUCTIONS,
    SALES_TEAM_LEAD_INSTRUCTIONS,
)

from agents import Agent, RunContextWrapper, RunResult, Runner, handoff
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from agent_tools.scrape_and_extract_linkedin_profile import extract_linkedin_profile
from agent_tools.research_lead_with_tavily import research_lead_with_tavily
from agent_tools.tool_generate_outbound_email import generate_email
from data.sales_leads import leads
from miscs.run_parallel_agents import run_dict_tasks_in_parallel
from miscs.reporting import generate_lead_report


async def on_handoff_callback(ctx: RunContextWrapper[SalesContext]):
    print("\n🔄 Handoff ocurrió")


# AGENTEs
sales_team_lead = Agent[SalesContext](
    name="Sales Team Lead",
    instructions=prompt_with_handoff_instructions(SALES_TEAM_LEAD_INSTRUCTIONS),
    model="gpt-4o",
)

sales_development_rep = Agent[SalesContext](
    name="Sales Development Rep",
    instructions=prompt_with_handoff_instructions(SALES_DEVELOPMENT_REP_INSTRUCTIONS),
    tools=[extract_linkedin_profile],
    model="gpt-4o",
)

# Nuevo agente usando búsqueda Tavily en lugar de raspado de LinkedIn
sales_development_rep_tavily = Agent[SalesContext](
    name="Sales Development Rep with Tavily",
    instructions=prompt_with_handoff_instructions(SALES_DEVELOPMENT_REP_TAVILY_INSTRUCTIONS),
    tools=[research_lead_with_tavily],
    model="gpt-4o",
)

cold_email_specialist = Agent[SalesContext](
    name="Cold Email Specialist",
    instructions=prompt_with_handoff_instructions(COLD_EMAIL_SPECIALIST_INSTRUCTIONS),
    tools=[generate_email],
    model="gpt-4o",
)

# Configuración original de handoff usando raspador de LinkedIn
# sales_team_lead.handoffs = [
#     handoff(agent=sales_development_rep, on_handoff=on_handoff_callback),
#     handoff(agent=cold_email_specialist, on_handoff=on_handoff_callback),
# ]

# Nueva configuración de handoff usando investigación Tavily
sales_team_lead.handoffs = [
    handoff(agent=sales_development_rep_tavily, on_handoff=on_handoff_callback),
    handoff(agent=cold_email_specialist, on_handoff=on_handoff_callback),
]

# Handoff original para el agente basado en LinkedIn
sales_development_rep.handoffs = [
    handoff(agent=sales_team_lead, on_handoff=on_handoff_callback)
]

# Handoff para el nuevo agente basado en Tavily
sales_development_rep_tavily.handoffs = [
    handoff(agent=sales_team_lead, on_handoff=on_handoff_callback)
]

cold_email_specialist.handoffs = [
    handoff(agent=sales_team_lead, on_handoff=on_handoff_callback)
]


async def process_sales_lead(lead: dict) -> RunResult:
    """Procesar un lead de ventas a través del flujo de trabajo multi-agente"""
    name = lead["name"]
    linkedin_url = lead["linkedin_url"]
    description = lead.get("description", "")
    email = lead.get("email", "")

    context: SalesContext = {
        "name": name,
        "linkedin_url": linkedin_url,
        "description": description,
        "email": email,
        "profile_data": None,
        "email_draft": None,
    }

    print(f"\n🔍 Procesando lead: {name} ({linkedin_url})")
    if description:
        print(f"   📝 Descripción: {description}")
    if email:
        print(f"   ✉️ Email: {email}")

    final_result = await Runner.run(
        starting_agent=sales_team_lead,
        input=f"Tenemos un nuevo lead: {name} ({linkedin_url}). Por favor, coordina el proceso para investigar este lead y crear un correo electrónico de prospección personalizado.",
        context=context,
        max_turns=15,
    )

    return final_result


def display_lead_result(lead: dict, final_result: RunResult):
    print("Resultados finales:")
    print(f"""
    Input: {final_result.input}
    Mensaje final del agente: {final_result.final_output}
    Último agente: {final_result.last_agent.name}
    """)


async def process_multiple_leads_in_parallel():
    """Procesar una lista de leads predefinidos en paralelo"""
    print("\n===== Sistema Multi-Agente de Prospección de Ventas =====")

    results = await run_dict_tasks_in_parallel(
        process_function=process_sales_lead,
        input_dicts=leads,
        show_progress=True,
        result_handler=display_lead_result,
    )
    
    # Generar reporte de leads
    report_file = generate_lead_report(results, leads)
    
    return results


def main():
    """Punto de entrada principal para la aplicación"""
    print("Iniciando Sistema Multi-Agente de Prospección de Ventas...")
    asyncio.run(process_multiple_leads_in_parallel())


if __name__ == "__main__":
    main()
