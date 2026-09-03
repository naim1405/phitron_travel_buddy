from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import Query
from prompts import task_classifier_prompt 

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


