from urllib.parse import urlparse, urljoin
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_website_status(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers,verify=False)
        if response.status_code == 200:
            print(f"Website {url} is up and running.")
        else:
            print(f"Website {url} returned status code {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"Website {url} is down. Error: {e}")

# Example usage
check_website_status("https://ict.dienbien.gov.vn/")
