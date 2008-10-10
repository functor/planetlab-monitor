import os

url = "http://www.emulab.net/downloads/plab_nodehist.txt"
os.popen("curl -s %s | tr ',' ';' | tr '\t' ',' " % url)
