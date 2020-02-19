def event(f):
	def wrapper(self, *args, **kwargs):
		retVal = f(self, *args, **kwargs)
		self.fireEvent(f.func_name, *args, **kwargs)
		return retVal
	return wrapper

class EventProducer(object):
	def __init__(self):
		self.eventListeners = {}
		
	def addEventListener(self, eventId, callback):
		if (eventId not in self.eventListeners):
			self.eventListeners[eventId] = []
		self.eventListeners[eventId].append(callback)
		
	def removeEventListener(self, eventId, callback):
		if (eventId in self.eventListeners):
			self.eventListeners[eventId].remove(callback)
			if (len(self.eventListeners[eventId]) == 0):
				del self.eventListeners[eventId]	
				
	def fireEvent(self, eventId, *args, **kwargs):
		if (eventId in self.eventListeners):
			for callback in self.eventListeners[eventId]:
				callback(*args, **kwargs)
		