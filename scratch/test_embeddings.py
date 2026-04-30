import os
from decouple import config

os.environ["GEMINI_API_KEY"] = config("GEMINI_API_KEY")

from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
)

texts = ["Hello", "World", "Foo", "Bar"]
res = embeddings.embed_documents(texts)
print(f"Number of input texts: {len(texts)}")
print(f"Number of embeddings returned: {len(res)}")
