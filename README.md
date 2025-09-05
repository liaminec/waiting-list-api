# WAITING LIST API

## Introduction
This project is the ground base for an API of ticket reservesion with an 
emphasis on the waiting list functionality.
It was done in Python (3.10) using FastAPI (WEB Framework), SQLModel (ORM) and 
Alembic (DB migrations).
It is structured in subapps
```
api
|__ alembic  // Folder regarding DB migrations
|__ common // Methods and classes used by all the subapps
|   |__ db
|   |   |__ models.py  // Abstract ORM models
|   |   |__ utils.py  // Methods to ease the use of the ORM
|   |__ dependencies.py  // Methods to be used as dependencies by all routes
|__ data  // Everything data related, data files, sqlite DBs
|__ events  // Subapp for events and other items linked to them, like offers, representations
|__ participations  // Subapps for models and routes regarding the logic of event participation and waiting list
|__ users  // Subapp for users and organizations
|__ tests  // Unit tests 
|__ app.py  // The main script of the app, also contains the routing
|__ .env  // Env variables
|__ config.py  // contains important elements of configurations, like the DB engine
```
Each subapp follows this simple structure
```
|__ models.py  // The ORM models
|__ serializers.py
|__  routes.py  // All the views regarding the logic of the subapp
```
## Launching the project
Prerequisite: Python310, Pip, Sqlite3


1) Install packages

```
cd api/
pip install -r requirements.txt
````

2) Launch the API

Before launching, make sure that the DB_URL env variable in the .env file does 
not point to the test database

```
fastapi dev app.py
```

Since we're using sqlite, the database have come ready, so now you are good 
to go :)

In case the DB does not work as expected:
- Delete the DB files and re-create them
```
sqlite3 data/db/database "VACUUM;"
sqlite3 data/db/test-database "VACUUM;"
```
Then to apply the migrations to a specific DB go to ``alembic.ini`` and set the
variable ```sqlalchemy.url``` to the url of the ``sqlite:///{path_of_your_db}``
and run
```
alembic upgrade head
```
This will create all the tables, finally, to fill it:
```
python data/init_db.py
```
## Swagger

To have information on the endpoints, a Swagger is available once the app is 
launched at this address:
````localhost:8000/docs````

## Launch the unit tests

1) Install the test requirements

````pip install -r requirements-dev.txt````

2) Launch the tests

````pytest````
