import { TwitterApi } from 'twitter-api-v2';

/**
 * 生成したテキストをXに投稿する。
 * @param {{xApiKey: string, xApiSecret: string, xAccessToken: string, xAccessSecret: string}} creds
 * @param {string} text 投稿する本文(140文字以内)
 * @returns {Promise<{id: string, text: string}>} 投稿されたツイート情報
 */
export async function postToX(creds, text) {
  const client = new TwitterApi({
    appKey: creds.xApiKey,
    appSecret: creds.xApiSecret,
    accessToken: creds.xAccessToken,
    accessSecret: creds.xAccessSecret,
  });

  const rwClient = client.readWrite;
  const { data } = await rwClient.v2.tweet(text);
  return data;
}
