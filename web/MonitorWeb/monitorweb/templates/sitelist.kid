<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site List"
from monitor.util import diff_time
from time import mktime
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">


  <script type="text/javascript">
    function sitelist_paginator(opts) { plekit_table_paginator(opts, "sitelist"); }
  </script>

<table id="sitelist" cellpadding="0" border="0" class="plekit_table sortable-onload-0 colstyle-alt no-arrow paginationcallback-sitelist_paginator max-pages-10 paginate-25">
  <thead>

    <tr class='pagesize_area'><td class='pagesize_area' colspan='6'>
        <form class='pagesize' action='satisfy_xhtml_validator'><fieldset>
            <input class='pagesize_input' type='text' id="sitelist_pagesize" value='25'
                   onkeyup='plekit_pagesize_set("sitelist","sitelist_pagesize", 25);' 
                   size='3' maxlength='3' />                                                          
            <label class='pagesize_label'> items/page </label>                                     
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset visible size"           
                 onmousedown='plekit_pagesize_reset("sitelist","sitelist_pagesize", 999);' />
    </fieldset></form></td></tr>                                                                        
    
    <tr class='search_area'><td class='search_area' colspan='6'>
        <div class='search'><fieldset>
            <label class='search_label'> Search </label>                 
            <input class='search_input' type='text' id='sitelist_search' 
                   onkeyup='plekit_table_filter("sitelist","sitelist_search","sitelist_search_and");'
                   size='self.search_width' maxlength='256' />                                            
            <label>and</label>                                                                        
            <input id='sitelist_search_and' class='search_and'                                        
                   type='checkbox' checked='checked'                                                      
                   onchange='plekit_table_filter("sitelist","sitelist_search","sitelist_search_and");' />
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset search"
                 onmousedown='plekit_table_filter_reset("sitelist","sitelist_search","sitelist_search_and");' />
    </fieldset></div></td></tr>
    
    <tr>
      <th class="sortable plekit_table">Site Name</th>        
      <th class="sortable plekit_table">Enabled</th>         
      <th class="sortable plekit_table">Penalty</th>    
      <th class="sortable plekit_table">Slices/Max</th>      
      <th class="sortable plekit_table">Nodes/Total</th>
      <th class="sortable plekit_table">Last Change</th>
    </tr>
  </thead>
  <tbody>
    <tr py:for="i,site in enumerate(query)">
      <td nowrap="true">
	<div class='oneline'>
	  <a class='left' href="${link('pcuview', loginbase=site.loginbase)}">${site.loginbase}</a>
	  <a class='right' href="${plc_site_uri_id(site.plc_siteid)}">
	    <img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
	</div>
      </td>
      <td py:content="site.enabled"></td>
      <td id="site-${site.penalty_level}">${site.penalty_level}</td>
      <td>${site.slices_used}/${site.slices_total}</td>
      <td>${site.nodes_up} / ${site.nodes_total}</td>
      <td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
    </tr>
  </tbody>  
</table>

  </div>

</html>
