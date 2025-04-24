import streamlit as st
from time import sleep


class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def delete_user(self):
        st.session_state.cd.delete_user(self.name)


if st.session_state.get("is_logged_in"):

    st.sidebar.success("Welcome, " + st.session_state["username"] + "!")
    st.sidebar.page_link(page="./Homepage.py", label="Homepage")
    st.sidebar.page_link(page="pages/chatbot.py", label="Chatbot")
    st.sidebar.page_link(page="pages/news.py", label="News")
    st.sidebar.page_link(page="pages/biomarker.py", label="Biomarker")
    st.sidebar.page_link(page="pages/admin.py", label="Admin")

    with st.container():
        user_col = st.tabs(["Users"])
        total_users = st.session_state.cd.get_all_users()
        l = len(total_users)
        with st.container():
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.markdown(
                    "<h5 style='text-align: center;'>Name</h4>", unsafe_allow_html=True)
            with c2:
                st.markdown(
                    "<h5 style='text-align: center;'>Email</h4>", unsafe_allow_html=True)
            with c3:
                pass
            for i in range(l):
                with st.container(border=True):
                    user = User(
                        total_users[i]['name'], total_users[i]['email'], total_users[i]['password'])
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        st.markdown(
                            f"<h5 style='text-align: center;'>{user.name}</h4>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(
                            f"<h5 style='text-align: center;'>{user.email}</h4>", unsafe_allow_html=True)
                    with c3:
                        if user.name == "admin":
                            delete = st.button(
                                "Delete User", key=i, disabled=True)
                        else:
                            delete = st.button("Delete User", key=i)
                    if delete:
                        user.delete_user()
                        st.success("User deleted successfully")
                        sleep(1)
                        st.rerun()


else:
    st.switch_page("./Homepage.py")
