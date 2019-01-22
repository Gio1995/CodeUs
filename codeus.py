from flask import Flask, session, render_template, request, redirect, url_for, g
import os
from flask_pymongo import PyMongo #Modulo per usare il database MongoDB
from flask_mail import Mail, Message #Modulo per inviare e configurare il servizio mail
import hashlib #Modulo per criptare una stringa in sha256
from flask_socketio import SocketIO, send, join_room, leave_room, emit #Moduli della libreria flask_socketio

#Dichiarazione di un oggetto di tipo Flask
app = Flask(__name__)
#Assegnazione di un codice random
app.secret_key = os.urandom(24)
#Dichiarazione di un oggetto di tipo SocketIO
socketio = SocketIO(app, async_mode='eventlet')

#Assegnazione indirizzo database MongoDB e dichiarazione oggetto di tipo PyMongo
app.config['MONGO_URI'] = 'mongodb://localhost:27017/CodeUs'
mongo = PyMongo(app)

#Inserire qui la vostra email e password
email = 'mail'
password = 'password'

#Configurazione del servizio mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = email
app.config['MAIL_PASSWORD'] = password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#Dichiarazione di un oggetto di tipo Mail
mail = Mail(app)

#Con app.route("/", methods = ['GET', 'POST']) ritorno la pagine index.html
#Quando l'utente effettua una POST elimino l'utente dal dizionario delle sessioni, 
# verifico nel database se i dati sono presenti, in caso di valore True creo una 
# sessione per l'utente e lo reindirizzo all'area protected, altrimenti ritorno la pagina index.html
@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        u = mongo.db.users.find_one({"user" : request.form['username'], "password" : hashlib.sha256((request.form['password']).encode('utf-8')).hexdigest()})
        if u:
            session['user'] = request.form['username']
            return redirect(url_for('protected'))
    return render_template("index.html")

#Ritorno la pagina info.html
@app.route("/info")
def info():
    return render_template("info.html")

#Ritorno la pagina contact.html
@app.route("/contact")
def contact():
    return render_template("contact.html")

#Avviene la registrazione dell'utente
#Quando l'utente inserisce dei dati, quest'ultimo viene tolto dalla sessione, il server cerca nel database 
#user o l'email, se esistono già l'utente viene reindirizzato alla pagina register.html, altrimenti se la password1 e la password2 sono uguali
#i dati dell'utente verranno inseriti nel database, verrà creata una sessione per l'utente, verrà creato l'oggetto di tipo Message,
#il body, e verrà inviata l'email all'indirizzo dell'utente, e infine verrà reindirizzato all'area protected.
@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        session.pop('user', None)
        u = mongo.db.users.find_one({"user" : request.form['username']}) or mongo.db.users.find_one({"email" : request.form['email']})
        if not u:
            if request.form['password1'] == request.form['password2']:
                mongo.db.users.insert({'user' : request.form['username'], 'email' : request.form['email'], 'password' : hashlib.sha256((request.form['password1']).encode('utf-8')).hexdigest()})
                session['user'] = request.form['username']
                msg = Message('Hello', sender = email, recipients = [request.form['email']])
                msg.body = "Salve " + request.form['username'] + " grazie per esserti iscritto a CodeUs."
                mail.send(msg)

                return redirect(url_for("protected"))
    return render_template("register.html")
            
#Creazione della pagina protected.html:
#Viene verificato se l'utente è loggato con g.user
#in caso affermativo si effettua una ricerca dei progetti creati 
# dall'utente e lo si reindirizza alla pagina protected.html passando user e documents
#altrimenti l'utente viene reindirizzato alla pagina index
@app.route("/protected")
def protected():
    if g.user:
        documents = mongo.db.doc.find({"user" : g.user})
        return render_template('protected.html', user = g.user, documents = documents)
    
    return redirect(url_for('index'))

# Redirect per la comparsa dell'editor di testo:
#Se l'utente è loggato verifico la corrispondenza tra progetto e proprietario.
#Se la verifica è andata a buon fine, prendo le informazioni dal database e lo reindirizza alla pagina
#project.html contenente il nome utente e il nome del progetto.
#Se la verifica non è andata a buon fine lo reindirizza alla pagina protected.
#Se l'utente non è loggato, viene reindirizzato alla pagina index
@app.route("/protected/project=<name>")
def project(name):
    if g.user:
        u = mongo.db.doc.find_one({'user':g.user, 'document':name})
        if u:
            info = mongo.db.doc.find_one({'user':g.user, 'document':name})
            return render_template("project.html", user = g.user, document = info['document'])
        else:
            return redirect(url_for('protected'))
    return redirect(url_for('index'))


#Se l'utente è loggato tramite una ricerca vengono ricavate le informazioni relative all'utente.
#Se la password1 è uguale alla password2 vengono aggiornate tutte le informazioni relative all'utente nel database
#e viene reindirizzato alla pagina protected.html. Se la password1 e la password2 non corrispondono, e se l'utente non ha
#effettuato una POST viene reindirizzato alla pagina modifica.html.
#Se l'utente non è loggato viene reindirizzato alla pagina index.
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
    
#Se l'utente è loggato ed ha effettuato la POST, il server verifica che non ci siano casi di omonimia relativi ai nomi dei progetti
#in tal caso verrà inserito il nome del nuovo progetto associato all'utente e successivamente verrà reindirizzato
#alla pagina protected.
#Se non ha effetuato la POST, l'utente verrà reindirizzato alla pagina new_project.html.
#Se non è loggato verrà reindirizzato alla pagina index.
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


#Assegnazione della sessione all'utente
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

#Rimozione del nome utente dalla sessione
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

#Alla chiamata di 'message' viene inviato il messaggio in msg alla stanza msg['room']
@socketio.on("message")
def text(msg):
    room = msg['room']
    send(msg['data'], room=room)

#*********************gestione delle rooms***********

#Alla chiamata 'join' vengono memorizzati i valori data['username'] nella variabile username e data['project'] nella variabile room.
#Con join_room() l'utente partecipa alla stanza che ha per nome il nome del progetto, ed infine con send()
#viene inviato il messaggio di accesso a tutti gli utenti che partecipano alla stanza.
@socketio.on('join')
def join(data):
    username = data['username']
    room = data['project']
    join_room(room)
    send(username + ' has entered the room.', room=room)

#*******************rooms link******************

#Alla richiesta dell'URL /room_link verifico che l'utente sia loggato e memorizzo tutti i dati relativi
#alla tabella doc nella variabile u, successivamente l'utente verrà reindirizzato alla pagina rooms.html
#mostrandogli i dati
@app.route('/room_link')
def Rooms():
    if g.user:
        u = mongo.db.doc.find()
        return render_template('rooms.html', dati=u)
    return redirect(url_for('index'))

#Se l'utente è loggato verrà reindirizzato alla pagina join_project.html mostrandogli il nome utente ed
#il nome del progetto
@app.route("/room_link/proj=<name>")
def link_proj(name):
    if g.user:
        return render_template('join_project.html', user = g.user, document = name)
    return redirect(url_for('index'))

#Avvio del server 
#Se il file codeus.py è il main del progetto verrà eseguito il server con parametri app per la configurazione,
#debug=True per l'attivazione del debug e host='0.0.0.0' per ricevere le richieste da tutti gli indirizzi IP
if __name__ == '__main__':
    socketio.run(app, debug=True, host = '0.0.0.0')
