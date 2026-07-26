#!/bin/sh
set -e
python CarStore/manage.py migrate --settings=config.settings
exec "$@"
