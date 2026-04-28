#!/usr/bin/env python3
"""
drafts/ フォルダの投稿案をDiscordに送信するスクリプト（GitHub Actions用）
翌日分のファイルを検索して送信する
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import pytz

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

CHANNEL_MAP = {
    "azabu": "1493037286831558678",
    "ryuuzen": "1494268561169059981",
    "ryuuzen_fudosan": "1494268561169059981",
}

LABEL_MAP = {
    "azabu": "麻布大門",
    "ryuuzen": "ryuuzen321（思想系）",
    "ryuuzen_fudosan": "ryuuzen321（不動産系）",
}


def send_to_discord(channel_id: str, content: str) -> bool:
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

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
    if not DISCORD_TOKEN:
        print("DISCORD_TOKEN が設定されていません")
        sys.exit(1)

    jst = pytz.timezone("Asia/Tokyo")
    tomorrow = (datetime.now(jst) + timedelta(days=1)).strftime("%Y%m%d")
    tomorrow_display = (datetime.now(jst) + timedelta(days=1)).strftime("%Y-%m-%d")

    drafts_dir = "drafts"
    sent = 0

    for key, channel_id in CHANNEL_MAP.items():
        filename = f"{key}_drafts_{tomorrow}.md"
        filepath = os.path.join(drafts_dir, filename)

        if not os.path.exists(filepath):
            print(f"[SKIP] ファイルなし: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            body = f.read()

        label = LABEL_MAP[key]
        header = f"📋 **{label} 投稿案 {tomorrow_display}**\n\n"
        full_content = header + body

        print(f"[SEND] {filepath} → channel {channel_id}")
        if send_to_discord(channel_id, full_content):
            print(f"[OK] {label} 送信完了")
            sent += 1
        else:
            print(f"[ERROR] {label} 送信失敗")

    print(f"\n完了: {sent} 件送信")
    if sent == 0:
        print("送信対象のファイルが見つかりませんでした")
        sys.exit(1)


if __name__ == "__main__":
    main()
