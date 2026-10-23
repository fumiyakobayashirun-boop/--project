"""画質向上ツールのローカルWebサーバー。

    python app.py            # ブラウザが自動で開く
    python app.py --port 8765 --no-browser

このPC（127.0.0.1）からのみアクセスでき、ファイルは外部に送信されない。
"""
from __future__ import annotations

import argparse
import io
import threading
import uuid
import webbrowser
import zipfile
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from flask import Flask, abort, jsonify, render_template, request, send_file

from enhancer.documents import Result, is_supported, process
from enhancer.filters import Options

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 1ファイル200MBまで

# CPUを使い切る処理なので、同時に走らせるのは1件だけにする
executor = ThreadPoolExecutor(max_workers=1)
jobs: dict = {}
jobs_lock = threading.Lock()
MAX_KEPT_JOBS = 50


class Job:
    def __init__(self, filename: str):
        self.id = uuid.uuid4().hex
        self.filename = filename
        self.status = "queued"  # queued / running / done / error
        self.progress = 0.0
        self.error = ""
        self.result: Result | None = None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "progress": round(self.progress, 3),
            "error": self.error,
            "output": self.result.filename if self.result else None,
            "notes": self.result.notes if self.result else [],
        }


def _run(job: Job, data: bytes, opts: Options) -> None:
    job.status = "running"
    try:
        job.result = process(data, job.filename, opts, lambda f: setattr(job, "progress", f))
        job.progress = 1.0
        job.status = "done"
    except Exception as e:  # 1ファイルの失敗で他の処理を止めない
        job.error = str(e) or e.__class__.__name__
        job.status = "error"


def _get_job(job_id: str) -> Job:
    job = jobs.get(job_id)
    if job is None:
        abort(404)
    return job


def _download(data: bytes, filename: str, mimetype: str):
    resp = send_file(io.BytesIO(data), mimetype=mimetype, as_attachment=True, download_name=filename)
    # 日本語ファイル名をSafariでも正しく扱えるようにする
    resp.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return resp


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/jobs")
def create_job():
    f = request.files.get("file")
    if f is None or not f.filename:
        return jsonify(error="ファイルがありません"), 400
    if not is_supported(f.filename):
        return jsonify(error="対応していない形式です（PDF・PNG・JPEG・WebP・BMP・TIFFに対応）"), 400
    try:
        opts = Options.from_form(request.form)
    except ValueError:
        return jsonify(error="設定値が不正です"), 400

    job = Job(f.filename)
    with jobs_lock:
        jobs[job.id] = job
        # 古い結果からメモリを解放する
        while len(jobs) > MAX_KEPT_JOBS:
            jobs.pop(next(iter(jobs)))
    executor.submit(_run, job, f.read(), opts)
    return jsonify(job.to_json()), 202


@app.get("/api/jobs/<job_id>")
def job_status(job_id: str):
    return jsonify(_get_job(job_id).to_json())


@app.get("/api/jobs/<job_id>/preview/<which>")
def job_preview(job_id: str, which: str):
    job = _get_job(job_id)
    if job.result is None or which not in ("before", "after"):
        abort(404)
    data = job.result.before if which == "before" else job.result.after
    return send_file(io.BytesIO(data), mimetype="image/png")


@app.get("/api/jobs/<job_id>/download")
def job_download(job_id: str):
    job = _get_job(job_id)
    if job.result is None:
        abort(404)
    mimetype = "application/pdf" if job.result.filename.endswith(".pdf") else "image/png"
    return _download(job.result.data, job.result.filename, mimetype)


@app.get("/api/download-all")
def download_all():
    ids = request.args.get("ids", "").split(",")
    results = [jobs[i].result for i in ids if i in jobs and jobs[i].result]
    if not results:
        abort(404)
    buf = io.BytesIO()
    used = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for r in results:
            name, n = r.filename, 1
            while name in used:  # 同名ファイルの上書きを避ける
                n += 1
                stem, _, ext = r.filename.rpartition(".")
                name = f"{stem}({n}).{ext}"
            used.add(name)
            zf.writestr(name, r.data)
    return _download(buf.getvalue(), "高画質化_まとめ.zip", "application/zip")


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF・画像の画質向上ツール")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="ブラウザを自動で開かない")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}/"
    print(f"\n  画質向上ツールを起動しました → {url}\n  終了するには、このウィンドウで Control + C を押してください。\n")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host="127.0.0.1", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
