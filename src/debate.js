import { GoogleGenAI } from '@google/genai';
import Anthropic from '@anthropic-ai/sdk';
import { BUZZ_ANALYST_PERSONA, EXPERT_PERSONA } from './personas.js';

const ROUNDS = 3; // 3往復 = バズ分析AI/専門知識AIがそれぞれ3回ずつ発言
const GEMINI_MODEL = 'gemini-2.0-flash';

function formatTranscript(transcript) {
  if (transcript.length === 0) return '(まだ発言はありません。あなたが最初の発言者です)';
  return transcript.map((t) => `${t.speaker}: ${t.text}`).join('\n\n');
}

async function askBuzzAnalyst(gemini, theme, transcript) {
  const res = await gemini.models.generateContent({
    model: GEMINI_MODEL,
    contents:
      `テーマ: 「${theme}」\n\n` +
      `これまでの議論:\n${formatTranscript(transcript)}\n\n` +
      'この続きとして、あなたの発言を1回分だけ出力してください。',
    config: {
      systemInstruction: BUZZ_ANALYST_PERSONA,
      temperature: 0.8,
    },
  });
  return res.text.trim();
}

async function askExpert(anthropic, theme, transcript) {
  const res = await anthropic.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 400,
    system: EXPERT_PERSONA,
    messages: [
      {
        role: 'user',
        content:
          `テーマ: 「${theme}」\n\n` +
          `これまでの議論:\n${formatTranscript(transcript)}\n\n` +
          'この続きとして、あなたの発言を1回分だけ出力してください。',
      },
    ],
  });
  return res.content[0].text.trim();
}

/**
 * バズ分析AIと専門知識AIに指定テーマについてROUNDS往復議論させる。
 * @returns {Promise<{speaker: string, text: string}[]>} 議論の全文
 */
export async function runDebate({ geminiApiKey, anthropicApiKey, theme }) {
  const gemini = new GoogleGenAI({ apiKey: geminiApiKey });
  const anthropic = new Anthropic({ apiKey: anthropicApiKey });

  const transcript = [];

  for (let round = 1; round <= ROUNDS; round++) {
    const buzzText = await askBuzzAnalyst(gemini, theme, transcript);
    transcript.push({ speaker: 'バズ分析AI', text: buzzText });

    const expertText = await askExpert(anthropic, theme, transcript);
    transcript.push({ speaker: '専門知識AI', text: expertText });

    console.log(`\n--- ラウンド ${round} ---`);
    console.log(`[バズ分析AI] ${buzzText}`);
    console.log(`[専門知識AI] ${expertText}`);
  }

  return transcript;
}
