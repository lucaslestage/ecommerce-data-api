from flask import Flask    
import requests

url = "http://localhost:5000/users/"

try:
    response = requests.get(url, timeout=5)
    print("Status code:", response.status_code)
    print("Response:", response.json())
except requests.exceptions.ConnectionError:
    print("Impossible de se connecter : le serveur Flask est-il lancé ?")
except requests.exceptions.JSONDecodeError:
    print("La réponse n'est pas du JSON :", response.text)