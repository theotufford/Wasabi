from flaskApi import create_app
from flaskApi.socketInstance import socketInstance

#TODO 
# crypt random key on first init that will set the 'SECRET_KEY' in create_app
app = create_app()
if __name__ == '__main__':
    socketInstance.run(app, host = "0.0.0.0", port = 5000)
