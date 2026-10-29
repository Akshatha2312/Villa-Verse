from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Global extension instances
db = SQLAlchemy()
csrf = CSRFProtect()
