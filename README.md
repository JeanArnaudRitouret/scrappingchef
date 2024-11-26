# scrappingchef
A personal repo used to scrap cooking platforms.
This repo is made for personal use and requires multiple settings not externally available to be effective, such as login, password and url of the scrapped platform.


## Platform New App
This app is dedicated to scrapping a new cooking platform. 

### How to scrap the new platform?
- The scrapping is only available locally in order to save processing power and time.
- activate the virtual environment and install the dependencies with `pip install -r requirements.txt`
- launch the app locally with `make run`
- reach the local url `http://localhost:8000/platform_new/scrap_paths_and_trainings/` to launch the scrapping of paths and trainings



### How to migrate the local database into the cloud sql instance?
- the sqlite database is created locally by scrapping the platform and should then be uploaded to the cloud sql instance.
- in order to migrate, run `make migrate_to_postgres`
- the script will create an export file of the local database called `data_export_<timestamp>.json`, upload it to the cloud sql instance and load it.

### How to deploy the platform_new app into Google App Engine?
- run `make deploy`

### How to delete previous versions of the app?
- run 

### Which urls are available?
Read-only urls are available on the cloud app:
- 'platform_new/list_scraped_paths/'
- 'platform_new/list_scraped_trainings/'


## Platform Old App
The scrapping of the old platform hasn'nt been maintained for a long time, and the code is not up to date. Use the new platform

