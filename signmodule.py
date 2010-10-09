#!/usr/bin/python

# This is a module to control a Alpha Big Dot led sign
# http://www.alpha-american.com/p-alpha-big-dot.html
#
# See http://www.alpha-american.com/alpha-manuals/M-Protocol.pdf
# for more information on the protocol used to speak to
# sign
#
# This module was originally written by Bryan Andregg and the
# original RHN crew. 
#
# The sign can do a lot of things this module doesn't support
# but it works pretty well for displaying basic text. Some things
# that could be added:
#       - pixmap support see (DOTS PICTURE in the docs above)
#       - custom char support (you could theorectially sort of
#         support the non default glyphs this way, though it
#         only understands ASCII)
#       - some sort of markup language to define what the text
#         looks like
#
#  Consider this code GPL v2 or newer.
#

import sys
class Sign:
	message = ""

	__null__ = "\000\000\000\000\000"
	__soh__ = "\001"
	__type__ = "Z"
#	__type__ = "!"
	__addr__ = "00"
	__stx__ = "\002"
	__eot__ = "\004"
	eot = "\004"

	header = (__null__ + __soh__ + __type__ + __addr__ + __stx__)

	modetab = {"rotate" : "a",
		   "hold" : "b",
		   "flash" : "c",
		   "roll-up" : "e",
		   "roll-down" : "f",
		   "roll-left" : "g",
		   "roll-right" : "h",
		   "wipe-up" : "i",
		   "wipe-down" : "j",
		   "wipe-left" : "k",
		   "wipe-right" : "l",
		   "scroll" : "m",
		   "auto" : "o",
		   "roll-in" : "p",
		   "roll-out" : "q",
		   "wipe-in" : "r",
		   "wipe-out" : "s",
		   "comp-rotate" : "t",
		   "twinkle" : "n0",
		   "sparkle" : "n1",
		   "snow" : "n2",
		   "interlock" : "n3",
		   "switch" : "n4",
		   "slide" : "n5",
		   "spray" : "n6",
		   "starburst" : "n7",
		   "welcome" : "n8",
		   "slot-machine" : "n9",
		   "thank-you" : "nS",
		   "no-smoking" : "nU",
		   "dont-drink" : "nV",
		   "animal" : "nW",
		   "fireworks" : "nX",
		   "car" : "nY",
		   "bomb" : "nZ"}

	colortab = {"red" : "1",
		    "green" : "2",
		    "amber" : "3",
		    "dim-red" : "4",
		    "dim-green" : "5",
		    "brown" : "6",
		    "orange" : "7",
		    "yellow" : "8",
		    "rainbow-1" : "9",
		    "rainbow=2" : "A",
		    "mix" : "B",
		    "auto" : "C"}

	chartab = {"5-high" : "1",
		   "7-high-standard" : "3",
		   "7-high-fancy" : "5",
		   "10-high" : "6",
		   "full-standard" : "9",
		   "full-fancy" : "8"}

	def portcfg(self,p):
		import os
		os.system("stty '0:1:6bd:8831:3:1c:7f:15:4:0:1:0:11:13:1a:0:12:f:17:16:0:0:73:0:0:0:0:0:0:0:0:0:0:0:0:0'< " + p)

	def connect(self,p):
	#	self.portcfg(p)
		self.port = open(p,"w")

	def __init__(self,p):
		#self.portcfg(p)
		self.connect(p)

	def write(self,m):
		try:
			self.port.write(m)
		except:
			# yeah, bad... shrug
			pass

	def reset(self):
		self.write(self.header + "E" + "," + self.eot)

	def clear(self):
		self.message = ""

	def configure(self,s):
		c = ""
		for key in s.keys():
			c = c + key + "AU" + s[key] + "FF00"
		self.write(self.header + "E" + "$" + c + self.eot)

	def time_set(self,t):
		self.write(self.header + "E" + " " + t + self.eot)

	def time_format(self,f):
		self.write(self.header + "E" + "'" + f + self.eot)

	def time_print(self):
		self.message = self.message + "\023"

	def day_set(self,d):
		self.write(self.header + "E" + "&" + d + self.eot)

	def day_print(self):
		self.message = self.message + "\013" + "9"

	def date_set(self,d):
		self.write(self.header + "E" + ";" + d + self.eot)

	def date_print(self):
		self.message = self.message + "\013" + "4"

	def color(self,c):
		self.message = self.message + "\034" + self.colortab[c]

	def charset(self,c):
		self.message = self.message + "\032" + self.chartab[c]

	def high(self,h):
		if h == "on":
			self.message = self.message + "\035" + "21"
		else:
			self.message = self.message + "\035" + "20"

	def wide(self,w):
		if w == "on":
			self.message = self.message + "\035" + "01"
		else:
			self.message = self.message + "\035" + "00"

	def dwide(self,w):
		if w == "on":
			self.message = self.message + "\035" + "11"
		else:
			self.message = self.message + "\035" + "10"

	def fancy(self,f):
		if f == "on":
			self.message = self.message + "\035" + "51"
		else:
			self.message = self.message + "\035" + "50"

	def fixed(self,f):
		if f == "on":
			self.message = self.message + "\035" + "41"
		else:
			self.message = self.message + "\035" + "40"

	def flash(self,f):
		if f == "on":
			self.message = self.message + "\007" + "1"
		else:
			self.message = self.message + "\007" + "0"

	def mode(self,m):
		try:
			self.message = self.message + "\033" + "0" + self.modetab[m]
		except KeyError:
			self.message = self.message + "\033" + "0" + self.modetab["hold"]

	def space(self,s):
		if s == "prop":
			self.message = self.message + "\036" + "0"
		else:
			self.message = self.message + "\036" + "1"

	def speed(self,s):
		if s == "1":
			self.message = self.message + "\025"
		elif s == "2":
			self.message = self.message + "\026"
		elif s == "4":
			self.message = self.message + "\030"
		elif s == "5":
			self.message = self.message + "\031"
		else:
			self.message = self.message + "\027"

	def text(self,t):
		self.message = self.message + t

	def load(self,l = "A",m = ""):
		self.write(self.header + "A" + l + self.message +
				m + self.eot)

	def seq(self,s):
		self.write(self.header + "E" + "." + "SU" + s + self.eot)

	def show(self, str, color=None, mode="hold"):
	        print "showing %s" % str
		#self.clear()
		#color="green"
		#mode="hold"
		if color:
			self.color(color)
	        #self.mode(mode)
#		self.charset("full-fancy")
		self.text(str)
#		self.charset("full-fancy")
		self.mode(mode)
		self.load()
		

if __name__ == "__main__":
#	sign = Sign("/dev/ttyS1") 
	sign = Sign("/dev/tty.KeySerial1")
	sign.show("".join(sys.argv[1:]), color="red", mode="scroll")
