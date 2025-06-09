from django.shortcuts import render, get_object_or_404, redirect
from Interactions.models import Message
from Tasks.models import Task
from Interactions.models import Message, UserNotes,Notification
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
from django.urls import reverse


def task_chat_view(request, task_id):
    # Retrieve the task object; adjust as per your Task model
    task = get_object_or_404(Task, id=task_id)
    
    # Fetch messages related to the task, ordered by timestamp
    try:
        messages = Message.objects.filter(task_id=task_id).order_by('timestamp')
    except Exception as e:
        print("Chat fetch error:", e)
        messages = []
    
    # Pass the task and messages to the template context
    context = {
        'task': task,
        'messages': messages
    }
    
    return render(request, 'Interactions/chat.html', context)


@method_decorator(login_required(login_url="/accounts/login/"),name='dispatch')
class NotesBoardView(View):
    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        notes = UserNotes.objects.filter(task=task, user=request.user).order_by('-updated_at')

        # Check if a specific note is requested
        note_id = request.GET.get('note_id')
        if note_id:
            note = get_object_or_404(UserNotes, id=note_id, user=request.user, task=task)
        else:
            note = notes.first() if notes.exists() else None

        return render(request, 'interactions/notes.html', {
            'task': task,
            'notes': notes,
            'note': note,
        })

@method_decorator(login_required(login_url="/accounts/login/"),name='dispatch')
class CreateNoteView(View):
    def post(self, request):
        task_id = request.POST.get('task_id')
        
        if not task_id:
            return JsonResponse({"error": "Task ID is required."}, status=400)
        
        task = get_object_or_404(Task, id=task_id)
        note = UserNotes.objects.create(
            user=request.user,
            task=task,
            title='Untitled',
            content=''
        )
        from_page = request.GET.get('from')  # get the context
        # return redirect('interactions:task_notes', task_id=task.id)
        return redirect(f"{reverse('interactions:task_notes', args=[task.id])}?from={from_page}")

@method_decorator(login_required(login_url="/accounts/login/"),name='dispatch')
class UpdateNoteView(View):
    def post(self, request, pk):
        note = get_object_or_404(UserNotes, pk=pk, user=request.user)
        title = request.POST.get('title', note.title)
        content = request.POST.get('content', note.content)
        note.title = title
        note.content = content
        note.save()
        return JsonResponse({'status': 'saved'})
    

@method_decorator(login_required(login_url="/accounts/login/"),name='dispatch')
class FetchNotifications(View):
    def get(self, request):
        print("Comes under the notification view")
        notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')[:10]
        print("notifications",notifications)
        data = [
            {
                "actor": n.actor.username if n.actor else "System",
                "verb": n.verb,
                "target": n.target,
                "link": n.url,
                "timestamp": n.timestamp.isoformat()  # UTC ISO string
            }
            for n in notifications
        ]
        print("data",data)
        return JsonResponse({"notifications": data})
    


@method_decorator(login_required(login_url="/accounts/login/"), name='dispatch')
class CalendarPageView(View):
    def get(self, request):
        return render(request, 'Interactions/calendar.html')


@method_decorator(login_required(login_url="/accounts/login/"), name='dispatch')
class CalendarEventsAPI(View):
    def get(self, request):
        user = request.user

        # Get all tasks where the user is either freelancer or client
        tasks = Task.objects.filter(freelancer=user) | Task.objects.filter(client=user)
        tasks = tasks.select_related('freelancer', 'client').distinct()

        # Build calendar event data
        events = []
        for task in tasks:
            role = "Freelancer" if task.freelancer == user else "Client"
            color = "#2563eb" if role == "Freelancer" else "#22c55e"

            events.append({
                "id": task.id,
                "title": task.title,
                "start": task.deadline.isoformat(),
                "backgroundColor": color,
                "extendedProps": {
                    "id": task.id,
                    "role": role,
                    "client": task.client.username if task.client else "Unassigned",
                    "freelancer": task.freelancer.username,
                }
            })

        return JsonResponse(events, safe=False)

