from mm18usb import *

class CoinServoDriver(object):
  #def __init__(self,x_servo=0,y_servo=1,z_servo=2):
	def __init__(self,x_servo=0):
		self.x_servo = x_servo
		#self.y_servo = y_servo
		#self.z_servo = z_servo
		self.device = mm18usb('/dev/ttyACM2', '/dev/ttyACM1')
		self.device.set_acceleration(self.x_servo,10)
		self.device.set_speed(self.x_servo,10)
		#self.device.set_acceleration(self.y_servo,10)
		#self.device.set_speed(self.y_servo,1)
		#self.device.set_acceleration(self.z_servo,10)
		#self.device.set_speed(self.z_servo,10)
		self.device.go_home()

	def __del__(self):
		del(self.device)
    
	def status_report(self):
		#return "X: %s\tY: %s\tZ: %s" % (self.device.get_position(self.x_servo),self.device.get_position(self.y_servo),self.device.get_position(self.z_servo))
		return "X: %s" % (self.device.get_position(self.x_servo))


	def set_speed(self, speed):
		self.device.set_speed(self.x_servo,speed)
		self.device.wait_until_at_target()

	def set_acceleration(self, acc):
		self.device.set_acceleration(self.x_servo,acc)
		self.device.wait_until_at_target()



	def pan(self,dx):
		x = self.device.get_position(self.x_servo)
		x += dx
		self.device.set_target(self.x_servo,x)
		self.device.wait_until_at_target()
 
	def tilt(self,dy):
		y = self.device.get_position(self.y_servo)
		y += dy
		self.device.set_target(self.y_servo,y)
		self.device.wait_until_at_target()

	def rotate(self,dz):
		z = self.device.get_position(self.z_servo)
		z += dz
		self.device.set_target(self.z_servo,z)
		self.device.wait_until_at_target()
    
	#def goto(self,x,y,z=0):
	def goto(self,x=0):
		print "x=", x
		self.device.set_target(self.x_servo,x)
		#self.device.set_target(self.y_servo,y)
		#self.device.set_target(self.z_servo,z)
		self.device.wait_until_at_target()
    
	def reset(self):
		self.device.go_home()
		self.device.wait_until_at_target()

	def arm_up(self, up):
		pos = 1425+up
		self.goto(pos)
		self.device.wait_until_at_target()

	def arm_down(self):
		self.goto(1425)
		self.device.wait_until_at_target()

if __name__=="__main__":

	#coinid_servo = mm18usb('/dev/ttyACM2', '/dev/ttyACM1')
	coinid_servo = CoinServoDriver()
	print coinid_servo.status_report()
	coinid_servo.set_speed(5)
	time.sleep(.5)
	coinid_servo.set_acceleration(5)
	print coinid_servo.status_report()
	time.sleep(.5)
	coinid_servo.arm_up(0)
	print coinid_servo.status_report()
	time.sleep(1)
	coinid_servo.arm_up(100)
	print coinid_servo.status_report()
	time.sleep(1)
	coinid_servo.arm_down()
	print coinid_servo.status_report()
	time.sleep(1)

	#print coinid_servo.get_errors()

	#print "Get Position"
	#pos = coinid_servo.get_position(0)
	#print pos      


	#print "moving arm up"
	#coinid_servo.reset()
	#print "Set Target:"
	#coinid_servo.set_target(0,1700)
	#coinid_servo.wait_until_at_target()
	#time.sleep(1)
	#coinid_servo.arm_up()

	del coinid_servo
	
