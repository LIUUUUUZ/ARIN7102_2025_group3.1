import streamlit as st
from st_chat_message import message
import time

st.set_page_config(
    page_title="Online Health Science Knowledge Chatbot",
    page_icon="👋",
    layout="wide",
)

# State management functions


def reset_states():
    st.session_state.update({
        "is_idle": True,
        "is_processing": False,
        "is_responding": False,
        "has_suggestions": False,
        "current_stream": None
    })


def clear_message():
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "content": "I am the Online Health Science Knowledge Chatbot serving ARIN7102 Group3.1. How can I assist you?", "type": "content"})
    st.session_state.new_message = ""
    st.session_state.chat_bot.reset()
    reset_states()


def clear_text():
    st.session_state.new_message = st.session_state["chat_input"]
    st.session_state["chat_input"] = ""
    st.session_state.has_suggestions = False


def click_suggestion():
    st.session_state.new_message = question
    st.session_state.has_suggestions = False


required_states = {
    "new_message": "",
    "messages": [],
    "current_stream": None,
    "reasoning_buffer": "",
    "last_render_time": 0,
    "is_idle": True,
    "is_processing": False,
    "is_responding": False,
    "has_suggestions": False
}

for key, default_value in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

if not st.session_state.get("is_logged_in"):
    st.switch_page("./Homepage.py")

# UI Components
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

# Chat display
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

    # Suggestions rendering
    if st.session_state.has_suggestions:
        suggestions = st.session_state.chat_bot.generate_nq()
        with st.container():
            cols = st.columns(3)
            for col, question in zip(cols, suggestions):
                with col:
                    st.button(
                        question,
                        key=f"suggest_{hash(question)}",
                        use_container_width=True,
                        on_click=click_suggestion
                    )

# Input handling
st.text_input(
    "💬 Chat Input",
    key="chat_input",
    placeholder="Type your message here...",
    label_visibility="collapsed",
    on_change=clear_text
)

# State machine logic
# State 1: Handle new input
if st.session_state.is_idle and st.session_state.new_message:
    user_input = st.session_state.new_message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.new_message = ""
    st.session_state.is_idle = False
    st.session_state.is_processing = True
    st.rerun()

# State 2: Process input and generate response
if st.session_state.is_processing:
    try:
        st.session_state.current_stream = st.session_state.chat_bot.generate_response(
            st.session_state.messages[-1]["content"]
        )
        st.session_state.messages.extend([
            {"role": "assistant", "type": "reasoning", "content": ""},
            {"role": "assistant", "type": "content", "content": ""}
        ])
        st.session_state.is_processing = False
        st.session_state.is_responding = True
        st.session_state.reasoning_buffer = ""
        st.session_state.last_render_time = 0
        st.rerun()
    except Exception as e:
        st.error(str(e))
        reset_states()
        st.rerun()

if st.session_state.is_responding and st.session_state.current_stream:
    chunks = []
    start_time = time.time()
    stream_exhausted = False

    try:
      # 批量处理chunk
        while (time.time() - start_time) < 0.3:
            chunk = next(st.session_state.current_stream)
            chunks.append(chunk)

    except StopIteration:
        stream_exhausted = True  # 标记流已耗尽
    except Exception as e:
        st.error(str(e))
        reset_states()
        st.rerun()
    else:
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
        if len(chunks) >= 3 or \
           (time.time() - st.session_state.last_render_time) > 0.2 or \
           len(st.session_state.reasoning_buffer) > 100:
            should_render = True

        if st.session_state.reasoning_buffer:
            st.session_state.messages[-2]["content"] += st.session_state.reasoning_buffer
            st.session_state.reasoning_buffer = ""

        if should_render or content_updates:
            st.session_state.last_render_time = time.time()
            st.rerun()

    finally:
        if stream_exhausted:
            if st.session_state.reasoning_buffer:
                st.session_state.messages[-2]["content"] += st.session_state.reasoning_buffer
                st.session_state.reasoning_buffer = ""

            st.session_state.last_render_time = 0
            st.session_state.current_stream = None
            st.session_state.is_responding = False
            st.session_state.is_idle = True
            st.session_state.has_suggestions = (
                len(st.session_state.messages) > 1 and
                st.session_state.messages[-1]["role"] == "assistant" and
                st.session_state.messages[-1]["type"] == "content"
            )
            st.rerun()
