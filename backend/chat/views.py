from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Room, Message
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import json
from .models import UserBlock
from auth_app.models import Utilisateurs
from amis.models import Ami

@login_required
def index(request):
    rooms = Room.objects.all()
    return render(request, 'chat/index.html', {
        'rooms': rooms
    })

@login_required
def room(request, room_name):
    users = sorted([request.user.nom, room_name])
    unique_room_name = f"private_{users[0]}_{users[1]}"
    
     # Récupérer l'ami (l'autre utilisateur)
    other_username = room_name  # car room_name contient le nom de l'autre utilisateur
    ami = get_object_or_404(Utilisateurs, nom=other_username)
    
    room, created = Room.objects.get_or_create(
        name=unique_room_name,
        defaults={'created_by': request.user}
    )
    
    messages = Message.objects.filter(room=room).order_by('timestamp')
    print(f"Chargement de {messages.count()} messages pour la salle {unique_room_name}")
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'room': room,
        'ami': ami,
        'messages': messages
    })

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        Room.objects.create(name=room_name, created_by=request.user)
        return redirect('chat:room', room_name=room_name)
    return render(request, 'chat/create_room.html')

@login_required
def conversations_list(request):
    user_rooms = Room.objects.filter(
        messages__user=request.user
    ).distinct()
    
    other_rooms = Room.objects.filter(
        messages__isnull=False
    ).exclude(
        id__in=user_rooms
    ).filter(
        name__contains=request.user.nom
    ).distinct()
    
    all_rooms = user_rooms.union(other_rooms)
    
    conversations = []
    for room in all_rooms:
        room_name_parts = room.name.replace('private_', '').split('_')
        other_user_name = room_name_parts[1] if room_name_parts[0] == request.user.nom else room_name_parts[0]
        
        last_message = Message.objects.filter(room=room).order_by('-timestamp').first()
        
        if last_message:
            conversations.append({
                'room': room,
                'other_user': other_user_name,
                'last_message': last_message,
                'timestamp': last_message.timestamp
            })
    
    conversations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render(request, 'chat/conversations.html', {
        'conversations': conversations
    })


User = get_user_model()

@login_required
@require_POST
def block_user(request):
    try:
        data = json.loads(request.body)
        blocked_username = data.get('blocked_user')
        
        print(f"Tentative de blocage de l'utilisateur: {blocked_username}")
        print(f"Par l'utilisateur: {request.user.nom}")
        
        # Récupérer l'utilisateur à bloquer en ignorant la casse
        blocked_user = User.objects.filter(nom__iexact=blocked_username).first()
        
        if not blocked_user:
            print(f"Utilisateur non trouvé: {blocked_username}")
            return JsonResponse({
                'success': False,
                'message': f"Utilisateur '{blocked_username}' non trouvé"
            }, status=404)
            
        # Vérifier si le blocage existe déjà
        block, created = UserBlock.objects.get_or_create(
            blocker=request.user,
            blocked=blocked_user
        )
        
        if not created:  # Si le blocage existait déjà, on le supprime
            block.delete()
            is_blocked = False
        else:
            is_blocked = True
            
        return JsonResponse({
            'success': True,
            'is_blocked': is_blocked,
            'message': 'Utilisateur bloqué' if is_blocked else 'Utilisateur débloqué'
        })
        
    except Exception as e:
        print(f"Erreur lors du blocage: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@login_required
def get_room_messages(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    messages = Message.objects.filter(room=room).order_by('created_at')[:50]
    
    messages_data = []
    for msg in messages:
        message_data = {
            'id': msg.id,
            'user': msg.user.nom,
            'content': msg.content,
            'timestamp': msg.created_at.strftime("%H:%M"),
            'message_type': msg.message_type,
            'sender': msg.user.nom  # Ajout du champ sender pour correspondre au format WebSocket
        }
        
        if msg.message_type == 'game_invite' and msg.game_data:
            try:
                game_data = msg.game_data if isinstance(msg.game_data, dict) else json.loads(msg.game_data)
                message_data['game'] = game_data.get('game')  # Ajout direct du type de jeu
                message_data['game_data'] = game_data  # Garder la compatibilité
            except json.JSONDecodeError:
                message_data['game'] = 'unknown'
                message_data['game_data'] = {'game': 'unknown'}
        
        messages_data.append(message_data)
    
    return JsonResponse({'messages': messages_data})