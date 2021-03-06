import eventlet
import eventlet.wsgi
eventlet.monkey_patch()
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import serial
from analyser import Analyser
from analyser import Reader
import copy

test_array = [1, 2, 3, 4, 5, -1, 1, 2, 3, 4, 5, 4, 3, 2, 1, -1, 1, 2, 3, -1, 1, 2, 3, 4, 5, 4, 3, 2, 1, 1, 2, 3, 4, 5, 4, 3]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
print("Socket started.")
rdr = Reader('COM9')
print("Serial opened.")
connected = False
exercise_in_progress = False
analyser = None

@socketio.on('connect')
def connect():
    print('connected')
    emit('log', 'connected')
    global connected
    connected = True

@socketio.on('log')
def log_event(data):
    print('log: ', str(data))

@socketio.on('disconnect')
def disconnect():
    print('disconnect')
    emit('log', 'connected')
    global connected
    # connected = False

@socketio.on('start_exercise')
def exercise(data):
    print(data)
    print("Started " + data["name"])
    global exercise_data
    exercise_data = data
    global exercise_in_progress
    exercise_in_progress = True # Start exercise processing
    global analyser
    analyser = Analyser('references_' + data["name"] + '.json', data, rdr) # Create analyser for data["name"] exercise
    # analyser = Analyser('references.json', data, rdr)
    # res = { "stateRes": -1, "error": False }
    # test_index = 0

@socketio.on('finish_exercise')
def finishEx():
    # start analyzer
    print("Finished.")
    exercise_in_progress = False

class Server(threading.Thread):
    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadID = thread_id

    def run(self):
        print("Start server")
        prevRes = { "progress": -4500}
        global exercise_in_progress 
        while True:
            if exercise_in_progress:
                # print("While inner")
                res = analyser.process_data()
                # print(res)
                if res["error"]: # Check error
                    message = { "name": "error"}
                else:
                    message = { "name": exercise_data["name"], "progress": res["progress"] , "finalState": res['is_finished']}

                # print(res)  
                # print(prevRes)
                if(res["progress"] != prevRes["progress"]): 
                    prevRes = copy.deepcopy(res)
                    # print(message)
                    socketio.emit('exercise', message)
                    # test_index = (test_index + 1) % len(test_array)
                    # res = { "stateRes": test_array[test_index], "error": test_array[test_index] == -1 }
                    # print(res)
                    # print(prevRes)
            time.sleep()
                # print(res)


# class Emitter(threading.Thread):
#     def __init__(self, thread_id):
#         threading.Thread.__init__(self)
#         self.threadID = thread_id

#     def run(self):
#         print("Starting " + self.name)
#         start_emit()

#     def start_emit():
#         i = 0
#         print('Connecting...')
#         states = [1, 2, 3, 4, 5, 4, 3, 2, 1]
#         while True:
#             if connected:
#                 to_send = {
#                     'name': 'biceps', 
#                     'progress': states[i % len(states)]
#                     }
#                 if i % len(states) == 0:
#                     to_send['initialState'] = True
#                 elif i % len(states) == 8:
#                     to_send['finalState'] = True
#                 print("Sending: ", str(to_send))
#                 socketio.emit('exercise', to_send)
#                 i += 1
#             time.sleep(0.5)

server_thread = Server("Server-thread")
server_thread.start()
# server_thread = Emitter("Emitter-thread")
# server_thread.start()
# serial_thread = Server("Serial-read-thread")
# serial_thread.start()

eventlet.wsgi.server(eventlet.listen(('', 8000)), app)