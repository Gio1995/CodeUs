from flask import Flask, session, render_template, request, redirect, url_for, flash, g
import os
import datetime
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
import hashlib
from flask_socketio import SocketIO, send, join_room, leave_room

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, async_mode='eventlet')

app.config['MONGO_URI'] = 'mongodb://localhost:27017/CodeUs'
mongo = PyMongo(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'gioiac1995@gmail.com'
app.config['MAIL_PASSWORD'] = 'natoanapoli'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        u = mongo.db.users.find_one({"user" : request.form['username'], "password" : hashlib.sha256((request.form['password']).encode('utf-8')).hexdigest()})
        if u:
            session['user'] = request.form['username']
            return redirect(url_for('protected'))

    return render_template("index.html")

@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        session.pop('user', None)
        u = mongo.db.users.find_one({"user" : request.form['username']}) or mongo.db.users.find_one({"email" : request.form['email']})
        if not u:
            if request.form['password1'] == request.form['password2']:
                mongo.db.users.insert({'user' : request.form['username'], 'email' : request.form['email'], 'password' : hashlib.sha256((request.form['password1']).encode('utf-8')).hexdigest()})
                session['user'] = request.form['username']
                msg = Message('Hello', sender = 'gioiac1995@gmail.com', recipients = [request.form['email']])
                msg.body = "Salve " + request.form['username'] + " grazie per esserti iscritto a CodeUs."
                mail.send(msg)

                return redirect(url_for("protected"))
    return render_template("register.html")
            

@app.route("/protected")
def protected():
    if g.user:
        documents = mongo.db.doc.find({"user" : g.user})
        return render_template('protected.html', user = g.user, documents = documents)
    
    return redirect(url_for('index'))

# Inizio modifica

# Redirect per la comparsa dell'editor di testo
@app.route("/protected/project=<name>")
def project(name):
    if g.user:
        u = mongo.db.doc.find_one({'user':g.user, 'document':name})
        if u:
            info = mongo.db.doc.find_one({'user':g.user, 'document':name})
            #print(info['content'])
            return render_template("project.html", user = g.user, document = info['document'])
        else:
            return redirect(url_for('protected'))
    return redirect(url_for('index'))

# Fine modifica

@app.route("/protected/modifica", methods = ['GET', 'POST'])
def modifica():
    if g.user:
        if request.method == 'POST':
            temp = mongo.db.users.find_one({"user" : session['user']})
            if request.form['password1'] == request.form['password2']:
                mongo.db.users.update({'user' : session['user']}, {'user' : session['user'], 'email' : temp['email'], 'password' : hashlib.sha256((request.form['password1']).encode('utf-8')).hexdigest()})
                return redirect(url_for('protected'))
            else:
                return render_template("modifica.html", user = g.user)
        return render_template("modifica.html", user = g.user)
    return redirect(url_for('index'))
    

@app.route("/protected/new_project", methods = ['GET', 'POST'])
def new_project():
    if g.user:
        if request.method == 'POST':
            u = mongo.db.doc.find_one({"user" : session['user'], 'document' : request.form['Nome']})
            if not u:
                mongo.db.doc.insert({"user" : session['user'], "document" : request.form['Nome'], "content":''})
                return redirect(url_for('protected'))
        return render_template('new_project.html', user = g.user)
    return redirect(url_for('index'))

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route("/getsession")
def getsession():
    if 'user' in session:
        return session['user']
    return 'Non sei loggato'

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@socketio.on("message")
def text(msg):
    send(msg, broadcast = True)

#*********************gestione delle rooms***********
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)

#*******************rooms link******************
@app.route('/room_link')
def Rooms():
    if g.user:
        u = mongo.db.doc.find()
        return render_template('rooms.html', dati=u)
    return redirect(url_for('index'))    


if __name__ == '__main__':
    #app.run(host = '0.0.0.0', port = 5000, debug = False)
    socketio.run(app, debug=True, host = '0.0.0.0')
