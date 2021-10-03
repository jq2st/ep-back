from datetime import datetime
from django.contrib.auth import login as login_user
from django.contrib.auth import logout as logout_user
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from ninja import NinjaAPI
from django.contrib.auth.models import Group
from ninja.security import HttpBearer
from django.http import JsonResponse
from typing import List, Optional
from todolist.models import Creds, Task, TasksTag, TaskData, TaskModel, User, Auth, TagModel, Error
from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token
from django.utils import timezone

from dateutil.relativedelta import relativedelta


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            token = AccessToken.objects.get(token=token)
            login_user(request, token.user)
            return token.user
        except:
            return False


api = NinjaAPI(csrf=True)


@api.post("/sign_up", tags=["auth"], response={201: Auth, 401: str})
@csrf_exempt
def sign_up(request, data: Creds):
    try:
        user = User.objects.create_user(data.login, data.login, data.password)
        login_user(request, user)

        tok = generate_token()
        app = Application.objects.first()
        user = User.objects.first()
        access_token = AccessToken.objects.create(
            user=user, application=app, expires=timezone.now() + relativedelta(year=1), token=tok
        )

        return 201, Auth(**{"access_token": str(access_token)})
    except Exception as err:
        return 401, f"{err}"


@api.post("/sign_in", tags=["auth"], response={200: Auth, 401: Error})
@csrf_exempt
def sign_in(request, data: Creds):
    user = authenticate(username=data.login, password=data.password)
    if user is not None:
        login_user(request, user)

        tok = generate_token()
        app = Application.objects.first()
        access_token = AccessToken.objects.create(
            user=user, application=app, expires=timezone.now() + relativedelta(year=1), token=tok
        )

        return 200, Auth(**{"access_token": str(access_token)})
    else:
        return 401, Error({"error": "error"})


@api.get("/sign_out", tags=["auth"], auth=AuthBearer())
@csrf_exempt
def sign_out(request):
    try:
        AccessToken.objects.get(token=request.token).delete()
    except:
        pass
    logout_user(request)
    return f"{request.auth}"


@api.get("/tasks", tags=["todo"], auth=AuthBearer())
@csrf_exempt
def get_task(request, filter: Optional[str] = None):
    ids = filter.split('_') if filter else []
    if ids:
        tasks = Task.objects.filter(owner=request.auth, tags__id__in=ids)
    else:
        tasks = Task.objects.filter(owner=request.auth)
    return [TaskModel.from_model(task) for task in tasks]


@api.get("/search", tags=["todo"], auth=AuthBearer())
@csrf_exempt
def search_task(request, q: Optional[str] = ''):
    tasks_title = Task.objects.filter(owner=request.auth, title__icontains=q)
    tasks_text = Task.objects.filter(owner=request.auth, text__icontains=q)

    return [TaskModel.from_model(task) for task in tasks_title | tasks_text]


@api.get("/tags", tags=["todo"], auth=AuthBearer(), response={200: List[Optional[TagModel]]})
@csrf_exempt
def get_all_tags(request):
    return [TagModel(id=tag.id, title=tag.title) for tag in TasksTag.objects.all()]


@api.post("/tasks", tags=["todo"], auth=AuthBearer(), response={200: TaskModel, 400: Error})
@csrf_exempt
def create_task(request, task_data: TaskData):
    group_vip = Group.objects.get(name='VIP')
    if len(Task.objects.filter(owner=request.user)) >= 5 and group_vip not in request.user.groups.all():
        return 400, JsonResponse({'error': 'you should buy VIP status'})
    task = Task.objects.create(
        title=task_data.title,
        text=task_data.text,
        created_at=datetime.now(),
        is_active=True,
        owner=request.auth,
    )
    task.tags.set(task_data.tags) if task_data.tags else None
    return TaskModel.from_model(task)


@api.post("/task/{id}/deactive", tags=["todo"], auth=AuthBearer(), response={200: TaskModel, 404: str})
@csrf_exempt
def active_task(request, id: int):
    try:
        task = Task.objects.get(id=id, owner=request.auth)
        task.is_active = False
        task.save()
        return 200, TaskModel.from_model(task)
    except Exception as err:
        return 404, f"{err}"


@api.put("/task/{id}", tags=["todo"], auth=AuthBearer())
@csrf_exempt
def update_task(request, id: int, data: TaskData):
    try:
        task = Task.objects.get(id=id, owner=request.auth)
        task.title = data.title if data.title else task.title
        task.text = data.text if data.text else task.text
        task.tags.set(data.tags) if data.tags else None
        task.save()
        return TaskModel.from_model(task)
    except Exception as err:
        return f"{err}"


@api.delete("/task/{id}", tags=["todo"], auth=AuthBearer())
@csrf_exempt
def delete_task(request, id: int):
    try:
        task = Task.objects.get(id=id, owner=request.auth)
        task.delete()
        return "deleted"
    except Exception as err:
        return f"{err}"
