<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Summary"
from monitor.util import diff_time
from monitor import config
from time import mktime
from links import *
?>
<html 
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <?python orig=True ?>
  	<table>
		<tbody>
  		<span py:for="primarykey in ['sites', 'nodes', 'pcus']">
			<tr>
    			<td width="50" rowspan="2">${primarykey.capitalize()}</td>
				<span py:for="i,key in enumerate(setorder + [s for s in set(sumdata[primarykey].keys())-set(setorder)]) ">
					<th valign="top" py:if="orig and i&lt;4" py:content="key.capitalize()"></th>
					<th valign="top" py:if="orig and i&gt;3" py:content="key.capitalize()"></th>
					<th valign="top" py:if="not orig and i&gt;3" py:content="key.capitalize()"></th>
					<th valign="top" py:if="not orig and i&lt;4" py:content=""></th>
				</span>
			</tr>
			<?python orig=False ?>
			<tr>
				<span py:for="key in setorder + [s for s in set(sumdata[primarykey].keys())-set(setorder)]">
					<td bgcolor="lightgrey" valign="top" align="center">
						<a target="_blank" href="${link(plc_myops_uri() + '/monitor/node2', filter=key)}" py:if="primarykey == 'nodes'" py:content="sumdata[primarykey][key]"></a>
						<div py:if="primarykey != 'nodes' and key in sumdata[primarykey]" py:content="sumdata[primarykey][key]"></div>
						</td>
				</span>
			</tr>
  		</span>
		</tbody>
	</table>
<div py:match="item.tag == 'content'">
</div>

</html>
