import requests
from typing import List, Dict

WHO_NEWS_API = "https://www.who.int/api/hubs/newsitems?sf_site=15210d59-ad60-47ff-a542-7ed76645f0c7&sf_provider=OpenAccessDataProvider&sf_culture=en&$orderby=PublicationDateAndTime%20desc&$select=Title,ItemDefaultUrl,FormatedDate,Tag,ThumbnailUrl&%24format=json&%24top=16&%24count=true"


def fetch_who_news() -> List[Dict]:
    try:
        response = requests.get(WHO_NEWS_API, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('value', [])
    except requests.exceptions.RequestException as e:
        print(e)
        return []
    except Exception as e:
        print(e)
        return []
