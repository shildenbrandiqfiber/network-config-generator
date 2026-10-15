#!/usr/bin/env python3
"""
management commands for the Web service (based on the Flask CLI, same as ``flask --app app <command>``), e.g.

    python3 manage.py db upgrade
    python3 manage.py run --host 0.0.0.0 --port 5000
"""
from flask.cli import FlaskGroup
from app import app

cli = FlaskGroup(create_app=lambda: app)

if __name__ == '__main__':
    cli()
