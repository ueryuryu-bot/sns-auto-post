#!/usr/bin/env python3
"""
ryuuzen321のnote記事を自動生成してDiscordに送信するスクリプト（GitHub Actions用）
週2回（水曜・日曜 9:00 JST）に起動
"""

import os
import sys
import requests
from datetime import datetime
import pytz

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
DISCORD_CHANNEL_ID = "1494268561169059981"

NOTE_WRITER_PROMPT = """あなたは@ryuuzen321のnote記事執筆担当です。

## ryuuzenのペルソナ

プロフィール：会社員のまま、居酒屋・バー・買取店・不動産会社・民泊を経営。稼ぐより"経験値"を積んできたマン。
経歴：激務で休職 → 副業での損失 → 立て直して会社員のまま複数事業経営。２児の父。

### 核心思想
- 経験値＝どこでも生きていける力。これがあると、会社にしがみつく必要がなくなる
- 外で積んだ経験値は、会社の仕事にも効く
- 会社は辞めなくていい。給料は生活を支える「土台」。辞めないのは、しがみついているからではなく、自分で選んでいるから
- 一人で全部やらない。「やりたい人」と組む
- 「このままでいいのか」というモヤモヤの正体は「経験値が止まっていること」

### ターゲット読者
30〜40代のミドルエイジの会社員。「このままでいいのか？」「このまま会社で終わるのか？」と感じている人。

## テーマ選定
以下のコンテンツ軸から、今回のテーマを1つ選んでください：
- 会社員のまま経験値を積む生き方
- 店の現場のリアル（飲食店・買取店・不動産・民泊）
- 人と組む方法・任せ方
- 会社は辞めなくていい、会社は「土台」
- 家族の挑戦（妻がAmazon物販を始めた話など。妻が特定される情報は出さない）
- 過去の失敗（激務での休職、副業での損失）からの立て直し

## 記事執筆ルール

### 基本
- 一人称：「私」
- 文体：ですます調
- 文字数：**5000字以上（厳守）**
- 見出し：5つ以上

### 構成テンプレート

# [タイトル]

[リード：200字以内。問いかけまたは共感から入る]

---

## [第一章：30〜40代会社員のモヤモヤを言語化する]
「このままでいいのか」の正体に切り込む

## [第二章：経験値という考え方]
なぜ会社の外に出ると世界が変わるのか

## [第三章：私自身の実体験（無料部分）]
店を始めた経緯、人と組んだ話、失敗から得た経験値など

---
※ここから有料（300〜500円想定）
---

## [第四章：具体的な実践①]
飲食店経営・買取店・不動産会社・民泊など、テーマに合わせて選択
- 現場で何が起きたか（場面、会話、判断）
- そこで得た経験値は何だったか

## [第五章：具体的な実践②]
人と組む方法、任せ方、会社員のまま経営する工夫など

## [おわりに]
哲学的な締め。押しつけがましくなく余韻で終わる

---

[CTA]

### CTAテンプレート
この記事を読んで、何か感じるものがあった方へ。

私のXでは、会社員のまま外で経験値を積む生き方について日々発信しています。
「こういう考え方、もっと聞きたい」と思った方はフォローしてもらえると嬉しいです。

→ X（@ryuuzen321）をフォローする

また、「自分の場合はどうすればいいか」「会社員のまま何か始めたいけど、何からやればいいか」など、
個別に話したい方はXのDMからご連絡ください。
一人で抱えずに、まず話してみてください。

### 引用してよい思想家・概念
- アリストテレス：「自由人は余暇の中でこそ人間らしく生きられる」
- ハイデガー：「人間の存在は時間そのもの」
- ハンナ・アーレント：労働・仕事・活動の三層。真の人間らしさは「活動」にある
- マックス・ウェーバー：「勤勉は美徳」は宗教と資本主義が設計した思想
- 老子・道徳経：「為学日益、為道日損」削ぎ落とした先に本質が残る
- 仏教・中道：苦行も快楽も極端。ちょうどいい場所に力を使う

### 絶対に避ける表現
- 「〜すべき」「〜べき」系の説教調
- 観察者・評論家の視点（常に当事者として語る）
- テクニック論・攻略法的な語り口
- 整いすぎた文学的表現（うまいな、と感じさせるものはNG）
- お金の数字（年商・売上・利益）、「稼げる」「儲かる」の訴求

## 出力
記事全文をそのまま出力してください。マークダウン形式で。
生成日：{date}
"""


def call_claude(prompt: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-5-20241022",
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }
    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=180,
    )
    if res.status_code != 200:
        raise Exception(f"Claude API error: {res.status_code} {res.text[:300]}")
    return res.json()["content"][0]["text"]


def send_to_discord(content: str) -> bool:
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"

    # 2000文字制限で分割
    chunks = []
    while len(content) > 1900:
        split_at = content.rfind("\n", 0, 1900)
        if split_at <= 0:
            split_at = 1900
        chunks.append(content[:split_at])
        content = content[split_at:].lstrip("\n")
    if content:
        chunks.append(content)

    for chunk in chunks:
        res = requests.post(url, headers=headers, json={"content": chunk})
        if res.status_code not in (200, 201):
            print(f"[ERROR] Discord送信失敗: {res.status_code} {res.text[:200]}")
            return False
    return True


def main():
    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)
    if not DISCORD_TOKEN:
        print("DISCORD_TOKEN が設定されていません")
        sys.exit(1)

    jst = pytz.timezone("Asia/Tokyo")
    today = datetime.now(jst)
    display_date = today.strftime("%Y-%m-%d")
    weekday = today.strftime("%A")

    print(f"note記事生成: {display_date} ({weekday})")

    # Claude APIで記事生成
    print("\n記事を生成中...")
    prompt = NOTE_WRITER_PROMPT.replace("{date}", display_date)
    article = call_claude(prompt)

    # Discord送信
    header = f"📝 **ryuuzen321 note下書き {display_date}**\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    footer = "\n\n━━━━━━━━━━━━━━━━━━━━━\n✅ 確認後、noteに手動で投稿してください。\n推奨ハッシュタグ：#会社員のまま挑戦 #経験値 #副業経営 #会社員 #生き方"
    full_content = header + article + footer

    print("Discordに送信中...")
    if send_to_discord(full_content):
        print("[OK] Discord送信完了")
    else:
        print("[ERROR] Discord送信失敗")
        sys.exit(1)

    print(f"\n完了: note記事をDiscordに送信しました")


if __name__ == "__main__":
    main()
