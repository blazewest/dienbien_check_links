import requests

Token = "7432171143:AAFyI9QZvf0Bak_CxOPhhhFhucoOzbug8Hc"
chat_id = "-4215174731"

# url = f"https://api.telegram.org/bot{Token}/getUpdates"
# print(requests.get(url).json())

message = "test"
url = f"https://api.telegram.org/bot{Token}/sendMessage?chat_id={chat_id}&text={message}"

r = requests.get(url)
print((r.json()))