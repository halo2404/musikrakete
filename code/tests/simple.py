import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

GPIO.setup(11,GPIO.OUT)
GPIO.output(11,GPIO.LOW)

#GPIO.output(11,GPIO.HIGH)
#time.sleep(10)

dauer = .5
for x in range(3):
        GPIO.output(11,GPIO.HIGH)
        time.sleep(dauer)
        GPIO.output(11,GPIO.LOW)
        time.sleep(dauer)

GPIO.cleanup()
