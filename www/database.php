
<?php 

# TODO: clean up this aweful hack.
system("/usr/share/monitor-server/phpconfig.py > /var/www/cgi-bin/monitor/monitorconfig.php");
include 'monitorconfig.php';
define("PICKLE_PATH", MONITOR_DATA_ROOT);

class Pickle
{
	public function load($name)
	{
		if ( ! $this->exists("production." . $name) )
		{
			print "Exception: No such file %s" . $name . "\n";
			return NULL;
		}
		$name = "production." . $name;
		$fname = $this->__file($name);
		$o = unserialize(file_get_contents($fname));

		return $o;
	}
	public function dump($name, $obj)
	{
		if ( ! file_exists(PICKLE_PATH) )
		{
			if ( ! mkdir(PICKLE_PATH, 0777, True) )
			{
				print "Exception: Unable to create directory :" . PICKLE_PATH . "\n";
			}
		}
		$name = "production." . $name;
		$fname = $this->__file($name);

		return file_put_contents($fname, serialize($obj));
	}
	private function __file($name)
	{
		return sprintf("%s/%s.phpserial", PICKLE_PATH, $name);
	}

	public function exists($name)
	{
		return file_exists($this->__file($name));
	}

	public function remove($name)
	{
		return unlink($this->__file($name));
	}

	public function if_cached_else($cond, $name, $function)
	{
		if ( $cond and $this->exists("production.%s" % $name) )
		{
			$o = $this->load($name);
		} else {
			$o = $function();
			if ($cond)
			{
				$this->dump($name, $o);	# cache the object using 'name'
			}
		}
		return o;
	}
}

?>
