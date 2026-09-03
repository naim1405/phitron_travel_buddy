import streamlit as st
from models import Message
from chatbot import ask_ai
from langchain.messages import HumanMessage, AIMessage


if "messages" not in st.session_state:
    st.session_state.messages = []


# Header
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.header("Travel Buddy! :airplane: :earth_americas: :world_map:")



# chat history sidebar
with st.sidebar:
    st.header("Chat history", divider="orange")
    for item in st.session_state.messages:
        if isinstance(item, HumanMessage):
            st.header(item.content, divider="orange")

# conversation 
for item in st.session_state.messages:
    role = "assistant" if isinstance(item, AIMessage) else "user"
    with st.chat_message(role):
        st.markdown(item.content)


if prompt := st.chat_input("Ask me anything"):
    # display user msg and add to chat history
    with st.chat_message("user"):
        st.markdown(prompt)
    st.sidebar.header(prompt, divider="orange")

    # generate assistant response and add to chat history
    ai_response = ask_ai(prompt, st.session_state.messages)
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.session_state.messages.append(AIMessage(content=ai_response))
    with st.chat_message("assistant"):
        st.markdown(ai_response)

