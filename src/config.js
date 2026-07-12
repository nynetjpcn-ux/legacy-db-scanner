import 'dotenv/config';

const REQUIRED_KEYS = [
  'OPENAI_API_KEY',
  'ANTHROPIC_API_KEY',
  'X_API_KEY',
  'X_API_SECRET',
  'X_ACCESS_TOKEN',
  'X_ACCESS_SECRET',
];

export function loadConfig({ requireTwitter = true } = {}) {
  const keys = requireTwitter
    ? REQUIRED_KEYS
    : REQUIRED_KEYS.filter((k) => !k.startsWith('X_'));

  const missing = keys.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    throw new Error(
      `.env に以下の環境変数が設定されていません: ${missing.join(', ')}\n` +
        '.env.example を参考に .env を作成してください。'
    );
  }

  return {
    openaiApiKey: process.env.OPENAI_API_KEY,
    anthropicApiKey: process.env.ANTHROPIC_API_KEY,
    xApiKey: process.env.X_API_KEY,
    xApiSecret: process.env.X_API_SECRET,
    xAccessToken: process.env.X_ACCESS_TOKEN,
    xAccessSecret: process.env.X_ACCESS_SECRET,
    defaultTheme: process.env.DEFAULT_THEME || '今話題のテーマ',
  };
}
