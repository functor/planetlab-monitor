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

<img id="toggle-image-visible-query" src="/plekit/icons/toggle-visible.png" style="height:18px;" onclick="plc_toggle('query')" />
<img id="toggle-image-hidden-query" src="/plekit/icons/toggle-hidden.png" style="height:18px;display:none" onclick="plc_toggle('query')" /> <span style="font-size:2em;">Monitor Query</span>

<div id="toggle-area-query">
		<table>
			<tr>
				<td>${queryform.display(method="GET", value=data)}</td>
			</tr>
		</table>
</div>

<h4>Results</h4>
	<table py:if="fields and len(fields.keys()) > 0" id="querylist" cellpadding="0" border="0" class="plekit_table sortable-onload-0 colstyle-alt no-arrow paginationcallback-querylist_paginator max-pages-10 paginate-999" width="100%">
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
                        <th class="plekit_table"> C </th>
		</tr>
	</thead>
	<tbody>
		<!-- for keys show value -->
<?python
num = 0
?>
		<tr py:for="row in query"  >
<?python
values = []
num += 1
checkboxname="checkbox%d" % num
?>
			<span py:for="key in sorted(fields.keys())" >
				<td>${row[key]}</td>
<?python
values.append(str(row[key]))
?>
			</span>
<?python
values = ",".join(values)
?>

                        <td><input type="checkbox" class="clippy_checkbox" name="${checkboxname}" value="${values}" onclick="setup_clippy()"/></td>

		</tr>

<tr>
  <span py:for="key in sorted(fields.keys())" ><td></td></span>
<td>
  <span style="display:none" id="values_box_clippy"></span>
    <object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000"
            width="110"
            height="14"
            id="clippy" >
      <param name="movie" value="static/flash/clippy.swf?v5"/>
      <param name="allowScriptAccess" value="always" />
      <param name="quality" value="high" />
      <param name="scale" value="noscale" />
      <param name="bgcolor" value="#FFFFFF" />
      <param name="FlashVars" value="id=values_box_clippy" />
        <embed src="static/flash/clippy.swf"
               width="110"
               height="14"
               name="clippy"
               quality="high"
               allowScriptAccess="always"
               type="application/x-shockwave-flash"
               pluginspage="http://www.macromedia.com/go/getflashplayer"
               FlashVars="id=values_box_clippy"
               bgcolor="#FFFFFF"
               />
    </object>
</td></tr>
        </tbody>
	</table>
        
<script type="text/javascript">
var lst = $("querylist");
var tbody = lst.getElementsBySelector("tbody")[0];
var trs = tbody.getElementsBySelector("tr");
if (trs.length > 2) {
 plc_toggle("query");
}


function setup_clippy () {
var values = "";
var checkboxes = $$$('.clippy_checkbox').each(function(e){if (e.checked == true) {values += e.value + "\n";} });
$$$('#values_box_clippy').each(function(e){e.innerHTML=values;});
}

</script>

  </div>


</html>
