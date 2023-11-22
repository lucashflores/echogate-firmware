import cv2
import base64
import json
import face_recognition
import numpy as np
import pickle
import gpiozero
import threading
from websocket import create_connection
import subprocess

MEET_URL="http://jitsi.member.fsf.org/echogate-streaming3#config.prejoinPageEnabled=false"

class AudioEmitter():

    def __init__(self, route):
        self.audio_emiiter_socket = create_connection(route)
        self.audio_emiiter_socket.send(json.dumps({"event": "audioEmitterClient", "data": "Audio Emitter"}))

class FaceRecognizer():

    def __init__(self, route):
        self.face_recognizer_socket = create_connection(route)
    
    def notify(self, name):
        self.face_recognizer_socket.send(json.dumps({"event": "faceRecognized", "data": str(name)}))

class BellNotifier():

    def __init__(self, route):
        print("Initing Bell notifier")
        self.bell_socket = create_connection(route)
        print("Bell connected")
        self.button = gpiozero.Button(17)
        self.notified = False

    def notify(self):
        self.bell_socket.send(json.dumps({"event": "bellRing", "data": str("Alguém tocou a campainha")}))

    def execute(self):
        if self.button.is_pressed:
            if not self.notified:
                self.notified = True
                self.notify()
                return True
        else:
            self.notified = False

        return False

class VideoStreamer():
    
    def __init__(self, route):
        pass

    def execute(self):
        subprocess.Popen(["chromium-browser", "-kiosk", MEET_URL])
        while True:
            pass

class FaceRecognitionTrainer():

    def __init__(self, route):
        self.face_training_socket = create_connection(route)
        self.face_training_socket.send(json.dumps({"event": "imageTrainerClient", "data": "Facial Trainer"}))
        #self.face_training_socket.on_message = self.handle_message

    def process_base64_image(self, base64_string):
        binary_data = base64.b64decode(base64_string)
        image_array = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image
    
    def write_face_data(self, knownEncodings, knownNames):
        print("Generating encondings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()
        print("Completed successfully!")
    
    def handle_message(self, message):
        data = json.loads(message)

        knownEncodings = []
        knownNames = []

        print("Data received!")

        data = data["users"]

        for person_data in data:
            person_name = person_data["name"]
            images_base64 = person_data["pictures"]
            for image_base64 in images_base64:
                image = self.process_base64_image(image_base64)
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                boxes = face_recognition.face_locations(rgb, model="hog")
                encodings = face_recognition.face_encodings(rgb, boxes)
                for encoding in encodings:
                    knownEncodings.append(encoding)
                    knownNames.append(person_name)

        self.write_face_data(knownEncodings, knownNames)
        
        

    def execute(self):
        while True:
            result = self.face_training_socket.recv()
            self.handle_message(result)

socket_route = "ws://localhost:3000/websocket"

#bell_notifier = BellNotifier(socket_route)
video_streamer = VideoStreamer(socket_route)
#face_trainer = FaceRecognitionTrainer(socket_route)

# threads principais

# coloca o código de espera para receber fotos do servidor
#threading.Thread(target=face_trainer.execute).start()
threading.Thread(target=video_streamer.execute).start()

while True:

    #video_streamer.execute()
    bell_notifier.execute()

   