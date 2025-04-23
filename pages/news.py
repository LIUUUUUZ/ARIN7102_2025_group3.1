import streamlit as st
from datetime import datetime
from utilities.spider import fetch_who_news

st.set_page_config(
    page_title="WHO health news",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.news-card {
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
    transition: transform 0.2s;
    background: white;
}
.news-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.12);
}
.news-image {
    border-radius: 10px;
    object-fit: cover;
    height: 220px;
}
.tag-badge {
    display: inline-block;
    padding: 0.25em 0.8em;
    border-radius: 20px;
    background: #e3f2fd;
    color: #2196f3;
    font-size: 0.85em;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.loading-spinner {
    animation: spin 1s linear infinite;
    font-size: 2rem;
}
</style>
""", unsafe_allow_html=True)


def format_news_url(item_url: str) -> str:
    return f"https://who.int/news/item{item_url}"


st.title("🌐 WHO global health news")
st.caption("The news is from official website of WHO (update per 5 min)")

if not st.session_state.get("is_logged_in"):
    st.switch_page("./Homepage.py")

st.sidebar.success("Welcome, " + st.session_state["username"] + "!")
st.sidebar.page_link(page="./Homepage.py", label="Homepage")
st.sidebar.page_link(page="pages/chatbot.py", label="Chatbot")
st.sidebar.page_link(page="pages/news.py", label="News")
if st.session_state.username == "admin":
    st.sidebar.page_link(page="pages/admin.py", label="Admin")

with st.status("loading...", expanded=True) as status:
    news_data = fetch_who_news()
    status.update(label="done！", state="complete", expanded=False)

if not news_data:
    st.error("⚠️ Fail to load news now. Please try it later...")
    st.switch_page("./Homepage")

for news in news_data:
    with st.container():
        col_img, col_content = st.columns([1, 3], gap="large")

        with col_img:
            thumbnail = news.get("ThumbnailUrl")
            if thumbnail:
                st.markdown(
                    f'<img src="{thumbnail}" class="news-image" alt="preface">',
                    unsafe_allow_html=True
                )
            else:
                st.image(
                    "https://via.placeholder.com/400x220.png?text=No+Preview",
                    use_column_width=True,
                    caption="No images"
                )

        with col_content:
            news_url = format_news_url(news["ItemDefaultUrl"])

            col_tag, col_date = st.columns([1, 4])
            with col_tag:
                st.markdown(
                    f'<div class="tag-badge">{news.get("Tag", "Latest update")}</div>',
                    unsafe_allow_html=True
                )
            with col_date:
                date_str = datetime.strptime(
                    news["FormatedDate"], "%d %B %Y"
                ).strftime("%Y/%m/%d")
                st.caption(f"🗓️ Publish time：{date_str}")

            st.markdown(f"### {news['Title']}")
            st.markdown(
                f'<a href="{news_url}" target="_blank" style="text-decoration:none;">'
                '🌐 Read details →'
                '</a>',
                unsafe_allow_html=True
            )

            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
