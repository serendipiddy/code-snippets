/** 
 * Playing with Metlink buses 
 *   for use on any page with a map 
 *   https://www.metlink.org.nz
 */

/* Displays the locations of the buses on given route */
function getBuses(route) { 
  selectedRoute = route; 
  refreshVehicleRealTime();
}

/* Displays the locations of all buses in array */
function getBusesList(routes) {
  // needs to modify refreshVehicleRealTime();
}

function refreshVehicleRealTimeMany(){

	if(!selectedRoute){ return; }
	
	ajaxcallrunning = 1;
	
	$('form[name="changeVehicleLocate"] input.btn').attr('value','Refreshing..');
	$('form[name="changeVehicleLocate"] input.btn').prop("disabled", true);
	
	// remove error message
	$("#VehicleRouteID .text-danger").remove();
		
	$.get('/api/VehicleLocationRequestJson', {route: selectedRoute}, function(data) {
		if(!data[0]){
			$("#VehicleRouteID").append("<p class='text-danger'>There were no vehicles found.</p>");
			hideAllVehicleMarkers();
		}else{
			hideAllVehicleMarkers();
			addVehicleLocations(data);
		}
	}, "json" )
	.always(function() {
		ajaxcallrunning = 0;
		$('form[name="changeVehicleLocate"] input.btn').attr('value','Go');
		$('form[name="changeVehicleLocate"] input.btn').prop("disabled", false);
	});	
	
	if(document.hasFocus() || mapExpanded){
		add_vehicle_refresh(locationRefreshRate);
	}

	locationLastRefresh = Date.now();
}