from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
button1 = 11

GPIO.setup(button1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
	if GPIO.input(button1) == 0:
		sleep(.1)
		print("pressed")
