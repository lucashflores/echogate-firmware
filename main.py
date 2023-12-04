import cv2
import base64
import json
import face_recognition
import numpy as np
import pickle
import gpiozero
import threading
import socket
from websocket import create_connection
import subprocess
from gtts import gTTS
import pygame
import time
import imutils
import socketserver
import logging
import io
import speech_recognition
import sounddevice
from threading import Condition
from http import server

MEET_URL="https://meet.mayfirst.org/echogate-streaming#config.prejoinPageEnabled=false"

PAGE="""\
<html>
<head>
<title>OpenCV MJPEG Streaming</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

lock = threading.Lock()

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, frame):
        with self.condition:
            self.frame = frame
            self.condition.notify_all()
        return self.buffer.write(frame.tobytes())


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg' or self.path == '/index.html/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with VideoStreamer.output.condition:
                        VideoStreamer.output.condition.wait()
                        frame = VideoStreamer.output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class VideoStreamer():
    
    output = StreamingOutput()

    def __init__(self, route):
        
        self.video_stream_socket = create_connection(route)
        ip_address = socket.gethostbyname(socket.gethostname())
        self.video_stream_socket.send(json.dumps({"event": "videoStreamIP", "data": str(ip_address)}))

        # Inicializa o servidor
        address = ('', 8000)
        self.server = StreamingServer(address, StreamingHandler)

        # Inicia o servidor
        threading.Thread(target=self.server.serve_forever).start()

    def execute(self):
        cap = cv2.VideoCapture(1)
        cap.set(cv2.CAP_PROP_FPS, 15)

        while True:
            try:
                _, frame = cap.read()
                _, jpeg = cv2.imencode('.jpg', frame)
                VideoStreamer.output.write(jpeg)
            except:
                print("[INFO] Video stream socket lost connection.")
                self.video_stream_socket = create_connection(self.route)
                print("[INFO] Video stream socket connected.")


class AudioStreamer():

    def __init__(self):
        pass

    def execute(self):
        subprocess.Popen(["chromium-browser", "-kiosk", MEET_URL])
        while True:
            pass


class AudioTranscriber():

    def __init__(self, route):
        self.route = route
        self.audio_transcriber_socket = create_connection(route)
        print("[INFO] Audio transcriber socket connected.")

    def send(self, text):
        self.audio_transcriber_socket.send(json.dumps({"event": "audioTranscription", "data": str(text)}))
        print(f"[AUDIO TRANSCRIBER] Transcription sent.")

    def recognize(self):
        
        recognizer = speech_recognition.Recognizer()

        try:
            with speech_recognition.Microphone(11) as mic:
                recognizer.adjust_for_ambient_noise(mic, duration=0.2)
                audio = recognizer.listen(mic)
                text = recognizer.recognize_google(audio_data=audio, language="pt-BR")
                text = text.lower()
                print(f"[AUDIO TRANSCRIBER] Recognized -> {text}")

        except:
            pass

    def execute(self):
        while True:
            try:
                recognized_text = self.recognize()
                self.send(recognized_text)
            except:
                print("[INFO] Audio transcriber socket lost connection.")
                self.audio_transcriber_socket = create_connection(self.route)
                print("[INFO] Audio transcriber reconnected.")



class AudioEmitter():

    def __init__(self, route):
        self.route = route
        self.audio_emitter_socket = create_connection(route)
        print("[INFO] Audio emitter socket connected.")
        self.audio_emitter_socket.send(json.dumps({"event": "audioEmitterClient", "data": "Audio Emitter"}))

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

    def emit_doorbell_sound(self):
        pygame.mixer.init()
        pygame.mixer.music.load('audios/doorbell.wav')
        pygame.mixer.music.set_volume(1)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy() == True:
            pass

        time.sleep(0.5)


    def handle_message(self, message):
        self.emit(message)
    
    def execute(self):

        while True:
            try:
                result = self.audio_emitter_socket.recv()
                self.handle_message(result)
            except:
                print("[INFO] Audio emitter socket lost connection.")
                self.audio_emitter_socket = create_connection(self.route)
                self.audio_emitter_socket.send(json.dumps({"event": "audioEmitterClient", "data": "Audio Emitter"}))
                print("[INFO] Audio emitter socket connected.")



class FaceRecognizer():

    def __init__(self, route, audio_emitter):
        self.route = route
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
        self.reload_binaries = False
    
    def notify(self, name):
        self.face_recognizer_socket.send(json.dumps({"event": "faceRecognized", "data": str(name)}))
        print("[FACE RECOGNIZER] Notification sent.")

    def execute(self):
        
        cap = cv2.VideoCapture(1)

        while True:

            try:
                if self.need_to_reload_binaries():
                    self.load_binaries()

                ret, frame = cap.read()
                frame = imutils.resize(frame, width=500)
                # detecta o local das faces

                with lock:

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
                            self.audio_emitter.emit(f"Oi {name}, vou avisar da sua chegada.")
                            self.notify(name)
                            recognized = True

                if recognized == True:
                    time.sleep(45)

            except:
                print("[INFO] Face recognizer socket lost connection.")
                self.face_recognizer_socket = create_connection(self.route)
                print("[INFO] Face recognizer socket reconnected.")


class BellNotifier():

    def __init__(self, route, audio_emitter):
        self.route = route
        self.bell_socket = create_connection(route)
        print("[INFO] Bell socket connected.")
        self.audio_emitter = audio_emitter
        self.button = gpiozero.Button(17)
        self.notified = False

    def notify(self):
        self.bell_socket.send(json.dumps({"event": "bellRing", "data": str("Alguém tocou a campainha")}))

    def execute(self):
        
        while True:
            try:
                if self.button.is_pressed:
                    if not self.notified:
                        self.notified = True
                        self.notify()
                        self.audio_emitter.emit_doorbell_sound()
                else:
                    self.notified = False
            except:
                print("[INFO] Bell socket lost connection.")
                self.bell_socket = create_connection(self.route)
                print("[INFO] Bell socket reconnected.") 


class FaceRecognitionTrainer():

    def __init__(self, route, facial_recognizer):
        self.route = route
        self.face_training_socket = create_connection(route)
        self.face_recognizer = facial_recognizer
        print("[INFO] Face recognizer trainer socket connected.")
        self.face_training_socket.send(json.dumps({"event": "imageTrainerClient", "data": "Facial Trainer"}))

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

                cv2.imwrite('image.jpg', image)
                image = cv2.imread('image.jpg')
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                boxes = face_recognition.face_locations(rgb,
                    model="hog")
                        
                encodings = face_recognition.face_encodings(rgb, boxes)
                        
                for encoding in encodings:
                    knownEncodings.append(encoding)
                    knownNames.append(person_name)

        self.write_face_data(knownEncodings, knownNames)
        

    def execute(self):

        while True:
            try:
                result = self.face_training_socket.recv()
                with lock:
                    self.handle_message(result)
            except Exception as e:
                print(e)
                print("[INFO] Face recognizer trainer socket lost connection.")
                self.face_training_socket = create_connection(self.route)
                self.face_training_socket.send(json.dumps({"event": "imageTrainerClient", "data": "Facial Trainer"}))
                print("[INFO] Face recognizer trainer socket reconnected.")

socket_route = "ws://142.93.4.38:80/websocket"

audio_emitter = AudioEmitter(socket_route)
bell_notifier = BellNotifier(socket_route, audio_emitter)
face_recognizer = FaceRecognizer(socket_route, audio_emitter)
face_trainer = FaceRecognitionTrainer(socket_route, face_recognizer)
video_streamer = VideoStreamer(socket_route)
audio_streamer = AudioStreamer()

print("[INFO] Modules loaded.")
audio_emitter.emit("Echogate inicializada")


# threads principais

threading.Thread(target=face_trainer.execute).start()
threading.Thread(target=audio_streamer.execute).start()
threading.Thread(target=video_streamer.execute).start()
threading.Thread(target=face_recognizer.execute).start()
threading.Thread(target=audio_emitter.execute).start()
threading.Thread(target=bell_notifier.execute).start()

while True:
    pass
   
