PROJECT_ID=scrappingchef

.PHONY: run

run:
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

shell:
	python manage.py shell

database_migration:
	python -m database_migration

move_contents:
	python -m move_contents_to_gcs

deploy:
	gcloud app deploy --project $(PROJECT_ID)

delete-old-deployed-versions:
	gcloud app versions list --project $(PROJECT_ID) --filter="TRAFFIC_SPLIT=0.00" --format="table(version.id)" | tail -n +2 | xargs -r gcloud app versions delete --project $(PROJECT_ID) --quiet

shebang:
	make database_migration
	make move_contents
	make deploy
	make delete-old-deployed-versions