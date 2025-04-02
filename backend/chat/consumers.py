import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.apps import apps
from datetime import datetime
from django.db.models import Q

class ChatConsumer(AsyncWebsocketConsumer):
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
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']
            user = self.scope["user"]

            is_blocked = await self.is_user_blocked()
            if is_blocked:
                await self.send(text_data=json.dumps({
                    'error': 'Vous ne pouvez pas envoyer de message à cet utilisateur',
                    'is_blocked': True
                }))
                return

            
            saved_message = await self.save_message(user, message)
            if saved_message:
                print(f"[{datetime.now()}] Message sauvegardé de {user.nom}: {message}")
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.message',
                        'message': message,
                        'user': user.nom,
                        'timestamp': saved_message.timestamp.isoformat()
                    }
                )
        except Exception as e:
            print(f"Erreur dans receive: {str(e)}")

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'user': event['user'],
                'timestamp': event['timestamp']
            }))
            print(f"[{datetime.now()}] Message envoyé au client: {event['message']} de {event['user']}")
        except Exception as e:
            print(f"Erreur dans chat_message: {str(e)}")

    @database_sync_to_async
    def save_message(self, user, message):
        try:
            Room = apps.get_model('chat', 'Room')
            Message = apps.get_model('chat', 'Message')
            
            room = Room.objects.get(name=self.room_name)
            message = Message.objects.create(
                room=room,
                user=user,
                content=message
            )
            return message
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {str(e)}")
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