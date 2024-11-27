from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import markdown
import yaml
from pathlib import Path
import frontmatter
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"))

def get_posts():
    posts_dir = Path("content/posts")
    posts = []
    for post_path in posts_dir.glob("*.md"):
        post = frontmatter.load(post_path)
        posts.append({
            "slug": post_path.stem,
            "title": post.metadata.get("title"),
            "date": post.metadata.get("date"),
            "tags": post.metadata.get("tags", []),
            "content": post.content
        })
    return sorted(posts, key=lambda x: x["date"], reverse=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    template = env.get_template("home.html")
    all_posts = get_posts()
    rendered_posts = []
    for post in all_posts[:2]:
        rendered_posts.append({
            **post,
            'content': markdown.markdown(post['content'], extensions=['fenced_code', 'footnotes'])
        })
    return template.render(
        posts=rendered_posts,
        more_posts=len(all_posts) > 2
    )

@app.get("/posts/{slug}", response_class=HTMLResponse)
async def post(slug: str):
    try:
        post = frontmatter.load(f"content/posts/{slug}.md")
        html_content = markdown.markdown(
            post.content,
            extensions=['fenced_code', 'footnotes']
        )
        template = env.get_template("post.html")
        return template.render(
            title=post.metadata.get("title"),
            date=post.metadata.get("date"),
            content=html_content
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404)

@app.get("/archive", response_class=HTMLResponse)
async def archive():
    template = env.get_template("archive.html")
    posts = get_posts()
    return template.render(posts=posts)

@app.get("/feed.xml")
async def rss():
    template = env.get_template("rss.xml")
    posts = get_posts()[:10]
    return template.render(posts=posts)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)