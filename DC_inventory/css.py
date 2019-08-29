CSS = """
<!--Thanks to www.racktables.org-->
<style>
th.rack {
        font: bold 12px Verdana, sans-serif;
}

.rack {
        font: bold 12px Verdana, sans-serif;
        border: 1px solid black;
        border-top: 0px solid black;
        border-right: 0px solid black;
        padding-right: 15px;
        text-align: center;
        float:left;
}

.rack th {
        border-top: 2px solid black;
        border-right: 2px solid black;
        background-color: #999999;
}

.rack td {
        border-top: 1px solid black;
        border-right: 1px solid black;
  max-width: 100px;
  overflow: hidden;
  white-space: nowrap;
}

.rack a {




        font: bold 10px Verdana, sans-serif;
        color: #000;
        text-decoration: none;
}

.rack a:hover {
        text-decoration: underline;
}

.rackspace {
}

.rackspace img {
        border: 0;
        display: inline;
        margin: 0;
        padding: 0;
}

.rackspace h2 {
        font: bold 25px Verdana, sans-serif;
}

.rackspace h3 {
        font: bold 20px Verdana, sans-serif;
}

.rackspace a {
        color: #000;
        text-decoration: none;
}

.rackspace a:hover {
        color: #000;
        text-decoration: underline;
}


/*common rack item attributes*/
.atom {
        text-align: center;
        font: bold 10px Verdana, sans-serif;
}
.state_F   { background-color: #8fbfbf; }
.state_A   { background-color: #bfbfbf; }
.state_U   { background-color: #bf8f8f; }
.state_T   { background-color: #408080; }
.state_Th  { background-color: #80ffff; }
.state_Tw  { background-color: #804040; }
.state_Thw { background-color: #ff8080; }
.state_Thw { background-color: #ff8080; }

/* highlighting for drag selection */
.atom.ui-selecting {
        background-color: #E2D087 !important;
}

/* link with single image as body */
a.img-link {
        vertical-align: bottom;
}

/* text label with rackcode (object-rackspace tab) */
.filter-text {
        font-family: "Courier New",Courier,monospace;
}

/* taken from: https://www.w3schools.com/howto/howto_js_filter_table.asp */
* {
  box-sizing: border-box;
}

#filterInput {
  background-position: 10px 10px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

#filterTable {
  border-collapse: collapse;
  width: 100%;
  border: 1px solid #ddd;
  font-size: 18px;
}

#filterTable th, #filterTable td {
  text-align: left;
  padding: 12px;
  word-wrap: break-word;         /* All browsers since IE 5.5+ */
  overflow-wrap: break-word;
}

#filterTable tr {
  border-bottom: 1px solid #ddd;
}

#filterTable tr.header, #filterTable tr:hover {
  background-color: #f1f1f1;
}

.storage {
  font-family: arial, sans-serif;
  border: 1px solid #dddddd;
}

.storage th {
  text-align: left;
  padding: 8px;
  border: 1px solid #000000;
}
#editServer {
  position: fixed;
  top: 70px;
  left: 2%;
  width: 18%;
  height: 100%;
  background-color: #EEEEEF;
}
#links {
  top: 5px;
  float: right;
  right: 0;
  height: auto%;
  background-color: #AAAAAA;
  padding: 5px;
  padding-right: 20px;
}
#updateDiv {
  position: fixed;
  top: 30px;
  left: 30px;
  width: 65px;
  height: auto%;
  background-color: #999999;
  padding: 5px;
}
#updateIPMI {
  position: fixed;
  left: 25%;
  width: 120px;
  height: auto%;
  background-color: #9999ff;
  padding: 5px;
}
#ipmiDiv {
  position: fixed;
  top: 30px;
  left: 95px;
  width: 50px;
  height: auto%;
  background-color: #9999FF;
  padding: 5px;
}
#deleteDiv {
  position: fixed;
  top: 30px;
  left: 140px;
  width: 62px;
  height: auto%;
  background-color: #FF1111;
  padding: 5px;
}
#colorDiv {
  position: fixed;
  top: 30px;
  left: 202px;
  width: 121px;
  height: auto%;
  background-image: linear-gradient(to right, green, yellow, orange,red);
  padding: 5px;
}
.tooltip {
  display: inline-block;
  border-bottom: 1px dotted black;
  color: black;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: auto;
  background-color: black;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 5px 0;

  /* Position the tooltip */
  position: absolute;
  z-index: 1;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
}

.blinking{
    animation:blinkingText 0.8s infinite;
}
@keyframes blinkingText{
    0%{     color: #000;    }
    50%{    color: red; }
    100%{   color: #000;    }
}
/* The Legend (background) */
.legend {
  display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  padding-top: 100px; /* Location of the box */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0,0,0); /* Fallback color */
  background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
}
}
/* Legend Content */
.legend-content {
  background-color: #fefefe;
  margin: auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
}

.ipmiPopup {
  display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1; /* Sit on top */
  padding-top: 100px; /* Location of the box */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0,0,0); /* Fallback color */
  background-color: rgba(0,0,0,0.4); /* Black w/ opacity */
}

/* Legend Content */
.ipmi-content {
  background-color: #fefefe;
  margin: auto;
  padding: 20px;
  border: 5px solid #333333;
  width: 50%;
  height: 70%;
}
/* The Close Button */
.close {
  color: #aaaaaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
}

.close:hover,
.close:focus {
  color: #000;
  text-decoration: none;
  cursor: pointer;
}

.grid-container {
  display: grid;
  grid-template-columns: auto auto auto;
  background-color: #2196F3;
  padding: 10px;
}

.grid-item {
  background-color: rgba(255, 255, 255, 0.8);
  padding: 20px;
  font: bold 20px Verdana, sans-serif;
  border: 2px solid black;
  border-bottom: 0px;
  text-align: center;
  float:center;
}

.dropbtn {
  background-color: #4CAF50;
  color: white;
  padding: 16px;
  font-size: 16px;
  border-color: #4AAA40;
}

.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-content {
  display: none;
  position: absolute;
  background-color: #f1f1f1;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
  z-index: 1;
}

.dropdown-content a {
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
}

.dropdown-content a:hover {background-color: #ddd;}

.dropdown:hover .dropdown-content {display: block;}

.dropdown:hover .dropbtn {background-color: #3e8e41;}

</style>
"""
