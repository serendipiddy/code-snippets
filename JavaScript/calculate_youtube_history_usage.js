/**
 * Calculates how long you've spent on youtube from 
 *   To use, go to your history page, scroll down to load all the history items you want to add up, and call getVisibleTime()
 *   Paste into web page console, and call functions.
 *  
 *  A limitation is that whether you watched the whole video or not is ignored (just clicking on a link will add it to your history)
 *
 *  TODO: load history items automatically (with a limit?) and calculate with more history items, less manually.
 *  
 *   Would be better to build a script using the Youtube API, but this does what I wanted (recent history)
 * 
 *  A nice addition might be to create a frequency/channel graph, finding the most view channels etc
 */

function getVisibleTime() {
  var count = 0; // number of items
  var time = [0,0,0]; // sum of total hours, mins and seconds
  
  // loop {
  //   take visible history items, sum their total time
  getNext(time, count);
  //   remove the visible items
  //   load the next group of items ('scroll down' or 'hit "load more" button'
  // }
  
  getTotalTime(time, count);
  
}

/* Get the time of the displayed history videos */
function getNext(time, count) {
  var b = document.getElementsByClassName('video-time');
  for (var i = 0; i<b.length; i++) {
    if (b[i].textContent.match('\\d+:\\d+')) {
      count++;
      var t = b[i].textContent.split(':');
      // console.log(time)
      if(t.length === 2) {
        // console.log(t[0]+' '+t[1]);
        time[1] += parseInt(t[0]);
        time[2] += parseInt(t[1]);
      }
      if(t.length === 3) {
        // console.log(t[0]+' '+t[1]+' '+t[2]);
        time[0] += parseInt(t[0]);
        time[1] += parseInt(t[1]); 
        time[2] += parseInt(t[2]);
      }
      // console.log(time);
    }
    // b[i].remove();
  }
}

/** Removes the videos from DOM that have been processed already
  *    not yet complete
  */
function removeChildren(){
  var a = document.getElementById('item-section-055264')
}

/** Given a time array (h,m,s) displays the total time.
  *    Rounds off to hours, 
  *    leaving the remainder of minutes and seconds.
  */
function getTotalTime(time, count) {
  var h = time[0];
  var m = time[1];
  var s = time[2];
  
  m += Math.floor(s/60);
  s =  s % 60;
  h += Math.floor(m/60);
  m =  m % 60;
  
  console.log('total '+h+'h '+m+'m '+s+'s, '+count+' videos');
}
