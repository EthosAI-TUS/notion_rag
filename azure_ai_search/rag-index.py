import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    CorsOptions,
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswVectorSearchAlgorithmConfiguration,
)

from dotenv import load_dotenv
load_dotenv()

# Cognitive SearchのエンドポイントとAPIキーを指定
endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
key = os.environ["AZURE_SEARCH_API_KEY"]

# Cognitive Search Clientの作成
client = SearchIndexClient(endpoint, AzureKeyCredential(key))
# インデックス名の指定
name = "index1"

# インデックスのフィールドを定義
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True),
    SearchableField(name="text", type=SearchFieldDataType.String,searchable=True), 
    SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True,vector_search_dimensions=3072, vector_search_configuration='vectorConfig'), 
]
cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
scoring_profiles = []

# ベクター検索用の設定を定義
vector_search = VectorSearch(
    algorithm_configurations=[
        HnswVectorSearchAlgorithmConfiguration(
            name="vectorConfig",
            kind="hnsw",
            parameters={
                "m": 4,
                "efConstruction": 400,
                "efSearch": 500,
                "metric": "cosine"
            }
        )
    ]
)

# インデックスの作成
index = SearchIndex(
    name=name,
    fields=fields,
    scoring_profiles=scoring_profiles,
    vector_search=vector_search,
    cors_options=cors_options)

result = client.create_index(index)