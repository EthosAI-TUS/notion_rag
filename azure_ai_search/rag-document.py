import os
import time
import textwrap

from dotenv import load_dotenv
from notion_client import Client
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import openai

load_dotenv()

# --- Notion API ---
notion = Client(auth=os.getenv("NOTION_API_KEY"))
DB_ID = os.getenv("NOTION_DATABASE_ID")

# --- Azure OpenAI設定 ---
openai.api_type = "azure"
openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]
openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]
openai.api_version = "2024-02-01"
model_name = "text-embedding-3-large"

# --- Azure Cognitive Search設定 ---
index_name = "index1"
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_API_KEY"]
search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

# --- Notionからドキュメント取得＆整形 ---
documents = []
pages = notion.databases.query(database_id=DB_ID)["results"]

for page in pages:
    page_id = page["id"]
    title_elements = page["properties"]["名前"]["title"]
    title = title_elements[0]["plain_text"] if title_elements else "Untitled"

    blocks = notion.blocks.children.list(block_id=page_id)["results"]
    body_lines = []

    for block in blocks:
        block_type = block["type"]
        if "rich_text" in block[block_type]:
            texts = block[block_type]["rich_text"]
            body_lines.append("".join([t["plain_text"] for t in texts]))

    full_text = textwrap.dedent("\n".join(body_lines))

    try:
        response = openai.Embedding.create(input=full_text, engine=model_name)
        embedding = response["data"][0]["embedding"]
        time.sleep(10)
    except:
        continue

    documents.append({
        "id": page_id,
        "category": title,
        "text": full_text,
        "text_vector": embedding,
    })

# --- Azure Searchへアップロード ---
if documents:
    search_client.upload_documents(documents=documents)
