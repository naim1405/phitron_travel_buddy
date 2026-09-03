from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnableParallel
from models import Query, QueryType, UserInput
from prompts import task_classifier_prompt_template , spot_recommendation_prompt_template , food_recommendation_prompt_template , budget_recommendation_prompt_template , all_recommendation_prompt_template, general_prompt_template
from langchain.messages import HumanMessage, AIMessage


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
food_recommendation_prompt = PromptTemplate(template=food_recommendation_prompt_template , input_variables=["query", "history"])
spot_recommendation_prompt = PromptTemplate(template=spot_recommendation_prompt_template , input_variables=["query", "history"])
budget_recommendation_prompt = PromptTemplate(template=budget_recommendation_prompt_template , input_variables=["query", "history"])
all_recommendation_prompt  = PromptTemplate(template=all_recommendation_prompt_template , input_variables=["spots", "food", "budget", "history"])


# chains for different tasks
food_chain = food_recommendation_prompt | model | string_parser
spot_chain = spot_recommendation_prompt | model | string_parser
budget_chain = budget_recommendation_prompt | model | string_parser


all_tasks_parallel_chain = RunnableParallel({
    "query": RunnableLambda( lambda query: query.query),
    "history": RunnableLambda(lambda query: query.history),
    "spots": RunnableLambda(lambda q : spot_chain.invoke({"query":q.query, "history":q.history})),
    "food": RunnableLambda(lambda q : food_chain.invoke({"query":q.query, "history":q.history})),
    "budget":RunnableLambda(lambda q : budget_chain.invoke({"query":q.query, "history":q.history})) 


})


all_merge_chain = all_recommendation_prompt | model | string_parser
all_chain = all_tasks_parallel_chain | all_merge_chain

# general fallback chain for unclassified queries
general_prompt  =  PromptTemplate(template=general_prompt_template , input_variables=["query", "history"])
general_chain = general_prompt | model | string_parser

conditional_chain = RunnableBranch(
    (
        lambda user_input: user_input.type == QueryType.ALL,  all_chain
    ),
    (
        lambda user_input: user_input.type == QueryType.FOOD, RunnableLambda(lambda q : food_chain.invoke({"query":q.query, "history":q.history}))
    ),
    (
        lambda user_input : user_input.type == QueryType.SPOTS, RunnableLambda(lambda q : spot_chain.invoke({"query":q.query, "history":q.history}))
    ),
    (
        lambda user_input: user_input.type == QueryType.BUDGET, RunnableLambda(lambda q : budget_chain.invoke({"query":q.query, "history":q.history}))
    ),
    RunnableLambda(lambda q : general_chain.invoke({"query":q.query, "history":q.history}))
)



chatbot = conditional_chain

def classify_query(query: str) -> Query:
    return classifier_chain.invoke({"query": query})

def ask_ai(query: str, history : list[AIMessage | HumanMessage]) -> str:
    user_query = classifier_chain.invoke({"query": query})
    user_input = UserInput(query=user_query.query, history=history, type=user_query.type)
    return chatbot.invoke(user_input)

if __name__ == "__main__":
    result = ask_ai("I'm going to Cox's Bazar for 3 days. What should I do, eat, and how much will it cost?", [])
    print(result)
