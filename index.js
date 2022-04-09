async function get() {
  let url = "./api/v1/last_update.json";
  let obj = await (await fetch(url)).json();
  return obj;
}

var tags;
(async () => {
  tags = await get();
  last_update = new Date(tags.last_update);
  document.getElementById("last-update").innerHTML = last_update.toLocaleString();
  setInterval(function() {
    // Get today's date and time
    var now = new Date().getTime();
    var next_update = new Date(last_update);
    next_update.setHours(next_update.getHours() + 12);

    // Find the distance between now and the count down date
    var distance = next_update - now;

    if (distance > 0) {
      // Time calculations for days, hours, minutes and seconds
      var days = Math.floor(distance / (1000 * 60 * 60 * 24));
      var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((distance % (1000 * 60)) / 1000);

      // Display the result in the element with id="demo"
      document.getElementById("next-update").innerHTML = hours + "h " + minutes + "m " + seconds + "s ";
    } else {
      document.getElementById("next-update").innerHTML = "now";
    }
  }, 100);
})()