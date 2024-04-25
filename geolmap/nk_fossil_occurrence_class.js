var __occurrence__sequence = 0;

class nk_fossil_occurrence_cluster {
    constructor() {
        this.occurrence_hash = {};
    }
    add_occurrence(a_occ){

    } 
}
// First, checks if it isn't implemented yet.
if (!String.prototype.format) {
    String.prototype.format = function() {
      var args = arguments;
      return this.replace(/{(\d+)}/g, function(match, number) { 
        return typeof args[number] != 'undefined'
          ? args[number]
          : match
        ;
      });
    };
 }



class nk_fossil_location {
    constructor(id,latitude, longitude) {
        this.id = id;
        this.location_key = latitude + '_' + longitude;
        this.latitude = latitude;
        this.longitude = longitude;
        this.occurrence_data = {};
        this.occurrence_list = [];
        this.occurrence_data_hash = {};
        this.age_formation_species_hash = {}
        //this.finid_list = [];
        this.display_hash = {};
        this.display_row = 0;
        this.visible = true;
        this.position  = new kakao.maps.LatLng(this.latitude, this.longitude);

        var imageSrc_t = 'trilobite_icon_tiny.png', // 마커이미지의 주소입니다    
        imageSize_t = new kakao.maps.Size(32, 32), // 마커이미지의 크기입니다
        imageOption_t = {offset: new kakao.maps.Point(20, 32)}; // 마커이미지의 옵션입니다. 마커의 좌표와 일치시킬 이미지 안에서의 좌표를 설정합니다.
        var markerImage_t = new kakao.maps.MarkerImage(imageSrc_t, imageSize_t, imageOption_t);

        var imageSrc_b = 'brachiopod_icon_white_tiny.png', // 마커이미지의 주소입니다    
        imageSize_b = new kakao.maps.Size(32, 26), // 마커이미지의 크기입니다
        imageOption_b = {offset: new kakao.maps.Point(16, 26)}; // 마커이미지의 옵션입니다. 마커의 좌표와 일치시킬 이미지 안에서의 좌표를 설정합니다.
        var markerImage_b = new kakao.maps.MarkerImage(imageSrc_b, imageSize_b, imageOption_b);


        this.marker_instance = new kakao.maps.Marker({position: this.position});
        this.custom_overlay_instance = new kakao.maps.CustomOverlay({position: this.position, xAnchor:0.5,yAnchor:3.5});
        //this.custom_overlay_instance.setMap()
        this.overlay_instance = new kakao.maps.CustomOverlay({'position': this.position,'marker': this.marker_instance,'content': ''});
        //this.break_point_label = '';
        this.iw_content = '<div style="padding:5px;"></div>';
        this.iw_position = this.position;
        this.infowindow_instance = new kakao.maps.InfoWindow({'position' : this.position, 'content' : this.div_instance, 'removable' : true});
        this.parent = null;
        this.children = [];
        this.cluster_max_show = 5;
        this.map = null;
        this.div_content = '';
        this.sticky = false;
    }
    add_children(a_occ){
        this.children[this.children.length] = a_occ;
        //console.log( "add children:", this.id, a_occ.id, " children count:", this.children.length);
    }
    calculate_distance(a_occ){
        dist = this.distance(this.latitude, this.longitude, a_occ.latitude, a_occ.longitude);
        return dist;
    }
    get_marker(){
        return this.marker_instance;
    }
    set_map(map){
        this.marker_instance.setMap(map);
        this.custom_overlay_instance.setMap(map);
        //console.log(this.custom_overlay_instance);
        this.map = map;
    }
    show_infowindow(){
        //this.infowindow_instance.setContent(this.div_content);
        this.infowindow_instance.open(this.map, this.marker_instance);
        //this.infowindow_instance.setMap(this.map);
        this.custom_overlay_instance.setMap(null);
    }
    hide_infowindow(){
        //this.infowindow_instance.setContent("<div>" + this.id + "</div>");
        this.infowindow_instance.setMap(null);
        this.custom_overlay_instance.setMap(this.map);
    }
    add_occurrence_data(occurrence_data){
        //console.log("add data", this.id, image_name)
        this.occurrence_list[this.occurrence_list.length] = occurrence_data;
    }

    update_content(){
        //console.log("update_content", this.id);

        var total_count = 0;
        var l_occurrence_hash = {}

        for( var idx=0;idx<this.occurrence_list.length;idx++){
        	occurrence_data = this.occurrence_list[idx];
        
        	if( occurrence_data['visible'] == true ){
        	
		        // make formation-species hash
		        var age_code = occurrence_data['strat_range'];
		        var formation_name = occurrence_data['unit_eng'];
		        var species_name = occurrence_data['species'];
		        
		        if( !Object.keys(l_occurrence_hash).includes(age_code) ){
		            l_occurrence_hash[age_code]={};
		        }
		        if( !Object.keys(l_occurrence_hash[age_code]).includes(formation_name) ){
		            l_occurrence_hash[age_code][formation_name]={};
		        }
		        if( !Object.keys(l_occurrence_hash[age_code][formation_name]).includes(species_name) ) {
		            l_occurrence_hash[age_code][formation_name][species_name] = [];
		        }
		        var occ_list = l_occurrence_hash[age_code][formation_name][species_name];
		        occ_list[occ_list.length] = occurrence_data;
		    }
        }
    	//if( this.id == 5 ){console.log(l_occurrence_hash);}
		//console.log("update_content 2");
        var age_list = Object.keys(l_occurrence_hash);
        for( var idx0=0;idx0<age_list.length;idx0++){
            var age_code = age_list[idx0];
            this.display_age_code( age_code );
            var formation_list = Object.keys(l_occurrence_hash[age_code])
            for( var idx1=0;idx1<formation_list.length;idx1++){
                var formation_name = formation_list[idx1];
                this.display_formation_name( formation_name );
                var species_list = Object.keys( l_occurrence_hash[age_code][formation_name] );
                for( var idx2=0;idx2<species_list.length;idx2++){
                    var species_name = species_list[idx2];
                    var occ_count = l_occurrence_hash[age_code][formation_name][species_name].length;
                    this.add_occurrence_display( species_name, occ_count );
                    total_count++;
                }
            }
            if( total_count >= 20 ) { 
                //break;
            }
        }
    }
    
    display_age_code( a_name ) {
        var tn = document.createTextNode("{0}".format(a_name));
        this.div_content.appendChild(tn);
        this.div_content.appendChild(document.createElement('br'));
        this.display_row += 1;
    }
    display_formation_name( a_name ) {
        var tn = document.createTextNode("-{0}".format(a_name));
        this.div_content.appendChild(tn);
        this.div_content.appendChild(document.createElement('br'));
        this.display_row += 1;
    }
    
    toggle_sticky() {
        this.sticky = !this.sticky;
    }
    spread_children() {
        // save for later use
        //console.log("spread children");
        this.toggle_sticky();
    }
    set_visible( visible_true ){
        if( visible_true ) {
            this.set_map(map);
        } else {
            this.set_map(null);
        }
        this.visible = visible_true;
    }
    reset_display(){
        //this.display_hash = {};
        this.div_content = document.createElement('div');
        this.div_content.style.fontSize = '12px';
        this.div_content.style.width = '220px';
        this.div_content.style.height = '20px';
        this.div_content.style.padding = '3px';
        this.display_row = 0;
        this.div_content.appendChild(document.createTextNode('#'+String(this.id)));
        this.div_content.appendChild(document.createElement('br'));
        this.infowindow_instance.setContent(this.div_content);
        //console.log(this.id,"children:", this.children.length);
    }
    add_occurrence_display( a_taxon, a_count ){
        //console.log("add_occurrence_display[" + String(a_taxon)+"]");
        var node1 = document.createTextNode("{0}".format(a_taxon));
        var node2 = document.createTextNode(" ({0})".format(a_count));
        var it = document.createElement('i');
        var a = document.createElement('a');
        a.href = "javascript:show_images('{0}','{1}');".format(this.location_key,a_taxon);
        a.appendChild(it);
        //var img = document.createElement('img');
        //img.src = a_imagename;
        it.appendChild(node1);
        this.div_content.appendChild(document.createTextNode("--"));
        this.div_content.appendChild(a);
        this.div_content.appendChild(node2);
        //this.div_content.appendChild(img);
        this.div_content.appendChild(document.createElement('br'));
        this.display_row += 1;
        var effective_rowcount = this.display_row;
        if( this.display_row >= 20 ) {
            effective_rowcount = 20;
            this.div_content.style.overflow = "auto";
        }
        this.div_content.style.height = String( 17 * (effective_rowcount + 1 )) + 'px';
        
    }
    update_cluster_display(){
        console.log("update cluster display", this.id, this.children.length);
        var local_div = document.createElement("div");
        //console.log("update display 1", this.id, this.children.length, local_div);
        local_div.appendChild(this.div_content);
        //console.log("update display 2", this.id, this.children.length, local_div);
        var max_len = this.children.length;
        if( max_len > this.cluster_max_show ) { max_len = this.cluster_max_show;}
        //local_div.appendChild(document.createTextNode("children"))
        for(idx=0;idx<max_len;idx++){
            local_div.appendChild(this.children[idx].div_content)
        }
        //console.log(local_div)
        if( this.children.length > this.cluster_max_show ) { 
            //console.log(this.id, "children length > 3");
            var more_div = document.createElement("div");
            more_div.style.fontSize = '12px';
            more_div.appendChild(document.createTextNode("...(+" + String( this.children.length-max_len)+")"))
            local_div.appendChild(more_div); 
        }
        //console.log("update display 3", this.id, this.children.length, this.div_content, local_div);
        //console.log("update cluster display:", this.infowindow_instance.getContent(), local_div);
        this.infowindow_instance.setContent(local_div);
        //console.log("update cluster display:", this.infowindow_instance.getContent(), local_div);
        //console.log("update display 4", this.id, this.children.length, this.div_content, local_div);
    }
    distance(lat1, lon1, lat2, lon2 ) {
        if ((lat1 == lat2) && (lon1 == lon2)) {
            return 0;
        }
        else {
            var radlat1 = Math.PI * lat1/180;
            var radlat2 = Math.PI * lat2/180;
            var theta = lon1-lon2;
            var radtheta = Math.PI * theta/180;
            var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
            if (dist > 1) {
                dist = 1;
            }
            dist = Math.acos(dist);
            dist = dist * 180/Math.PI;
            dist = dist * 60 * 1.1515;
            dist = dist * 1.609344;
            return dist;
        }
    }
}