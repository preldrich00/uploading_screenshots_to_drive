from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=api_key)

models = client.models.list()

for model in models.data:
    print(model.id)
