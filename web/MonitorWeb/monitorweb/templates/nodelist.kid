<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Node List"
from monitor.util import diff_time
from time import mktime
from links import *

?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

<div py:match="item.tag == 'content'">

  <script type="text/javascript">
    function nodelist_paginator(opts) { plekit_table_paginator(opts, "nodelist"); }
  </script>

  <center>
  <b py:content="'BOOT: %d' % len([agg for agg in query if agg.node.observed_status == 'BOOT'])"></b> | 
  <b py:content="'DOWN: %d' % len([agg for agg in query if agg.node.observed_status == 'DOWN'])"></b><br/>
  </center>

<table id="nodelist" cellpadding="0" border="0" class="plekit_table sortable-onload-2 colstyle-alt no-arrow paginationcallback-nodelist_paginator max-pages-10 paginate-25">
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
            <label class='search_label'> Search </label>                 
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
      <th class="sortable plekit_table">ID</th>
      <th class="sortable plekit_table">Hostname</th>
      <th class="sortable plekit_table">Site</th>
      <th class="sortable plekit_table">Ping</th>
      <th class="sortable plekit_table">SSH</th>
      <th class="sortable plekit_table">Stat</th>
      <th class="sortable plekit_table">pcu</th>
      <th class="sortable plekit_table">kernel</th>
      <th class="sortable plekit_table">BootCD</th>
      <th class="sortable plekit_table">Last_contact</th>
  </tr>
  </thead>
  <tbody>
    <tr py:for="i,node in enumerate(query)">
      ${nodewidget.display(node=node, header=None)}
    </tr>

  </tbody>  
</table>

</div>

</html>
