import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_website_status(url, proxies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            print(f"Website {url} is up and running.")
        else:
            print(f"Website {url} returned status code {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"Website {url} is down. Error: {e}")

# Example usage with proxy
proxies = {
    'http': 'http://8.8.8.8:8080',  # Replace with your HTTP proxy
    'https': 'http://8.8.8.8:8080'  # Replace with your HTTPS proxy
}
check_website_status("https://hscv.stnmt.dienbien.gov.vn", proxies)
