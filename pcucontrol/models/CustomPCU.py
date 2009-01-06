# Each method follows the following format:
#    CustomPCU_loginbase()
# 
# This provides a simple means of lookup given the custom type.
#    The only problem might come up if a single site has multiple custom PCUs.
#    That would be pretty wierd though...

from pcucontrol.reboot import *

class CustomPCU_uniklu(PCUControl):
	def run_http(self, node_port, dryrun):
		url = "https://www-itec.uni-klu.ac.at/plab-pcu/index.php" 

		if not dryrun:
			# Turn host off, then on
			formstr = "plab%s=off" % node_port
			os.system("curl --user %s:%s --form '%s' --insecure %s" % (self.username, self.password, formstr, url))
			time.sleep(5)
			formstr = "plab%s=on" % node_port
			os.system("curl --user %s:%s --form '%s' --insecure %s" % (self.username, self.password, formstr, url))
		else:
			os.system("curl --user %s:%s --insecure %s" % (self.username, self.password, url))


		

