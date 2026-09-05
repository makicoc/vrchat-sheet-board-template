#!/usr/bin/env python3
import csv
import html
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MAKISheetBoard/1.0)"}
FETCH_ATTEMPTS = 3
FETCH_TIMEOUT_SECONDS = 30
RETRY_DELAYS_SECONDS = (5, 15)
COLOR_NAMES = {
    "青": "#AFCBFF",
    "ブルー": "#AFCBFF",
    "blue": "#AFCBFF",
    "ピンク": "#FFD6E7",
    "pink": "#FFD6E7",
    "緑": "#D7F5D0",
    "グリーン": "#D7F5D0",
    "green": "#D7F5D0",
    "黄": "#FFF0A8",
    "黄色": "#FFF0A8",
    "イエロー": "#FFF0A8",
    "yellow": "#FFF0A8",
    "紫": "#DCCBFF",
    "パープル": "#DCCBFF",
    "purple": "#DCCBFF",
    "オレンジ": "#FFD0A6",
    "orange": "#FFD0A6",
    "グレー": "#D9DEE8",
    "灰": "#D9DEE8",
    "gray": "#D9DEE8",
    "grey": "#D9DEE8",
}


def set_action_output(name: str, value: str):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")


class FetchError(RuntimeError):
    """A temporary or external error while downloading the published CSV."""

    def __init__(self, message: str, *, transient: bool = True):
        super().__init__(message)
        self.transient = transient


def fetch_text(url: str) -> str:
    last_error = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
                data = response.read()
            return data.decode("utf-8-sig", errors="replace")
        except urllib.error.HTTPError as exc:
            # Retry only errors that are commonly temporary. A 403/404 should
            # remain visible as a configuration or sharing error.
            if exc.code not in {408, 425, 429} and not 500 <= exc.code <= 599:
                raise FetchError(
                    f"Google Sheetsの取得に失敗しました（HTTP {exc.code}）。",
                    transient=False,
                ) from exc
            last_error = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc

        if attempt < FETCH_ATTEMPTS:
            delay = RETRY_DELAYS_SECONDS[min(attempt - 1, len(RETRY_DELAYS_SECONDS) - 1)]
            print(f"Google Sheetsの取得に失敗しました。{delay}秒後に再試行します（{attempt}/{FETCH_ATTEMPTS}）")
            time.sleep(delay)

    raise FetchError(
        f"Google Sheetsの取得が{FETCH_ATTEMPTS}回連続で失敗しました。"
        f"一時的な通信エラーの可能性があります: {last_error}"
    ) from last_error


def read_field(row: dict, *names: str) -> str:
    for name in names:
        if name in row and row[name] is not None:
            return str(row[name]).strip()
    return ""


def normalize_color(value: str) -> str:
    value = value.strip()
    if not value:
        return "#AFCBFF"
    mapped = COLOR_NAMES.get(value)
    if mapped:
        return mapped
    mapped = COLOR_NAMES.get(value.lower())
    if mapped:
        return mapped
    if not value.startswith("#"):
        value = "#" + value
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.upper()
    return "#AFCBFF"


def normalize_rows(csv_text: str):
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise RuntimeError("CSVにヘッダー行がありません。title, body, date, color の列を用意してください。")

    notices = []
    max_items = int(CONFIG.get("max_items", 0) or 0)
    for row in reader:
        title = read_field(row, "title", "タイトル", "件名")
        body = read_field(row, "body", "本文", "内容")
        date = read_field(row, "date", "日付", "日時")
        color = normalize_color(read_field(row, "color", "色", "カラー"))

        if not title and not body:
            continue
        if not title:
            title = "お知らせ"

        notices.append({
            "title": html.unescape(title),
            "body": html.unescape(body),
            "date": html.unescape(date),
            "color": color,
        })
        if max_items > 0 and len(notices) >= max_items:
            break
    return notices


def main():
    owner, repo = os.environ.get("GITHUB_REPOSITORY", "YOUR_NAME/YOUR_REPO").split("/", 1)
    base_url = f"https://{owner}.github.io/{repo}"
    sheet_csv_url = str(CONFIG.get("sheet_csv_url", "")).strip()

    if not sheet_csv_url:
        set_action_output("skipped", "true")
        print("sheet_csv_url が未設定のため、同期と公開をスキップしました。")
        print("config.json の sheet_csv_url に Google Sheets の公開CSV URLを設定してください。")
        return
    if not sheet_csv_url.startswith("https://"):
        raise RuntimeError("config.json の sheet_csv_url には https:// で始まる公開CSV URLを設定してください。")

    try:
        csv_text = fetch_text(sheet_csv_url)
    except FetchError as exc:
        # Keep the last successful Pages deployment by skipping the deploy.
        # Pages retains the previous deployment even when this checkout has no
        # generated site files. Configuration errors still fail visibly.
        if exc.transient:
            set_action_output("skipped", "true")
            print(f"一時的にGoogle Sheetsを取得できないため、公開をスキップして前回のPagesデータを維持します: {exc}")
            return
        raise

    notices = normalize_rows(csv_text)
    set_action_output("skipped", "false")
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "board.json").write_text(json.dumps({"notices": notices}, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    (SITE / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>MAKI Sheet Board</title>"
        "<h1>MAKI Sheet Board 公開完了</h1>"
        f"<p>お知らせ {len(notices)} 件</p>"
        f"<p>Unityへ貼るURL：<code>{base_url}</code></p>"
        f"<p>JSON：<a href='{base_url}/board.json'>{base_url}/board.json</a></p>",
        encoding="utf-8",
    )
    print(f"同期完了: {len(notices)} 件")
    print(f"Unityへ貼るURL: {base_url}")


if __name__ == "__main__":
    main()
