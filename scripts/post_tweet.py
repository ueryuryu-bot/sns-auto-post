import os, json, tweepy, requests, base64
from datetime import datetime, timezone

GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

ACCOUNTS = {
    "azabu": {
        "consumer_key": os.environ["AZABU_API_KEY"],
        "consumer_secret": os.environ["AZABU_API_SECRET"],
        "access_token": os.environ["AZABU_ACCESS_TOKEN"],
        "access_token_secret": os.environ["AZABU_ACCESS_TOKEN_SECRET"],
        "username": "JBgNL1GrHp56492",
        "discord_ch": "1493037286831558678"
    },
    "ryuuzen": {
        "consumer_key": os.environ["RYUUZEN_API_KEY"],
        "consumer_secret": os.environ["RYUUZEN_API_SECRET"],
        "access_token": os.environ["RYUUZEN_ACCESS_TOKEN"],
        "access_token_secret": os.environ["RYUUZEN_ACCESS_TOKEN_SECRET"],
        "username": "ryuuzen321",
        "discord_ch": "1494268561169059981"
    }
}

now_utc = datetime.now(timezone.utc)
now_jst_h = (now_utc.hour + 9) % 24
now_jst_m = now_utc.minute
now_total = now_jst_h * 60 + now_jst_m

hdrs_gh = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}

schedule_files = ["schedule/azabu.json", "schedule/ryuuzen.json"]

for schedule_path in schedule_files:
    r = requests.get(
        f"https://api.github.com/repos/{GH_REPO}/contents/{schedule_path}",
        headers=hdrs_gh
    )
    if r.status_code != 200:
        continue

    file_data = r.json()
    schedule = json.loads(base64.b64decode(file_data["content"]).decode())
    sha = file_data["sha"]

    account_name = schedule.get("account", "azabu")
    acct = ACCOUNTS[account_name]
    client = tweepy.Client(
        consumer_key=acct["consumer_key"],
        consumer_secret=acct["consumer_secret"],
        access_token=acct["access_token"],
        access_token_secret=acct["access_token_secret"]
    )

    updated = False
    for post in schedule["posts"]:
        if post.get("posted"):
            continue
        tgt_h, tgt_m = map(int, post["time_jst"].split(":"))
        tgt_total = tgt_h * 60 + tgt_m
        if tgt_total - 10 <= now_total < tgt_total + 10:
            try:
                res = client.create_tweet(text=post["text"])
                url = f"https://x.com/{acct['username']}/status/{res.data['id']}"
                post["posted"] = True
                post["tweet_url"] = url
                updated = True
                label = post.get("label", "")
                requests.post(
                    f"https://discord.com/api/v10/channels/{acct['discord_ch']}/messages",
                    headers={"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"},
                    json={"content": f"✅ {account_name} {label} 投稿完了\n{url}"}
                )
                print(f"Posted [{account_name}] {label}: {url}")
            except Exception as e:
                print(f"Error [{account_name}] {post.get('label','')}: {e}")

    if updated:
        content_str = json.dumps(schedule, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content_str.encode()).decode()
        requests.put(
            f"https://api.github.com/repos/{GH_REPO}/contents/{schedule_path}",
            headers=hdrs_gh,
            json={"message": f"Update: mark posts as posted", "content": encoded, "sha": sha}
        )
        print(f"Schedule updated: {schedule_path}")

print("Done.")
