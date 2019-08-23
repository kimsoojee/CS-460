######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
#for image uploading
from werkzeug import secure_filename
import os, base64
from datetime import datetime
import requests
from urllib2 import urlopen

#today date
now=datetime.now()

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email, first_name from Users")
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
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
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
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register/", methods=['POST'])
def register_user():
	try:
		first_name=str(request.form.get('firstname')).upper()
		last_name=str(request.form.get('lastname')).upper()
		email=request.form.get('email')
		date_birth=request.form.get('date_birth')
		hometown=str(request.form.get('bio')).upper()
		upload=request.form.get('upload')
		if upload == "default":
			url='http://deafhhcenter.org/wp-content/uploads/2017/12/profile-default.jpg'
			profile_pic = base64.standard_b64encode(urlopen(url).read())
		if upload == "upload":
			file=request.files['profile_pic']
			profile_pic=base64.standard_b64encode(file.read())
		gender="Secret"
		if request.form.get('gender'):
			gender=request.form.get('gender')
		password=request.form.get('password')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, first_name, last_name, date_birth, bio, gender, profile_pic, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, first_name, last_name, date_birth, hometown, gender, profile_pic, password))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=first_name, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
	email=flask_login.current_user.id
	if request.method == 'POST':
		file=request.files['profile_pic']
		print file
		profile_pic=base64.standard_b64encode(file.read())
		UpdateProfilePicture(profile_pic, email)
	return render_template('profile.html', userInfo=getUserInfo(email), message="Here's your profile")

def UpdateProfilePicture(profile_pic, email):
	cursor = conn.cursor()
	cursor.execute("UPDATE Users SET profile_pic = '{0}' WHERE email = '{1}'".format(profile_pic, str(email)))
	conn.commit()

def getUserInfo(email):
	cursor = conn.cursor()
	cursor.execute("SELECT email, first_name, last_name, profile_pic, date_birth, bio, gender FROM Users WHERE email = '{0}'".format(email))
	#(email, first_name, last_name, date_birth, bio, gender, password, profile_pic)
	return cursor.fetchall()

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def GetAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT P.caption, P.data, U.first_name, U.last_name, P.photo_id FROM Photos P, Users U WHERE U.user_id = P.user_id")
	photos = [[p[0],p[1],p[2],p[3],p[4]] for p in cursor.fetchall()]
	cursor.execute("SELECT * FROM Tagged_Photos")
	tags = [[str(t[0]), t[1]] for t in cursor.fetchall()]
	for p in photos:
		taglist=[t for t in tags if t[1]==p[4]]
		p.append(taglist)
		comments=GetComments(p[4])
		likes=GetLikes(p[4])
		p.append(comments)
		p.append(likes)
	return photos

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.data, P.photo_id, P.caption, A.title FROM Photos P, Albums A WHERE P.user_id = '{0}' AND P.album_id = A.album_id".format(uid))
	photos = [[p[0],p[1],p[2],p[3]] for p in cursor.fetchall()]
	cursor.execute("SELECT T.* FROM Tagged_Photos T, Photos P, Users U WHERE U.user_id='{0}' and T.photo_id = P.photo_id and P.user_id =U.user_id".format(uid))
	tags = [[str(t[0]), t[1]] for t in cursor.fetchall()]
	for p in photos:
		taglist=[t for t in tags if t[1]==p[1]]
		p.append(taglist)
		comments=GetComments(p[1])
		likes=GetLikes(p[1])
		p.append(comments)
		p.append(likes)
	return photos #NOTE list of tuples, [(imgdata, pid), ...]

def uploadPhotos(caption, photo_data, uid, album_id):
 	cursor = conn.cursor()
	cursor.execute("INSERT INTO Photos (caption, data, user_id, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(caption, photo_data, uid, album_id))
 	conn.commit()
	photo_id=cursor.lastrowid
	return photo_id

def DeletePhotos(uid, photo_id):
	#delete tags
	tags = GetUsersTag(uid)
	for t in tags:
		DeleteTags(str(t[0]),photo_id)
	#delete likes
	DeleteLikes(photo_id)
	#delete comments
	DeleteComments(photo_id)
	#delete photos
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Photos WHERE user_id = '{0}' AND photo_id='{1}'".format(uid, photo_id))
	conn.commit()

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	allalbumtitles=ListAlbums(uid)
	# check if there is any album exists
	if allalbumtitles:
		if request.method == 'POST':
			imgfile = request.files['photo']
			caption = request.form.get('caption')
			photo_data = base64.standard_b64encode(imgfile.read())
			tags=str(request.form.get('tags')).lower().split(" ")
			albumtitle=request.form.get('albumtitle')
			album_id=request.form.get('album_id')

			if CheckAlbumExist(uid):
				#upload photo
				photo_id=uploadPhotos(caption, photo_data, uid, album_id)
				#add tags
				AddTagtoPhotos(tags, photo_id)
				return render_template('albums.html', message='Photo uploaded!', albums=ListAlbums(uid))
			else:
				return render_template('upload.html', message='Pick an valid album', albums=allalbumtitles)
		else:
			return render_template('upload.html', albums=allalbumtitles)
	else:
		return render_template('albums.html', message="Create an album first")

@app.route('/allphotos', methods=['GET', 'POST'])
def viewallPhotos():
	if flask_login.current_user.is_authenticated():
		uid = getUserIdFromEmail(flask_login.current_user.id)
	else:
		uid = -1
	if GetAllPhotos():
		if request.method == 'POST':
			tags=request.form.get('tags')
			splitedTags=str(request.form.get('tags')).split(" ")
			splitedTags=list(set(splitedTags))
			comment=request.form.get('comment')
			photo_id=request.form.get('photo_id')
			like_photo_id=request.form.get('like_photo_id')
			popularTag=[str(request.form.get('popularTag'))]
			#serach by tag
			if tags and CheckExistTag(splitedTags):
				return render_template('photos_all.html', searchedPhotos=SearchAllPhotosbyTag(splitedTags))
			#add comment
			if comment:
				if CheckValidComments(uid, photo_id):
					LeaveComments(comment, photo_id)
					return render_template('photos_all.html', message="Comment posted", popularTags=PopularTag(), allphotos=GetAllPhotos())
				else:
					return render_template('photos_all.html', message="Failed", popularTags=PopularTag(), allphotos=GetAllPhotos())
			#add likes
			if like_photo_id and flask_login.current_user.is_authenticated():
				if CheckValidLike(uid, like_photo_id):
					AddLikes(uid, like_photo_id)
					return render_template('photos_all.html', message="Like added", popularTags=PopularTag(), allphotos=GetAllPhotos())
				else:
					return render_template('photos_all.html', popularTags=PopularTag(), allphotos=GetAllPhotos())
			if popularTag:
				return render_template('photos_all.html', popularTags=PopularTag(), PopularTagPhotos=SearchAllPhotosbyTag(popularTag))
			else:
				return render_template('photos_all.html', message="Failed", popularTags=PopularTag(), allphotos=GetAllPhotos())
		return render_template('photos_all.html', popularTags=PopularTag(), allphotos=GetAllPhotos())
	return render_template('hello.html', message="No photos uploaded yet")

@app.route('/myphotos', methods=['GET', 'POST'])
@flask_login.login_required
def viewmyPhotos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if CheckAlbumExist(uid):
		if getUsersPhotos(uid):
			if request.method == 'POST':
				#view photos by tag
				tag=request.form.get('tag')
				if tag:
					return render_template('photos_my.html', myTags=GetUsersTag(uid), myPhotosbyTag=ViewUserPhotosbyTag(tag, uid))
				#add more tags
				addtags=str(request.form.get('addtags')).split(" ")
				photo_id=request.form.get('photo_id')
				if photo_id:
					AddTagtoPhotos(addtags, photo_id)
				#delete the tag
				tag_delete=request.form.get('tag_delete')
				delete_tag_pid=request.form.get('delete_tag_pid')
				if tag_delete:
					DeleteTags(tag_delete, delete_tag_pid)
					#if the tag is not exist, then show all photos
					if ViewUserPhotosbyTag(tag_delete, uid):
						return render_template('photos_my.html', myTags=GetUsersTag(uid), myPhotosbyTag=ViewUserPhotosbyTag(tag_delete, uid))
				#delete photos
				delete_photo_id=request.form.get('delete_photo_id')
				if delete_photo_id:
					DeletePhotos(uid, delete_photo_id)
				#photos in the album
				photos_title=request.form.get('photos_title')
				if photos_title:
					if ListPhotosbyAlbum(photos_title, uid):
						return render_template('photos_my.html', myTags=GetUsersTag(uid), AlbumPhotos=ListPhotosbyAlbum(photos_title, uid))
					else:
						return render_template('albums.html', message="There is no picture", albums=ListAlbums(uid))
				searchtags=str(request.form.get('searchtags')).split(" ")
				if searchtags:
					return render_template('photos_my.html', myTags=GetUsersTag(uid), myPhotos=getUsersPhotos(uid), recommendation=recommendTags(searchtags, uid))
			return render_template('photos_my.html', myTags=GetUsersTag(uid), myPhotos=getUsersPhotos(uid))
		else:
			return render_template('upload.html', message="Upload a photo first", albums=ListAlbums(uid))
	else:
		return render_template('albums.html', message="Create an album first")

#end photo uploading code

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare', TopUsers=GetContributions())

	#count user contribution
def GetContributions():
	cursor = conn.cursor()
	contribution = "SELECT U.email, U.first_name, U.last_name, SUM(X.count) FROM Users U, "
	contribution += " (SELECT COUNT(user_id) as count, user_id FROM Photos GROUP BY user_id UNION SELECT COUNT(writer_id), writer_id FROM Comments GROUP BY writer_id) X "
	contribution += " WHERE X.user_id = U.user_id AND U.user_id != -1 GROUP BY X.user_id ORDER BY SUM(X.count) DESC LIMIT 10 "
	cursor.execute( contribution )
	return cursor.fetchall()

#begin friends code
def SearchUser(email):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, email FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchall()

def ListFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.first_name, U.last_name, U.email, U.profile_pic FROM Friends F, Users U WHERE F.user_id = '{0}' AND F.friend_id = U.user_id".format(uid))
	return cursor.fetchall()

def CheckExistFriend(uid, friend_id):
	#if user is already friend with this person, return true
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(uid, friend_id)):
		return True
	else:
		return False

def AddFriend(uid, friend_id):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friends (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, friend_id))
	conn.commit()

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		#search user
		email=request.form.get('email')
		if email:
			if SearchUser(email):
				return render_template('friends.html', friends=ListFriends(uid), userInfo=SearchUser(email))
			else:
				return render_template('friends.html', friends=ListFriends(uid), message='Search Failed')
		#add friend
		friend_email=request.form.get('friendemail')
		friend_id=getUserIdFromEmail(friend_email)
		if friend_email:
			if uid == friend_id:
				return render_template('friends.html', friends=ListFriends(uid), message='It Is You')
			if CheckExistFriend(uid, friend_id):
				return render_template('friends.html', friends=ListFriends(uid), message='Already Friend With This Person')
			AddFriend(uid, friend_id)
			return render_template('friends.html', friends=ListFriends(uid), message='Friend Added')
	return render_template('friends.html', friends=ListFriends(uid))

#end friends code


#begin albums code
def isAlbumUnique(title, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Albums WHERE title = '{0}' And user_id = '{1}'".format(title, uid)):
		return False
	else:
		return True

def CheckAlbumExist(uid):
	#if the user has an album, then true
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Albums WHERE user_id = '{0}'".format(uid)):
		return True
	else:
		return False

def ListAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT title, date_creation, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def ListPhotosbyAlbum(title, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.caption, P.data , P.photo_id, A.title FROM Photos P, Albums A WHERE A.title = '{0}' AND A.user_id = '{1}' AND A.album_id = P.album_id".format(title,uid))
	photos = [[p[0],p[1],p[2],p[3]] for p in cursor.fetchall()]
	cursor.execute("SELECT T.* FROM Tagged_Photos T, Photos P, Users U WHERE U.user_id='{0}' and T.photo_id = P.photo_id and P.user_id =U.user_id".format(uid))
	tags = [[str(t[0]), t[1]] for t in cursor.fetchall()]
	for p in photos:
		taglist=[t for t in tags if t[1]==p[2]]
		p.append(taglist)
		comments=GetComments(p[2])
		likes=GetLikes(p[2])
		p.append(comments)
		p.append(likes)
	return photos

def CreateAlbum(title, date_creation, uid):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Albums (title, date_creation, user_id) VALUES ('{0}', '{1}', '{2}')".format(title, date_creation, uid))
	conn.commit()

def DeleteAlbums(uid, title):
	#delete photos
	photos = getUsersPhotos(uid) #(P.data, P.photo_id, P.caption, A.title)
	for p in photos:
		if p[3] == title:
			DeletePhotos(uid, p[1])
	#delete albums
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE user_id = '{0}' AND title='{1}'".format(uid, title))
	conn.commit()

@app.route('/albums', methods=['GET', 'POST'])
@flask_login.login_required
def Albums():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		#create album
		createtitle=request.form.get('createtitle')
		date_creation=now.strftime('%y-%m-%d')
		if createtitle and isAlbumUnique(createtitle,uid):
			CreateAlbum(createtitle, date_creation, uid)
			return render_template('upload.html', message='Album Created', albums=ListAlbums(uid))
		#delete album
		deletetitle=request.form.get('deletetitle')
		if deletetitle:
			DeleteAlbums(uid, deletetitle)
			return render_template('albums.html', message='Album Deleted', albums=ListAlbums(uid))
		else:
			return render_template('albums.html', message="The album already exist", albums=ListAlbums(uid))
	if CheckAlbumExist(uid) == False:
		return render_template('albums.html', message="Create an album first")
	return render_template('albums.html', albums=ListAlbums(uid))

#end albums code

#begein tags code
def ValidTag(tag, photo_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Tagged_Photos WHERE word = '{0}' AND photo_id='{1}'".format(tag, photo_id)):
		return False
	return True

def AddTagtoPhotos(tags, photo_id):
	for t in list(set(tags)):
		if t != "" and ValidTag(t, photo_id):
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Tagged_Photos (word, photo_id) VALUES ('{0}', '{1}')".format(t, photo_id))
			conn.commit()

def GetUsersTag(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT T.word FROM Tagged_Photos T, Photos P WHERE P.user_id='{0}' AND T.photo_id = P.photo_id".format(uid))
	tags=cursor.fetchall()
	return list(set(tags))

def ViewUserPhotosbyTag(tag, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT P.caption, P.data , T.word, T.photo_id FROM Photos P, Tagged_Photos T WHERE T.word = '{0}' AND P.user_id = '{1}' AND P.photo_id = T.photo_id".format(tag,uid))
	photos = [[p[0],p[1],p[2],p[3]] for p in cursor.fetchall()]
	for p in photos:
		comments=GetComments(p[3])
		likes=GetLikes(p[3])
		p.append(comments)
		p.append(likes)
	return photos

def SearchAllPhotosbyTag(tags):
	photos=[]
	cursor = conn.cursor()
	for t in tags:
		cursor.execute("SELECT P.caption, P.data, U.first_name, U.last_name, P.photo_id FROM Photos P, Tagged_Photos T, Users U WHERE T.word = '{0}' AND P.photo_id = T.photo_id AND P.user_id = U.user_id".format(t))
		photos += [[p[0],p[1],p[2],p[3],p[4]] for p in cursor.fetchall()]
	cursor.execute("SELECT * FROM Tagged_Photos")
	tags = [[str(t[0]), t[1]] for t in cursor.fetchall()]
	for p in photos:
		taglist=[t for t in tags if t[1]==p[4]]
		p.append(taglist)
		comments=GetComments(p[4])
		likes=GetLikes(p[4])
		p.append(comments)
		p.append(likes)
	return photos

def PopularTag():
	cursor = conn.cursor()
	cursor.execute("SELECT word, count(word) FROM Tagged_Photos GROUP BY word ORDER BY count(word) DESC LIMIT 10")
	return cursor.fetchall()

def CheckExistTag(tags):
	#check if the tag exists, then true
	cursor = conn.cursor()
	for t in tags:
		if cursor.execute("SELECT * FROM Tagged_Photos WHERE word = '{0}'".format(t)):
			continue
		else:
			return False
	return True

def DeleteTags(tag, photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Tagged_Photos WHERE word = '{0}' AND photo_id='{1}'".format(tag, photo_id))
	conn.commit()
#end tags code

#begin comment code

def CheckValidComments(uid, photo_id):
	#if the user can leave comment on this photo, then True
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Photos WHERE user_id = '{0}' AND photo_id='{1}'".format(uid, photo_id)):
		return False
	else:
		return True

def LeaveComments(comment, photo_id):
	if flask_login.current_user.is_authenticated():
		writer_id = getUserIdFromEmail(flask_login.current_user.id)
	else:
		writer_id = -1
	date_left=now.strftime('%y-%m-%d')
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments(text, writer_id, date_left, photo_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment, writer_id, date_left, photo_id))
	conn.commit()

def GetComments(photo_id):
	if flask_login.current_user.is_authenticated():
		uid = getUserIdFromEmail(flask_login.current_user.id)
	else:
		uid = -1
	cursor = conn.cursor()
	cursor.execute("SELECT C.text, C.photo_id, U.first_name, U.last_name FROM Comments C, Users U, Photos P WHERE C.photo_id = '{0}' AND C.photo_id = P.photo_id AND C.writer_id = U.user_id".format(photo_id))
	commentlist = [[c[0], c[1], c[2], c[3]] for c in cursor.fetchall()]
	return commentlist

def DeleteComments(photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Comments WHERE photo_id='{0}'".format(photo_id))
	conn.commit()

# #end comment code

#begin Likes code

def CheckValidLike(uid, photo_id):
	#if the user can leave comment on this photo, then True
	cursor = conn.cursor()
	if cursor.execute("SELECT * FROM Likes WHERE user_id = '{0}' AND photo_id='{1}'".format(uid, photo_id)):
		return False
	else:
		return True

def AddLikes(uid, photo_id):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Likes(user_id, photo_id) VALUES ('{0}', '{1}')".format(uid, photo_id))
	conn.commit()

def GetLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT U.email, C.count FROM Users U, Likes L, (SELECT COUNT(user_id) as count FROM Likes WHERE photo_id = '{0}') C WHERE L.photo_id = '{0}' AND L.user_id = U.user_id".format(photo_id))
	likelist = [[l[0], l[1]] for l in cursor.fetchall()]
	return likelist

def DeleteLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Likes WHERE photo_id='{0}'".format(photo_id))
	conn.commit()

# begin recommendation code

def YouMayAlsoLike(uid):
	cursor = conn.cursor()
	commontags = " (SELECT T.word AS word FROM Tagged_photos T, Photos P WHERE T.photo_id = P.photo_id AND P.user_id = '{0}' GROUP BY T.word ORDER BY COUNT(T.word) DESC LIMIT 5) F ".format(uid)
	selectfrom = " SELECT P.photo_id, COUNT(P.photo_id) FROM Photos P, Tagged_photos T, (SELECT COUNT(word) AS count, photo_id FROM Tagged_photos GROUP BY photo_id) TP, "
	where = " WHERE P.photo_id=T.photo_id AND T.word=F.word AND P.photo_id=TP.photo_id AND P.user_id != '{0}'".format(uid)
	cursor.execute(selectfrom + commontags + where + " GROUP BY TP.photo_id ORDER BY COUNT(P.photo_id) DESC, TP.count")
	photos = [[p[0]] for p in cursor.fetchall()]
	cursor.execute("SELECT * FROM Tagged_Photos")
	tags = [[str(t[0]), t[1]] for t in cursor.fetchall()]
	for p in photos:
		#add photo data
		cursor.execute("SELECT P.caption, P.data, U.first_name, U.last_name FROM Photos P, Users U WHERE photo_id='{0}' and P.user_id = U.user_id".format(p[0]))
		photoInfo=[[i[0], i[1], i[2], i[3]] for i in cursor.fetchall()][0]
		taglist=[t for t in tags if t[1] == p[0]]
		photoInfo.insert(4,taglist)
		p.extend(photoInfo)
		comments=GetComments(p[0])
		likes=GetLikes(p[0])
		p.append(comments)
		p.append(likes)
	return photos


@app.route('/recommendphotos', methods=['GET', 'POST'])
@flask_login.login_required
def recommendPhotos():
	uid=getUserIdFromEmail(flask_login.current_user.id)
	# YouMayAlsoLike(uid)
	return render_template('recommendPhotos.html', youmaylike=YouMayAlsoLike(uid))


def recommendTags(tags, uid):
	cursor = conn.cursor()
	search = "SELECT T.word, COUNT(T.word) FROM Tagged_Photos T, ("
	for t in tags:
		search += " SELECT photo_id from Tagged_Photos WHERE word='{0}' UNION ".format(t)
	search = search[ :-6] + " ) P WHERE T.photo_id = P.photo_id "
	for t in tags:
		search += " AND T.word != '{0}' ".format(t)
	search += " GROUP BY T.word ORDER BY COUNT(T.word) DESC"
	cursor.execute(search)
	return cursor.fetchall()


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
