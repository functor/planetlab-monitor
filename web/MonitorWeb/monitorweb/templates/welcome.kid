<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
from links import *
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to MyOps</title>
</head>
<body>

  <div id="sidebar">
    <h2>Learn more</h2>
    Learn more about MyOps default policies, and take part in its development
    <ul class="links">
    <!--
      <li><a href="https://svn.planet-lab.org/wiki/MyOpsDocs">Documentation</a></li>
      <li><a href="https://svn.planet-lab.org/wiki/MyOpsPolicyForPlanetLab">Policy</a></li>
      <li><a href="https://svn.planet-lab.org/svn/MyOps">Latest Source</a></li>
    -->
      <li><a href="http://svn.planet-lab.org/svn/Monitor">Latest Source</a></li>
    </ul>
    <span py:replace="now">now</span>
  </div>
  <div id="getting_started">
    <ol id="getting_started_steps">
      <li class="getting_started">
        <h3>Sites</h3>
        <p> All monitored sites : <a href="site">Sites</a> <br/> </p>
      </li>
      <li class="getting_started">
        <h3>PCUs</h3>
        <p> All PCUs : <a href="pcu">PCUs</a> <br/> </p>
      </li>
      <li class="getting_started">
        <h3>Nodes</h3>
        <p> All nodes: <a href="node">Nodes</a> <br/> </p>
      </li>
    </ol>
	<p>If you'd like to track things a little more informally, you can install
	these Google Gadgets for summaries of the entire system or a specific
	site.</p>
    <ul class="links">
      <li><a href="http://fusion.google.com/add?source=atgs&amp;moduleurl=${plc_myops_uri()}/monitor/gadget.xml">MyOps Summary</a></li>
      <li><a href="http://fusion.google.com/add?source=atgs&amp;moduleurl=${plc_myops_uri()}/monitor/sitemonitor.xml">Site Summary</a></li>
    </ul>
  </div>
  <!-- End of getting_started -->
</body>
</html>
