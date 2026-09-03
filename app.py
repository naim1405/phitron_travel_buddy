import streamlit as st
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


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
for item in st.session_state.chat_history:
    with st.sidebar:
        st.header(item, divider="orange")

# conversation 
for item in st.session_state.messages:
    with st.chat_message(item.role):
        st.markdown(item.content)


if prompt := st.chat_input("Ask me anything"):
    # display user msg and add to chat history
    usr_msg = Message(role="user", content=prompt)
    st.session_state.messages.append(usr_msg)
    st.session_state.chat_history.append(prompt)
    with st.chat_message(usr_msg.role):
        st.markdown(usr_msg.content)
    st.sidebar.header(prompt, divider="orange")

    # generate assistant response and add to chat history
    assistant_msg = Message(role="assistant", content="Echo: ")
    st.session_state.messages.append(assistant_msg)
    with st.chat_message(assistant_msg.role):
        st.markdown(assistant_msg.content)

