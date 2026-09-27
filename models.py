from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MonitoredURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)

    def __repr__(self):
        return f"<MonitoredURL {self.url}>"


class URLCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    url_id = db.Column(
        db.Integer,
        db.ForeignKey("monitored_url.id"),
        nullable=False
    )

    status = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    response_time_ms = db.Column(db.Float, nullable=True)
    checked_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<URLCheck {self.status}>"
