#!/usr/bin/env python3

from pathlib import Path

FILE = Path("/usr/lib/python3/site-packages/flasgger/ui3/templates/flasgger/head.html")

TARGET = '<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700|Source+Code+Pro:300,600|Titillium+Web:400,600,700" rel="stylesheet">'
REPLACEMENT = f"<!-- {TARGET} -->"


def main():
    if not FILE.exists():
        print(f"[ERROR] Файл не найден: {FILE}")
        return

    text = FILE.read_text(encoding="utf-8")

    if REPLACEMENT in text:
        print("[INFO] Строка уже закомментирована.")
        return

    if TARGET not in text:
        print("[ERROR] Целевая строка не найдена.")
        return

    text = text.replace(TARGET, REPLACEMENT)

    FILE.write_text(text, encoding="utf-8")

    print("[OK] Строка успешно закомментирована.")


if __name__ == "__main__":
    main()
