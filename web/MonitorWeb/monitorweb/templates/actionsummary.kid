<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Node View"
from monitor.util import diff_time
from monitor import config
from time import mktime
from links import *

def zabbix_event_ack_link(eventid):
	return "http://" + config.MONITOR_HOSTNAME + "/zabbix/acknow.php?eventid=" + str(eventid)

?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<table width="100%">
		<thead>
			<tr>
				<th>Last Day</th>
				<th>Last Week</th>
				<th>Last Month</th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Notice Name</th>
					<th>Count</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="key in results.keys()">
					<td></td>
					<td nowrap="true" py:content="key"></td>
					<td nowrap='true' py:content="results[key]"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
