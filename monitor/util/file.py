#!/usr/bin/python
import os
import sys

def setFileFromList(file, list):
	f = open(file, 'w')
	for line in list:
		f.write(line + "\n")
	f.close()
	return True

def getListFromFile(file):
	f = open(file, 'r')
	list = []
	for line in f:
		line = line.strip()
		list += [line]
	return list

def loadFile(file):
	f = open(file,'r')
	buf = f.read()
	f.close()
	return buf

def dumpFile(file, buf):
	f = open(file, 'wb')
	f.write(buf)
	f.close()
	return
