import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.apps import apps
from datetime import datetime
from django.db.models import Q
from django.contrib.auth import get_user_model
from chat.models import Room, Message

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
                message_data['game'] = game_type
                game_data = {'game': game_type}
                
                # Sauvegarder en BDD
                await self.save_message(current_user, message_text, room_name, 'game_invite', game_data)
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

    @database_sync_to_async
    def save_message(self, sender, message_text, room_name, message_type='text', game_data=None):
        try:
            User = get_user_model()
            
            # Récupérer l'utilisateur et la salle
            user = User.objects.get(nom=sender)
            room = Room.objects.get(name=room_name)
            
            # Afficher des logs pour débogage
            print(f"Sauvegarde du message: {sender}, '{message_text}', type={message_type}")
            
            # Créer le message avec les nouveaux champs
            message = Message.objects.create(
                user=user,
                room=room,
                content=message_text,
                message_type=message_type,
                game_data=game_data
            )
            
            print(f"Message sauvegardé avec succès, ID: {message.id}")
            return message
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @database_sync_to_async
    def is_user_blocked(self):
        try:
            User = get_user_model()
            current_user = self.scope["user"]
            
            # Le format est "private_user1_user2"
            users = self.room_name.replace('private_', '').split('_')
            other_username = users[1] if users[0] == current_user.nom else users[0]
            
            try:
                other_user = User.objects.get(nom=other_username)
            except User.DoesNotExist:
                return False
            
            UserBlock = apps.get_model('chat', 'UserBlock')
            block_exists = UserBlock.objects.filter(
                Q(blocker=current_user, blocked=other_user) |
                Q(blocker=other_user, blocked=current_user)
            ).exists()
            
            return block_exists
        except Exception as e:
            print(f"Erreur lors de la vérification du blocage: {str(e)}")
            return False