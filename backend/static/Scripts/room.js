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
        console.log("Message reçu:", data);
        
        // Gérer les messages d'erreur
        if (data.error) {
            const messagesContainer = document.getElementById('messages');
            const errorElement = document.createElement('div');
            errorElement.classList.add('message', 'error');
            errorElement.textContent = data.error;
            messagesContainer.appendChild(errorElement);
            setTimeout(() => errorElement.remove(), 3000); // Disparaît après 3 secondes
            return;
        }
        
        // Référence à la zone d'affichage des messages
        const messagesContainer = document.getElementById('messages');
        
        // Créer l'élément de message approprié selon le type
        let messageElement;
        
        if (data.type === 'game_invite') {
            // Pour les invitations de jeu
            messageElement = document.createElement('div');
            messageElement.classList.add('message');
            
            if (data.sender === userName) {
                messageElement.classList.add('sent');
            } else {
                messageElement.classList.add('received');
            }
            
            // Format du message d'invitation
            messageElement.innerHTML = `
                <strong>${data.sender}</strong>
                <div class="game-invitation">
                    ${data.message}
                    ${data.sender !== userName ? 
                        `<button class="join-game-btn" data-game="${data.game}" data-sender="${data.sender}">
                            Rejoindre la partie
                        </button>` : ''}
                </div>
                <span class="timestamp">${data.timestamp}</span>
            `;
            
            // Ajouter l'événement au bouton si présent
            const joinButton = messageElement.querySelector('.join-game-btn');
            if (joinButton) {
                joinButton.addEventListener('click', function() {
                    const gameType = this.getAttribute('data-game');
                    const creator = this.getAttribute('data-sender');
                    window.location.href = `/game/join/?game=${gameType}&creator=${creator}`;
                });
            }
        } else {
            // Pour les messages texte standard
            messageElement = document.createElement('div');
            messageElement.classList.add('message');
            
            if (data.sender === userName) {
                messageElement.classList.add('sent');
            } else {
                messageElement.classList.add('received');
            }
            
            // Format du message standard
            messageElement.innerHTML = `
                <strong>${data.sender}</strong>${data.message}
                <span class="timestamp">${data.timestamp}</span>
            `;
        }
        
        // Ajouter le message à la conversation
        messagesContainer.appendChild(messageElement);
        
        // Faire défiler vers le bas
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
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

// Modal d'invitation à jouer
const gameInviteModal = document.getElementById('game-invite-modal');
const sendGameInviteBtn = document.getElementById('send-game-invite');
const closeModalBtn = document.querySelector('.close');
const gameChoices = document.querySelectorAll('.game-choice');

// Ouvrir modal au clic sur "Inviter à jouer"
sendGameInviteBtn.addEventListener('click', function() {
    gameInviteModal.style.display = 'block';
});

// Fermer modal au clic sur X
closeModalBtn.addEventListener('click', function() {
    gameInviteModal.style.display = 'none';
});

// Fermer modal si clic en dehors
window.addEventListener('click', function(event) {
    if (event.target == gameInviteModal) {
        gameInviteModal.style.display = 'none';
    }
});

// Envoyer invitation au jeu choisi
gameChoices.forEach(function(button) {
    button.addEventListener('click', function() {
        const gameType = this.getAttribute('data-game');
        
        chatSocket.send(JSON.stringify({
            'type': 'game_invite',
            'game': gameType,
            'message': `Invitation à jouer à ${gameType === 'morpion' ? 'Morpion' : 'Pong'}`
        }));
        
        gameInviteModal.style.display = 'none';
    });
});

// Fonction pour créer un élément de message pour invitation de jeu
function createGameInviteElement(data) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    
    if (data.sender === userName) {
        messageElement.classList.add('sent');
    } else {
        messageElement.classList.add('received');
    }
    
    // En-tête du message avec nom et heure
    const messageHeader = document.createElement('div');
    messageHeader.classList.add('message-header');
    
    const messageAuthor = document.createElement('span');
    messageAuthor.classList.add('message-author');
    messageAuthor.textContent = data.sender;
    
    const messageTime = document.createElement('span');
    messageTime.classList.add('message-time');
    messageTime.textContent = data.timestamp;
    
    messageHeader.appendChild(messageAuthor);
    messageHeader.appendChild(messageTime);
    
    // Contenu du message
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content', 'game-invitation');
    messageContent.innerHTML = `<p>${data.message}</p>`;
    
    // Ajouter le bouton Rejoindre seulement si on n'est pas l'expéditeur
    if (data.sender !== userName) {
        const joinButton = document.createElement('button');
        joinButton.classList.add('join-game-btn');
        joinButton.textContent = 'Rejoindre la partie';
        joinButton.setAttribute('data-game', data.game);
        joinButton.setAttribute('data-sender', data.sender);
        
        joinButton.addEventListener('click', function() {
            const gameType = this.getAttribute('data-game');
            const creator = this.getAttribute('data-sender');
            
            // Rediriger vers la page de jeu
            window.location.href = `/game/join/?game=${gameType}&creator=${creator}`;
        });
        
        messageContent.appendChild(joinButton);
    }
    
    messageElement.appendChild(messageHeader);
    messageElement.appendChild(messageContent);
    
    return messageElement;
}

// Fonction pour charger les messages existants
function loadExistingMessages(roomId) {
    // Faire une requête AJAX pour récupérer les messages
    fetch(`/chat/messages/${roomId}/`)
        .then(response => response.json())
        .then(data => {
            const messagesContainer = document.getElementById('messages');
            
            // Afficher chaque message
            data.messages.forEach(msg => {
                let messageElement = document.createElement('div');
                messageElement.classList.add('message');
                
                if (msg.user === userName) {
                    messageElement.classList.add('sent');
                } else {
                    messageElement.classList.add('received');
                }
                
                // Si c'est une invitation de jeu
                if (msg.message_type === 'game_invite') {
                    messageElement.innerHTML = `
                        <strong>${msg.user}</strong>
                        <div class="game-invitation">
                            ${msg.content}
                            ${msg.user !== userName ? 
                                `<button class="join-game-btn" data-game="${msg.game_data.game}" data-sender="${msg.user}">
                                    Rejoindre la partie
                                </button>` : ''}
                        </div>
                        <span class="timestamp">${msg.timestamp}</span>
                    `;
                } else {
                    // Message texte normal
                    messageElement.innerHTML = `
                        <strong>${msg.user}</strong>${msg.content}
                        <span class="timestamp">${msg.timestamp}</span>
                    `;
                }
                
                messagesContainer.appendChild(messageElement);
            });
            
            // Faire défiler vers le bas
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        })
        .catch(error => console.error('Erreur lors du chargement des messages:', error));
}

// Appeler cette fonction au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Extraire l'ID de la salle depuis l'URL
    const pathParts = window.location.pathname.split('/');
    const roomId = pathParts[pathParts.length - 2];
    
    // Charger les messages
    loadExistingMessages(roomId);
});

connectWebSocket();
