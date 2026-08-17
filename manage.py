"""Flask CLI and migration helper for MJ WebTech.

Usage:
  set FLASK_APP=manage
  flask db init
  flask db migrate -m "Initial schema"
  flask db upgrade
"""

import os
from app import create_app

env = os.environ.get("FLASK_ENV", "development")
application = create_app(env)
app = application

if __name__ == "__main__":
    application.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=application.config.get("DEBUG", False),
    )
