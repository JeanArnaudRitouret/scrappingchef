.PHONY: run

run:
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	python manage.py runserver

migrate:
	python manage.py migrate

migrations:
	python manage.py makemigrations

shell:
	python manage.py shell

migrate_to_postgres:
	python migrate_to_postgres.py

deploy:
	gcloud app deploy
