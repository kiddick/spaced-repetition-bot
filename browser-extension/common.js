BASE_URL = "http://localhost:8080/api/";
LOGIN_URL = BASE_URL + "authorize/";
ADD_URL = BASE_URL + "add_term/";

CHATID = "chatId";
APIKEY = "apiKey";
MAX_SELECTION_LENGTH = 25;

function get(url, params, callback){
    var xhr = new XMLHttpRequest();
    var getParams = "?";
    Object.keys(params).forEach(function(key){
        getParams += (key + "=" + encodeURIComponent(params[key]) + "&");
    });
    url += getParams;
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            var response = xhr.responseText? JSON.parse(xhr.responseText): null;
            callback(response);
        }
    }
    xhr.send();
}

function setVisibility(element, visible){
    var value = visible ? "block" : "none";
    document.getElementById(element).style.display = value;
}
