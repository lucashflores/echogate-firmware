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
from gtts import gTTS
import pygame
import time
import imutils

MEET_URL="http://jitsi.member.fsf.org/echogate-streaming3#config.prejoinPageEnabled=false"

class AudioEmitter():

    def __init__(self, route):
        self.audio_emitter_socket = create_connection(route)
        print("[INFO] Audio emitter socket connected.")
        self.audio_emitter_socket.send(json.dumps({"event": "audioEmitterClient", "data": "Audio Emitter"}))
        self.audio_emitter_socket.on_message = self.handle_message

    def emit(self, audio):
    
        language = 'pt'
        myobj = gTTS(text=audio, lang=language, slow=False)
        myobj.save("audios/audio.mp3")

        time.sleep(0.5)

        pygame.mixer.init()
        pygame.mixer.music.load('audios/audio.mp3')
        pygame.mixer.music.set_volume(1)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy() == True:
            pass

        time.sleep(0.5)

    def handle_message(self, message):
        self.emit(message)
    
    def execute(self):
        while True:
            result = self.audio_emitter_socket.recv()
            self.handle_message(result)

class FaceRecognizer():

    def __init__(self, route, audio_emitter):
        self.face_recognizer_socket = create_connection(route)
        print("[INFO] Face recognizer socket connected.")
        self.audio_emitter = audio_emitter
        self.load_binaries()
        self.reload_binaries = False

    def warn(self):
        self.reload_binaries = True

    def need_to_reload_binaries(self):
        return self.reload_binaries

    def load_binaries(self):
        encodings_file_name = "encodings.pickle"
        print("[FACE RECOGNIZER] Loading encodings.")
        self.encodings = pickle.loads(open(encodings_file_name, "rb").read())
    
    def notify(self, name):
        self.face_recognizer_socket.send(json.dumps({"event": "faceRecognized", "data": str(name)}))

    def execute(self):
        
        cap = cv2.VideoCapture(1)

        while True:

            if self.need_to_reload_binaries():
                self.load_binaries()

            ret, frame = cap.read()
            frame = imutils.resize(frame, width=500)
            # detecta o local das faces
            boxes = face_recognition.face_locations(frame)
            # detecta cada face na frame
            find_encodings = face_recognition.face_encodings(frame, boxes)
            names = []
            # itera sobre as faces
            for encoding in find_encodings:
                # realiza a comparação de cada face detectada com as faces cadastradas
                matches = face_recognition.compare_faces(self.encodings["encodings"], encoding)
                name = "Unknown" # se a face não é reconhecida, printa "Unknown"

                # checa se houve um match de face
                if True in matches:
                    # encontra o índice de todas as faces que deram match e inicializa
                    # um dicionário para contar a quantidade de vezes que cada face deu match
                    matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    # itera sobre os índices de cada face que deu match e mantém a contagem
                    # para cada face reconhecida
                    for i in matchedIdxs:
                        name = self.encodings["names"][i]
                        counts[name] = counts.get(name, 0) + 1

                    # determina a face reconhecida com o maior número de votos
                    # caso empate, é pego a primeira do dicionário
                    name = max(counts, key=counts.get)

                # atualiza a lista de nomes
                names.append(name)

            recognized = False

            for name in names:
                if name != "Unknown":
                    print(f"[FACE RECOGNIZER] Recognized {name}, notifying server...")
                    self.audio_emitter.emit(f"Oi {name}, vou avisar que voc� chegou")
                    self.notify(name)
                    recognized = True

            if recognized == True:
                time.sleep(60)


class BellNotifier():

    def __init__(self, route, audio_emitter):
        self.bell_socket = create_connection(route)
        print("[INFO] Bell socket connected.")
        self.audio_emitter = audio_emitter
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

    def __init__(self, route, facial_recognizer):
        self.face_training_socket = create_connection(route)
        self.face_recognizer = facial_recognizer
        print("[INFO] Face recognizer trainer socket connected.")
        self.face_training_socket.send(json.dumps({"event": "imageTrainerClient", "data": "Facial Trainer"}))
        self.face_training_socket.on_message = self.handle_message

    def process_base64_image(self, base64_string):
        binary_data = base64.b64decode(base64_string)
        image_array = np.frombuffer(binary_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image

    def write_face_data(self, knownEncodings, knownNames):
        print("[FACE TRAINER] Generating encondings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()
        print("[FACE TRAINER] Completed successfully.")

        self.face_recognizer.warn()
    
    def handle_message(self, message):
        data = json.loads(message)

        knownEncodings = []
        knownNames = []

        print("[FACE TRAINER] Data received.")

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

socket_route = "ws://142.93.4.38:80/websocket"

audio_emitter = AudioEmitter(socket_route)
bell_notifier = BellNotifier(socket_route, audio_emitter)
face_recognizer = FaceRecognizer(socket_route, audio_emitter)
face_trainer = FaceRecognitionTrainer(socket_route, face_recognizer)

print("[INFO] Modules loaded.")
audio_emitter.emit("Echogate inicializada")
#video_streamer = VideoStreamer(socket_route)

# threads principais

# coloca o código de espera para receber fotos do servidor
threading.Thread(target=face_trainer.execute).start()
#threading.Thread(target=video_streamer.execute).start()
#threading.Thread(target=face_recognizer.execute()).start()
#threading.Thread(target=audio_emitter.execute()).start()

while True:
    #video_streamer.execute()
    #bell_notifier.execute()
    pass
   
