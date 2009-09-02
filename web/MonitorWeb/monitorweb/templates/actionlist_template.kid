<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
from monitor.util import diff_time
from time import mktime
from links import *
?>
<span xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">
	<h4>Actions Over the Last ${since} Days</h4>
		<p py:if="actions and len(actions) == 0">
			There are no recent actions taken for this site.
		</p>
		<table py:if="actions and len(actions) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>At</th>
					<th>MyOps acted on</th>
					<th>Using</th>
					<th>Message/Log</th>
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
					<td py:content="act.action_type"></td>

					<td>
						<span py:if="act.message_id != 0">
							<a class="ext-link" href="${plc_mail_uri(act.message_id)}">
							<span  class="icon">${act.message_id}</span></a>
						</span>
						<span py:if="act.message_id == 0 and act.log_path is not None">
							<a class="ext-link" href="/monitorlog/${act.log_path}">
							<span  class="icon">orig bm log</span></a>
						</span>
					</td>
					<!--td py:if="'bootmanager' in act.action_type or 'unknown' in act.action_type">
						<a href="/monitorlog/bm.${act.hostname}.log">latest bm log</a>
					</td-->

					<td py:if="act.error_string">
						<div id="links">
						<a class="info" href="#">Stack Trace<span>
							<pre>${act.error_string}</pre>
						</span>
						</a>
						</div>
					</td>
				</tr>
			</tbody>
		</table>
</span>
