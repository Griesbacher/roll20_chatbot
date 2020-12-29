// ==UserScript==
// @name         Roll20 Chat Connector
// @namespace    https://github.com/Griesbacher/roll20_chatbot
// @version      0.1
// @description  Connects the Roll20 chat to a WebSocket
// @author       Philip Griesbacher
// @match        https://app.roll20.net/*
// @updateURL    https://raw.githubusercontent.com/Griesbacher/roll20_chat_bot/master/chat_connector.js
// @downloadURL  https://raw.githubusercontent.com/Griesbacher/roll20_chat_bot/master/chat_connector.js
// ==/UserScript==
(function() {
    'use strict';

    const webSocketAdress = "ws://localhost:5678" // CHANGE ME?!

    const targetNode = document.getElementById('textchat');
    var webSocket;
    function connectToBackend(){
        console.log("connecting...");
        webSocket = new WebSocket(webSocketAdress)
        webSocket.onopen = function(event) {
            alert("ChatBot connected");
        };
        webSocket.onmessage = function (event) {
            console.log("<",event.data);
            var textArea;
            Array.from(document.getElementsByClassName("ui-autocomplete-input")).forEach(
                function(element, index, array) {
                    if (element.nodeName === "TEXTAREA") {
                        element.value = event.data;;
                    }
                }
            );
            Array.from(document.getElementsByClassName("btn")).forEach(
                function(element, index, array) {
                    if (element.innerText === "Send") {
                        element.click();
                    }
                }
            );
        }
        webSocket.onclose = function(event) {
            console.log(`[close] Connection closed code=${event.code} reason=${event.reason} clean=${event.wasClean}`);
            setTimeout(connectToBackend, 5000);
        };
    }
    connectToBackend();

    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            console.log(mutation);
            if (webSocket.readyState === WebSocket.OPEN){
                mutation.addedNodes.forEach(node => webSocket.send(JSON.stringify({type:"chat", data:node.outerHTML})));
            }
        });
    });

    observer.observe(targetNode, {
        childList: true, subtree: true
    });
})();