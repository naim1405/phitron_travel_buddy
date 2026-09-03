from pydantic import BaseModel
from enum import Enum
from dataclasses import dataclass
from langchain.messages import HumanMessage, AIMessage


class Message(BaseModel):
    role: str
    content: str

class QueryType(str, Enum):
    ALL = "all"
    SPOTS = "spots"
    FOOD = "food"
    BUDGET = "budget"
    GENERAL = "general"
    
        
class Query(BaseModel):
    query: str
    type: QueryType
    history: list[HumanMessage | AIMessage] = []


@dataclass
class UserInput:
    query: str
    history: list[HumanMessage | AIMessage]
    type: QueryType
