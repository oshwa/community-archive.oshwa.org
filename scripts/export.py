import asyncio
from pathlib import Path
import aiohttp
from rich import print
import json

DOMAIN = "community.oshwa.org"
BASE_URL = f"https://{DOMAIN}"
OUTROOT = Path("./out")

BASIC_URLS = [
    "/site/basic-info.json",
    "/site.json",
    "/categories.json",
    "/groups.json",
]

SESSION = None


def out_path(path: Path | str):
    if isinstance(path, str):
        path = OUTROOT / path.lstrip("/")
    path.parent.mkdir(exist_ok=True, parents=True)
    return path

def save_as_json(dst: Path | str, data):
    dst = out_path(dst)
    dst.write_text(json.dumps(data, indent=2))
    print(f"Saved to {dst}")


def load_from_json(src: Path | str):
    src = out_path(src)
    return json.loads(src.read_text())


def save_as_bin(dst: Path | str, data):
    dst = out_path(dst)
    dst.write_bytes(data)


def normalize_url(url: str):
    if not url.startswith("http:"):
        url = f"{BASE_URL}{url}"
    return url

async def fetch(url: str, params=None, save: bool | str=False, binary = False):
    await asyncio.sleep(0.15)

    url = normalize_url(url)

    async with SESSION.get(url, params=params) as response:
        if binary:
            result = await response.read()
        else:
            result = await response.json()

    print(f"Fetched {response.url} {response.status}")

    if save:
        if save is True:
            save = response.url.path

        if binary:
            save_as_bin(save, result)
        else:
            save_as_json(save, result)

    return result


async def download_urls(urls: list[str]):
    for url in urls:
        await fetch(url, save=True)


def _load_categories():
    categories_resp = load_from_json("/categories.json")
    categories = categories_resp["category_list"]["categories"]
    return categories


async def download_categories():
    categories = _load_categories()

    urls = []
    for category in categories:
        urls.append(f"/c/{category['id']}/show.json")

    await download_urls(urls)


async def download_category_users_and_topics_lists():
    categories = _load_categories()

    for category in categories:
        users = {}
        topics = {}

        url = f"/c/{category['id']}.json"
        params = dict(no_subcategories="false", page=0)

        while True:
            resp = await fetch(url, params)

            for user in resp.get("users", []):
                users[user["id"]] = user

            page_topics = resp["topic_list"]["topics"]
            for topic in page_topics:
                topics[topic["id"]] = topic

            if not page_topics:
                break

            params["page"] += 1

        save_as_json(f"/c/{category['id']}/users.json", list(users.values()))
        save_as_json(f"/c/{category['id']}/topics.json", list(topics.values()))


async def download_topics():
    category_topic_files = OUTROOT.glob("c/*/topics.json")

    for src in category_topic_files:
        category_topics = load_from_json(src)
        for topic in category_topics:
            await fetch(f"/t/{topic['id']}.json", save=True)

async def download_posts():
    topic_files = OUTROOT.glob("t/*.json")

    for src in topic_files:
        topic = load_from_json(src)
        for post in topic["post_stream"]["posts"]:
            await fetch(f"/posts/{post['id']}.json", save=True)

async def download_users():
    category_user_files = OUTROOT.glob("c/*/users.json")
    userid_to_username = {}

    for src in category_user_files:
        category_users = load_from_json(src)
        for user in category_users:
            userid_to_username[user["id"]] = user["username"]

    for uid, uname in userid_to_username.items():
        await fetch(f"/u/{uname}.json", save=f"/u/{uid}.json")


async def download_user_avatars():
    users_files = OUTROOT.glob("u/*.json")

    for user_file in users_files:
        user = load_from_json(user_file)["user"]
        avatar_url = user["avatar_template"].replace("{size}", "240")
        await fetch(avatar_url, save=True, binary=True)


async def main():
    OUTROOT.mkdir(parents=True, exist_ok=True)
    global SESSION

    async with aiohttp.ClientSession() as session:
        SESSION = session

        await download_urls(BASIC_URLS)
        await download_categories()
        await download_category_users_and_topics_lists()
        await download_topics()
        await download_posts()
        await download_users()
        await download_user_avatars()

asyncio.run(main())


