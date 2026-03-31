from fastapi import HTTPException

def is_admin(user):
    return user.role.name == "admin"

def is_editor(user):
    return user.role.name == "editor"

def can_edit_article(user, article):
    return (
        article.owner_id == user.id or
        is_editor(user) or
        is_admin(user)
    )

def can_delete_article(user, article):
    return (
        article.owner_id == user.id or
        is_admin(user)
    )