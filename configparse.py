from xml.sax import saxutils

class parse(saxutils.DefaultHandler):
	def __init__(self, title, number):
		self.search_title, self.search_number = title, number
