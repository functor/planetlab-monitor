<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns:py="http://purl.org/kid/ns#">
  <head>
    <title>App Name - ${page_title}</title>
    <link href="static/css/style.css" type="text/css" rel="stylesheet" />
    <script type="text/javascript" src="${tg.tg_js}/MochiKit.js"></script>
    <script type="text/javascript" src="static/javascript/sortable_tables.js"></script>

  </head>

  <body>
    <div id="header">Monitor : ${page_title}</div>
  	<table valign="top" border="1" bgcolor="white" align="center" width="700px">
	<tr>
		<td>
			<table id="nps-table" width="100%">
			<thead>
			<tr>
				<th><a href="${tg.url('node')}">Nodes</a></th>
				<th><a href="${tg.url('pcu')}">PCUs</a></th>
				<th><a href="${tg.url('site')}">Sites</a></th>
				<th><a href="${tg.url('action')}">Actions</a></th>
			</tr>
			</thead>
			<tbody>
			<tr>
				<td colspan="4">
    				<content>Default content - this will be replaced by an element marked with 
					py:match="item.tag == 'content'"</content>
				</td>
			</tr>
			</tbody>
			</table>
		</td>
	</tr>
  	</table>

    <div id="footer">Copywrite © 2007-2008 The Trustees of Princeton University</div>
  </body>
</html>
