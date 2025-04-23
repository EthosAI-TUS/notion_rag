import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import openai

from dotenv import load_dotenv
load_dotenv()

# インデックス名の指定
index_name = "index1"
# Cognitive SearchのエンドポイントとAPIキーを指定
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_API_KEY"]

# OpenAIのAPIキーを設定 
openai.api_type = 'azure'
openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]
openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]
model_name = "text-embedding-3-large"
openai.api_version = "2024-02-01"

# 検索クエリの指定
search_word = "採用に関する会議の内容なんだっけ？"

response_search_word_vector = openai.Embedding.create(input=search_word, engine=model_name)
client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

results = client.search(
    search_text="",
    include_total_count=True,
    vectors=[
        {
            "value": response_search_word_vector['data'][0]['embedding'],
            "k": 3,
            "fields": 'text_vector'
        }
    ]
)

results_text = ""
for result in results:
    store_info = f"""
会議体種別: {result["category"]}
議事録: {result["text"]}"""

    results_text += store_info + "\n---\n"
print(results_text)
