#!/usr/bin/env python3
"""Забирает последние посты публичного канала Telegram и сохраняет их в tg.json.
Фото постов скачиваются в папку tg/, чтобы сайт не зависел от ссылок Telegram."""
import html
import json
import os
import re
import urllib.request

CHANNEL = "crisvandal"
LIMIT = 3                # сколько постов показывать
ONLY_WITH_PHOTO = False  # True: брать только посты, в которых есть фото
MAX_TEXT = 400

HEADERS = {"User-Agent": "Mozilla/5.0"}
BG = r"background-image:url\('([^']+)'\)"
IMAGE_PATTERNS = [
    r"tgme_widget_message_photo_wrap[^>]*" + BG,
    r"tgme_widget_message_video_thumb[^>]*" + BG,
    r"link_preview_(?:right_)?image[^>]*" + BG,
]


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def clean_text(raw):
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).strip()
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT].rstrip() + "…"


def parse(page):
    posts = []
    for chunk in page.split("tgme_widget_message_wrap")[1:]:
        m = re.search(r'data-post="[^"]+/(\d+)"', chunk)
        if not m or "service_message" in chunk or "tgme_widget_message_service" in chunk:
            continue  # служебные записи пропускаем
        t = re.search(r'class="tgme_widget_message_text[^"]*"[^>]*>([\s\S]*?)</div>', chunk)
        text = clean_text(t.group(1)) if t else ""
        image = None
        for pattern in IMAGE_PATTERNS:
            found = re.search(pattern, chunk)
            if found:
                image = html.unescape(found.group(1))
                break
        if not text and not image:
            continue
        d = re.search(r'<time[^>]*datetime="([^"]+)"', chunk)
        posts.append({
            "id": m.group(1),
            "url": f"https://t.me/{CHANNEL}/{m.group(1)}",
            "text": text,
            "date": d.group(1) if d else None,
            "remote": image,
        })
    if ONLY_WITH_PHOTO:
        posts = [p for p in posts if p["remote"]]
    return posts[-LIMIT:][::-1]  # новые сверху


def main():
    posts = parse(fetch(f"https://t.me/s/{CHANNEL}").decode("utf-8", "replace"))
    if not posts:
        raise SystemExit("Посты не найдены, tg.json не изменён")
    os.makedirs("tg", exist_ok=True)
    keep = set()
    for p in posts:
        remote = p.pop("remote")
        p["image"] = None
        if remote:
            path = f"tg/{p['id']}.jpg"
            try:
                with open(path, "wb") as f:
                    f.write(fetch(remote))
                p["image"] = path
                keep.add(os.path.basename(path))
            except Exception as e:  # фото не скачалось: показываем пост без него
                print("Не удалось скачать фото", p["id"], e)
    for name in os.listdir("tg"):
        if name not in keep:
            os.remove(os.path.join("tg", name))
    with open("tg.json", "w", encoding="utf-8") as f:
        json.dump({"posts": posts}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("Готово:", [p["id"] for p in posts])


if __name__ == "__main__":
    main()
