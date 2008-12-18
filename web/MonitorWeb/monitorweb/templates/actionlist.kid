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
				<th></th>
				<th><a href="${tg.url('action', filter='active')}">Not Acknowledged(${fc['active']})</a></th>
				<th><a href="${tg.url('action', filter='acknowledged')}">Acknowledged(${fc['acknowledged']})</a></th>
				<th><a href="${tg.url('action', filter='all')}">All(${fc['all']})</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th mochi:format="str">Site</th>
					<th>Hostname</th>
					<th>Issue (severity)</th>
					<th>Last change</th>
					<th>Notes (acknowledged)</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td><a href="${link('pcuview', loginbase=node[0])}">${node[0]}</a></td>
					<td nowrap="true" py:content="node[1]"></td>
					<td nowrap='true' id="severity-${node[3]}" py:content="node[2]"></td>
					<td nowrap='true' py:content="diff_time(int(node[4]))"></td>
					<?python
						try:
							int(node[5])
							val = True
						except:
							val = False
					?>
					<!-- NOTE: only one of the next two columns will be displayed. -->
					<td py:if="val"><a href="${zabbix_event_ack_link(node[5])}">Provide Ack</a></td>
					<td py:if="not val" py:content="node[5]">Message from user</td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
