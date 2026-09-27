from flask import Flask, request, jsonify
from urllib.parse import urlparse

from models import db, MonitoredURL


app = Flask(__name__)

# SQLite database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///uptime.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Connect database to Flask
db.init_app(app)


# Create database tables
with app.app_context():
    db.create_all()


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
        return jsonify({
            "error": "Invalid URL"
        }), 400

    # Check whether URL already exists
    existing_url = MonitoredURL.query.filter_by(url=url).first()

    if existing_url:
        return jsonify({
            "error": "URL already registered"
        }), 409

    # Create database record
    new_url = MonitoredURL(url=url)

    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        "message": "URL registered successfully",
        "id": new_url.id,
        "url": new_url.url
    }), 201


@app.route("/urls", methods=["GET"])
def get_urls():

    urls = MonitoredURL.query.all()

    result = []

    for item in urls:
        result.append({
            "id": item.id,
            "url": item.url
        })

    return jsonify({
        "urls": result
    }), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
