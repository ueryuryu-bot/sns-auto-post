#!/usr/bin/env python3
"""
ryuuzen321の投稿案を自動生成してdrafts/フォルダに保存するスクリプト（GitHub Actions用）
Usage: python generate_ryuuzen_drafts.py [YYYYMMDD]  ← 省略時は翌日
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime, timedelta
import pytz

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GH_PAT = os.environ.get("GH_PAT", "")
GH_REPO = os.environ.get("GH_REPO", "ueryuryu-bot/sns-auto-post")


RYUUZEN_WRITER_PROMPT = """あなたは@ryuuzen321のSNS投稿ライターです。

## @ryuuzen321 のペルソナ・文体

コンセプト：「キャリア教から抜け出し、時間と人生を自分でコントロールする」
仕事に人生を支配されている会社員に向けて、別の選択肢を見せる。

キャラクター：ryuuzen本人。体験談ベース。「俺はこうしてた」スタイル。
実体験軸：不動産投資（一棟メイン）、飲食店経営、会社員×副業の両立

口調：「俺」「まじで」「〜よな」「〜んだよな」「〜わ」OK。断定より余韻で終わらせる。
文字数：140〜280字、改行で余白を大切に。

絶対に避ける：「〜すべき」系の説教調、整いすぎた文学的表現、観察者・評論家の視点

## 生成してください

以下の15パターンの角度で投稿案を生成してください。必ず全部生成すること。

1. 衝撃ファクト型 ── 有給・休職・副業に関する驚きの事実で掴む
2. 逆張り意見型 ── 「頑張ることが正義」への反論
3. 体験談型 ── 自分の実際の経験から語る
4. 行動促進型 ── 今日から1つだけできる小さな行動を示す
5. 比較対照型 ── 「以前の自分」vs「今の自分」の具体的な違い
6. 名言引用型 ── 偉人の言葉×ノンキャリアの生き方
7. 問いかけ型 ── 読者の「当たり前」を一文で揺さぶる
8. ビフォーアフター型 ── ゆるワークや休職前後の変化
9. 失敗談型 ── キャリア教を信じすぎて失った時間・機会の話
10. 初心者向け解説型 ── 「ノンキャリアとは何か」入門
11. 上級者向け洞察型 ── 有給・休職・副業を戦略的に使いこなす方法
12. 長期思考型 ── 5年・10年でライフコントロールを手に入れる視点
13. マネタイズ橋渡し型 ── note有料記事（不動産投資・飲食店経営ノウハウ）への自然な誘導
14. トレンド乗り型 ── 旬の話題×ノンキャリア
15. ストーリー型 ── 起承転結のある短い体験談

## 出力形式（厳守）

━━━━━━━━━━━━━━━━━━━━━
@ryuuzen321 15パターン投稿案
━━━━━━━━━━━━━━━━━━━━━
テーマ：副業・ノンキャリア・会社員の働き方
生成日時：{date}
投稿予定日：{date}

---

[No.1] 衝撃ファクト型

（投稿本文）

推奨投稿時間：朝9時 / 昼13時 / 夜21時のいずれか

---

（No.2〜No.15まで同様）

━━━━━━━━━━━━━━━━━━━━━
次のステップ
投稿したい番号を選んで「No.X を投稿して」と送ってください。
「投稿して」と言うまで投稿しません。"""


RYUUZEN_RE_WRITER_PROMPT = """あなたは@ryuuzen321の不動産ライン投稿ライターです。

## ブランドコンセプト
「不動産屋が言わないことを、不動産屋が言う。」

発信者：会社員をしながら不動産投資15年・融資総額10億超・建築詐欺経験あり・不動産会社も経営。
現役投資家だからこそ語れる業界の本音と落とし穴を教育・警告・実体験ベースで発信。

## 投稿スタイル
- 純粋な不動産・ファイナンス情報のみ（ノンキャリア系の話は混ぜない）
- 集客臭を出さない。信頼・教育ベース
- 「まじで」「〜んだよな」「〜だったりする」OK
- 専門用語は使うが必ず一言解説を添える
- 140〜280字、改行で余白

## 生成してください

以下の15パターンの角度で投稿案を生成してください。必ず全部生成すること。

1. 危険警告型 ── 「この投資は実は危ない」「やってはいけない物件の特徴」
2. 業界本音型 ── 「不動産会社が言わないこと」「業界の裏側」
3. 失敗談型 ── 自分や周囲の実際の失敗事例（建築詐欺経験含む）
4. 初心者罠型 ── 「投資初心者が誤りがちな○○」
5. 融資・ファイナンス型 ── 「融資を断られる人の共通点」「金融機関の本音」
6. 利回りの罠型 ── 「表面利回りに騙されるな」「実質利回りの計算」
7. 市場データ型 ── 数字で語る最新相場・統計・価格動向
8. 売却タイミング型 ── 「今が売り時か買い時か」の判断軸
9. 自宅購入型 ── 「家を買うときに誰も教えてくれないこと」
10. 管理・運用型 ── 「物件を持ってから始まる本当の苦労」
11. 相続・贈与型 ── 「不動産×相続で揉める家族のパターン」
12. エリア選定型 ── 「なぜそのエリアは上がるのか・下がるのか」
13. 金利・ローン型 ── 住宅ローン・投資ローンの選び方と落とし穴
14. 問いかけ型 ── 読者の「当たり前」の不動産観を一文で揺さぶる
15. 法改正・制度型 ── 知っておかないと損する制度変更・税制

## 出力形式（厳守）

━━━━━━━━━━━━━━━━━━━━━
@ryuuzen321 15パターン投稿案（不動産投資特化）
━━━━━━━━━━━━━━━━━━━━━
テーマ：不動産投資（会社員が副業としてやるリアル体験談）
生成日時：{date}
投稿予定日：{date}

---

[No.1] 危険警告型

（投稿本文）

推奨投稿時間：朝9時 / 昼13時 / 夜21時のいずれか

---

（No.2〜No.15まで同様）

━━━━━━━━━━━━━━━━━━━━━
次のステップ
投稿したい番号を選んで「No.X を投稿して」と送ってください。
「投稿して」と言うまで投稿しません。"""


def call_claude(prompt: str) -> str:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=120,
    )
    if res.status_code != 200:
        raise Exception(f"Claude API error: {res.status_code} {res.text[:300]}")
    return res.json()["content"][0]["text"]


def push_to_github(filepath: str, content: str) -> bool:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{filepath}"
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Content-Type": "application/json",
    }
    # 既存ファイルのSHAを取得
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None

    payload = {"message": f"Auto-generate: {filepath}", "content": encoded}
    if sha:
        payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in (200, 201):
        print(f"[OK] pushed: {filepath}")
        return True
    else:
        print(f"[ERROR] {filepath}: {res.status_code} {res.text[:200]}")
        return False


def main():
    if not ANTHROPIC_API_KEY:
        print("ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    jst = pytz.timezone("Asia/Tokyo")
    if len(sys.argv) > 1:
        target_date = sys.argv[1]  # YYYYMMDD
        display_date = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}"
    else:
        tomorrow = datetime.now(jst) + timedelta(days=1)
        target_date = tomorrow.strftime("%Y%m%d")
        display_date = tomorrow.strftime("%Y-%m-%d")

    print(f"生成対象日: {display_date}")

    success = 0

    # ryuuzen思想系
    print("\n[1/2] ryuuzen思想系 生成中...")
    try:
        prompt = RYUUZEN_WRITER_PROMPT.replace("{date}", display_date)
        content = call_claude(prompt)
        github_path = f"drafts/ryuuzen_drafts_{target_date}.md"
        if push_to_github(github_path, content):
            success += 1
    except Exception as e:
        print(f"[ERROR] ryuuzen思想系: {e}")

    # ryuuzen不動産系
    print("\n[2/2] ryuuzen不動産系 生成中...")
    try:
        prompt = RYUUZEN_RE_WRITER_PROMPT.replace("{date}", display_date)
        content = call_claude(prompt)
        github_path = f"drafts/ryuuzen_fudosan_drafts_{target_date}.md"
        if push_to_github(github_path, content):
            success += 1
    except Exception as e:
        print(f"[ERROR] ryuuzen不動産系: {e}")

    print(f"\n完了: {success}/2 ファイル生成・push済み")
    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
