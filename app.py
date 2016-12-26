######################################
#Skeleton code can be found at: https://github.com/benlawson/Photoshare-Skeleton
#The rest of the code is written by Jessica McAloon <mcaloonj@bu.edu>
######################################


import flask
from flask import Flask, Response, request, render_template, redirect, url_for, flash, Markup
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from datetime import datetime
import ast

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!


#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'change_to_your_password'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM User") 
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM User") 
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM User WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0] )
    user.is_authenticated = request.form['password'] == pwd 
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET': #login template is rendered here
        return ''' 
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='password' id='password' placeholder='password'></input>
                <input type='submit' name='submit'></input>
               </form></br>
	       <a href='/'>Home</a>
               '''
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT password FROM User WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            #return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file
            first_name = getFirstNameFromEmail(flask_login.current_user.id)
            uid = getUserIdFromEmail(flask_login.current_user.id)
            contributors = getContributors()
            return render_template('hello.html', name = first_name, top_contributors_names = contributors, message = 'Welcome Back!')

    #information did not match
    return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    contributors = getContributors()
    return render_template('hello.html', message='Logged out', top_contributors_names = contributors) 

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html')  

@app.route("/register", methods=['POST'])
def register_user():
    email=request.form.get('email')
    password=request.form.get('password')
    first_name=request.form.get('first_name')
    last_name=request.form.get('last_name')
    dob=request.form.get('dob')

    fields = [email,password,first_name, last_name, dob]

    for field in fields:
        if field =='':
            message = Markup ('<font color = "red"> Please complete all required fields. </font>')
            flash(message) 
            return flask.redirect(flask.url_for('register'))

    hometown=request.form.get('hometown')
    gender=request.form.get('gender')

    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print cursor.execute("INSERT INTO User (email, password, first_name, last_name, dob, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}' )".format(email, password, first_name, last_name, dob, hometown, gender))
        conn.commit()
        #log user in
        user = User()
        user.id = email #for python, not sql
        flask_login.login_user(user)
        contributors = getContributors()
        return render_template('hello.html', name=first_name, message='Account Created!', top_contributors_names = contributors )
    else:

        message = Markup('<font color = "red"> Sorry! Email already in use. Use another one or <a href="/login">login</a> </font>')
        flash(message)
        return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, id, caption FROM Photo WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    row_count = cursor.execute("SELECT id  FROM User WHERE email = '{0}'".format(email))
    if row_count == 0:
        return ''
    return cursor.fetchone()[0]

def getFirstNameFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT first_name  FROM User WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def getUserAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT  *  FROM Album WHERE owner_id = '{0}'".format(uid))
    return cursor.fetchall()

def getAlbumId(album_name,uid):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id  FROM Album WHERE name = '{0}' AND owner_id = '{1}'".format(album_name,uid))
    return cursor.fetchone()[0]

def getPhotosFromAlbum(album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT  imgdata, id, caption FROM Photo P, Album A WHERE P.album_id = '{0}' AND P.album_id = A.album_id".format(album_id))
    return cursor.fetchall()


def getAlbumFromId(album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Album A WHERE A.album_id = '{0}'".format(album_id))
    return cursor.fetchone()


def getPhotoId(photo_data,album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Photo WHERE imgdata = '{0}' AND album_id = '{1}'".format(photo_data,album_id)) #might need to change to album
    return cursor.fetchone()[0]

def getPhotoTags(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM Tag WHERE photo_id = '{0}'".format(photo_id))
    return cursor.fetchall()

def getUserFriends(uid):
     cursor = conn.cursor()
     row_count = cursor.execute("SELECT id2 FROM Has_Friends WHERE id1 = '{0}'".format(uid))
     if row_count == 0:
        return ''
     return cursor.fetchall()

def getFirstNameLastNameFromId(uid):
    cursor = conn.cursor()
    row_count = cursor.execute("SELECT first_name, last_name FROM User WHERE id = '{0}'".format(uid))
    if row_count == 0:
        return ''
    results = cursor.fetchone()
    lst = [str(result) for result in results]
    lst[0] = lst[0] + ' '
    return ''.join(lst)

def getUserTags(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT T.text FROM Tag T, Photo P WHERE P.id = T.photo_id AND P.user_id = '{0}'".format(uid))
    tags = cursor.fetchall()
    tags = [tag[0] for tag in tags]
    return tags

def getPhotosFromTag(tag_text):
    cursor = conn.cursor()
    cursor.execute("SELECT  P.id, P.album_id, P.caption, P.imgdata FROM Tag T, Photo P WHERE T.text = '{0}' AND P.id = T.photo_id".format(tag_text))
    return cursor.fetchall()

def getContributors():
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM User ORDER BY contributions DESC LIMIT 10")
    top_contributors = cursor.fetchall()
    top_contributors_names = [getFirstNameLastNameFromId(user[0]) for user in top_contributors ]
    return top_contributors_names

def getMostPopularTags():
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM Tag GROUP BY text ORDER BY COUNT(text) DESC LIMIT 10")
    top_tags = cursor.fetchall()
    top_tags = [tag[0] for tag in top_tags]
    return top_tags

def getHometown(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT hometown FROM User WHERE id = '{0}'".format(uid))
    return cursor.fetchone()[0]

def getDOB(uid):
    conn.cursor()
    cursor.execute("SELECT dob FROM User WHERE id = '{0}'".format(uid))
    return cursor.fetchone()[0]




def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM User WHERE email = '{0}'".format(email)): 
        #this means there are greater than zero entries with that email
        return False
    else:
        return True
#end login code

@app.route('/you_may_also_like')
@flask_login.login_required
def you_may_also_like():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT T.text FROM Tag T, Photo P WHERE T.photo_id = P.id AND P.user_id = '{0}' GROUP BY text ORDER BY COUNT(text) DESC LIMIT 5".format(uid))  #top 5 tags used by this user
    user_top_tags = cursor.fetchall()
    user_top_tags = [str(tag[0]) for tag in user_top_tags]
    photos = [] #get recommended photos
    for tag in user_top_tags:
        cursor = conn.cursor()
        cursor.execute("SELECT  P.id, P.album_id, P.caption, P.imgdata FROM Tag T, Photo P WHERE T.text = '{0}' AND P.id = T.photo_id".format(tag))
        recs = cursor.fetchall()
        photos += recs
    return render_template('you_may_also_like.html', photos = photos)


@app.route('/profile')
@flask_login.login_required
def protected():
    first_name = getFirstNameFromEmail(flask_login.current_user.id)
    uid = getUserIdFromEmail(flask_login.current_user.id)
    friends = getUserFriends(uid)
    hometown = cursor.execute("SELECT hometown FROM User WHERE id = '{0}'".format(uid))
    tags = getUserTags(uid)
    tags = {tag for tag in tags}
    hometown = getHometown(uid)
    dob = getDOB(uid)
    if friends == '':
        return render_template('profile.html', name=first_name, hometown = hometown, dob = dob, photos=getUsersPhotos(uid), albums=getUserAlbums(uid), uid = uid, tags = tags)
    friends = [friend[0] for friend in friends]
    friend_names = [getFirstNameLastNameFromId(friend_id) for friend_id in friends]

    return render_template('profile.html', name=first_name, hometown = hometown, dob = dob, photos=getUsersPhotos(uid), albums=getUserAlbums(uid), uid = uid, tags = tags, friends = friend_names)

@app.route('/albumpage/<album_id>') #view all photos in an album
def albumpage(album_id):
    photos = getPhotosFromAlbum(album_id)
    cursor = conn.cursor()
    album_info = getAlbumFromId(album_id)
    album_name = album_info[2]
    return render_template('album.html', album_name = album_name, album_id = album_id, photos = photos)

@app.route('/tagpage/<uid>/<tag_text>') #view your photos that have a certain tag
@flask_login.login_required
def tagpage(uid, tag_text):

    cursor = conn.cursor()
    cursor.execute("SELECT  P.id, P.album_id, P.caption, P.imgdata FROM Tag T, Photo P WHERE T.text = '{0}' AND T.photo_id = P.id AND P.user_id = '{1}' ".format(tag_text,uid))
    photos = cursor.fetchall()
    return render_template('tag_page.html', uid = uid, tag_text = tag_text, photos = photos)

@app.route('/tagpage_public/<tag_text>') #view ALL photos that have a certain tag (for clickable top 10, searched tags handled elsewhere)
def tagpage_public(tag_text):
    cursor = conn.cursor()
    cursor.execute("SELECT T.text FROM Tag T WHERE T.text = '{0}'".format(tag_text))
    tag_text = cursor.fetchone()[0]
    photos = getPhotosFromTag(tag_text)
    return render_template('tagpage_public.html', tag_text = tag_text, photos = photos)

@app.route('/photo/<photo_id>')
def photo(photo_id):

    tags = getPhotoTags(photo_id)
    tags = [str(tag[0]) for tag in tags]

    cursor = conn.cursor()
    cursor.execute("SELECT imgdata FROM Photo WHERE id = '{0}'".format(photo_id))
    imgdata = cursor.fetchone()[0]

    cursor.execute ("SELECT caption FROM Photo WHERE id = '{0}'".format(photo_id))
    caption = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Likes WHERE photo_id = '{0}'".format(photo_id))
    num_likes = cursor.fetchone()[0]

    #order comments by most recent date
    cursor.execute("SELECT owner_id, text, date FROM Comment WHERE photo_id = '{0}' ORDER BY date DESC".format(photo_id)) 
    comments = cursor.fetchall()
    if comments == '':
        return render_template('photo.html', photo_id = photo_id, imgdata = imgdata, tags = tags, caption = caption, num_likes = num_likes)
    comments = [comment for comment in comments]
    comment_attributes = []
    for (uid,text,date) in comments:
        if uid is None:
            uid = 'Anonymous' #Replace empty names with anonymous
        else:
            uid = getFirstNameLastNameFromId(uid)
        text = str(text)
        date = get_date(str(date))
        comment_attributes += [[uid,text,date]]
    if flask_login.current_user.is_authenticated:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM Photo P WHERE id = '{0}'".format(photo_id))
        photo_owner = cursor.fetchone()[0]
        if photo_owner == uid:
            return render_template('photo.html', photo_id = photo_id, imgdata = imgdata, tags = tags, caption = caption, num_likes = num_likes, comment_attributes = comment_attributes, owner = 'true')

    return render_template('photo.html', photo_id = photo_id, imgdata = imgdata, tags = tags, caption = caption, num_likes = num_likes, comment_attributes = comment_attributes)


def get_date(date):
    month = date[5:7]
    day = date[8:10]
    year = date[:4]
    return month + '/' + day + '/' + year



def processTags(tags):
    tags = tags.replace(" ", "")
    tags = tags.split(",")
    tags = [str(tag) for tag in tags]
    return tags


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    albums = getUserAlbums(uid)
    albums = [str(album[2]) for album in albums]
    if request.method == 'POST':
        if 'possible_tags' in request.form: #if they hit tag reccomend button, return top 10 most used similar tags
            possible_tags = request.form.get('possible_tags')
            possible_tags = processTags(possible_tags)
            cursor = conn.cursor()
            photo_ids = []
            for tag in possible_tags:
                cursor.execute("SELECT photo_id FROM Tag WHERE text = '{0}'".format(tag))
                photo_ids += cursor.fetchall()
            photo_ids = [photo_id[0] for photo_id in photo_ids]
            found_tags = []
            for id in photo_ids:
                cursor.execute ("SELECT text FROM Tag WHERE photo_id = '{0}' GROUP BY text ORDER BY COUNT(text) DESC LIMIT 10".format(id)) 
                found_tags += cursor.fetchall()
            found_tags = [tag[0] for tag in found_tags]
            found_tags = {str(tag) for tag in found_tags if tag not in possible_tags}

            return render_template('upload.html', found_tags = found_tags, albums = albums)

        else:
            imgfile = request.files['file']
            caption = request.form.get('caption')
            album_name = request.form.get('album')
            tags = request.form.get('tag')
            tags = processTags(tags)


            if album_name != '':
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Album (name, owner_id) VALUES ('{0}', '{1}')".format(album_name,uid))
                cursor.execute("UPDATE User SET contributions = contributions + 1 WHERE id = '{0}'".format(uid))
                conn.commit()

            else:
                album_name = (request.form.get('myoptions'))
                if album_name == '':
                    return render_template('upload.html')
                if album_name[0] == ' ':
                    album_name = album_name[1:]

            photo_data = base64.standard_b64encode(imgfile.read())
            album_id = getAlbumId(album_name,uid)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Photo (imgdata,caption, album_id, user_id) VALUES ('{0}', '{1}','{2}','{3}' )".format(photo_data,caption,album_id,uid))
            conn.commit()

            photo_id = getPhotoId(photo_data,album_id)

            for tag in tags:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Tag (text, photo_id) VALUES ('{0}', '{1}')".format(tag,photo_id))
                conn.commit()


            return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!',top_contributors_names = getContributors())


    return render_template('upload.html', albums=albums)


#add tags after photo is uploaded, tags must be separated by commas and can't have spaces
@app.route('/add_tags/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def add_tags(photo_id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        tags = request.form.get('tag')
        tags = tags.replace(" ", "")
        tags = tags.split(",")
        tags = [str(tag) for tag in tags]

        for tag in tags:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Tag (text, photo_id) VALUES ('{0}', '{1}')".format(tag,photo_id))
            conn.commit()


        return render_template('add_tags.html', photo_id = photo_id, message = "Tag added!")
    return render_template('add_tags.html', photo_id = photo_id)

@app.route('/add_caption/<photo_id>', methods=['GET', 'POST'])
@flask_login.login_required
def add_caption(photo_id):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        caption = request.form.get('caption')
        cursor = conn.cursor()
        cursor.execute("UPDATE Photo SET caption = '{0}' WHERE id = '{1}'".format(caption,photo_id))
        conn.commit()

        return flask.redirect(flask.url_for('photo',  photo_id = photo_id, message = 'Caption added!'))
    return render_template('add_caption.html', photo_id = photo_id)


@app.route('/add_friends', methods = ['GET','POST'])
@flask_login.login_required
def add_friends():
    # message you are now friends with ___!
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        friend_email = request.form.get('friend')
        friend_id = getUserIdFromEmail(friend_email)
        if friend_id == '':
            return render_template('add_friends.html', message = 'Friend not found!')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Has_Friends (id1, id2) VALUES ('{0}', '{1}')".format(uid,friend_id))
        cursor.execute("INSERT INTO Has_Friends (id1, id2) VALUES ('{0}', '{1}')".format(friend_id,uid))
        conn.commit()
        return render_template('add_friends.html', message = 'You are now friends with ' + friend_email +'!')



    return render_template('add_friends.html')

@app.route('/delete_album/<uid>/<album_id>', methods = ['GET','POST'])
@flask_login.login_required
def delete_album(uid,album_id):
    if request.method == 'POST':
        if request.form.get('submit') == 'Yes':
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Album WHERE owner_id = '{0}' AND album_id = '{1}' ".format(uid,album_id))
            conn.commit()
            return flask.redirect(flask.url_for('protected'))
            
        else:
            return flask.redirect(flask.url_for('protected'))
    album = getAlbumFromId(album_id)
    return render_template('delete_album.html', uid = uid, album_id = album_id, album_name = album[2])


@app.route('/delete_photo/<photo_id>', methods = ['GET','POST'])
@flask_login.login_required
def delete_photo(photo_id):
    if request.method == 'POST':
        if request.form.get('submit') == 'Yes':
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Photo WHERE id = '{0}'".format(photo_id))
            conn.commit()
            return flask.redirect(flask.url_for('protected'))
            
        else:
            return flask.redirect(flask.url_for('protected'))
    return render_template('delete_photo.html', photo_id = photo_id)


@app.route('/like_or_comment/<photo_id>', methods = ['GET','POST']) 
def like_or_comment(photo_id):
    if request.method == 'POST':
        comment = request.form.get('comment')
        cursor = conn.cursor()
        if flask_login.current_user.is_authenticated: #if commenter is authenticated, insert their id into comment table
            uid = getUserIdFromEmail(flask_login.current_user.id)
            if comment != '':
                cursor.execute("INSERT INTO Comment (owner_id, photo_id, text) VALUES ('{0}', '{1}','{2}')".format(uid,photo_id,comment))
                conn.commit()
                cursor.execute("SELECT user_id FROM Photo WHERE id = '{0}'".format(photo_id))
                owner_id = cursor.fetchone()
                if uid != owner_id: #if commenter isn't owner, increase score
                    cursor.execute("UPDATE User SET contributions = contributions + 1 WHERE id = '{0}'".format(uid))
                    conn.commit()

        else: #commenter not authenticated, don't insert their id in comment table
            cursor.execute("INSERT INTO Comment (photo_id, text) VALUES ('{0}', '{1}')".format(photo_id,comment))
            conn.commit()
        if request.form.get('like'):
            if flask_login.current_user.is_authenticated:
                uid = getUserIdFromEmail(flask_login.current_user.id)
                cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(photo_id,uid))
                conn.commit()
            else: #don't insert id if user is not authenticated
                cursor.execute("INSERT INTO Likes (photo_id) VALUES ('{0}')".format(photo_id))
                conn.commit()
        return flask.redirect(flask.url_for('photo',  photo_id = photo_id))
        

    return render_template('like_or_comment.html', photo_id = photo_id)

#page for searching by tag
@app.route('/browse_tags', methods = ['GET','POST'])
def browse_tags():
    top_tags = getMostPopularTags()
    if request.method == 'POST':
        tags = request.form.get('tag')
        tags = tags.replace(" ", "")
        tags = tags.split(",")
        tags = [str(tag) for tag in tags]
        tags = '+'.join(tags)
        return flask.redirect(flask.url_for('search_results',  top_tags = top_tags, tags = tags))
    return render_template('browse_tags.html', top_tags = top_tags)


@app.route('/search_results/<tags>')
def search_results(tags):
    photos = []
    if '+' in tags:
        tags = tags.split("+")
    else:
        try:
            tags = ast.literal_eval(tags)
        except: tags = [tags]
    for tag in tags:
        cursor = conn.cursor()
        cursor.execute("SELECT P.id, P.caption, P.imgdata, P.user_id FROM Photo P, Tag T WHERE  T.text = '{0}' AND P.id = T.photo_id  ".format(tag))
        photos += cursor.fetchall()
    photos = {photo for photo in photos} #remove duplicates
    return render_template('search_results.html', photos = photos, tags = tags)

#browse all albums, not just your own
@app.route('/browse_albums')
def browse_albums():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ALbum")
    albums = cursor.fetchall()
    return render_template('browse_albums.html', albums = albums)







#default page  
@app.route("/", methods=['GET'])
def hello():
    top_contributors_names = getContributors()
    if flask_login.current_user.is_authenticated:
        first_name = getFirstNameFromEmail(flask_login.current_user.id)
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('hello.html', message='Welcome back!', name = first_name, top_contributors_names = top_contributors_names)
    else:

        return render_template('hello.html', top_contributors_names = top_contributors_names)


if __name__ == "__main__":
    #this is invoked when in the shell  you run 
    #$ python app.py 
    app.run(port=5000, debug=True)
