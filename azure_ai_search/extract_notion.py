import json, os, textwrap
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

# Notionクライアントの初期化
notion = Client(auth=os.getenv("NOTION_API_KEY"))
DB_ID = os.getenv("NOTION_DATABASE_ID")

# Notionからドキュメントを取得して整形
docs = []
for page in notion.databases.query(database_id=DB_ID)["results"]:
    # ページIDとタイトルを取得
    page_id = page["id"]
    title_raw = page["properties"]["名前"]["title"]
    title = title_raw[0]["plain_text"] if title_raw else "Untitled"

    # 子ブロックから本文を抽出
    blocks = notion.blocks.children.list(block_id=page_id)["results"]
    body_lines = []
    for b in blocks:
        block_type = b["type"]
        if "rich_text" in b[block_type]:
            rich_text = b[block_type]["rich_text"]
            line = "".join([t["plain_text"] for t in rich_text])
            body_lines.append(line)

    full_text = textwrap.dedent("\n".join(body_lines))

    
    doc = {
        "id": page_id,
        "category": title,
        "text": full_text
    }

    docs.append(doc)

