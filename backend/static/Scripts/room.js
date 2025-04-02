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

document.getElementById('block-user').addEventListener('click', function() {
    const button = this;
    const roomName = document.querySelector('[data-room-name]').getAttribute('data-room-name');
    const userName = document.querySelector('[data-user-name]').getAttribute('data-user-name');
    
    // Correction de l'extraction du nom de l'autre utilisateur
    console.log('Current user:', userName);
    console.log('Room name:', roomName);
    
    // const otherUser = roomName.split('-').map(part => part.trim())
    //                          .find(part => part !== userName);

    const otherUser = roomName;
    
    console.log('Other user:', otherUser);

    fetch('/chat/api/block-user/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            blocked_user: otherUser
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            button.textContent = button.textContent === 'Bloquer' ? 'Débloquer' : 'Bloquer';
            button.classList.toggle('blocked');
            document.getElementById('chat-message-input').disabled = button.textContent === 'Débloquer';
            document.getElementById('chat-message-submit').disabled = button.textContent === 'Débloquer';
        } else {
            console.error('Block request failed:', data.message);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
});

// Fonction utilitaire pour obtenir le cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

connectWebSocket();
