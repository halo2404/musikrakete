# Control script for the piPlayer. In order to run with PulseAudio, the OSS
# sound driver has to be set as first option in ~/.moc/config
# The mocp server is then run over the padsp wrapper.
#
# ~/.moc/config
#	# Use OSS for Pulseaudio compatibility (run 'padsp mocp')
#	SoundDriver = OSS:ALSA:JACK

import RPi.GPIO as GPIO
import logging
import time
import subprocess
import select  # see http://stackoverflow.com/a/10759061/3761783
import os

# Configuration
MUSIC_BASE_DIRECTORY = "/media/share/Audio/Kinder/"
SOUND_SCANNING = "/home/pi/scanning.mp3"
SOUND_OK = "/home/pi/263133__pan14__tone-beep.mp3"
SOUND_SCAN_FAIL = "/home/pi/159367__huminaatio__7-error.mp3"
SOUND_PLAYBACK_ERROR = "/home/pi/no.mp3"
QR_SCANNER_TIMEOUT = 3
BUTTON_PAUSE = 0.4

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s - %(message)s')
logging.info('Initializing')

# photo sensor on PIN 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)

# LED on PIN 17
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW)

# Buttons on PINs 14, 15 and 18
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

photo_sensor_still_active = False

try:
	logging.info('Start moc server')
	subprocess.call(["padsp", "mocp", "--server"])
	subprocess.call(["mocp", "--clear"])
	subprocess.call(["mocp", "-l", SOUND_OK])
	
	while True:
		
		# TODO what's a good value here?
		time.sleep(0.01)
		
		if (GPIO.input(14) == False):
			logging.debug('mocp --previous')
			subprocess.call(["mocp", "--previous"])
			time.sleep(BUTTON_PAUSE)
			# TODO wait for ~0.25 s, if button is still pressed, seek instead of skipping
	
		if (GPIO.input(15) == False):
			logging.debug('mocp --toggle-pause')
			subprocess.call(["mocp", "--toggle-pause"])
			time.sleep(BUTTON_PAUSE)
	
		if (GPIO.input(18) == False):
			logging.debug('mocp --next')
			subprocess.call(["mocp", "--next"])
			time.sleep(BUTTON_PAUSE)
			# TODO wait for ~0.25 s, if button is still pressed, seek instead of skipping
		
		# check photo sensor
		if ((not photo_sensor_still_active) and (GPIO.input(4) == GPIO.HIGH)):
			logging.debug('Photo sensor active, activating light and camera')
			subprocess.call(["mocp", "-l", SOUND_SCANNING])
			
			# turn LED on
			GPIO.output(17, GPIO.HIGH)
			
			# scan QR code
			zbarcam = subprocess.Popen(['zbarcam', '--nodisplay', '--raw', '-Sdisable', '-Sqrcode.enable', '--prescale=320x240', '/dev/video0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			
			poll_obj = select.poll()
			poll_obj.register(zbarcam.stdout, select.POLLIN)
			
			# wait for scan result (or timeout)
			start_time = time.time()
			poll_result = False
			while ((time.time() - start_time) < QR_SCANNER_TIMEOUT and (not poll_result)):
				poll_result = poll_obj.poll(100)
			
			if (poll_result):
				
				try:
				
					qr_code = zbarcam.stdout.readline().rstrip()
					qr_code = qr_code.decode("utf-8") # python3
					logging.debug("QR Code: {}".format(qr_code))
					
					if (not qr_code.startswith("http://")):
						# create full path
						full_path = MUSIC_BASE_DIRECTORY + qr_code
	
						logging.debug("Full Path {}".format(full_path))
						if (not os.path.isfile(full_path)):
							logging.debug("not a file > add as directory")
							directory = full_path
							logging.debug("Directory {}".format(directory))
						else:
							logging.debug("it's a file")
							directory = os.path.dirname(os.path.realpath(full_path))
							filename = os.path.basename(full_path)
							logging.debug("Directory {}".format(directory))
							logging.debug("Filename {}".format(filename))
						
						os.chdir(directory)
						
						#onlyfiles = [f for f in os.listdir('.') if os.path.isfile(os.path.join('.', f))]
						#logging.debug(onlyfiles)
						
					else:
						logging.debug("URL > open as stream")
						stream_url = qr_code
					
					subprocess.call(["mocp", "--clear"])
					subprocess.call(["mocp", "--stop"])
	
					logging.debug("Stopped")
					
					# play confirmation sound
					subprocess.call(["mocp", "-l", SOUND_OK])
					
					if ('stream_url' in locals()):
						logging.debug("Add stream")
						subprocess.check_call(["mocp", "-a", stream_url])
						del stream_url
					elif ('filename' in locals()):
						logging.debug("Add file {}".format(filename))
						subprocess.check_call(["mocp", "-a", filename])
						del filename
					else:
						logging.debug("Add directory {}".format(directory))
						subprocess.check_call(["mocp", "-a", "."])
					
					# subprocess.check_call(["mocp", "-a", target, "-p"])
					logging.debug("Start playback")
					subprocess.check_call(["mocp", "-p"])
					
				except subprocess.CalledProcessError as e:
					logging.debug("Error starting playback, mocp returned {}".format(e.returncode))
					logging.debug(e.output)
					subprocess.call(["mocp", "-l", SOUND_PLAYBACK_ERROR])
				except FileNotFoundError as e:
					logging.debug("Could not open directory {}".format(directory))
					subprocess.call(["mocp", "-l", SOUND_PLAYBACK_ERROR])
			else:
				logging.debug('Timeout on zbarcam')
				subprocess.call(["mocp", "-l", SOUND_SCAN_FAIL])
				
			# consider the photo sensor to be blocked
			photo_sensor_still_active = True
			
			zbarcam.terminate()
			
			# LED off
			GPIO.output(17, GPIO.LOW)
			
		elif (GPIO.input(4) == GPIO.LOW):
			# the photo sensor is not blocked (anymore)
			photo_sensor_still_active = False
			
# Exit when Ctrl-C is pressed
except KeyboardInterrupt:
		logging.info('Close moc server')
		subprocess.call(["mocp", "--exit"])
		logging.info('Reset GPIO configuration and close')
		GPIO.cleanup()
