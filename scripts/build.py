from pathlib import Path
import json
import dateutil.parser
import jinja2
import dateutil

parent_path = Path(__file__).parent
data_path = parent_path / "../data"
templates_path = parent_path / "templates"
www_path = parent_path / "../www"

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_path))


def fixup_string(val: str):
    # Replace URLs with community.oshwa.org with URLs relative to the root.
    val = val.replace("http://community.oshwa.org/", "/")
    val = val.replace("https://community.oshwa.org/", "/")
    val = val.replace("//community.oshwa.org/", "/")
    return val


def fixup_data(data: dict):
    for k, v in data.items():
        match v:
            case dict():
                data[k] = fixup_data(v)
            case str():
                data[k] = fixup_string(v)
            case _:
                pass
    return data


def load_data(filename: str) -> dict:
    with open(data_path / filename, "r") as fh:
        return fixup_data(json.load(fh))


def load_data_set(glob: str) -> list[dict]:
    results = []
    for path in data_path.glob(glob):
        results.append(load_data(path.relative_to(data_path)))
    return results


categories = {
    c["category"]["id"]: c["category"] for c in load_data_set("c/*/show.json")
}
topics = {
    t["id"]: t
    for t in sorted(
        load_data_set("t/*.json"),
        key=lambda t: dateutil.parser.parse(t["last_posted_at"] or t["created_at"]),
        reverse=True,
    )
}
posts = {p["id"]: p for p in load_data_set("posts/*.json")}


def filter_avatar(value):
    return value.replace("{size}", "240")


jinja.filters["avatar"] = filter_avatar


def filter_format_date(value):
    dt = dateutil.parser.parse(value)
    month = dt.strftime("%b")
    day = dt.day
    year = dt.year

    return (
        f'<span class="timestamp" title="{dt.isoformat()}">{month} {day}, {year}</span>'
    )


jinja.filters["format_date"] = filter_format_date

css_template = jinja.get_template("index.css")
index_template = jinja.get_template("index.html")
topic_template = jinja.get_template("topic.html")

(www_path / "index.css").write_text(css_template.render())
(www_path / "index.html").write_text(
    index_template.render(
        categories=categories,
        topics=topics,
    )
)

for topic in topics.values():
    topic_post_ids = topic["post_stream"]["stream"]
    topic_posts = [posts[id] for id in topic_post_ids]

    dst = www_path / f"t/{topic["slug"]}/{topic["id"]}/index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        topic_template.render(
            topic=topic,
            posts=topic_posts,
        )
    )
