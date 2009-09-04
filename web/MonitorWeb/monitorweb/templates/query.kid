<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Detail View"
from monitor.util import diff_time
from monitor import config
from time import mktime
from pcucontrol.reboot import pcu_name, model_to_object
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  		<h2>Functional, but Under Development...</h2>
		<table>
			<tr>
				<td>${queryform.display(method="GET", value=data)}</td>
			</tr>
		</table>
<h4>Results</h4>
	<table py:if="fields and len(fields.keys()) > 0" id="querylist" cellpadding="0" border="0" class="plekit_table sortable-onload-0 colstyle-alt no-arrow paginationcallback-querylist_paginator max-pages-10 paginate-50" width="100%">
	<thead>
    	<tr class='pagesize_area'><td class='pagesize_area' colspan='5'>
       	 <form class='pagesize' action='satisfy_xhtml_validator'><fieldset>
            <input class='pagesize_input' type='text' id="querylist_pagesize" value='50'
                   onkeyup='plekit_pagesize_set("querylist","querylist_pagesize", 50);' 
                   size='3' maxlength='3' />                                                          
            <label class='pagesize_label'> items/page </label>                                     
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset visible size"           
                 onmousedown='plekit_pagesize_reset("querylist","querylist_pagesize", 999);' />
    	</fieldset></form></td></tr>                                                                        
    	<tr class='search_area'><td class='search_area' colspan='5'>
        <div class='search'><fieldset>
            <label class='search_label'> Search </label>                 
            <input class='search_input' type='text' id='querylist_search' 
                   onkeyup='plekit_table_filter("querylist","querylist_search","querylist_search_and");'
                   size='self.search_width' maxlength='256' />                                            
            <label>and</label>                                                                        
            <input id='querylist_search_and' class='search_and'                                        
                   type='checkbox' checked='checked'                                                      
                   onchange='plekit_table_filter("querylist","querylist_search","querylist_search_and");' />
            <img class='reset' src="/planetlab/icons/clear.png" alt="reset search"
                 onmousedown='plekit_table_filter_reset("querylist","querylist_search","querylist_search_and");' />
    	</fieldset></div></td></tr>
		<!-- for keys show each th -->
		<tr>
			<span py:for="key in sorted(fields.keys())" >
				<span py:if="key == 'uptime'">
					<th class="sortable-numeric plekit_table">${key}</th>
				</span>
				<span py:if="key != 'uptime'">
					<th class="sortable plekit_table">${key}</th>
				</span>
			</span>
		</tr>
	</thead>
	<tbody>
		<!-- for keys show value -->
		<tr py:for="row in query"  >
			<span py:for="key in sorted(fields.keys())" >
				<td>${row[key]}</td>
			</span>
		</tr>
      </tbody>
	</table>
  </div>
</html>
