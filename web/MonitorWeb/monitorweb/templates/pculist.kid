<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor PCU List"
from pcucontrol.reboot import pcu_name, model_to_object
from monitor import config
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">



  <script type="text/javascript">
    function pculist_paginator(opts) { plekit_table_paginator(opts, "pculist"); }
  </script>

<table id="pculist" cellpadding="0" border="0" class="plekit_table sortable-onload-0 colstyle-alt no-arrow paginationcallback-pculist_paginator max-pages-10 paginate-25">
  <thead>

    <tr class='pagesize_area'><td class='pagesize_area' colspan='5'>
        <form class='pagesize' action='satisfy_xhtml_validator'><fieldset>
            <input class='pagesize_input' type='text' id="pculist_pagesize" value='25'
                   onkeyup='plekit_pagesize_set("pculist","pculist_pagesize", 25);' 
                   size='3' maxlength='3' />                                                          
            <label class='pagesize_label'> items/page </label>                                     
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset visible size"           
                 onmousedown='plekit_pagesize_reset("pculist","pculist_pagesize", 999);' />
    </fieldset></form></td></tr>                                                                        
    
    <tr class='search_area'><td class='search_area' colspan='5'>
        <div class='search'><fieldset>
            <label class='search_label'> Search </label>                 
            <input class='search_input' type='text' id='pculist_search' 
                   onkeyup='plekit_table_filter("pculist","pculist_search","pculist_search_and");'
                   size='self.search_width' maxlength='256' />                                            
            <label>and</label>                                                                        
            <input id='pculist_search_and' class='search_and'                                        
                   type='checkbox' checked='checked'                                                      
                   onchange='plekit_table_filter("pculist","pculist_search","pculist_search_and");' />
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset search"
                 onmousedown='plekit_table_filter_reset("pculist","pculist_search","pculist_search_and");' />
    </fieldset></div></td></tr>
    
    <tr>
      <th class="sortable plekit_table">Site</th>        
      <th class="sortable plekit_table">PCU Name</th>         
      <th class="sortable plekit_table">Port Status</th>    
      <th class="sortable plekit_table">Test Results</th>      
      <th class="sortable plekit_table">Model</th>
      <th class="sortable plekit_table">Nodes</th>
    </tr>
  </thead>
  <tbody>
    <tr py:for="i,node in enumerate(query)">
      <td nowrap='true'>
	<div class='oneline'>
	  <a class='left' href="${link('pcuview', loginbase=node.loginbase)}">${node.loginbase}</a>
	  <a class='right' href="${plc_site_uri(node.loginbase)}">
	    <img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
	</div>
      </td>
      <td nowrap='true'>
	<div class='oneline'>
	  <a class='left' href="${link('pcuview', pcuid=node.plc_pcuid)}">${pcu_name(node.plc_pcu_stats)}</a>
	  <a class='right' href="${plc_pcu_uri_id(node.plc_pcu_stats['pcu_id'])}">
	    <img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
	</div>
      </td>
      <td nowrap='true'>
	<span py:for="port,state in node.ports" 
	      id="port${state}" py:content="'%s, ' % port">80</span>
      </td>
      <td width="20%" nowrap='true' align='center' id="status-${node.status}">
	<div id="links">
	  <a class="info" py:if="'error' in node.status" 
	     href="${link('pcuview', pcuid=node.plc_pcuid)}">
	    Error<span><pre>${node.reboot_trial_status}</pre></span></a>
	  <a py:if="'error' not in node.status" 
	     href="${link('pcuview', pcuid=node.plc_pcuid)}"
	     py:content="node.status">Reboot Status</a>
	</div>
      </td>
      <td py:content="node.plc_pcu_stats['model']"></td>
      <td py:content="len(node.plc_pcu_stats['node_ids'])"></td>
    </tr>
  </tbody>  
</table>
  </div>

</html>
