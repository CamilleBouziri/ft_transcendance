import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.apps import apps
from datetime import datetime
from django.db.models import Q
from django.contrib.auth import get_user_model
from chat.models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    connected_users = {}

    async def connect(self):
        current_user = self.scope["user"].nom
        other_user = self.scope['url_route']['kwargs']['room_name']
        
        users = sorted([current_user, other_user])
        self.room_name = f"private_{users[0]}_{users[1]}"
        self.room_group_name = f"chat_{self.room_name}"

        print(f"[{datetime.now()}] Connexion de {current_user} à la salle {self.room_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.get_or_create_room()

        # Ajouter l'utilisateur à la liste des connectés pour cette salle
        self.connected_users.setdefault(self.room_name, set()).add(self.scope["user"].nom)
        
        # Informer tout le monde du statut de tous les utilisateurs connectés
        for user in self.connected_users.get(self.room_name, set()):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_connect',
                    'user': user
                }
            )
        
        await self.accept()

    @database_sync_to_async
    def get_or_create_room(self):
        Room = apps.get_model('chat', 'Room')
        room, created = Room.objects.get_or_create(
            name=self.room_name,
            defaults={'created_by': self.scope["user"]}
        )
        print(f"Salle {'créée' if created else 'récupérée'}: {self.room_name}")
        return room

    async def disconnect(self, close_code):
        print(f"[{datetime.now()}] Déconnexion de {self.scope['user'].nom} de la salle {self.room_name}")
        
        # Retirer l'utilisateur de la liste des connectés
        if self.room_name in self.connected_users:
            self.connected_users[self.room_name].discard(self.scope["user"].nom)
            if not self.connected_users[self.room_name]:
                del self.connected_users[self.room_name]
        
        # Informer les autres utilisateurs de la déconnexion
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_disconnect',
                'user': self.scope["user"].nom
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            # Vérifier si l'un des utilisateurs a bloqué l'autre
            is_blocked = await self.is_user_blocked()
            if is_blocked:
                # Optionnel: informer l'expéditeur que le message n'a pas été envoyé
                await self.send(text_data=json.dumps({
                    'error': 'Message non envoyé - Communication bloquée'
                }))
                return

            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'text')
            message_text = text_data_json.get('message', '')
            
            current_user = self.scope["user"].nom
            room_name = self.room_name
            current_time = datetime.now().strftime("%H:%M")
            
            print(f"Message reçu: type={message_type}, text={message_text}, user={current_user}")
            
            # Préparer le message à envoyer
            message_data = {
                'sender': current_user,
                'timestamp': current_time,
                'message': message_text,
                'type': message_type,
                'room': room_name
            }
            
            # Ajouter des infos pour invitation de jeu
            if message_type == 'game_invite':
                game_type = text_data_json.get('game')
                message_data['game'] = game_type  # Ajout du type de jeu directement dans message_data
                game_data = {'game': game_type}
                
                # Sauvegarder en BDD avec le même format
                await self.save_message(
                    current_user, 
                    f"Invitation à jouer à {'Morpion' if game_type == 'morpion' else 'Pong'}", 
                    room_name, 
                    'game_invite', 
                    game_data
                )
            else:
                # Message texte normal
                await self.save_message(current_user, message_text, room_name, 'text')
            
            # Envoyer au groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
            
            print(f"Message envoyé au groupe: {self.room_group_name}")
        except Exception as e:
            print(f"Erreur dans receive: {str(e)}")
            import traceback
            traceback.print_exc()

    async def chat_message(self, event):
        message = event['message']
        
        # Envoyer au WebSocket
        await self.send(text_data=json.dumps(message))

    async def user_connect(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user': event['user'],
            'status': 'online'
        }))

    async def user_disconnect(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user': event['user'],
            'status': 'offline'
        }))

    @database_sync_to_async
    def save_message(self, sender, message_text, room_name, message_type='text', game_data=None):
        try:
            User = get_user_model()
            user = User.objects.get(nom=sender)
            room = Room.objects.get(name=room_name)
            
            # S'assurer que game_data est un dictionnaire JSON valide
            if game_data and isinstance(game_data, str):
                game_data = json.loads(game_data)
            
            message = Message.objects.create(
                user=user,
                room=room,
                content=message_text,
                message_type=message_type,
                game_data=game_data
            )
            
            print(f"Message sauvegardé: type={message_type}, game_data={game_data}")
            return message
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @database_sync_to_async
    def is_user_blocked(self):
        # Le format est maintenant "private_user1_user2"
        users = self.room_name.replace('private_', '').split('_')
        other_user = users[1] if users[0] == self.scope["user"].nom else users[0]
        
        UserBlock = apps.get_model('chat', 'UserBlock')
        block_exists = UserBlock.objects.filter(
            (Q(blocker=self.scope["user"]) & Q(blocked__nom=other_user)) |
            (Q(blocker__nom=other_user) & Q(blocked=self.scope["user"]))
        ).exists()
        
        return block_exists