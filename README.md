## 🚀 セットアップ手順

### 1. 仮想環境の作成・有効化

```bash
python -m venv venv
source venv/bin/activate  # Windows の場合: venv\Scripts\activate
```

### 2. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

プロジェクト直下に `.env` ファイルを作成し、以下のように記述します：

```env
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_API_KEY=<your-azure-search-key>
AZURE_OPENAI_ENDPOINT=https://<your-openai-endpoint>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-openai-key>
NOTION_API_KEY=<your-notion-api-key>
NOTION_DATABASE_ID=<your-notion-database-ID>
```

※ `.env.sample` にサンプルを用意しています

---

## ▶️ アプリの起動

```bash
streamlit run app.py
```