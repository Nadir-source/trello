#!/usr/bin/env bash
set -e
export PYTHONPATH=.
gunicorn -c gunicorn.conf.py app.app:app
