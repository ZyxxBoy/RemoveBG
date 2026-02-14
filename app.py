"""
AI Background Remover — Flask Application
==========================================
Removes image backgrounds using rembg (U2Net model).
"""

import os
import uuid
import time
import threading
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, jsonify, send_file, abort
)
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = int(
    os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
)

UPLOAD_FOLDER = Path(app.static_folder) / "uploads"
PROCESSED_FOLDER = Path(app.static_folder) / "processed"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
CLEANUP_AGE_SECONDS = 600  # 10 minutes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(original: str) -> str:
    ext = original.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def cleanup_old_files():
    """Delete files older than CLEANUP_AGE_SECONDS from upload & processed folders."""
    now = time.time()
    for folder in (UPLOAD_FOLDER, PROCESSED_FOLDER):
        for f in folder.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > CLEANUP_AGE_SECONDS:
                try:
                    f.unlink()
                except OSError:
                    pass


def start_cleanup_daemon(interval: int = 300):
    """Run periodic cleanup in a background thread."""
    def _run():
        while True:
            cleanup_old_files()
            time.sleep(interval)
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def process_image(input_path: Path, output_path: Path):
    """Remove background from an image and save as transparent PNG."""
    with open(input_path, "rb") as inp:
        input_data = inp.read()
    output_data = remove(input_data)
    output_path = output_path.with_suffix(".png")
    with open(output_path, "wb") as out:
        out.write(output_data)
    return output_path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/remove", methods=["POST"])
def remove_bg():
    """Accept an image upload, remove background, return JSON with paths."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only JPG, JPEG, and PNG are accepted."}), 400

    # Save uploaded file
    safe_name = secure_filename(file.filename)
    new_name = unique_filename(safe_name)
    upload_path = UPLOAD_FOLDER / new_name
    file.save(str(upload_path))

    # Process
    try:
        output_name = f"{Path(new_name).stem}.png"
        output_path = PROCESSED_FOLDER / output_name
        process_image(upload_path, output_path)
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({
        "original": f"/static/uploads/{new_name}",
        "processed": f"/static/processed/{output_name}",
    })


@app.route("/api/remove", methods=["POST"])
def api_remove_bg():
    """API endpoint — returns the processed image bytes directly."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or missing file."}), 400

    safe_name = secure_filename(file.filename)
    new_name = unique_filename(safe_name)
    upload_path = UPLOAD_FOLDER / new_name
    file.save(str(upload_path))

    try:
        output_name = f"{Path(new_name).stem}.png"
        output_path = PROCESSED_FOLDER / output_name
        process_image(upload_path, output_path)
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return send_file(str(output_path), mimetype="image/png", as_attachment=True,
                     download_name="removed_bg.png")


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 5 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found."}), 404


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    start_cleanup_daemon()
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=5000)
