import speech_recognition

recognizer = speech_recognition.Recognizer()

while True:

    try:
        with speech_recognition.Microphone(1) as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.2)
            audio = recognizer.listen(mic)
            text = recognizer.recognize_google(audio_data=audio, language="pt-BR")
            text = text.lower()
            print(f"Recognized: {text}")

    except:
        recognizer = speech_recognition.Recognizer()
        continue
