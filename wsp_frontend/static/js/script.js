/* Author:
    Sascha Grabsch
    grabsch@bbaw.de
*/



$("#search-results li").click(function() {
  //alert("Handler for .click() called.");
  //  $(".fragments", this).clone().appendTo("#results-info");
});

/*
$("#search-results li").hover(
    function() {
    $(".fragments", this).clone().appendTo(".results-info");
    },
   function() {
       $('.results-info .fragments').remove();
   }
);
*/
/*
$("#search-results li").mouseover(function() {
    $(".fragments").toggle();
    });
*/

$(".previewLink").colorbox({iframe:true, width:"500px", innerHeight:"550px"});    

 window.onload = function () {
 console.log("Running Raphael...")
 var r = Raphael("projekte_stat");
 data = [7763, 5052, 1708, 920, 712];
 projekte = ["Sekundärliteraturdatenbank zu Alexander von Humboldt", "Inscriptiones Graecae", "Registres de l'Academie", "Deutsches Textarchiv", "Die unselbständigen Schriften Alexander von Humboldts"];
 r.hbarchart(0, 0, 300, 190, data, { stacked: false });
 console.log(r);
 console.log("Done.");

 r = null;
 
 console.log("Running Raphael...");
 var r = Raphael("autoren_stat");
 console.log(r);
 autoren_data = [1019, 293, 165, 108, 81];
 autoren = ["Humboldt, Alexander von", "Biermann, Kurt-Reinhard", "Schwarz, Ingo", "Beck, Hanno", "Ette, Ottmar"];
 r.hbarchart(0, 0, 300, 190, autoren_data, { stacked: false });
 console.log(r);
 console.log("Done.")
 //alert("Test");
 };