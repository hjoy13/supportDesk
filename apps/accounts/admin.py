from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("SupportDesk", {"fields": ("role",)}), #tupple
    )

    # here (SupportDesk, something) -> tuple
    # SupportDesk -> string 
    # {"fields":("role",)} ->dictionary
    # inside dictionary fields -> key, role->value
    #("role",) also a tuple, comma matters in tuple, 
    #without comma ("role") will be treated as string 

    #fieldsets -> editing an existing user

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("SupportDesk", {"fields": ("role",)}),
    )

    #add_fieldsets -> creating a new user

    list_display = UserAdmin.list_display + ("role",)
