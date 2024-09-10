#!/bin/bash

echo "Running tests with psycopg2"
rm -rf .venv
poetry install --with dev,psycopg2 --without psycopg3
poetry run pytest

echo "Running tests with psycopg3"
rm -rf .venv
poetry install --with dev,psycopg3 --without psycopg2
poetry run pytest
