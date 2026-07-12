import { loadConfig } from './src/config.js';
import { runDebate } from './src/debate.js';
import { optimizePost } from './src/optimize.js';
import { postToX } from './src/postToX.js';

async function main() {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run');
  const theme = args.find((a) => !a.startsWith('--'));

  const config = loadConfig({ requireTwitter: !isDryRun });
  const finalTheme = theme || config.defaultTheme;

  console.log(`テーマ: ${finalTheme}`);
  console.log('AI同士の議論を開始します...');

  const transcript = await runDebate({
    openaiApiKey: config.openaiApiKey,
    anthropicApiKey: config.anthropicApiKey,
    theme: finalTheme,
  });

  console.log('\n議論から投稿文を生成します...');
  const postText = await optimizePost({
    openaiApiKey: config.openaiApiKey,
    theme: finalTheme,
    transcript,
  });

  console.log('\n=== 生成された投稿文 ===');
  console.log(postText);
  console.log(`(${[...postText].length}文字)`);

  if (isDryRun) {
    console.log('\n--dry-run が指定されているため、Xへの投稿はスキップしました。');
    return;
  }

  console.log('\nXに投稿します...');
  const posted = await postToX(config, postText);
  console.log(`投稿完了: https://x.com/i/web/status/${posted.id}`);
}

main().catch((err) => {
  console.error('エラーが発生しました:', err.message);
  process.exit(1);
});
