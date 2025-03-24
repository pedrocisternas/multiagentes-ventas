"""
Módulo para la generación de reportes de leads procesados.
"""
import os
import re
from datetime import datetime

def extract_profile_from_text(text):
    """
    Extrae información del perfil de un texto (típicamente salida de consola).
    
    Args:
        text: Texto que puede contener información del perfil
        
    Returns:
        list: Lista de líneas del perfil o None si no se encuentra
    """
    if not text or not isinstance(text, str):
        return None
        
    # Patrones para buscar la sección de perfil
    patterns = [
        r"📋 Resumen del Perfil del Lead:(.*?)(?:✅|\n\n)",
        r"Resumen del Perfil del Lead:(.*?)(?:✅|\n\n)",
        r"Perfil del Lead:(.*?)(?:✅|\n\n)"
    ]
    
    # Intentar con cada patrón
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            profile_section = match.group(1).strip()
            # Extraer líneas que contengan información relevante
            lines = []
            for line in profile_section.split('\n'):
                line = line.strip()
                if line.startswith('  • '):
                    lines.append(line)
            if lines:
                return lines
    
    return None

def extract_email_subject(text):
    """
    Extrae el asunto del correo electrónico de un texto.
    
    Args:
        text: Texto que puede contener el asunto del correo
        
    Returns:
        str: Asunto del correo o "No especificado" si no se encuentra
    """
    if not text or not isinstance(text, str):
        return "No especificado"
    
    # Patrones para buscar el asunto
    patterns = [
        r"Asunto: ([^\n]+)",
        r"\*\*Asunto:\*\* ([^\n]+)"
    ]
    
    # Intentar con cada patrón
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return "No especificado"

def generate_lead_report(results, leads):
    """
    Genera un reporte de los leads procesados en formato Markdown.
    Sobreescribe cualquier reporte anterior.
    
    Args:
        results: Lista de resultados del procesamiento de leads.
        leads: Lista de diccionarios con la información original de los leads.
        
    Returns:
        str: Ruta del archivo de reporte generado.
    """
    # Crear directorio output si no existe
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Nombre fijo del archivo de reporte
    report_file = os.path.join(output_dir, "report.md")
    
    # Inicializar el reporte en formato Markdown
    md_content = "# Reporte de Leads Procesados\n\n"
    md_content += f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    md_content += "---\n\n"
    
    # Procesar cada resultado
    for i, result in enumerate(results):
        # Extraer datos relevantes del resultado
        lead_name = None
        ultimo_agente = None
        email_draft = None
        profile_data = None
        
        # Extraer el nombre del lead desde el input
        input_text = result.input if hasattr(result, 'input') else ""
        if "lead:" in input_text:
            lead_parts = input_text.split("lead: ")[1].split("(")[0].strip()
            lead_name = lead_parts
        
        # Obtener el último agente
        ultimo_agente = result.last_agent.name if hasattr(result, 'last_agent') else "Desconocido"
        
        # Extraer información del correo electrónico del mensaje final
        final_output = result.final_output if hasattr(result, 'final_output') else ""
        
        # Extraer el borrador del correo (contenido entre las líneas de triple guión)
        asunto = "No especificado"
        if "---" in final_output:
            parts = final_output.split("---")
            if len(parts) >= 3:
                email_draft = parts[1].strip()
                asunto = extract_email_subject(email_draft)
        
        # Añadir sección del lead al reporte Markdown
        md_content += f"## Lead {i+1}: {lead_name or 'Desconocido'}\n\n"
        
        # Para email y descripción, buscar en los leads originales
        for lead in leads:
            if lead["name"] == lead_name:
                if "email" in lead:
                    md_content += f"**Email:** {lead['email']}\n\n"
                if "description" in lead:
                    md_content += f"**Descripción:** {lead['description']}\n\n"
                break
        
        md_content += f"**Último Agente:** {ultimo_agente}\n\n"
        
        # Construir un texto consolidado para buscar perfiles
        all_text = final_output
        
        # Agregar texto de todos los new_items
        if hasattr(result, 'new_items'):
            for item in result.new_items:
                if hasattr(item, 'output') and isinstance(item.output, str):
                    all_text += "\n" + item.output
                # También revisar en raw_item
                if hasattr(item, 'raw_item'):
                    if hasattr(item.raw_item, 'output') and isinstance(item.raw_item.output, str):
                        all_text += "\n" + item.raw_item.output
        
        # Buscar perfil en el texto consolidado
        profile_lines = extract_profile_from_text(all_text)
        if profile_lines:
            md_content += "### Perfil del Lead\n\n"
            md_content += "\n".join(profile_lines) + "\n\n"
        
        if email_draft:
            md_content += f"### Correo Generado\n\n"
            md_content += f"**Asunto:** {asunto}\n\n"
            
            # Limpiar formato del email para Markdown
            clean_email = email_draft.replace("**Asunto:**", "").strip()
            # Eliminar cualquier línea que contenga el asunto
            lines = clean_email.split("\n")
            clean_lines = []
            for line in lines:
                if not re.search(r"(A|a)sunto:", line):
                    clean_lines.append(line)
            clean_email = "\n".join(clean_lines).strip()
            
            md_content += "```\n"
            md_content += clean_email + "\n"
            md_content += "```\n\n"
        else:
            md_content += "### No se generó correo para este lead\n\n"
        
        md_content += "---\n\n"
    
    # Escribir el reporte (sobreescribiendo cualquier versión anterior)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"\n✅ Reporte generado: {report_file}")
    
    return report_file 