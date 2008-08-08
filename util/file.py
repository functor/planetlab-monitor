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

