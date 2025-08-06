from .socketInstance import socketInstance 

def register(socketio):
    @socketio.on('test')
    def handle_client_message(data):
        print("Received:", data["data"])
        # Echo back to the same client
def emitter(arg):
    socketInstance.emit('timer', arg)
