# DJ DB Rotated Secret

AWS Secrets auto-rotation will cause a `password authentication failure` in Django that is unhandled.

This is a low level wrapper around Django's `_cursor` and `connect` db functions to handle and and allow graceful rotation.

## WARNING

This is very much an alpha release. Jenfi uses it in production, but it is entirely suited to our needs. PRs welcome to expand the capabilities.

## Things to Know

- Postgres only via psycopg 2 & 3
- It is a monkey patch and can only be added via installed_apps.
  - i.e. if a password gets rotated _after_ django loads but _before_ this library gets loaded _while_ another app makes a DB connection, the password error won't get caught. Extremely narrow window.
- This library does not know/care about how to obtain the updated password. Simply tell it a function path to run and it will call it assuming a return dict of:

  ```python
  {
    "username": "...",
    "password": "...",
  }
  ```

## Install

1. `poetry add dj-db-rotated-secret`
1. Add to installed apps, below django and above other apps.

   ```python
       INSTALLED_APPS = [
         ...
         "dj_db_rotated_secret",
         ...
       ]
   ```

1. Declare a function to run when password auth fails:

   ```python
       DJ_DB_ROTATED_SECRET_FUNC = "path.to.function"
   ```

## Function Info

- The function takes no arguments.
- The function must return a dictionary with the keys `username` and `password`.

## Development

- Uses poetry

## Run Tests

1. Run `docker compose up`
1. Run `pytest`
