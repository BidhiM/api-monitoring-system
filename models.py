from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class MonitoredURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)

    def __repr__(self):
        return f"<MonitoredURL {self.url}>"
