# Book database app

Uses flask and postgresql.
Allows adding and removing books, searching books by title and genre and adding reviews with scores.

## Python requirements (at `requirements.txt`)

```
flask
psycopg2
```

## External requirements

- Postgresql database
  - Running at `localhost:5432` (port 5432 should be the default during installation)
  - With user `postgres`
  - With no password or empty password
  - App reserves database name `library`
- Available port 8080
- Python module `venv` probably belongs here.

## Deployment

- Deploy Postgresql database mentioned above
- Create venv: `$ python -m venv venv`
- Install python requirements: `$ pip install -r requirements.txt`
- Launch the app: `$ python server.py`
- Open in web browser: `http://localhost:8080`

