import time
from functools import wraps

import psycopg2
from django.db import connections
from django.db.backends.postgresql.base import BaseDatabaseWrapper
from django.db.utils import OperationalError

from dj_db_rotated_secret.settings import get_handler_function

# This function is SCARY.
#

# This covers if the lambda was started just after the rotation but didn't connect with it.
# Also covers new rotation connection attempts if the SecretCache isn't broken yet w/
# a basic backoff strategy.
original_connect = BaseDatabaseWrapper.connect


@wraps(original_connect)
def wrapped_connect(self):
    max_retries = 5
    initial_wait = 0.1
    backoff_factor = 2

    for attempt in range(max_retries):
        try:
            return original_connect(self)
        except (psycopg2.OperationalError, OperationalError) as e:
            if "password authentication failed" not in str(e).lower():
                raise
            if attempt >= max_retries - 1:
                raise Exception(f"Max retries ({max_retries}) exceeded for reconnecting with new credentials")

            wait_time = initial_wait * (backoff_factor**attempt)
            time.sleep(wait_time)

            reconnect_new_credentials()


BaseDatabaseWrapper.connect = wrapped_connect

#
# It's a monkey patch that replaces the cursor with a wrapped version that retries
# the connection if the password is bad. This assumes the PW was rotated by AWS Secrets Manager.
#
# It uses the cursor because that's the most common entry point for all DB operations.

original_cursor = BaseDatabaseWrapper._cursor


@wraps(original_cursor)
def wrapped_cursor(self, name=None):
    try:
        return original_cursor(self, name)
    except (psycopg2.OperationalError, OperationalError) as e:
        if "password authentication failed" in str(e).lower():
            reconnect_new_credentials()
        else:
            raise


BaseDatabaseWrapper._cursor = wrapped_cursor


# Call this function early in your Django app's initialization
def reconnect_new_credentials():
    # Update credentials
    updated_secret = get_handler_function()()
    username = updated_secret["username"]
    password = updated_secret["password"]

    # Update Django settings dynamically
    from django.conf import settings

    settings.DATABASES["default"]["USER"] = username
    settings.DATABASES["default"]["PASSWORD"] = password

    # Close existing database connections
    connections.close_all()

    # Reopen the database connection with the new credentials
    connections["default"].connect()
