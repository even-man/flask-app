from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from databaseConfig import getHost, getDB, getPassword, getUser
import sqlite3
from setup import SecretKey, DatabasePath

#app setup
app = Flask(__name__)
app.secret_key = SecretKey()

#database setup
DB_PATH = DatabasePath()


#user authentication for controlling routing
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            session['messages'] = 'Login to access this resource.'
            return redirect(url_for('home'))
    return wrap


# home route : GET and POST
# GET
#   renders home.html template
# POST
#   gets data from forms and logs user in if appropriate
#   sets session
@app.route("/", methods = ['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'GET':
        return render_template("home.html")
    if request.method == 'POST':

        username = request.form['UserName']
        password = request.form['Password']

        sql = 'SELECT * FROM admins'
        data = sql_data_to_list_of_dicts(DB_PATH, sql)

        loginStatus = login(data, username, password)

        if loginStatus:
            session['logged_in'] = True
            session['username'] = username

            return redirect(url_for('dashboard'))
        
        else:
            message = 'Invalid Login'
            return render_template('home.html', message=message)

# dashboard route : GET
# GET
#   returns the dashboard.html template IF user logged in
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')
       
# about route : GET
# GET
#   returns the about.html template
@app.route("/about")
def about():
    return render_template("about.html")

# logout route : POST
# POST
#   gets data from form by js script on _navbar.html 
#   IF userInput TRUE, clear session and redirect home
#   ELSE redirect to dashboard

# ISSUES
#   despite user input in js script alert window, always redirects to home.html
@app.route("/logout", methods=['POST'])
def logout():

    if request.method == 'POST':
        userInput = request.form.get("userInput")
        app.logger.info(f'userInput: {userInput}')

        if userInput:
            session.clear()
            return redirect(url_for('home'))

        else:
            return redirect(url_for('/dashboard'))

# DATA ACCESS METHODS #

# get sql data and return as dict object  
def sql_data_to_list_of_dicts(path_to_db, select_query):

    try:
        con = sqlite3.connect(path_to_db)
        con.row_factory = sqlite3.Row
        things = con.execute(select_query).fetchall()
        unpacked = [{k: item[k] for k in item.keys()} for item in things]
        return unpacked
    except Exception as e:
        print(f"Failed to execute. Query: {select_query}\n with error:\n{e}")
        return []
    finally:
        con.close()

# check user accounts for provided username, password candidates
def login(data, username, password):
    for item in data:
        if item['Password'] == password and item['UserName'] == username:
                 return True
    return False


# RUN APP #

if __name__ == '__main__':
    app.run(debug = True)