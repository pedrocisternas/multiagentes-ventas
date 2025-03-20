import os
import logging
from typing import Any, Dict
import json
from agents import RunContextWrapper, function_tool
from openai import OpenAI
from dotenv import load_dotenv
from models.sales import SalesContext
from agent_tools.tavily_search import search_tavily

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


@function_tool
async def research_lead_with_tavily(
    wrapper: RunContextWrapper[SalesContext], name: str, linkedin_url: str = None
) -> Dict[str, Any]:
    """Research a lead using Tavily web search and format the results similar to a LinkedIn profile"""
    print(f"Starting web research for lead: {name}")
    logger.info(f"Researching lead: {name} (LinkedIn URL: {linkedin_url})")
    
    # First, create search queries to gather information about the person
    search_queries = [
        f"{name} professional background",
        f"{name} current job position",
        f"{name} career history",
        f"{name} education background",
        f"{name} professional interests"
    ]
    
    # Extract domain from LinkedIn URL if available for additional context
    domain = None
    if linkedin_url:
        parts = linkedin_url.split("/")
        if len(parts) > 2:
            # Extract username from LinkedIn URL
            username = parts[-1] if parts[-1] else parts[-2]
            if username:
                search_queries.append(f"{name} {username} professional background")
    
    # Collect search results
    print(f"Searching web for information about {name}...")
    combined_results = ""
    for query in search_queries:
        results = await search_tavily(query=query, max_results=3)
        combined_results += f"\n\n{results}"
    
    print("✅ Web search completed")
    
    # Use OpenAI to extract structured information from search results
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at extracting professional information about people from web search results.
                    Extract information about the person's career, education, interests, and professional activities.
                    Format the information to match a LinkedIn profile structure.
                    Please return the information as a JSON object with these exact fields at the top level (do NOT nest them under a 'profile' key):
                    - current_role: their current job title
                    - company: their current company
                    - industry: their industry
                    - experience: array of objects with title, company, and duration fields
                    - education: array of strings
                    - interests: array of strings
                    - recent_activity: string
                    
                    If information is not available, make a reasonable guess based on context but indicate uncertainty."""
                },
                {
                    "role": "user",
                    "content": f"Here are web search results about {name}. Extract professional information and return it as a JSON object formatted like a LinkedIn profile with the exact fields specified:\n\n{combined_results}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse the structured data from the response
        structured_data = json.loads(response.choices[0].message.content)
        
        # Check if the data is nested under a 'profile' key
        if 'profile' in structured_data and isinstance(structured_data['profile'], dict):
            profile_data = structured_data['profile']
        else:
            profile_data = structured_data
        
        # Ensure the response matches the LinkedIn schema format, with proper mapping
        formatted_profile = {
            "current_role": profile_data.get("current_role") or profile_data.get("headline") or "Unknown",
            "company": profile_data.get("company") or (profile_data.get("experience", [{}])[0].get("company") if profile_data.get("experience") else "Unknown"),
            "industry": profile_data.get("industry", "Unknown"),
            "experience": []
        }
        
        # Handle experience with proper format
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
        
        # Handle education
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
        
        # Handle interests
        formatted_profile["interests"] = profile_data.get("interests", ["Unknown"])
        if not isinstance(formatted_profile["interests"], list):
            formatted_profile["interests"] = ["Unknown"]
        
        # Handle recent activity
        formatted_profile["recent_activity"] = profile_data.get("recent_activity") or "No recent activity information available"
        
        # Print a summary of the information found
        print("\n📋 Lead Profile Summary:")
        print(f"  • Current role: {formatted_profile['current_role']} at {formatted_profile['company']}")
        print(f"  • Industry: {formatted_profile['industry']}")
        if formatted_profile['education'] and formatted_profile['education'][0] != "Unknown":
            print(f"  • Education: {formatted_profile['education'][0]}")
        if formatted_profile['interests'] and formatted_profile['interests'][0] != "Unknown":
            print(f"  • Key interests: {', '.join(formatted_profile['interests'][:3])}")
        
        # Update the context with the structured profile data
        wrapper.context["profile_data"] = formatted_profile
        
        print("✅ Lead research completed")
        return formatted_profile
        
    except Exception as e:
        logger.error(f"Error processing web search results: {str(e)}")
        # Return fallback data that matches the required schema
        fallback_data = {
            "current_role": "Unknown",
            "company": "Unknown",
            "industry": "Unknown",
            "experience": [{"title": "Unknown", "company": "Unknown", "duration": "Unknown"}],
            "education": ["Unknown"],
            "interests": ["Unknown"],
            "recent_activity": f"Error extracting profile information. Error: {str(e)}"
        }
        wrapper.context["profile_data"] = fallback_data
        return fallback_data
