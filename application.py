import os
import time
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_session import Session
from wtform_fields import *
from models import *

# set up Flask and SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "b'U\x8fw^{\xca\x92E\x12w`\xce\xf9_S\xb2'"
app.config['WTF_CSRF_SECRET_KEY'] = "b'f\xfa\x8b{X\x8b\x9eM\x83l\x19\xad\x84\x08\xaa"

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://calqfxvqbxtbbn:6fe9fc7be82a96c7b3509f396af0c71b4a63e0185ec67b369b6c89dabd656a38@ec2-107-20-198-176.compute-1.amazonaws.com:5432/dbin3qup59b8ra"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize login manager
login = LoginManager(app)
login.init_app(app)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


socketio = SocketIO(app, async_mode = None, manage_session=False)

# keep track of the users, channels and the messages in each channel
channels = []
my_messages = {}
users = {}



@socketio.on("username")
def receive_username(username):
	# pair usernames with session IDs
	users[username] = request.sid

# execute when a message is sent
@socketio.on("room_message")
def messageHandler(json):
	# grab the timestamp for when the message was sent
	my_time = time.ctime(time.time())
	# organize the data into a dict
	my_data ={"user": json["user"], "msg" : json["msg"], "my_time": my_time}
	# add data to the messages of the channel in question
	my_messages[json["channel"]].append(my_data)
	# store only the 100 most recent messages per channel
	if len(my_messages[json["channel"]]) > 100:
		my_messages[json["channel"]].pop(0)
	# send back the time, the message and the username to the client side
	print("Message passed on!")
	emit("room_message", my_data, room = json["channel"])

# execute when the user tries to create a channel
@socketio.on("channel_creation")
def channel_creation(channel):
	# channel name is taken
	if channel in channels:
		emit("channel_error", "This name is already taken!")
	# success
	else:
		# add channel to the list of channels
		channels.append(channel)
		my_messages[channel] = []
		# add user to the channel
		join_room(channel)
		current_channel = channel
		data = {"channel": channel, "messages": my_messages[channel]}
		emit("join_channel", data)

# execute when the user joins a channel
@socketio.on("join_channel")
def join_channel(channel):
	# add user to the channel
	join_room(channel)
	data = {"channel": channel, "messages": my_messages[channel]}
	print(data)
	emit("join_channel", data)

# execute when the user leaves the channel they are on
@socketio.on("leave_channel")
def leave_channel(channel):
	# remove user from the channel
	leave_room(channel)
	emit("leave_channel", channel)

# execute when the user changes channels
@socketio.on("change_channel")
def change_channel(old_channel, new_channel):
	# remove user from the old channel
	leave_room(old_channel)
	# add user to the new channel
	join_room(new_channel)
	data = {"channel": new_channel, "messages": my_messages[new_channel]}
	emit("join_channel", data)


@app.route("/", methods=['GET', 'POST'])
def index():
	# return the main page
	return render_template("index.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    reg_form = RegistrationForm()

    #Update database if validation success
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data

        # Hash password
        hashed_pswd = pbkdf2_sha256.hash(password)

        # Add username & hashed password to DB
        user = User(username=username, hashed_pswd=hashed_pswd)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template("register.html", form=reg_form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    #Allow login if validation success
    if login_form.validate_on_submit():
        user_object = User.query.filter_by(username=login_form.username.data).first()
        login_user(user_object)
        return render_template("chat.html", username=user_object.username, async_mode = socketio.async_mode)
    
    return render_template("login.html", form=login_form)


@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    flash("You have logged out successfully.", "primary")
    return render_template("login.html")


@app.route("/chat", methods=['GET', 'POST'])
def chat():

    if not current_user.is_authenticated:
        flash('Please login', 'danger')
        return redirect(url_for('login'))

    return render_template("chat.html", username=current_user.username, async_mode = socketio.async_mode)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404



if __name__ == "__main__":
	socketio.run(app, debug = True)
