SQLAlchemy version: 1.4.0
To set up, install SQLAlchemy1.4.0
pip install SQLAlchemy==1.4.0
Incorrect version of SQLAlchemy might result in errors

For running the server
cmd-> cd your_file_path_to_app.py
flask run --host 0.0.0.0

For initialization of the tables and records in the database, uncomment line 51-60 of app.py and run the server. For subsequent runs, comment these lines again.

Please make sure that there is no tables named "users", "vlogs", "likes", "comments" in the database before initialization.

Before running, change the ip address in line 21 of video.html to your ip address, and the database URI in line 11 of app.py to your database URI. 

To start, type your ip+":5000/reg" in the address bar of your browser.

There are some error alerts in video.html when open in Pycharm due to duplicate element ids in the if-else clauses but will not affect the running of the application.
