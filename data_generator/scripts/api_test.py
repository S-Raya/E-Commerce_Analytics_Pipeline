import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

API_URL=os.getenv("API_URL")
response = requests.get(API_URL)
data = response.json()
with open("data_generator/output/products.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)