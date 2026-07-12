# x-auto-bot

2つのAIペルソナ(バズ分析AI / 専門知識AI)に指定テーマについて3往復議論させ、
その内容をもとにXでインプレッションが最大化しやすい140文字以内の投稿文を生成し、
X(Twitter)に自動投稿するNode.jsスクリプトです。

## 構成

```
x-auto-bot/
├── index.js            # エントリーポイント
├── src/
│   ├── config.js        # .env の読み込み・検証
│   ├── personas.js       # 2つのAIペルソナのプロンプト定義
│   ├── debate.js         # AI同士の3往復議論を実行
│   ├── optimize.js       # 議論結果から140字以内の投稿文を生成
│   └── postToX.js        # twitter-api-v2 でXに投稿
├── .env.example
└── package.json
```

## 1. 事前準備

- Node.js 18以上をインストールしてください(未インストールの場合は https://nodejs.org/ から)
- ターミナルで `node -v` を実行し、バージョンが表示されればOKです

## 2. パッケージのインストール

このフォルダ(`x-auto-bot`)で以下を実行します。

```bash
cd x-auto-bot
npm install
```

これで `package.json` に書かれた以下のライブラリがすべてインストールされます。

- `openai` … バズ分析AI(GPT)呼び出し用
- `@anthropic-ai/sdk` … 専門知識AI(Claude)呼び出し用
- `twitter-api-v2` … Xへの投稿用
- `dotenv` … `.env` ファイルの読み込み用

もし `package.json` を使わず個別にインストールしたい場合は次のコマンドでも同じです。

```bash
npm install openai @anthropic-ai/sdk twitter-api-v2 dotenv
```

## 3. APIキーの取得と設定

### OpenAI APIキー
1. https://platform.openai.com/api-keys にアクセスしてログイン
2. 「Create new secret key」でキーを発行(`sk-...`)

### Anthropic APIキー
1. https://console.anthropic.com/settings/keys にアクセスしてログイン
2. 「Create Key」でキーを発行(`sk-ant-...`)

### X (Twitter) APIキー
1. https://developer.x.com/ でDeveloperアカウントを作成し、Projectとアプリを作成
2. アプリの **Settings > User authentication settings** で
   **App permissions を「Read and Write」に変更**(これをやらないと投稿できません)
3. **Keys and tokens** タブで以下4つを取得
   - API Key / API Key Secret(Consumer Keys)
   - Access Token / Access Token Secret
     - App permissionsを変更した後に発行しないと、Read権限のトークンのままなので
       権限変更後に「Regenerate」して再発行してください

### .env ファイルの作成

`x-auto-bot` フォルダ直下に `.env.example` をコピーして `.env` を作成し、
取得したキーを貼り付けます。

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxx

X_API_KEY=your-consumer-api-key
X_API_SECRET=your-consumer-api-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_SECRET=your-access-token-secret

DEFAULT_THEME=生成AIが変える働き方の未来
```

`.env` はAPIキーなど機密情報を含むため、`.gitignore` で除外済みです。
**絶対にGitHubなどに公開しないでください。**

## 4. 実行方法

### まずは投稿せずに動作確認(推奨)

Xへの投稿はスキップして、議論の様子と生成される投稿文だけを確認できます。

```bash
node index.js "AIエージェントの未来" --dry-run
```

引数のテーマを省略すると `.env` の `DEFAULT_THEME` が使われます。

```bash
node index.js --dry-run
```

### 実際にXへ投稿する

```bash
node index.js "AIエージェントの未来"
```

実行すると、以下の流れでログが出力されます。

1. バズ分析AI・専門知識AIが3往復(計6発言)議論する様子
2. 議論をもとに生成された140字以内の投稿文
3. Xへの投稿完了メッセージと投稿URL

## 5. 仕組みの概要

1. **議論フェーズ(`src/debate.js`)**
   - `バズ分析AI`(OpenAI `gpt-4o-mini`)と`専門知識AI`(Anthropic `claude-sonnet-4-6`)が
     お互いの発言を読みながら、指定テーマについて3往復議論します。
2. **最適化フェーズ(`src/optimize.js`)**
   - 議論の全文をOpenAIに渡し、「感情を動かす」または「保存したくなるほど有益」な
     140文字以内の投稿文を生成します。140文字を超えた場合は最大3回まで自動で短縮を再試行します。
3. **投稿フェーズ(`src/postToX.js`)**
   - `twitter-api-v2` のOAuth 1.0aユーザーコンテキストを使い、生成した文章をXに投稿します。

## 6. よくあるエラー

- `.env に以下の環境変数が設定されていません` → `.env` のキー名・値を再確認してください
- Xへの投稿で `403 Forbidden` → アプリの権限が「Read and Write」になっているか、
  Access Token/Secretを権限変更後に再発行したか確認してください
- OpenAI/Anthropicで `401` → APIキーが正しいか、利用枠(クレジット)が残っているか確認してください

## 7. モデルを変更したい場合

- `src/debate.js` の `model: 'gpt-4o-mini'` / `model: 'claude-sonnet-4-6'`
- `src/optimize.js` の `model: 'gpt-4o-mini'`

をそれぞれ好きなモデル名に書き換えてください。
