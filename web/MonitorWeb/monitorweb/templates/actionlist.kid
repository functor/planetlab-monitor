<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Action List"
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
				<th><a href="${link('actionlist', action_type='online_notice', since=1)}">Last Day</a></th>
				<th><a href="${link('actionlist', action_type='online_notice', since=7)}">Last Week</a></th>
				<th><a href="${link('actionlist', action_type='online_notice', since=30)}">Last Month</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
	<h4>Actions Over the Last ${since} Days</h4>
		<p py:if="actions and len(actions) == 0">
			There are no recent actions taken for this site.
		</p>
		<table py:if="actions and len(actions) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Date</th>
					<th>Action taken on</th>
					<th>Action Type</th>
					<th>Message ID</th>
					<th>Errors</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,act in enumerate(actions)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td py:content="act.date_created"></td>
					<td py:if="act.hostname is not None" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri(act.hostname)}">
							<span class="icon">${act.hostname}</span></a>
					</td>
					<td py:if="act.hostname is None" nowrap="true">
						<a class="ext-link" href="${plc_site_uri(act.loginbase)}">
							<span class="icon">${act.loginbase}</span></a>
					</td>
					<!--td py : content="diff_time(mktime(node.date_checked.timetuple()))"></td-->
					<td py:content="act.action_type"></td>
					<td><a class="ext-link" href="${plc_mail_uri(act.message_id)}">
							<span py:if="act.message_id != 0" class="icon">${act.message_id}</span></a></td>
					<td py:if="'bootmanager' in act.action_type or 'unknown' in act.action_type">
						<a href="/monitorlog/bm.${act.hostname}.log">latest bm log</a>
					</td>
					<td py:if="'bootmanager' not in act.action_type">
						<pre py:content="act.error_string"></pre></td>
				</tr>
			</tbody>
		</table>

		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
