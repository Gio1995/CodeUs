# </> CodeUs
CodeUs is a project created to write code together with friends and colleagues, or for educational purposes.
The idea was born from the need to write code with my friend Amy in real time without the use of usbdrive, the cloud, or any other support to share files.
And so with this site we can have a personal page to create projects, share and write and accessible in any part of the world.

**Informations**

To develop CodeUs we used Flask python framework server-side and Javascript client-side. In the subdirectory "websocket" there is the core of the project that include the part of CodeUs to write in real time character after character the text. To create this we used the Socket.IO.

**Development**

The project was developed on Linux 64bit 

**How Execute**

After cloned the repository, to exec the project you must install MongoDB database from https://www.mongodb.com then the dependency with the command "sudo pip install -r requirements.txt" and in finally "python codeus.py" or "python3 codeus.py" to exec.
