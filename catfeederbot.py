from firebase import firebase
firebase = firebase.FirebaseApplication('https://catfeeder-38829.firebaseio.com/', None)
import datetime

import RPi.GPIO as GPIO
import time
pulse_duration = 0
distance = 0
pulse_start_time = 0
pulse_end_time = 0
us_depan_trigger = 13
us_depan_echo = 15
us_atas_trigger = 7
us_atas_echo = 12

GPIO.setmode(GPIO.BOARD)
GPIO.setup(03, GPIO.OUT)
pwm = GPIO.PWM(03,50)
pwm.start(0)

GPIO.setup(35, GPIO.IN)
GPIO.setup(37, GPIO.IN)

input_value = GPIO.input(35)
input_value2 = GPIO.input(37)


def scan_us(trigger, echo):
	GPIO.setmode(GPIO.BOARD)
	PIN_TRIGGER = trigger
	PIN_ECHO = echo

	GPIO.setup(PIN_TRIGGER, GPIO.OUT)
	GPIO.setup(PIN_ECHO, GPIO.IN)

	GPIO.output(PIN_TRIGGER, GPIO.LOW)
	GPIO.output(PIN_TRIGGER, GPIO.HIGH)

	time.sleep(0.00001)

	GPIO.output(PIN_TRIGGER, GPIO.LOW)

	while GPIO.input(PIN_ECHO)==0:
		global pulse_start_time
		pulse_start_time = time.time()
	while GPIO.input(PIN_ECHO)==1:
		global pulse_end_time
		pulse_end_time = time.time()
		
	pulse_duration = pulse_end_time - pulse_start_time
	distance = round(pulse_duration * 17150, 2)
	return distance
	
def levelFood():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(29, GPIO.IN)       
	GPIO.setup(31, GPIO.IN)  
	GPIO.setup(33, GPIO.IN)  
	GPIO.setup(35, GPIO.IN)  
	
	bit1 = GPIO.input(29)
	bit2 = GPIO.input(31)
	bit3 = GPIO.input(33)
	bit4 = GPIO.input(35)
	
	if (bit1==0) and (bit2==0) and (bit3==0) and (bit4==0):
		return 100
	if (bit1==1) and (bit2==0) and (bit3==0) and (bit4==0):
		return 75
	if (bit1==1) and (bit2==1) and (bit3==0) and (bit4==0):
		return 50
	if (bit1==1) and (bit2==1) and (bit3==1) and (bit4==0):
		return 25
	if (bit1==1) and (bit2==1) and (bit3==1) and (bit4==1):
		return 0
	
def SetAngle(angle):
	duty = angle / 18 + 2
	GPIO.output(03, True)
	pwm.ChangeDutyCycle(duty)
	time.sleep(0.500)
	GPIO.output(03, False)
	pwm.ChangeDutyCycle(0)
	
def openBucket():
	SetAngle(35)
	time.sleep(1)
	SetAngle(55)
	time.sleep(1)
	st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
	firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' success open bucket')
	time.sleep(.500)
	
def scandepan():
	cek_depan = scan_us(us_depan_trigger, us_depan_echo)
	return cek_depan

def scanatas():
	cek_atas = scan_us(us_atas_trigger, us_atas_echo)
	return cek_atas	
def fire():
	GPIO.setup(40, GPIO.OUT)  
	GPIO.output(40, 0)
	time.sleep(1)
	GPIO.output(40, 1)
	time.sleep(1)
	
def bowl():
	GPIO.setup(37, GPIO.IN)
	bowlstat = GPIO.input(37)
	return bowlstat
	
def autoMode():
	evening = firebase.get('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/feedTime','eveningFeed')
	morning = firebase.get('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/feedTime','morningFeed')
	localtime = time.localtime(time.time())	
	minute = str(localtime.tm_min)
	if len(minute) == 1:
		minute = '0'+minute
	timeNow = int(str(localtime.tm_hour)+minute)
	print timeNow, evening, morning
	iscat = 'default'
	if (timeNow == evening) or (timeNow == morning):
		while timeNow < (evening + 5) or timeNow < (morning + 5):
			if scandepan()< 20:
				while not iscat == True:
					print "nunggu stat kucing"		
					iscat = firebase.get('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/','isCatDeepLens')
					if iscat == False:
						fire()
						firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/','isCatDeepLens','default')
						firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' success activate water canon')
					if timeNow == (evening + 5) or timeNow == (morning + 5):
						st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
						firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' no cat detected')						
						return
				if bowl() == 0:
					st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
					firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' bowl is not empty')
					time.sleep(1)
				if bowl() == 1:
					openBucket()								
				while scanatas() > 30 :
					print "nunggu makan"
					time.sleep(.250)
				st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
				firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' cat is eating')						
				time.sleep(1)
				firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/','lastfeed', st)
				return		
			
				
				
	
def manualMode():
	gate = firebase.get('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1','openBucket')	
	if gate == True and bowl() == 1:
		openBucket()
		firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1','openBucket', False)		
	if gate == True and bowl() == 0:
		st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1','openBucket', False)
		firebase.post('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/message/', st + ' fail to open bucket, bowl is not empty')

while True:	
	firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/','bowlstat',bowl())
	firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1/','isCatDeepLens','default')
	mode = firebase.get('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1','autoControl')
	firebase.put('feeders/w4ly4dU291Y6cXDIju9j3BBAfZh1','foodLevel', levelFood())
	if mode == False:
		manualMode()
	if mode == True:
		autoMode()
