pip install -r requirements.txt

if you want to start project in development mode, run the following command:
uvicorn main:app --reload

if you want to start project in production mode, run the following command:
uvicorn main:app --workers 4

all the db tables are in the tables.py file in the next update i will add the db migration

just change the db connection string in the db.py file ".env coming soon"

for now the scrapper is using firefox browser and geckodriver, in the next updates the other browser supports will be added

for now the scrapper is only scrapping single user posts, profile details.

there is a little bug ThreadPoolExecutor is not working properly
so please add single item in the db table and run the scrapper.py
```
UPDATE: i think its about browser cache, i will fix it in the next updates
```
proxy support will be added in the next updates

also you need to fill settings table in the db "LOGIN IS OPTIONAL" but if you want more data you need to provide the uname and pass
and also please provide post_count in the settings table otherwise the scrapper will only scrap the 3 posts

```
UPDATE: i added headless support and database writing support, now the scrapper is working fine
UPDATE: i added router for results, now you can see the results in the browser
```
