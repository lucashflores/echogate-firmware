from gtts import gTTS
import pygame
import time

def emit_audio(audio):
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

emit_audio("echogate inicializada")
emit_audio("trabalhando no treinamento da inteligencia artificial")
