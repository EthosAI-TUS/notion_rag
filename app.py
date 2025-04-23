import os

import streamlit as st
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
emb_model_name = "text-embedding-3-large"
llm_model_name = "gpt-4o"
openai.api_version = "2024-02-01"

search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

# Embeddingを取得する関数
def get_embedding(text):
    response = openai.Embedding.create(input=text, engine=emb_model_name)
    return response["data"][0]["embedding"]

# Azure Cognitive Searchから結果を取得する関数
def cognitive_search(query, k=3):
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

# LLMにプロンプトを渡して回答を取得する関数
def generate_response(question, context_docs):
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

# Streamlit UIの構築
st.title("📚 Azure RAG Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

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

    # LLMからの回答を生成
    with st.spinner("回答生成中..."):
        answer = generate_response(prompt, docs)

    # 回答を表示
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
