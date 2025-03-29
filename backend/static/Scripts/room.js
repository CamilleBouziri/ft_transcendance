const roomName = document.currentScript.getAttribute('data-room-name');
const userName = document.currentScript.getAttribute('data-user-name');
let chatSocket = null;

// Fonction pour scroll en bas
function scrollToBottom() {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Exécuter le scroll au chargement de la page
window.onload = function() {
    scrollToBottom();
};

function connectWebSocket() {
    // const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsScheme = 'wss:';
    const socketUrl = `${wsScheme}//${window.location.host}/ws/chat/${roomName}/`;
    console.log('Connexion à:', socketUrl);
    
    chatSocket = new WebSocket(socketUrl);

    chatSocket.onopen = function(e) {
        console.log('WebSocket connecté');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Message reçu:', data);
        
        const messagesDiv = document.getElementById('messages');
        const messageElement = document.createElement('div');
        
        const isSentByMe = data.user === userName;
        messageElement.className = `message ${isSentByMe ? 'sent' : 'received'}`;
        
        const time = new Date(data.timestamp).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageElement.innerHTML = `
            <strong>${data.user}</strong>${data.message}
            <span class="timestamp">${time}</span>
        `;
        
        messagesDiv.appendChild(messageElement);
        scrollToBottom();
    };

    chatSocket.onclose = function(e) {
        console.log('WebSocket déconnecté');
        setTimeout(connectWebSocket, 1000);
    };
}

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value.trim();
    
    if (message && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.value = '';
    }
};

document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // touche Entrée
        document.querySelector('#chat-message-submit').click();
    }
};

connectWebSocket();
