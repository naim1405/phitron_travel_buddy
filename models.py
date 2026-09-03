from pydantic import BaseModel
from enum import Enum


class Message(BaseModel):
    role: str
    content: str

class QueryType(str, Enum):
    ALL = "all"
    SPOTS = "spots"
    FOOD = "food"
    BUDGET = "budget"
    
        
class Query(BaseModel):
    query: str
    type: QueryType
