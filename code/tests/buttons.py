import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    if (GPIO.input(14) == False):
	print('Button 1')

    if (GPIO.input(15) == False):
	print('Button 2')

    if (GPIO.input(18) == False):
	print('Button 3')

    time.sleep(0.25)