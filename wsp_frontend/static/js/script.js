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