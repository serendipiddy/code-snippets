/**
  * Phantom.js script, requires phantomjs to be installed.
  *   script to log in to my university wifi network
  *   avoids losing all my wonderful open tabs when connecting to the uni network
  */



casper = require('casper').create({});

casper.echo('Connecting to wireless.vuw');

casper.start('https://wireless.victoria.ac.nz/fs/customwebauth/login.html', function() {
	
	this.evaluate(function(username, password) {
		document.getElementById('username').value = username;
		document.getElementById('password').value = password;
	}, 'username', 'password');

});


casper.then(function() {
	this.evaluate(function() {
		SubmitStudentAction();
	});
});

casper.echo('Logged in');

/* Captures image to show successful login */
// casper.then(function() {
	// this.capture('img.png', {top: 0, left: 0, width:0, height:0});
// });

casper.run(function() {
	this.exit();
});