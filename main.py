import os
import eventlet
from flask_wtf import FlaskForm
from wtforms import SelectField
from flask import Flask, render_template, request, g, session, make_response, current_app, redirect, url_for
from flask_socketio import SocketIO, emit
import cv2
import json
import base64


eventlet.monkey_patch()
#cap=cv2.VideoCapture(0)  ##when removing debug=True or using gevent or eventlet uncomment this line and comment the cap=cv2.VideoCapture(0) in gen(json)
app = Flask(__name__)
app.config['SECRET_KEY'] = '78581099#lkjh'
path_to_videos = ['Videos/remote_server_client1.mp4', 'Videos/remote_server_client2.mp4', 'Videos/yH.gif']
socketio = SocketIO(app, async_mode='eventlet')


# our gloabal worker
workerObject = None

class Worker(object):

    #switch = False
    unit_of_work = 0


    def __init__(self, socketio):
        """
        assign socketio object to emit
        """
        self.video_num = 0
        self.cap = cv2.VideoCapture(path_to_videos[self.video_num])
        self.socketio = socketio
        self.switch = True

    def do_work(self):
        """
        do work and emit message
        """
        #cap = cv2.VideoCapture(path_to_videos[self.video_num])
        frame_counter = 0
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        #print(self.switch)
        while(self.switch):
            ret, img = self.cap.read()
            if ret:
                frame_counter += 1
                # If the last frame is reached, reset the capture and the frame_counter
                if frame_counter == self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    frame_counter = 0  # Or whatever as long as it is the same as next line
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
                frame = cv2.imencode('.jpg', img)[1].tobytes()
                frame = base64.encodebytes(frame).decode("utf-8")
                self.message(frame)
                #print(self.video_num)
                eventlet.sleep(1 / fps)
            else:
                break


        # while self.switch:
        #     self.unit_of_work += 1
        #
        #     # must call emit from the socket io
        #     # must specify the namespace
        #     self.socketio.emit("update", {"msg": self.unit_of_work}, namespace="/work")
        #
        #     # important to use eventlet's sleep method
        #     eventlet.sleep(1)


    def switch_video_stream(self, num):
        """
        stop the loop
        """
        self.switch = False
        self.video_num = num
        self.cap = cv2.VideoCapture(path_to_videos[self.video_num])
        self.switch = True

    def start(self):
        self.switch = True

    def message(self, json, methods=['GET', 'POST']):
        #print("Recieved message")
        self.socketio.emit("update", {"json": json}, namespace="/work")


class Form(FlaskForm):
    model = SelectField('model', choices=[i + 1 for i, _ in enumerate(path_to_videos)])

@app.route('/')
def index():
    """
    renders demo.html
    """
    form = Form()
    return render_template('index.html', form=form)


@socketio.on('connect', namespace='/work')
def connect():
    """
    connect
    """
    global worker
    worker = Worker(socketio)
    #emit("re_connect", {"msg": "connected"})


@socketio.on('start', namespace='/work')
def start_work():
    """
    trigger background thread
    """
    print("start")
    #emit("update", {"msg": "starting worker"})

    # notice that the method is not called - don't put braces after method name
    socketio.start_background_task(target=worker.do_work)


@socketio.on('stop', namespace='/work')
def stop_work():
    """
    trigger background thread
    """
    print("stop")
    worker.stop()
    # worker.video_num = 1
    # worker.start()
    #emit("update", {"msg": "worker has been stoppped"})


@socketio.on('selected', namespace='/work')
def selected(msg):
    global worker
    worker.switch_video_stream(int(msg) - 1)
    print(msg)

    # worker.video_num = 1
    # worker.start()
    #emit("update", {"msg": "worker has been stoppped"})


if __name__ == '__main__':
    """
    launch server
    """
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)#host="0.0.0.0"