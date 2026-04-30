import os
from decouple import config

os.environ["GEMINI_API_KEY"] = config("GEMINI_API_KEY")

import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

for m in genai.list_models():
    if 'embedContent' in m.supported_generation_methods:
        print(m.name)
