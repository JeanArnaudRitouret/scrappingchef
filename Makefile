.PHONY: run

run:
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

shell:
	python manage.py shell

migrate_to_postgres:
	python migrate_to_postgres.py

deploy:
	gcloud app deploy

delete-old-deployed-versions:
	gcloud app versions list --filter="TRAFFIC_SPLIT=0.00" --format="table(version.id)" | tail -n +2 | xargs -r gcloud app versions delete --quiet