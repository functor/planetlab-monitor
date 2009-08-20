<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Action Summary"
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
				<th><a href="actionsummary?since=1">Last Day</a></th>
				<th><a href="actionsummary?since=7">Last Week</a></th>
				<th><a href="actionsummary?since=30">Last Month</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="actionsummarylist" cellpadding="0" border="0" class="plekit_table sortable-onload-0 colstyle-alt no-arrow paginationcallback-actionsummarylist_paginator max-pages-10 paginate-50" >
			<thead>
				<tr>
					<th class="sortable plekit_table">Type</th>
					<th class="sortable plekit_table">Notice Name</th>
					<th class="sortable plekit_table">Count</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="key in results.keys()">
					<td nowrap="true" py:content="'bootman' in key and 'bootmanager' or ( 'notice' in key and 'notice' or ( 'penalty' in key and 'penalty' or 'unknown' ) ) "></td>
					<td nowrap="true"><a href="actionlist?action_type=${key}" py:content="key"></a></td>
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
