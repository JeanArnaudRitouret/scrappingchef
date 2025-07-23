# scrappingchef
A personal repo used to scrap cooking platforms.
This repo is made for personal use and requires multiple settings not externally available to be effective, such as login, password and url of the scrapped platform.

## Terraform
This project uses terraform to manage the infrastructure.

### What's included in the infrastructure?
- a VPC network
- a Cloud SQL instance (PostgreSQL 16)
- Secret Manager secrets for the following remote database credentials
  - DB_HOST
  - DB_PORT
  - DB_NAME
  - DB_USER
  - DB_PASSWORD

### How to deploy the infrastructure?
- run `terraform init`
- run `terraform apply`

### How to delete previous deployed versions of the infrastructure which have no traffic split anymore?
- run `terraform destroy`

### How to fill in the remote database credentials?
- These credentials are stored in the Google Secret Manager. They have to be filled directly there for security


## Platform New App
This app is dedicated to scrapping a new cooking platform. 

### PostgreSQL16
- the app uses a PostgreSQL16 database. If postgres is not installed, install it with `brew install postgresql16` and start it with `brew services start postgresql16`
- If you don't have a user and a database created, create them with `createuser <user_name> --createdb --pwprompt` and `createdb <database_name> --owner=<user_name>`
- You can check the user and database with `psql -U <user_name> -d <database_name>`
- Define the environment variables in the `.envrc` file (see section below)

### How to Set Up the Environment
- create a `.envrc` file by copying the `.envrc_template` file and filling the variables

### How to migrate the local database into the cloud sql instance?
- the sqlite database is created locally by scrapping the platform and should then be uploaded to the cloud sql instance.
- in order to migrate, run `make migrate_to_postgres`
- the script will create an export file of the local database called `data_export_<timestamp>.json`, upload it to the cloud sql instance and load it.

### How to scrap the new platform?
- The scrapping is only available locally
- this project uses python 3.11.12
- install the dependencies with `poetry install`
- if it's the first time you run the app, run `make migrate` to create the tables in the database
- launch the app locally with `make run`
 - if you have issues wiht unapplied migrations, run `make migrate` again
- reach the local url `http://localhost:8000/platform_new/scrap_all_paths_and_trainings/` to launch the scrapping of paths and trainings




### How to deploy the platform_new app into Google App Engine?
- run `make deploy`

### How to delete previous deployed versions of the app which have no traffic split anymore?
- run `make delete-old-deployed-versions`

### Which urls are available?
Read-only urls are available on the cloud app:
- 'platform_new/list_scraped_paths/'
- 'platform_new/list_scraped_trainings/'


## Platform Old App
The scrapping of the old platform hasn'nt been maintained for a long time, and the code is not up to date. Use the new platform

