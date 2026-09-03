from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from models import Query
from prompts import task_classifier_prompt, spot_recommendation_prompt, food_recommendation_prompt, budget_recommendation_prompt, all_recommendation_prompt

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-3.7-flash",
    temperature=1.0,
)

parser = PydanticOutputParser(pydantic_object=Query)
prompt = PromptTemplate(template=task_classifier_prompt, input_variables=["query"], partial_variables={
    "format_instructions": parser.get_format_instructions()
})


classifier_chain = prompt | model | parser

string_parser = StrOutputParser()

# prompt templates for different tasks
all_recommendation_prompt = PromptTemplate(template=all_recommendation_prompt, input_variables=["query"])
food_recommendation_prompt = PromptTemplate(template=food_recommendation_prompt, input_variables=["query"])
spot_recommendation_prompt = PromptTemplate(template=spot_recommendation_prompt, input_variables=["query"])
budget_recommendation_prompt = PromptTemplate(template=budget_recommendation_prompt, input_variables=["query"])


# chains for different tasks
all_chain = all_recommendation_prompt | model | string_parser
food_chain = food_recommendation_prompt | model | string_parser
spot_chain = spot_recommendation_prompt | model | string_parser
budget_chain = budget_recommendation_prompt | model | string_parser

# general fallback chain for unclassified queries
general_prompt  =  PromptTemplate(template="You are a helpful assistant. Answer the following question: {query}", input_variables=["query"])
general_chain = general_prompt | model | string_parser

