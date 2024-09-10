#!/bin/bash

echo "=================Running tests with psycopg2================="
echo ""

echo "  - Removing .venv"
rm -rf .venv

echo "  - Recreating venv"
poetry install --with dev,psycopg2 --without psycopg3

echo "  - Running tests"
poetry run pytest

echo "=================Running tests with psycopg3================="
echo ""

echo "  - Removing .venv"
rm -rf .venv

echo "  - Recreating venv"
poetry install --with dev,psycopg3 --without psycopg2

echo "  - Running tests"
poetry run pytest
