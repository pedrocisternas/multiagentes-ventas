from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SalesContext:
    name: Optional[str]
    linkedin_url: Optional[str]
    description: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    email_draft: Optional[str] = None
