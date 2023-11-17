# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import cv2
import threading

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

# initialize the video stream and allow the camera sensor to warm up
# Set the ser to the followng
# src = 0 : for the build in single web cam, could be your laptop webcam
# src = 2 : I had to set it to 2 inorder to use the USB webcam attached to my laptop
#vs = VideoStream(src=2,framerate=10).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)

# inicia contador de fps
fps = FPS().start()

# itera sobre os frames da câmera
while True:
	# armazena o frame e redimensiona para 500px
	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	# detecta o local das faces
	boxes = face_recognition.face_locations(frame)
	# detecta cada face na frame
	encodings = face_recognition.face_encodings(frame, boxes)
	names = []
	# itera sobre as faces
	for encoding in encodings:
		# realiza a comparação de cada face detectada com as faces cadastradas
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
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
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1

			# determina a face reconhecida com o maior número de votos
			# caso empate, é pego a primeira do dicionário
			name = max(counts, key=counts.get)

			# se alguém no dataset foi identificado, printa o nome na tela
			if currentname != name:
				currentname = name
				print(currentname)

		# atualiza a lista de nomes
		names.append(name)

	# itera sobre as faces reconhecidas
	for ((top, right, bottom, left), name) in zip(boxes, names):
		# desenha o retângulo na face
		cv2.rectangle(frame, (left, top), (right, bottom),
			(0, 255, 225), 2)
		y = top - 15 if top - 15 > 15 else top + 15
		cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
			.8, (0, 255, 255), 2)

	# mostra a imagem na tela
	cv2.imshow("Facial Recognition is Running", frame)
	key = cv2.waitKey(1) & 0xFF

	# sair ao pressionar 'q'
	if key == ord("q"):
		break

	# atualiza o fps
	fps.update()

# para o timer e mostra as informações
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# limpa
cv2.destroyAllWindows()
vs.stop()
