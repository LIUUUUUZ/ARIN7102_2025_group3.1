import streamlit as st
from st_chat_message import message
import time

st.set_page_config(
    page_title="Online Health Science Knowledge Chatbot",
    page_icon="👋",
    layout="wide",
)


def clear_message():
    st.session_state.messages = []
    st.session_state.new_message = ""
    st.session_state.chat_bot.reset()
    st.session_state.pending_response = False
    st.session_state.reasoning_buffer = ""


def clear_text():
    st.session_state.new_message = st.session_state["chat_input"]
    st.session_state["chat_input"] = ""


required_states = {
    "new_message": "",
    "messages": [],
    "current_stream": None,
    "pending_response": False,
    "reasoning_buffer": "",
    "last_render_time": 0
}

for key, default_value in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

if not st.session_state.get("is_logged_in"):
    st.switch_page("./Homepage.py")

st.sidebar.success("Welcome, " + st.session_state["username"] + "!")
st.sidebar.page_link(page="./Homepage.py", label="Homepage")
st.sidebar.page_link(page="pages/chatbot.py", label="Chatbot")
st.sidebar.page_link(page="pages/news.py", label="News")
if st.session_state.username == "admin":
    st.sidebar.page_link(page="pages/admin.py", label="Admin")

chat_container = st.container()
with chat_container:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("## 🤖 💬 ChatBot")
    with col2:
        if len(st.session_state.messages) > 1:
            st.button("🗑️ Clear Chat", on_click=clear_message)

with st.container(height=550, border=True, key="chat-container"):
    messages = st.session_state.messages
    for idx, m in enumerate(messages):
        if m["role"] == "user":
            message(m["content"], is_user=True, key=f"user_{idx}")
        elif m["type"] == "reasoning":
            message(
                f"💭 {m['content']}",
                is_user=False,
                avatar_style="pixel-art",
                key=f"assistant_reasoning_{idx}",
            )
        elif m["type"] == "content":
            message(
                m["content"],
                is_user=False,
                avatar_style="bottts",
                key=f"assistant_content_{idx}",
            )

st.text_input(
    "💬 Chat Input",
    key="chat_input",
    placeholder="Type your message here...",
    label_visibility="collapsed",
    on_change=clear_text
)

if st.session_state.new_message and not st.session_state.pending_response:
    user_input = st.session_state.new_message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.new_message = ""
    st.session_state.pending_response = True
    st.rerun()

if st.session_state.pending_response:
    st.session_state.current_stream = st.session_state.chat_bot.generate_response(
        st.session_state.messages[-1]["content"]
    )
    st.session_state.messages.extend([
        {"role": "assistant", "type": "reasoning", "content": ""},
        {"role": "assistant", "type": "content", "content": ""}
    ])
    st.session_state.pending_response = False
    st.session_state.reasoning_buffer = ""
    st.session_state.last_render_time = time.time()

if st.session_state.current_stream:
    chunks = []
    start_time = time.time()
    try:
        while len(chunks) < 10 and (time.time() - start_time) < 0.3:
            chunk = next(st.session_state.current_stream)
            chunks.append(chunk)

        reasoning_updates = []
        content_updates = []
        for chunk in chunks:
            if chunk.get("reasoning"):
                reasoning_updates.append(chunk["reasoning"])
            if chunk.get("content"):
                content_updates.append(chunk["content"])

        if reasoning_updates:
            st.session_state.reasoning_buffer += "".join(reasoning_updates)
        if content_updates:
            st.session_state.messages[-1]["content"] += "".join(
                content_updates)

        should_render = False
        if len(chunks) >= 5 or (time.time() - st.session_state.last_render_time) > 0.3:
            should_render = True

        if st.session_state.reasoning_buffer:
            st.session_state.messages[-2]["content"] += st.session_state.reasoning_buffer
            if should_render:
                st.session_state.reasoning_buffer = ""

        if should_render or content_updates:
            st.session_state.last_render_time = time.time()
            st.rerun()

    except StopIteration:
        if st.session_state.reasoning_buffer:
            st.session_state.messages[-2]["content"] += st.session_state.reasoning_buffer
            st.session_state.reasoning_buffer = ""
        del st.session_state.current_stream
        st.rerun()
