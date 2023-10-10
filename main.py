import keyboard
import cv2
import base64
import json
import face_recognition
import numpy as np
import pickle
import threading
from websocket import create_connection

class BellNotifier():

    def __init__(self, route):
        self.bell_socket = create_connection(route)
        self.notified = False

    def notify(self):
        self.bell_socket.send(json.dumps({"event": "event", "data": str("Alguém tocou a campainha")}))

    def execute(self):
        if keyboard.is_pressed('b'):
            if not self.notified:
                self.notified = True
                self.notify()
                return True
        else:
            self.notified = False

        return False

class VideoStreamer():
    
    def __init__(self, route):
        self.video_stream_socket = create_connection(route)
        self.image = cv2.VideoCapture(0)

    def send_image(self, image_as_text):
        self.video_stream_socket.send(json.dumps({"event": "stream", "data": str(image_as_text)}))

    def execute(self):
        ret, frame = self.image.read()
        ret, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        self.send_image(jpg_as_text)

class FaceRecognitionTrainer():

    def __init__(self, route):
        self.face_training_socket = create_connection(route)
        self.face_training_socket.on_message = self.handle_message

    def process_base64_image(self, base64_string):
        binary_data = base64.b64decode(base64_string)
        image_array = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image
    
    def write_face_data(self, data, knownEncodings, knownNames):
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()
    
    def handle_message(self, ws, message):
        data = json.loads(message)

        knownEncodings = []
        knownNames = []

        for person_data in data:
            person_name = person_data["name"]
            images_base64 = person_data["images"]
            for image_base64 in images_base64:
                image = self.process_base64_image(image_base64)
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(rgb, model="hog")
                encodings = face_recognition.face_encodings(rgb, boxes)
                for encoding in encodings:
                    knownEncodings.append(encoding)
                    knownNames.append(person_name)

        self.write_face_data(data)
        
        

    def execute(self):
        while True:
            result = self.face_training_socket.recv()

bell_notifier = BellNotifier("ws://localhost:3000/websocket/bell")
#video_streamer = VideoStreamer("ws://localhost:3000/websocket/image-stream")
#face_trainer = FaceRecognitionTrainer("ws://localhost:3000/websocket/face-trainer")

# threads principais

# coloca o código de espera para receber fotos do servidor
#threading.Thread(target=face_trainer.execute).start()

while True:

    #video_streamer.execute()
    bell_notifier.execute()

   