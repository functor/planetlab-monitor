<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns:py="http://purl.org/kid/ns#">
  <head>
    <title>App Name - ${page_title}</title>
    <link href="/static/css/style.css" type="text/css" rel="stylesheet" />
  </head>

  <body>
    <h1>Monitor : ${page_title}</h1>
  	<table valign="top" border="1" bgcolor="white" align="center" width="800">
	<tr>
		<td>
			<table>
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

    <div class="footer">Copywrite XYZ</div>
  </body>
</html>
