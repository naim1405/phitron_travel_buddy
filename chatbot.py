from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnableParallel
from models import Query, QueryType
from prompts import task_classifier_prompt_template , spot_recommendation_prompt_template , food_recommendation_prompt_template , budget_recommendation_prompt_template , all_recommendation_prompt_template, general_prompt_template

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
)

parser = PydanticOutputParser(pydantic_object=Query)
prompt = PromptTemplate(template=task_classifier_prompt_template , input_variables=["query"], partial_variables={
    "format_instructions": parser.get_format_instructions()
})


classifier_chain = prompt | model | parser

string_parser = StrOutputParser()

# prompt templates for different tasks
food_recommendation_prompt = PromptTemplate(template=food_recommendation_prompt_template , input_variables=["query"])
spot_recommendation_prompt = PromptTemplate(template=spot_recommendation_prompt_template , input_variables=["query"])
budget_recommendation_prompt = PromptTemplate(template=budget_recommendation_prompt_template , input_variables=["query"])
all_recommendation_prompt  = PromptTemplate(template=all_recommendation_prompt_template , input_variables=["spots", "food", "budget"])


# chains for different tasks
food_chain = food_recommendation_prompt | model | string_parser
spot_chain = spot_recommendation_prompt | model | string_parser
budget_chain = budget_recommendation_prompt | model | string_parser


all_tasks_parallel_chain = RunnableParallel({
    "query": RunnableLambda( lambda query: query),
    "spots": spot_chain,
    "food": food_chain,
    "budget": budget_chain

})


all_merge_chain = all_recommendation_prompt | model | string_parser
all_chain = all_tasks_parallel_chain | all_merge_chain

# general fallback chain for unclassified queries
general_prompt  =  PromptTemplate(template=general_prompt_template , input_variables=["query"])
general_chain = general_prompt | model | string_parser

conditional_chain = RunnableBranch(
    (
        lambda query : query.type == QueryType.ALL, RunnableLambda(lambda q : all_chain.invoke(q.query))
    ),
    (
        lambda query : query.type == QueryType.FOOD, RunnableLambda(lambda q : food_chain.invoke(q.query))
    ),
    (
        lambda query : query.type == QueryType.SPOTS, RunnableLambda(lambda q : spot_chain.invoke(q.query))
    ),
    (
        lambda query : query.type == QueryType.BUDGET, RunnableLambda(lambda q : budget_chain.invoke(q.query))
    ),
    general_chain
)



chatbot = classifier_chain | conditional_chain

def ask_ai(query: str) -> str:
    return chatbot.invoke({"query": query})

if __name__ == "__main__":
    result = chatbot.invoke({
        "query": "I'm going to Cox's Bazar for 3 days. What should I do, eat, and how much will it cost?"
    })

    print(result)
