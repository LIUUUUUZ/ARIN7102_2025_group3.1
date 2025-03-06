"""
Web-based Demo App for the Streamlit-NewsAPI Connector.

Author:
    @dcarpintero : https://github.com/dcarpintero
"""
import streamlit as st
import pandas as pd

from typing import Any, Dict, List, Optional
from datetime import datetime
import requests

from streamlit.connections import BaseConnection
from streamlit.runtime.caching import cache_data

from typing import Any, Dict, Optional
from requests.adapters import HTTPAdapter


st.set_page_config(
    page_title="Online Health Science Knowledge Chatbot News",
    page_icon="👋",
)

class NewsAPIConnection(BaseConnection[requests.session]):
    """
    Handles a connection with the NewsAPI and retrieves news articles.

    See also: https://docs.streamlit.io/library/advanced-features/connecting-to-data#build-your-own-connection
              https://newsapi.org/docs 
    """

    def _connect(self, **kwargs) -> requests.session:
        """
        Initializes the connection parameters and creates a persistent requests.Session for connecting with the NewsAPI.
        The Session object uses an HTTPAdapter to allow for maximum retries in case of network issues.

        See also: https://docs.python-requests.org/en/latest/user/advanced/#session-objects

        :return: A requests.Session object, with a mounted HTTPAdapter for connection retries
        """
        self.key = kwargs.get('NEWSAPI_KEY') or st.secrets['NEWSAPI_KEY']
        if not self.key:
            raise ValueError('Missing NEWSAPI_KEY')

        self.base = kwargs.get(
            'NEWSAPI_BASE_URL') or st.secrets['NEWSAPI_BASE_URL']
        if not self.base:
            raise ValueError('Missing NEWSAPI_BASE_URL')

        self.retries = kwargs.get('NEWSAPI_MAX_RETRIES') or st.secrets.get(
            'NEWSAPI_MAX_RETRIES', 5)

        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=self.retries))
        return self.session

    def cursor(self) -> requests.Session:
        """
        Gets the current session object, creating a new one if it doesn't exist.

        :return: A requests.Session object for making API requests
        """
        if self.session is None:
            self._connect()
        return self.session

    def everything(self, ttl: int = 3600, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieves News Articles on a specific topic from the NewsAPI.
        The results are cached for a period specified by ttl.

        :param kwargs: Requests parameters as defined in https://newsapi.org/docs/endpoints/everything
        :param ttl: Duration to cache the result (in seconds)

        :return: Dictionary containing:
            - status: If the request was successful or not
            - totalResults: The total number of results available for your request.
            - articles: The results of the request.
        """
        @cache_data(ttl=ttl)
        def _everything(**_kwargs) -> Optional[Dict[str, Any]]:
            """
            Performs the actual API call and data conversion.
            """
            url = f"{self.base}everything?apiKey={self.key}"
            return self._make_api_request(url=url, params=_kwargs)

        return _everything(**kwargs)

    def top_headlines(self, ttl: int = 3600, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieves Top-Headlines Articles in a specific country ('US' by default) and category from the NewsAPI.
        The results are cached for a period specified by ttl.

        :param kwargs: Requests parameters as defined in https://newsapi.org/docs/endpoints/top-headlines
        :param ttl: Duration to cache the result (in seconds)
        :return: Dictionary containing:
            - status: If the request was successful or not
            - totalResults: The total number of results available for your request.
            - articles: The results of the request.
        """
        @cache_data(ttl=ttl)
        def _top_headlines(**_kwargs) -> Optional[Dict[str, Any]]:
            """
            Performs the actual API call and data conversion.
            """
            url = f"{self.base}top-headlines?apiKey={self.key}"
            return self._make_api_request(url=url, params=_kwargs)

        return _top_headlines(**kwargs)

    def _make_api_request(self, url: str, params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Performs a GET request to the provided URL and returns the parsed JSON response.

        :param url: URL to send the GET request to
        :return: JSON response data as a dictionary, None in case of an error
        """
        try:
            response = self.cursor().get(url=url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get('results') == 0 or data.get('status') != 'ok':
                return None
            return data
        except (requests.exceptions.RequestException, ValueError) as e:
            st.error(f'NewsAPI Server Error')
            return None

def get_country_code(name: str) -> str:
    """Return the 2-letter country code for a given country name."""
    if name.lower() == "united states" or name.lower() == "usa" or name.lower() == "us":
        return "us"
    else:
        raise ValueError(f'No country code found for "{name}"')



def format_date(date_string: str) -> Optional[str]:
    try:
        date = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        return None
    return date.strftime('%d %B %Y')


def to_dataframe(data: Optional[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    """
    Converts the JSON data containing News Articles into a DataFrame.

    :param data: JSON data from the NewsAPI response
    :return: DataFrame of News Articles, None if no Articles were found
    """
    if data is None:
        return None

    articles = data.get('articles', None)
    return pd.DataFrame(articles)


COUNTRY_CODES = ['us']

COUNTRY_NAMES = ['United States']


def sidebar():
    """Configure the sidebar and return the user's preferences."""
    st.sidebar.header("📰 News settings")
    with st.sidebar.expander("🔎 TOPIC", expanded=True):
        topic = st.text_input(
            'Keywords or phrases to search in the News', 'Health')
        topic = topic.strip()
        if not topic:
            st.warning('Please enter a valid topic.')
        if "topic" not in st.session_state:
            st.session_state.topic = topic
        else:
            if st.session_state.topic != topic:
                st.session_state.topic = topic
                st.session_state.active_tab = 'tab_topic'

    with st.sidebar.expander("🔝 TOP-STORIES", expanded=True):
        category = st.selectbox(
            'Category', ('Business', 'Entertainment', 'General', 'Health', 'Science', 'Sports', 'Technology'), index=3)

        # country = st.selectbox('Country/Region', COUNTRY_NAMES, index=51, disabled=True)
        country = COUNTRY_NAMES[0]

        if "category" not in st.session_state:
            st.session_state.category = category
        else:
            if st.session_state.category != category:
                st.session_state.category = category
                st.session_state.active_tab = 'tab_headlines'

    # with st.sidebar.expander("🔧 FIELDS", expanded=True):
    #     fields = st.multiselect(
    #         "Fields",
    #         ['source', 'author', 'title', 'description',
    #             'url', 'urlToImage', 'publishedAt', 'content'],
    #         ['title', 'description', 'url', 'publishedAt'],
    #         key="Fields",
    #         label_visibility="hidden"
    #     )

    feed = st.sidebar.slider('Story Feed', min_value=0,
                             max_value=100, value=10, step=5)

    return topic, category, country, "", feed


def display_news(df, feed=5):
    if df is None:
        st.info("No News")
    else:
        for i in range(min(feed, len(df))):
            story = df.iloc[i]

            title = story["title"]
            url = story["url"]
            urlToImage = story["urlToImage"]
            publishedAt = format_date(story["publishedAt"])

            if title is not None:
                if publishedAt is not None:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if urlToImage is not None:
                            st.image(urlToImage, width=150)
                    with col2:
                        st.markdown(f'[{title}]({url})')
                        st.text(publishedAt)


def display_news_as_raw(df, fields):
    if df is None:
        st.info("No News")
    else:
        st.dataframe(df[fields], hide_index=True)


def layout(conn_newsapi, topic, category, country, fields, feed):
    """
    Defines Interface Layout
    """
    st.header("📰 Your Briefing Articles")

    
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'tab_headlines'

    if st.session_state.active_tab == 'tab_headlines':
        tab_headlines, tab_topic  = st.tabs([f'Top Stories in {category}', topic])
    
    else:
        tab_topic, tab_headlines = st.tabs([f'{topic}', category])

    # Your Topic
    with tab_topic:
        if topic:
            data = conn_newsapi.everything(q=topic)
            df = to_dataframe(data)
            display_news(df, feed)

    # Top Stories
    with tab_headlines:
        data = conn_newsapi.top_headlines(
            country=get_country_code(country), category=category)
        df = to_dataframe(data)
        display_news(df, feed)


if st.session_state.get("is_logged_in"):
    st.sidebar.success("Welcome, " + st.session_state["username"] + "!")
    st.sidebar.page_link(page="./Homepage.py", label="Homepage")
    st.sidebar.page_link(page="pages/chatbot.py", label="Chatbot")
    st.sidebar.page_link(page="pages/news.py", label="News")
    if st.session_state.username == "admin":
        st.sidebar.page_link(page="pages/admin.py", label="Admin")

    conn_newsapi = st.connection(
        "NewsAPI", type=NewsAPIConnection)
    topic, category, country, fields, feed = sidebar()
    layout(conn_newsapi, topic, category, country, fields, feed)

else:
    st.switch_page("./Homepage.py")