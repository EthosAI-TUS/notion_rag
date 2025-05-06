import os
import time
import textwrap
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from notion_client import Client
import openai

from dotenv import load_dotenv
load_dotenv()

# 環境変数のバリデーション
required_env_vars = [
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "NOTION_API_KEY",
    "NOTION_DATABASE_ID"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Azure AI Search設定
index_name = "index1"
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_API_KEY"]
search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

# Azure OpenAI設定
openai.api_type = 'azure'
openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]
openai.api_key = os.environ["AZURE_OPENAI_API_KEY"]
emb_model_name = "text-embedding-3-large"
llm_model_name = "gpt-4o"
openai.api_version = "2024-02-01"

# Notion設定
notion = Client(auth=os.environ["NOTION_API_KEY"])
DB_ID = os.environ["NOTION_DATABASE_ID"]

def get_embedding(text, retries=3):
    """テキストのembeddingを取得する関数"""
    for attempt in range(retries):
        try:
            response = openai.Embedding.create(input=text, engine=emb_model_name)
            return response["data"][0]["embedding"]
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1)  # レート制限対策

def initialize_search_index():
    """NotionデータベースからドキュメントをAzure AI Searchに登録する関数"""
    docs = []
    progress_text = "インデックスを更新中..."
    try:
        # Notionからページを取得
        pages = notion.databases.query(database_id=DB_ID)["results"]
        total_pages = len(pages)
        
        progress_bar = st.progress(0, text=progress_text)
        for i, page in enumerate(pages, 1):
            progress_bar.progress(i / total_pages, f"{progress_text} ({i}/{total_pages}ページ処理中)")
            
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

            # Embeddingの生成
            try:
                embedding = get_embedding(full_text)
                time.sleep(1)  # レート制限対策
            except Exception as e:
                st.warning(f"Embedding生成エラー (ID: {page_id}): {str(e)}")
                continue

            doc = {
                "id": page_id,
                "category": title,
                "text": full_text,
                "text_vector": embedding,
            }
            docs.append(doc)

            # Azure AI Searchにアップロード
        if docs:
            result = search_client.upload_documents(documents=docs)
            success_count = sum(1 for r in result if r.succeeded)
            st.success(f"✅ {success_count}/{len(docs)} 件のドキュメントを登録しました")
            progress_bar.empty()
            return True
        else:
            st.warning("⚠️ 登録対象のドキュメントがありませんでした")
            progress_bar.empty()
            return False

    except Exception as e:
        st.error(f"初期化中にエラーが発生しました: {str(e)}")
        progress_bar.empty()
        return False

def cognitive_search(query, k=3):
    """Azure AI Searchで類似文書を検索する関数"""
    try:
        embedding = get_embedding(query)
        results = search_client.search(
            search_text="",
            vectors=[{
                "value": embedding,
                "k": k,
                "fields": "text_vector"
            }]
        )
        documents = []
        for result in results:
            documents.append(result["text"])
        return documents
    except Exception as e:
        st.error(f"検索中にエラーが発生しました: {str(e)}")
        return []

def generate_response(question, context_docs):
    """LLMを使用して回答を生成する関数"""
    try:
        context = "\n\n".join(context_docs)
        prompt = f"""
コンテキストに基づいてユーザーの質問に答えてください。

# コンテキスト
{context}
"""
        completion = openai.ChatCompletion.create(
            engine=llm_model_name,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"回答生成中にエラーが発生しました: {str(e)}")
        return "申し訳ありません。回答の生成中にエラーが発生しました。"

# Streamlit UIの構築
st.title("📚 Azure RAG Chatbot")

# 初期化処理
if "messages" not in st.session_state:
    st.session_state.messages = []

if "initialized" not in st.session_state:
    with st.spinner("データベースを初期化中..."):
        success = initialize_search_index()
        st.session_state.initialized = success

if not st.session_state.initialized:
    st.error("データベースの初期化に失敗しました。ページを更新して再試行してください。")
    st.stop()

# 更新ボタン
if st.sidebar.button("🔄 インデックスを更新"):
    with st.spinner("インデックスを更新中..."):
        success = initialize_search_index()
        if success:
            st.success("インデックスを更新しました")
        else:
            st.error("インデックスの更新に失敗しました")

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力の取得
if prompt := st.chat_input("質問を入力してください。"):
    # ユーザーの質問を表示
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 検索結果を取得
    with st.spinner("検索中..."):
        docs = cognitive_search(prompt)

    if docs:
        # LLMからの回答を生成
        with st.spinner("回答生成中..."):
            answer = generate_response(prompt, docs)

        # 回答を表示
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        with st.chat_message("assistant"):
            st.markdown("申し訳ありません。関連する情報が見つかりませんでした。")
