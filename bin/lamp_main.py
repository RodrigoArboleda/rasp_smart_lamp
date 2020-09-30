import threading
import time
from bluetooth import *
import select
#import board
#import neopixel

USER_MAX_CONNECT = 5

TIME_VF_THREAD = 5

TIME_OUT_SOCK = 7200

#led_pin = board.NEOPIXEL
#num_leds = 10
#ORDER = neopixel.RGB

#leds_lamp = neopixel.NeoPixel(
#    led_pin, num_leds, brightness=0.2, auto_write=False, pixel_order=ORDER
#)


sem = threading.Lock()

server_sock = BluetoothSocket(RFCOMM)
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service( server_sock, "LampRasp",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
                    )

class connection_bluetooth(threading.Thread):
		
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
		super(connection_bluetooth,self).__init__(group=group, target=target, name=name, verbose=verbose)		
		self.client_sock = args
		self._stop_event = threading.Event()
	
	def stop(self):
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()

	def run(self):

		if self.client_sock != None:

			self.client_sock.setblocking(0)

			time = 0

			while time != TIME_OUT_SOCK:
				
				data = ""
				
				try:
					ready = select.select([self.client_sock], [], [], 1)
					
					if ready[0]:
						data = self.client_sock.recv(10)

					if data == 'quit000000':
						time = 0
						self.client_sock.close()
						print("Thread finished")
						break
					
					elif len(data) == 10:
						print ("received [%s]" % data)
						a = float(int(data[2:4], 16))/255
						r = int(data[4:6], 16)
						g = int(data[6:8], 16)
						b = int(data[8:10], 16)
												
						sem.acquire()
						print(r, g, b, a)
						#leds_lamp.brightness = a
						#leds_lamp.fill((r, g, b))
						#leds_lamp.show
						sem.release()
					
					elif len(data) > 0 and len(data) < 10:
						print("Error receiving message")

					if len(data) == 0:
						time = time + 1
					
					else:
						time = 0
				
				except Exception as e:
					self.client_sock.close()
					print(e)
					print("Thread finished")
					break

				if self.stopped():
					break

			print("Thread finished")
			self.client_sock.close()	
		
		else:
			print("Client socket problem")



def main():
	
	thread_list = []
	sock_client_list = []
	try:
		while True:  

			print ("Waiting for connection on RFCOMM channel %d" % port)

			client_sock, client_info = server_sock.accept()
			t = connection_bluetooth(args=(client_sock))
			t.start()

			print ("Accepted connection from ", client_info)

			thread_list.append(t)
			sock_client_list.append(client_sock)

			for i in thread_list:
				if not(i.is_alive()):
					index = thread_list.index(i)
					thread_list.remove(i)
					del sock_client_list[index]
					

			while len(thread_list) >= USER_MAX_CONNECT:
				print ("Waiting for a connection to finish")
				for i in thread_list:
					if not(i.is_alive()):
						index = thread_list.index(i)
						thread_list.remove(i)
						del sock_client_list[index]
				time.sleep(TIME_VF_THREAD)

	except KeyboardInterrupt:
		
		print("Ending program ...")

		for i in thread_list:
			if not(i.is_alive()):
				index = thread_list.index(i)
				thread_list.remove(i)
				del sock_client_list[index]
		
		while(len(thread_list) == 0):
		
			for i in thread_list:
				i.stop()
				i.join()

			for i in thread_list:
				if not(i.is_alive()):
					index = thread_list.index(i)
					thread_list.remove(i)
					del sock_client_list[index]

		server_sock.close()

if __name__ == '__main__':
    main()