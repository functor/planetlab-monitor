/*
 *  NOTE: requires the Google JSAPI using a key for your domain.
    <script type='text/javascript' src='https://www.google.com/jsapi?key=KEY-GOES-HERE'></script>
 */
google.load('visualization', '1', {'packages':['annotatedtimeline']});
google.load("jquery", "1");

function getData2() {
    // To see the data that this visualization uses, browse to
    var link = 'http://spreadsheets.google.com/tq?key=0AubvfWUvLDrpdGs2eGdwNndDUEZSV2hfNFprTkQxUkE&hl=en&authkey=CO3y2JoO&sheet=NodeHistory';
    var query = new google.visualization.Query(link);
    
    // Apply query language.
    //console.log("run select");
    query.setQuery('SELECT A,B+E,I,J,G+H,K,L');
    // Send the query with a callback function.
    query.send(handleQueryResponse);
}
function handleQueryResponse(response) {
    if (response.isError()) {
        alert('Error in query: ' + response.getMessage() + ' ' + response.getDetailedMessage());
        return;
    }
    var data = response.getDataTable();
    //console.log("loaded data");
    //console.log(data);
    if ( data ) {
        drawChart2(data);
    }
}
function drawChart2(data) {
      //data.insertColumn(2, "string", "title1");
      //data.insertColumn(3, "string", "text1");
      //data.insertColumn(5, "string", "title1");
      //data.insertColumn(6, "string", "text1");
      data.setColumnLabel(1, "Production Nodes");
      data.setColumnLabel(4, "Failing Nodes");
      console.log(data);
      var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('chart_div'));
      var st = new Date();
      st.setDate(st.getDate()-60);
      chart.draw(data, {displayAnnotations: true, zoomStartTime: st, zoomEndTime: new Date()});
}
