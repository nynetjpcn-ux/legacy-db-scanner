import { GoogleGenAI } from '@google/genai';

const MAX_LENGTH = 140;
const MAX_ATTEMPTS = 3;
const GEMINI_MODEL = 'gemini-3.5-flash';

const SYSTEM_PROMPT = `あなたはX(Twitter)の投稿最適化のプロです。
与えられた「AI同士の議論」の内容をもとに、
・読者の感情を動かす(驚き/共感/危機感など)、または
・思わず保存/リポストしたくなるほど有益
な投稿文を1つだけ作成してください。

制約:
- 日本語で140文字以内(絶対厳守)
- ハッシュタグは多くても2個まで
- 説明や前置き、括弧書きの補足は一切つけず、投稿文そのものだけを出力する
- 絵文字は使ってもよいが多用しない`;

function buildUserPrompt(theme, transcript, previousAttempt) {
  const transcriptText = transcript.map((t) => `${t.speaker}: ${t.text}`).join('\n\n');
  let prompt =
    `テーマ: 「${theme}」\n\n` +
    `以下はこのテーマについての「バズ分析AI」と「専門知識AI」の議論です。\n\n` +
    `${transcriptText}\n\n` +
    'この議論の要点を踏まえて、Xのインプレッションが最大化するような投稿文を140文字以内で1つ作成してください。';

  if (previousAttempt) {
    prompt +=
      `\n\n直前の案は${previousAttempt.length}文字で140文字を超えていました:\n` +
      `"${previousAttempt}"\n` +
      '内容の魅力を保ったまま、140文字以内に収まるように短くしてください。';
  }
  return prompt;
}

/**
 * 議論のトランスクリプトから、140文字以内の投稿文を生成する。
 * @returns {Promise<string>}
 */
export async function optimizePost({ geminiApiKey, theme, transcript }) {
  const gemini = new GoogleGenAI({ apiKey: geminiApiKey });

  let candidate = '';
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const res = await gemini.models.generateContent({
      model: GEMINI_MODEL,
      contents: buildUserPrompt(theme, transcript, attempt > 1 ? candidate : null),
      config: {
        systemInstruction: SYSTEM_PROMPT,
        temperature: 0.9,
      },
    });

    candidate = res.text.trim().replace(/^["']|["']$/g, '');

    if ([...candidate].length <= MAX_LENGTH) {
      return candidate;
    }
  }

  // どうしても収まらない場合は安全側で切り詰める
  return [...candidate].slice(0, MAX_LENGTH).join('');
}
