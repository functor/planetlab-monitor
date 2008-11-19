<?php

$path = '/var/www/html/zabbix/include';
set_include_path(get_include_path() . PATH_SEPARATOR . $path);

require "defines.inc.php";

$const = get_defined_constants(true);
foreach ( $const['user'] as $k => $v ):
	if ( is_int($v) ):
		print "$k=$v\n";
	endif;
endforeach;

?>
