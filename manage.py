"""Flask CLI and migration helper for MJ WebTech.

Usage:
  set FLASK_APP=manage
  flask db init
  flask db migrate -m "Initial schema"
  flask db upgrade
"""

import os
from app import create_app

# Render injects RENDER=true on every service. Default to production there so
# CORS, secure cookies, and HSTS apply even if FLASK_ENV was left unset.
if os.environ.get("RENDER"):
    os.environ.setdefault("FLASK_ENV", "production")

env = os.environ.get("FLASK_ENV", "development")
application = create_app(env)
app = application

if __name__ == "__main__":
    application.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=application.config.get("DEBUG", False),
    )
