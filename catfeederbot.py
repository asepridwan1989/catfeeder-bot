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

statfeed = False
condition = 'morning'
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
	firebase.put(dblink,'allert', st + ' success open bucket')
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

def getTime():
	localtime = time.localtime(time.time())	
	minute = str(localtime.tm_min)
	if len(minute) == 1:
		minute = '0'+minute
	timeNow = int(str(localtime.tm_hour)+minute)
	return timeNow
def autoMode():
	global statfeed
	global condition
	global dblink
	evening = firebase.get(dblink + 'feedTime','eveningFeed')
	morning = firebase.get(dblink + 'feedTime','morningFeed')
	
	if (getTime() == evening - 1) or (getTime() == morning - 1):
		statfeed = False
	#print getTime(), evening, morning
	iscat = 'default'
	if ((getTime() == evening) or (getTime() == morning)) and statfeed == False:
		if getTime() == evening :
			condition = 'evening'
		if getTime() == morning :
			condition = 'morning'
		while getTime() < (evening + 4) or getTime() < (morning + 4):
			if scandepan() < 25:
				while not iscat == True:
					#print "nunggu stat kucing", scandepan()
					iscat = firebase.get(dblink,'isCatDeepLens')
					if iscat == False:
						fire()
						st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
						firebase.put(dblink,'isCatDeepLens','default')
				if bowl() == 0:
					st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
					firebase.put(dblink,'allert', st + ' fail to open bucket bowl is not empty')
					time.sleep(1)
				if bowl() == 1:
					openBucket()	
					statfeed = True				
				while scanatas() > 15 and scandepan() > 25:
					if getTime() == (evening + 4) or getTime() == (morning + 4):
						st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
						firebase.post(dblink + 'message/', st + " your cat hasn't been fed this " + condition)						
						return
				st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
				firebase.post(dblink + 'message/', st + ' cat is eating')						
				time.sleep(1)
				firebase.put(dblink,'lastfeed', st)
				return				
			if getTime() == (evening + 4) or getTime() == (morning + 4):
				st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
				firebase.post(dblink + 'message/', st + " your cat hasn't been fed this " + condition)						
				return
								
	
def manualMode():
	global dblink
	gate = firebase.get(dblink,'openBucket')	
	if gate == True and bowl() == 1:
		openBucket()
		st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		firebase.put(dblink,'openBucket', False)
		firebase.put(dblink,'lastfeed', st)		
	if gate == True and bowl() == 0:
		st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		firebase.put(dblink,'openBucket', False)
		firebase.put(dblink,'allert', st + ' fail to open bucket bowl is not empty')

def checkCon():
	firebase.put(dblink,'connectStat', True)
	time.sleep(1)
	firebase.put(dblink,'connectStat', False)
	firebase.put(dblink,'connectReq', False)
	
while True:
	key = firebase.get('login/', 'currentUser')
	dblink = 'feeders/'+key + '/'
	conreq = firebase.get(dblink,'connectReq')
	if conreq == 'ping':
		checkCon()
	firebase.put(dblink,'bowlstat',bowl())
	firebase.put(dblink,'isCatDeepLens','default')
	mode = firebase.get(dblink,'autoControl')
	firebase.put(dblink,'foodLevel', levelFood())
	if mode == False:
		manualMode()
	if mode == True:
		autoMode()
