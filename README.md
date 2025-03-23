# Sistema Multi-Agente de Prospección de Ventas

Este repositorio contiene un sistema multi-agente desarrollado con el SDK de OpenAI Agents que automatiza el proceso de prospección de ventas, investigando leads y generando correos electrónicos personalizados.

## Arquitectura del Sistema

El sistema consta de varios agentes que trabajan juntos:

1. **Líder del Equipo de Ventas**: Coordina el flujo de trabajo general y asigna tareas a otros agentes.
2. **Representante de Desarrollo de Ventas**: Investiga leads utilizando:
   - Extracción de perfiles de LinkedIn (versión original)
   - Búsqueda web con Tavily (versión actual)
3. **Especialista en Emails Fríos**: Genera correos electrónicos de prospección personalizados basados en la investigación.

## Requisitos

- Python 3.12 o superior
- Claves API para:
  - OpenAI
  - Tavily Search
  - Scraper API (para la extracción de LinkedIn, opcional si solo usas Tavily)

## Configuración

### 1. Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd <nombre-del-repositorio>
```

### 2. Crear un entorno virtual

El proyecto utiliza Python 3.12 como se especifica en el archivo `.python-version`.

```bash
# Crear el entorno virtual
python3.12 -m venv .venv

# Activar el entorno virtual
# En macOS/Linux:
source .venv/bin/activate
# En Windows:
# .venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -e .
```

### 4. Configurar las variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
OPENAI_API_KEY=tu-clave-de-api-de-openai
TAVILY_API_KEY=tu-clave-de-api-de-tavily
SCRAPER_API_KEY=tu-clave-de-api-de-scraper-api
```

Reemplaza los valores con tus propias claves API:
- Obtén una clave API de OpenAI en: https://platform.openai.com/api-keys
- Obtén una clave API de Tavily en: https://tavily.com/
- Obtén una clave API de Scraper en: https://www.scraperapi.com/ (opcional si solo usas Tavily)

## Ejecución del proyecto

Para ejecutar el sistema multi-agente de ventas:

```bash
python3 agents_and_tools/multi_agents.py
```

El sistema procesará los leads definidos en `agents_and_tools/data/sales_leads.py` y generará correos electrónicos personalizados utilizando la información recopilada.

## Personalización

- Para modificar los leads, edita el archivo `agents_and_tools/data/sales_leads.py`
- Las instrucciones de los agentes se pueden personalizar en `agents_and_tools/prompts/sales.py`
- Para ajustar el proceso de generación de correos electrónicos, edita `agents_and_tools/agent_tools/tool_generate_outbound_email.py`
