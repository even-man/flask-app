from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from databaseConfig import getHost, getDB, getPassword, getUser
import sqlite3
from setup import SecretKey, DatabasePath
import datetime

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


#dict for standing filter
standingFilters = {
    'GoodStanding' : 'Good Standing',
    'FacilityBanSemester' : 'Facility Ban (Semester)',
    'PermaBan' : 'PermaBan',
    'FacilityBanMonth' : 'Facility Ban (One Month)'
}


# dashboard route : GET
# GET
#   returns the dashboard.html template IF user logged in
@app.route('/dashboard', methods=['GET', 'POST'])
@is_logged_in
def dashboard():

    if request.method == 'GET':
        return render_template('dashboard.html')
    
    if request.method == 'POST':
        
        username = request.form.get('username')
        numbermarks = request.form.get('numbermarks')
        reason = request.form.get('reason')
        issuer = request.form.get('issuer')
        date = datetime.date.today().strftime('%Y-%m-%d')
        
        error = 'All inputs must contain info'

        if username == '' or reason == '' or issuer == '' or numbermarks == '':
            return render_template('dashboard.html', error = error)
        
        data = search_by_username(username)

        if len(data) == 0:
            #create new user and create new marks
        else:
            #update user in system and create new marks


        return render_template('dashboard.html')

# users route : GET POST
# GET
#   returns a form for filtering users and searching by username

@app.route('/users', methods = ['GET', 'POST'])
@is_logged_in
def users():
    
    if request.method == 'GET':
        return render_template('users.html')
    if request.method == 'POST':

        value1 = request.form.get('Users')
        app.logger.info(f'Users Value from form: {value1}')


        if request.form.get('Users') == 'standingForm':
            app.logger.info('standing form submitted')

            standing = request.form['standings']
            app.logger.info(f'standing filter: {standing}')

            sql = f'SELECT * FROM Users WHERE CurrentStanding == "{standingFilters[standing]}"'

            app.logger.info(f'sql: {sql}')

            data = sql_data_to_list_of_dicts(DB_PATH, sql)
            
            return render_template('users.html', data=data)

        if request.form.get('Users') == 'usernameForm':
            app.logger.info('username search form submitted')

            username = request.form['username']
            app.logger.info(f'username: {username}')

            sql = f'SELECT * FROM Users WHERE UserName == "{username}"'
            data = sql_data_to_list_of_dicts(DB_PATH, sql)

            return render_template('users.html', data=data)

@app.route('/marks', methods=['GET', 'POST'])
@is_logged_in
def marks():

    if request.method == 'GET':
        return render_template('marks.html')
    if request.method == 'POST':

        if request.form.get('marks') == 'usernameFilter':
            #search by username
            username = request.form['username']
            sql = f'SELECT * FROM Marks WHERE UserName = "{username}"'
            data = sql_data_to_list_of_dicts(DB_PATH, sql)
            return render_template('marks.html', data=data)

        if request.form.get('marks') == 'refresh':
            #return all data
            sql = f'SELECT * FROM Marks'
            data = sql_data_to_list_of_dicts(DB_PATH, sql)
            return render_template('marks.html', data=data)


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

@app.route("/logout", methods=['GET', 'POST'])
def logout():
     session.clear()
     return redirect(url_for('home'))



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

def search_by_username(username):
    sql = f'SELECT * FROM Users WHERE UserName == "{username}"'
    data = sql_data_to_list_of_dicts(DB_PATH, sql)
    return data

# RUN APP #

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0')