<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
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
      <li><a href="https://svn.planet-lab.org/wiki/MyOpsDocs">Documentation</a></li>
      <li><a href="https://svn.planet-lab.org/wiki/MyOpsPolicyForPlanetLab">Policy</a></li>
      <li><a href="https://svn.planet-lab.org/svn/MyOps">Latest Source</a></li>
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
    <!--div class="notice"> If you create something cool, please <a href="http://groups.google.com/group/turbogears">let people know</a>, and consider contributing something back to the <a href="http://groups.google.com/group/turbogears">community</a>.</div-->
  </div>
  <!-- End of getting_started -->
</body>
</html>
