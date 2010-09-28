<?php
if (isset($_REQUEST['node_id'])) {
    # setup the same random times for each distinct node_id by seeding rand()
    $node_id = intval($_REQUEST['node_id']);
    srand($node_id);
}
$m = rand(0,59);
$h = rand(0,23);
echo "# random time on first day of week upload bash logs to monitor\n";
echo "$m $h * * 0,3,5 root /usr/bin/collect_snoopylog.sh\n";
?>
