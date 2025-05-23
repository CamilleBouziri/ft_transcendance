const roomName = document.currentScript.getAttribute('data-room-name');
const userName = document.currentScript.getAttribute('data-user-name');
let chatSocket = null;
let isOtherUserOnline = false;
const otherUserName = roomName; // Car roomName contient le nom de l'autre utilisateur
let connectedUsers = new Set(); // Ajouter au début du fichier avec les autres variables globales

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

        if (data.type === 'user_status') {
            if (data.status === 'online') {
                connectedUsers.add(data.user);
            } else {
                connectedUsers.delete(data.user);
            }
            
            // Mettre à jour le statut si le message concerne l'autre utilisateur
            if (data.user === otherUserName) {
                isOtherUserOnline = connectedUsers.has(otherUserName);
                updateInviteButton();
            }
            return;
        }
        
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
                    window.location.href = `/invited-game/?from=${creator}`;
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
    const otherUser = roomName;
    
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
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Inverser l'état de blocage
            window.currentBlockState = !window.currentBlockState;
            button.dataset.blocked = window.currentBlockState;
            
            // Mettre à jour le texte du bouton
            button.textContent = window.currentBlockState ? 
                window.TRANSLATIONS["Unblock"] : 
                window.TRANSLATIONS["Block"];
            
            // Mettre à jour l'état des champs de saisie
            document.getElementById('chat-message-input').disabled = window.currentBlockState;
            document.getElementById('chat-message-submit').disabled = window.currentBlockState;
            document.getElementById('send-game-invite').disabled = window.currentBlockState;
            
            // Mettre à jour l'interface
            updateInviteButton();
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
    if (!isOtherUserOnline) {
        alert("L'utilisateur doit être en ligne pour recevoir une invitation");
        return;
    }
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
    fetch(`/chat/messages/${roomId}/`)
        .then(response => response.json())
        .then(data => {
            const messagesContainer = document.getElementById('messages');
            
            data.messages.forEach(msg => {
                let messageElement;
                
                if (msg.message_type === 'game_invite') {
                    messageElement = document.createElement('div');
                    messageElement.classList.add('message');
                    
                    // Utiliser msg.user au lieu de msg.sender pour la cohérence
                    if (msg.user === userName) {
                        messageElement.classList.add('sent');
                    } else {
                        messageElement.classList.add('received');
                    }
                    
                    const gameType = msg.game || (msg.game_data && msg.game_data.game);
                    messageElement.innerHTML = `
                        <strong>${msg.user}</strong>
                        <div class="game-invitation">
                            ${msg.content}
                            ${msg.user !== userName ? 
                                `<button class="join-game-btn" data-game="${gameType}" data-sender="${msg.user}">
                                    Rejoindre la partie
                                </button>` : ''}
                        </div>
                        <span class="timestamp">${msg.timestamp}</span>
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
                    // Message texte normal (code existant)
                    messageElement = document.createElement('div');
                    messageElement.classList.add('message');
                    
                    if (msg.user === userName) {
                        messageElement.classList.add('sent');
                    } else {
                        messageElement.classList.add('received');
                    }
                    
                    messageElement.innerHTML = `
                        <strong>${msg.user}</strong>${msg.content}
                        <span class="timestamp">${msg.timestamp}</span>
                    `;
                }
                
                messagesContainer.appendChild(messageElement);
            });
            
            scrollToBottom();
        })
        .catch(error => console.error('Erreur lors du chargement des messages:', error));
}

// Modifier la fonction updateInviteButton pour inclure la mise à jour du statut
function updateInviteButton() {
    const inviteButton = document.getElementById('send-game-invite');
    const statusIndicator = document.getElementById('user-status-indicator');
    const statusText = document.getElementById('user-status-text');
    const blockButton = document.getElementById('block-user');
    
    // Mettre à jour l'état en ligne
    window.currentOnlineState = connectedUsers.has(otherUserName);
    // Mettre à jour le texte et l'état du bouton de blocage
    if (blockButton) {
        window.currentBlockState = blockButton.dataset.blocked === 'true';
        blockButton.textContent = window.currentBlockState ? 
            window.TRANSLATIONS["Unblock"] : 
            window.TRANSLATIONS["Block"];
    }
    // Mettre à jour le bouton d'invitation
    if (inviteButton) {
        inviteButton.disabled = !window.currentOnlineState || window.currentBlockState;
        inviteButton.title = !window.currentOnlineState ? 
            window.TRANSLATIONS["User must be online to receive an invitation"] : 
            window.currentBlockState ? 
            window.TRANSLATIONS["Unblock user to send invitation"] : 
            "";
    }
    // Mettre à jour l'indicateur de statut
    if (statusIndicator) {
        statusIndicator.className = window.currentOnlineState ? 'online' : 'offline';
    }
    // Mettre à jour le texte du statut
    if (statusText) {
        statusText.textContent = window.currentOnlineState ? 
            window.TRANSLATIONS["online"] : 
            window.TRANSLATIONS["offline"];
    }
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
