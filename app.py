
from flask import Flask, request, jsonify
from urllib.parse import urlparse
import requests

app = Flask(__name__)

# Temporary storage (we'll replace this with a database)
monitored_urls = []


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "uptime-monitor"
    }), 200


@app.route("/urls", methods=["POST"])
def add_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({"error": "Invalid URL"}), 400

    if url in monitored_urls:
        return jsonify({"error": "URL already registered"}), 409

    monitored_urls.append(url)

    return jsonify({
        "message": "URL registered successfully",
        "url": url
    }), 201


@app.route("/urls", methods=["GET"])
def get_urls():
    return jsonify({
        "urls": monitored_urls
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
