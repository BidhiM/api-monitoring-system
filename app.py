from flask import Flask, request, jsonify, render_template
from urllib.parse import urlparse
import requests
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, MonitoredURL, URLCheck


app = Flask(__name__)

# SQLite database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///uptime.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Connect database to Flask
db.init_app(app)

def check_all_urls():

    with app.app_context():

        urls = MonitoredURL.query.all()

        for monitored_url in urls:

            result = check_one_url(monitored_url)

            print(
                f"Checked {monitored_url.url}: "
                f"{result['status']}"
            )

# Create database tables
with app.app_context():
    db.create_all()

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

def check_one_url(monitored_url):

    start_time = time.time()

    try:
        response = requests.get(
            monitored_url.url,
            timeout=5
        )

        end_time = time.time()

        response_time = round(
            (end_time - start_time) * 1000,
            2
        )

        check = URLCheck(
            url_id=monitored_url.id,
            status="UP",
            status_code=response.status_code,
            response_time_ms=response_time,
            checked_at=datetime.utcnow()
        )

        db.session.add(check)
        db.session.commit()

        return {
            "status": "UP",
            "status_code": response.status_code,
            "response_time_ms": response_time
        }

    except requests.RequestException:

        check = URLCheck(
            url_id=monitored_url.id,
            status="DOWN",
            status_code=None,
            response_time_ms=None,
            checked_at=datetime.utcnow()
        )

        db.session.add(check)
        db.session.commit()

        return {
            "status": "DOWN",
            "status_code": None,
            "response_time_ms": None
        }

@app.route("/urls/<int:url_id>/check", methods=["GET"])
def check_url(url_id):

    monitored_url = db.session.get(
        MonitoredURL,
        url_id
    )

    if monitored_url is None:
        return jsonify({
            "error": "URL not found"
        }), 404

    result = check_one_url(monitored_url)

    return jsonify({
        "id": monitored_url.id,
        "url": monitored_url.url,
        **result
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

@app.route("/urls/<int:url_id>/history", methods=["GET"])
def get_history(url_id):

    monitored_url = db.session.get(MonitoredURL, url_id)

    if monitored_url is None:
        return jsonify({
            "error": "URL not found"
        }), 404

    checks = URLCheck.query.filter_by(
        url_id=url_id
    ).order_by(
        URLCheck.checked_at.desc()
    ).all()

    result = []

    for check in checks:
        result.append({
            "status": check.status,
            "status_code": check.status_code,
            "response_time_ms": check.response_time_ms,
            "checked_at": check.checked_at.isoformat()
        })

    return jsonify({
        "url": monitored_url.url,
        "history": result
    }), 200

@app.route("/urls/<int:url_id>/stats", methods=["GET"])
def get_stats(url_id):

    monitored_url = db.session.get(
        MonitoredURL,
        url_id
    )

    if monitored_url is None:
        return jsonify({
            "error": "URL not found"
        }), 404

    # Get all checks for this URL
    checks = URLCheck.query.filter_by(
        url_id=url_id
    ).all()

    # Get the most recent check
    latest_check = URLCheck.query.filter_by(
        url_id=url_id
    ).order_by(
        URLCheck.checked_at.desc()
    ).first()

    total_checks = len(checks)

    # No checks have been performed yet
    if total_checks == 0:
        return jsonify({
            "url": monitored_url.url,
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "uptime_percentage": 0,
            "average_response_time_ms": None,
            "current_status": "UNKNOWN"
        }), 200

    # Count successful and failed checks
    successful_checks = 0
    failed_checks = 0

    response_times = []

    for check in checks:

        if check.status == "UP":
            successful_checks += 1

            if check.response_time_ms is not None:
                response_times.append(
                    check.response_time_ms
                )

        else:
            failed_checks += 1

    # Calculate uptime percentage
    uptime_percentage = round(
        (successful_checks / total_checks) * 100,
        2
    )

    # Calculate average response time
    if response_times:
        average_response_time = round(
            sum(response_times) / len(response_times),
            2
        )
    else:
        average_response_time = None

    # Return statistics
    return jsonify({
        "url": monitored_url.url,
        "total_checks": total_checks,
        "successful_checks": successful_checks,
        "failed_checks": failed_checks,
        "uptime_percentage": uptime_percentage,
        "average_response_time_ms": average_response_time,
        "current_status": latest_check.status
    }), 200

scheduler = BackgroundScheduler()

scheduler.add_job(
    check_all_urls,
    "interval",
    minutes=1
)

scheduler.start()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

