function authenticate(){
    var apiKey = document.getElementById("apiKeyInput").value;
    get(LOGIN_URL, {
        apiKey: apiKey
    },
    function(response){
        if (!response){
            document.getElementById("loginHelpText").innerHTML = "Server issues";
        }
        else if(!response.status){
            document.getElementById("loginHelpText").innerHTML = "Invalid API key";
        }
        else {
            localStorage.setItem(CHATID, response.chat_id);
            localStorage.setItem(APIKEY, response.api_key);
            setVisibility("login", false);
            setVisibility("loggedIn", true);
        }
    });
};

document.getElementById("loginButton").addEventListener("click", authenticate);

document.addEventListener("DOMContentLoaded", function(){
    if (localStorage.getItem(CHATID)){
        setVisibility("loggedIn", true);
    }
    else {
        setVisibility("login", true);
    }
});
