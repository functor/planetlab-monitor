<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Node Scan History"
from monitor.util import diff_time
from time import mktime
from links import *
from cherrypy import request, response

?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

<div py:match="item.tag == 'content'">

  <script type="text/javascript">
    function nodelist_paginator(opts) { plekit_table_paginator(opts, "nodelist"); }
  </script>
  	<table width="100%">
		<thead>
			<tr>
				<th><a href="${link('nodescanhistory', length=42, **params)}">Last Week</a></th>
				<th><a href="${link('nodescanhistory', length=180, **params)}">Last Month</a></th>
				<th><a href="${link('nodescanhistory', length=1000, **params)}">Last 1000</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">

<table id="nodelist" cellpadding="0" border="0" class="plekit_table sortable-onload-2 colstyle-alt no-arrow paginationcallback-nodelist_paginator max-pages-10 paginate-999">
  <thead>
    <tr class='pagesize_area'><td class='pagesize_area' colspan='10'>
        <form class='pagesize' action='satisfy_xhtml_validator'><fieldset>
            <input class='pagesize_input' type='text' id="nodelist_pagesize" value='25'
                   onkeyup='plekit_pagesize_set("nodelist","nodelist_pagesize", 25);' 
                   size='3' maxlength='3' />                                                          
            <label class='pagesize_label'> items/page </label>                                     
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset visible size"           
                 onmousedown='plekit_pagesize_reset("nodelist","nodelist_pagesize", 999);' />
    </fieldset></form></td></tr>                                                                        
    
    <tr class='search_area'><td class='search_area' colspan='10'>
        <div class='search'><fieldset>
            <label class='search_label'> Refine List </label>                 
            <input class='search_input' type='text' id='nodelist_search' 
                   onkeyup='plekit_table_filter("nodelist","nodelist_search","nodelist_search_and");'
                   size='self.search_width' maxlength='256' />                                            
            <label>and</label>                                                                        
            <input id='nodelist_search_and' class='search_and'                                        
                   type='checkbox' checked='checked'                                                      
                   onchange='plekit_table_filter("nodelist","nodelist_search","nodelist_search_and");' />
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset search"
                 onmousedown='plekit_table_filter_reset("nodelist","nodelist_search","nodelist_search_and");' />
    </fieldset></div></td></tr>
    
    <tr>
      <th nowrap="true" class="sortable plekit_table">Date Checked</th>
      <th class="sortable plekit_table">Hostname</th>
      <th class="sortable plekit_table">Ping</th>
      <th class="sortable plekit_table">SSH</th>
      <th class="sortable plekit_table">Stat</th>
      <th class="sortable plekit_table">kernel</th>
      <th class="sortable plekit_table">BootCD</th>
      <th class="sortable plekit_table">Boot Server</th>
      <th class="sortable plekit_table">Installation Date</th>
      <th class="sortable plekit_table">Last_contact</th>
  </tr>
  </thead>
  <tbody>
    <tr py:for="i,node in enumerate(query)">
	<span py:if="node is not None">
                <td nowrap="true" py:content="node.node.date_checked">date_checked</td>
		<td nowrap="true">
		  <a target="_top" href="${link('pcuview', hostname=node.node.hostname)}" py:content="node.node.hostname">your.host.org</a></td>
                <td py:content="node.node.ping_status">ping</td>
                <td py:content="node.node.ssh_status">ssh</td>
                <td py:content="node.node.plc_node_stats['boot_state']">boot</td>
		<td nowrap="true" py:content="node.kernel"></td>
		<td nowrap="true" py:content="node.node.bootcd_version"></td>
		<td nowrap="true" py:content="node.node.boot_server"></td>
		<td nowrap="true" py:content="node.node.install_date"></td>
		<td  id="node-${node.node.observed_status}" py:content="diff_time(node.node.plc_node_stats['last_contact'])"></td>
	</span>
    </tr>

  </tbody>  
</table>
		</td>
		</tr>
		</tbody>
	</table>

</div>

</html>
