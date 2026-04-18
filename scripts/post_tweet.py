import os, json, tweepy, requests, base64
from datetime import datetime, timezone

with open("schedule/today.json", "r") as f:
    schedule = json.load(f)

now_utc = datetime.now(timezone.utc)
now_jst_h = (now_utc.hour + 9) % 24
now_jst_m = now_utc.minute
now_total = now_jst_h * 60 + now_jst_m

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]

updated = False

for post in schedule["posts"]:
    if post.get("posted"):
        continue
    tgt_h, tgt_m = map(int, post["time_jst"].split(":"))
    tgt_total = tgt_h * 60 + tgt_m
    if tgt_total <= now_total < tgt_total + 10:
        account = schedule.get("account", "azabu")
        if account == "azabu":
            client = tweepy.Client(
                consumer_key=os.environ["AZABU_API_KEY"],
                consumer_secret=os.environ["AZABU_API_SECRET"],
                access_token=os.environ["AZABU_ACCESS_TOKEN"],
                access_token_secret=os.environ["AZABU_ACCESS_TOKEN_SECRET"]
            )
            username = "JBgNL1GrHp56492"
            discord_ch = "1493037286831558678"
        else:
            client = tweepy.Client(
                consumer_key=os.environ["RYUUZEN_API_KEY"],
                consumer_secret=os.environ["RYUUZEN_API_SECRET"],
                access_token=os.environ["RYUUZEN_ACCESS_TOKEN"],
                access_token_secret=os.environ["RYUUZEN_ACCESS_TOKEN_SECRET"]
            )
            username = "ryuuzen321"
            discord_ch = "1494268561169059981"
        try:
            res = client.create_tweet(text=post["text"])
            url = f"https://x.com/{username}/status/{res.data['id']}"
            post["posted"] = True
            post["tweet_url"] = url
            updated = True
            label = post.get("label", "")
            requests.post(
                f"https://discord.com/api/v10/channels/{discord_ch}/messages",
                headers={"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"},
                json={"content": f"✅ {account} {label} 投稿完了\n{url}"}
            )
            print(f"Posted {label}: {url}")
        except Exception as e:
            print(f"Error: {e}")

if updated:
    content_str = json.dumps(schedule, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content_str.encode()).decode()
    r = requests.get(
        f"https://api.github.com/repos/{GH_REPO}/contents/schedule/today.json",
        headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}
    )
    sha = r.json().get("sha", "")
    requests.put(
        f"https://api.github.com/repos/{GH_REPO}/contents/schedule/today.json",
        headers={"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"},
        json={"message": "Update: mark posts as posted", "content": encoded, "sha": sha}
    )
    print("Schedule updated.")
else:
    print("No posts due now.")
