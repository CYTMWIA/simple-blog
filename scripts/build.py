#! /usr/bin/python3

import datetime
import json
import os
import shutil

import jinja2
import markdown
import md4mathjax
from common import load_config, ls, make_time_formatter, open


class Article:
    title: str
    pub_time: str
    mod_time: str
    html: str
    path: str
    link: None | str = None

    def __str__(self) -> str:
        d = vars(self).copy()
        d["html"] = "..."
        return f"{self.__class__.__name__}({str(d)})"


class ArticleLoader:
    def __init__(self, mathjax_src=None, time_format=None) -> None:
        assert (mathjax_src != None)
        assert (time_format != None)
        self.mathjax_src = mathjax_src
        self.time_format = time_format

    def __take_front_matter(self, raw_text: str):
        if raw_text.startswith("{"):
            split_point, stack, flag_string = None, 0, ""
            for i, c in enumerate(raw_text):
                if len(flag_string):
                    if c == flag_string:
                        flag_string = ""
                else:
                    if c == "{":
                        stack += 1
                    elif c == "}":
                        stack -= 1
                    elif c in "'\"":
                        flag_string = c
                    if stack == 0:
                        split_point = i+1
                        break
            if split_point:
                front = json.loads(raw_text[:split_point])
                text = raw_text[split_point:].lstrip("\n")
                return front, text
        return {}, raw_text

    def load(self, path: str):
        art = Article()

        art.path = path
        with open(path, "r") as f:
            raw = f.read()

        front, text = self.__take_front_matter(raw)
        art.title = front.get("title", os.path.basename(path))
        art.pub_time = front.get("pub_time", None)
        art.mod_time = front.get("mod_time", None)
        strptime = datetime.datetime.strptime
        if art.pub_time != None:
            art.pub_time = strptime(art.pub_time, self.time_format).timestamp()
        if art.mod_time != None:
            art.mod_time = strptime(art.mod_time, self.time_format).timestamp()

        art.html = markdown.markdown(text, extensions=[
            # https://python-markdown.github.io/extensions/
            "markdown.extensions.extra",
            "markdown.extensions.toc",
            "markdown_del_ins",
            md4mathjax.makeExtension(mathjax_src=self.mathjax_src)
        ])

        return art


def make_template_loader(templates_dir: str, filters={}):
    loader = jinja2.FileSystemLoader(templates_dir)
    env = jinja2.Environment(loader=loader)
    env.filters.update(filters)
    return env.get_template


def make_output_functions(output_dir: str):
    def write(path: str, content: any):
        os.makedirs(output_dir, exist_ok=True)
        p = os.path.join(output_dir, path)
        with open(p, "w") as f:
            f.write(content)

    def copy(path: str):
        os.makedirs(output_dir, exist_ok=True)
        if os.path.isdir(path):
            dst = os.path.join(output_dir, os.path.basename(path))
            shutil.copytree(path, dst, dirs_exist_ok=True)
        else:
            shutil.copy(path, output_dir)

    return write, copy


def main():
    config = load_config()

    filters = {
        "datetime": make_time_formatter(config["format_datetime"], config["timezone"]),
        "datetime_full": make_time_formatter(config["format_datetime_full"], config["timezone"])
    }
    use_template = make_template_loader(config["templates_dir"], filters)
    write, copy = make_output_functions(config["output_dir"])
    load_article = ArticleLoader(
        config["mathjax_src"],
        config["format_datetime_full"]
    ).load

    about = None
    articles = []
    copyfiles = []
    for cp in ls(config["content_dir"]):
        filename = os.path.basename(cp)
        if filename == "about.md":
            about = load_article(cp)
        elif filename.startswith("."):
            pass
        elif filename.endswith(".md"):
            articles.append(load_article(cp))
        else:
            copyfiles.append(cp)

    articles.sort(key=lambda a: a.pub_time, reverse=True)
    for art in articles:
        art.link = os.path.basename(art.path)+".html"

    write("index.html", use_template("index.html").render(
        blog_name=config["blog_name"],
        about=about,
        articles=articles,
    ))

    article_template = use_template("article.html")
    for art in articles:
        print(art)
        write(art.link, article_template.render(
            blog_name=config["blog_name"],
            article=art
        ))

    for cp in copyfiles:
        print("COPY", cp)
        copy(cp)


if __name__ == "__main__":
    main()
