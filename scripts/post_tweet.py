import os, json, tweepy, requests, base64, time, sys
from datetime import datetime, timezone, timedelta

GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
JST = timezone(timedelta(hours=9))

# 引数で時間範囲を受け取る: python post_tweet.py 09:00 14:45
start_str = sys.argv[1] if len(sys.argv) > 1 else "00:00"
end_str   = sys.argv[2] if len(sys.argv) > 2 else "23:59"
start_h, start_m = map(int, start_str.split(":"))
end_h,   end_m   = map(int, end_str.split(":"))
start_total = start_h * 60 + start_m
end_total   = end_h   * 60 + end_m

ACCOUNTS = {
    "azabu": {
        "consumer_key":        os.environ["AZABU_API_KEY"],
        "consumer_secret":     os.environ["AZABU_API_SECRET"],
        "access_token":        os.environ["AZABU_ACCESS_TOKEN"],
        "access_token_secret": os.environ["AZABU_ACCESS_TOKEN_SECRET"],
        "username":   "JBgNL1GrHp56492",
        "discord_ch": "1493037286831558678"
    },
    "ryuuzen": {
        "consumer_key":        os.environ["RYUUZEN_API_KEY"],
        "consumer_secret":     os.environ["RYUUZEN_API_SECRET"],
        "access_token":        os.environ["RYUUZEN_ACCESS_TOKEN"],
        "access_token_secret": os.environ["RYUUZEN_ACCESS_TOKEN_SECRET"],
        "username":   "ryuuzen321",
        "discord_ch": "1494268561169059981"
    }
}

hdrs_gh = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}

def get_schedule(path):
    r = requests.get(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=hdrs_gh)
    if r.status_code != 200:
        return None, None
    d = r.json()
    return json.loads(base64.b64decode(d["content"]).decode()), d["sha"]

def save_schedule(path, schedule, sha):
    content = base64.b64encode(json.dumps(schedule, ensure_ascii=False, indent=2).encode()).decode()
    requests.put(f"https://api.github.com/repos/{GH_REPO}/contents/{path}", headers=hdrs_gh,
        json={"message": "update: mark posts as posted", "content": content, "sha": sha})

def discord_notify(channel, msg):
    requests.post(f"https://discord.com/api/v10/channels/{channel}/messages",
        headers={"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"},
        json={"content": msg})

schedule_files = [
    ("schedule/azabu.json",   "azabu"),
    ("schedule/ryuuzen.json", "ryuuzen"),
]

# 対象投稿を収集（この時間帯のもの・未投稿のもの）
todos = []
for path, account_name in schedule_files:
    schedule, sha = get_schedule(path)
    if not schedule:
        continue
    acct = ACCOUNTS[account_name]
    for post in schedule["posts"]:
        if post.get("posted"):
            continue
        h, m = map(int, post["time_jst"].split(":"))
        total = h * 60 + m
        if start_total <= total <= end_total:
            todos.append({
                "path": path, "account_name": account_name,
                "acct": acct, "post": post,
                "total": total
            })

todos.sort(key=lambda x: x["total"])
print(f"対象投稿: {len(todos)}本 ({start_str}〜{end_str} JST)")
for t in todos:
    print(f"  {t['post']['time_jst']} [{t['account_name']}] {t['post']['label']}")

for item in todos:
    post = item["post"]
    acct = item["acct"]
    account_name = item["account_name"]

    # 投稿時刻まで待機
    now_jst = datetime.now(JST)
    now_total = now_jst.hour * 60 + now_jst.minute
    wait_min = item["total"] - now_total
    if wait_min > 0:
        print(f"{post['time_jst']} まで {wait_min}分 待機...", flush=True)
        time.sleep(wait_min * 60)

    # 投稿実行
    try:
        client = tweepy.Client(
            consumer_key=acct["consumer_key"], consumer_secret=acct["consumer_secret"],
            access_token=acct["access_token"], access_token_secret=acct["access_token_secret"]
        )
        res = client.create_tweet(text=post["text"])
        url = f"https://x.com/{acct['username']}/status/{res.data['id']}"
        post["posted"] = True
        post["tweet_url"] = url
        print(f"✅ [{account_name}] {post['label']}: {url}", flush=True)

        # スケジュール更新
        schedule, sha = get_schedule(item["path"])
        for p in schedule["posts"]:
            if str(p["no"]) == str(post["no"]):
                p["posted"] = True
                p["tweet_url"] = url
        save_schedule(item["path"], schedule, sha)

        # Discord通知
        discord_notify(acct["discord_ch"], f"✅ {account_name} {post['label']} 投稿完了\n{url}")

    except Exception as e:
        print(f"❌ [{account_name}] {post['label']} エラー: {e}", flush=True)

print("Done.")
