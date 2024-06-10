pip install -r requirements.txt

if you want to start project in development mode, run the following command:
uvicorn main:app --reload

if you want to start project in production mode, run the following command:
uvicorn main:app --workers 4

all the db tables are in the tables.py file in the next update i will add the db migration

just change the db connection string in the db.py file ".env coming soon"

just for now scrapper.py is the main file to run the scrapper.py you need to provide the id of row in the db table
in the next update i will add dynamic database connection and the scrapper will run automatically
the output of the scrapper will be saved in the facebook_posts.json file in the same directory "/scripts"

for now the scrapper is using firefox browser and geckodriver, in the next updates the other browser supports will be added

for now the scrapper is only scrapping single user posts, profile details.

there is a little bug ThreadPoolExecutor is not working properly
so please add single item in the db table and run the scrapper.py

proxy support will be added in the next updates

also you need to fill settings table in the db "LOGIN IS OPTIONAL" but if you want more data you need to provide the uname and pass
and also please provide post_count in the settings table otherwise the scrapper will only scrap the 3 posts
