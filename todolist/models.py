from datetime import datetime
from typing import List, Optional
from django.db import models
from pydantic import BaseModel
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class TasksTag(models.Model):
    title = models.TextField()

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.TextField()
    text = models.TextField()
    created_at = models.DateTimeField()
    is_active = models.BooleanField()
    tags = models.ManyToManyField(TasksTag, blank=True)  # фильтрация по этому полю

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.owner.username} | {self.title}"


class TaskData(BaseModel):
    title: str
    text: str
    tags: Optional[List[int]]


class TagModel(BaseModel):
    id: int
    title: str


class Error(BaseModel):
    error: str


class TaskModel(BaseModel):
    id: int
    title: str
    text: str
    created_at: datetime
    is_active: bool
    tags: Optional[List[TagModel]]

    class Config:
        orm_mode = True

    @classmethod
    def from_model(cls, task):
        return cls(
            id=task.id,
            title=task.title,
            text=task.text,
            created_at=task.created_at,
            is_active=task.is_active,
            tags=[TagModel(title=tag.title, id=tag.id) for tag in task.tags.all()]
        )


class Creds(BaseModel):
    login: str
    password: str


class Auth(BaseModel):
    access_token: str
