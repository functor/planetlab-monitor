<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns:py="http://purl.org/kid/ns#">
  <head>
    <title>${page_title}</title>
    <link href="static/css/style.css" type="text/css" rel="stylesheet" />
    <script type="text/javascript" src="tg_js/MochiKit.js"></script>

    <script type="text/javascript" src="/plekit/prototype/prototype.js"></script>

    <script type="text/javascript" src="/plekit/tablesort/tablesort.js"></script>
    <script type="text/javascript" src="/plekit/tablesort/customsort.js"></script>
    <script type="text/javascript" src="/plekit/tablesort/paginate.js"></script>
    <script type="text/javascript" src="/plekit/table/table.js"></script>
    <link href="/plekit/table/table.css" rel="stylesheet" type="text/css" />

    <script type="text/javascript" src="/plekit/niftycorner/niftycube.js"></script>
    <script type="text/javascript" src="/plekit/niftycorner/nifty_init.js"></script>
    <script type="text/javascript"> Event.observe(window,"load", nifty_init); </script>


	<!-- If in an iframe, then include this... -->
	<?python from monitor import config ?>
	<base py:if="config.embedded" target="_top" href="https://${config.MONITOR_HOST}/db/monitor/" />

  </head>

  <body>
  	<table valign="top" border="1" bgcolor="white" align="center" width="700px">
	<tr> <td> <div id="header">${page_title}</div> </td> 
		<td>
			<form action="pcuview" method="GET"> 
				<table>
					<tr><td> Quick Search:</td>
						<td><input type="text" name="query"/></td>
						<td><input type="submit"/></td>
					</tr>
				</table>
			</form>
		</td>
	</tr>
	<tr>
		<td colspan="2">
			<table id="nps-table" width="100%">
			<thead>
			<tr>
				<?python from monitorweb.templates.links import link ?>
				<th><a href="${link('site')}">Sites</a></th>
				<th><a href="${link('pcu')}">PCUs</a></th>
				<th><a href="${link('node')}">Nodes</a></th>
				<th><a href="${link('actionsummary')}">Actions</a></th>
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
	<tr> <td> <div id="footer">Copyright © 2007-2008 The Trustees of Princeton University</div> </td> </tr>
  	</table>

  </body>
</html>
