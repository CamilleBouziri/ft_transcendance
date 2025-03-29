from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Room, Message

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
    
    room, created = Room.objects.get_or_create(
        name=unique_room_name,
        defaults={'created_by': request.user}
    )
    
    messages = Message.objects.filter(room=room).order_by('timestamp')
    print(f"Chargement de {messages.count()} messages pour la salle {unique_room_name}")
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'room': room,
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
