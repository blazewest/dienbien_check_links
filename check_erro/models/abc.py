from urllib.parse import urlparse, urljoin
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


url = 'https://hscvlqd.dienbien.gov.vn'
def check_website_status(url):
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            print(f"Website {url} is up and running.")
        else:
            print(f"Website {url} returned status code {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"Website {url} is down. Error: {e}")

# Example usage
check_website_status("https://hscvlqd.dienbien.gov.vn")
