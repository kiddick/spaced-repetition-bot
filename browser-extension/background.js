chrome.contextMenus.onClicked.addListener(function(info, tab){
    if (!localStorage.getItem(APIKEY)){
        alert("Please login first");
        return;
    }
    var term = info.selectionText;
    if (term.length > MAX_SELECTION_LENGTH) {
        alert("Term is too long")
        return;
    }
    get(ADD_URL,
        {
            apiKey: localStorage.getItem(APIKEY),
            term: term
        },
        function(response){
            if (!response || !response.status){
                alert("Error while adding the term");
            }
            else {
                console.log('added');
                // TODO: Convert to notification
            }
        }
    );
});

chrome.runtime.onInstalled.addListener(function() {
    chrome.contextMenus.create({
        "title": "Add this stuff",
        "contexts": ["selection"],
        "id": "selectionContext"
    });
});
