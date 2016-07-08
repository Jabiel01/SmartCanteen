from common.permission import have_permission
from blog.models import Menu, Post


def delete_date(post_dict):
    try:
        post_dict.pop('date')
    except Exception:
        pass


def have_items(post_dict):
    try:
        post_dict.get('items')
    except Exception:
        return False
    return True


def add_dishes_to_menu(post_dict, menu):
    items_list = post_dict.getlist('items')
    items_list = [Post.objects.get(id=item) for item in items_list]
    menu.items = items_list


# TODO need roles
def menu_edit(request, menu):
    user = have_permission(request)
    if user:
        obj_dict = menu.__dict__
        request_dict = request.POST
        delete_date(request_dict)
        if have_items(request_dict):
            add_dishes_to_menu(request_dict, menu)
        for item in request_dict.items():
            key, value = item
            if key in obj_dict:
                if value:
                    obj_dict[key] = value
        menu.save()
        return menu.id
    return False


def create_menu(request):
    user = have_permission(request)
    if user:
        request_dict = request.POST
        menu = Menu(title=request_dict.pop('title'))
        menu.author = user
        menu.save()
        return menu_edit(request, menu)
    return False
