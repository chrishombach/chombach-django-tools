from django.shortcuts import render, redirect
from django.http import HttpResponse
from lists.models import Item, List

# Create your views here.
def home_page(request):
    return render(request, 'home.html')

def view_list(request, list_id: int):
    list_ = List.objects.get(id=list_id)
    open_items = list_.item_set.filter(state=3)
    filtered_items = [list_.item_set.filter(state=_state) for _state in
                      range(1,4)]
    states = ['Open','In Progress','Done']
    return render(request, 'list.html', {'list': list_, 
                                         'filtered_items': filtered_items,
                                         'states': states})

def new_list(request):
    list_ = List.objects.create()
    Item.objects.create(text=request.POST['item_text'], list=list_)
    return redirect(f'/lists/{list_.id}/')

def add_item(request, list_id: int):
    list_ = List.objects.get(id=list_id)
    Item.objects.create(text=request.POST['item_text'], list=list_)
    return redirect(f'/lists/{list_.id}/')

def state_up(request, list_id: int, item_id: int):
    item = Item.objects.get(id=item_id)
    item.state += 1
    item.save()
    return redirect(f'/lists/{list_id}/')

def state_down(request, list_id: int, item_id: int):
    item = Item.objects.get(id=item_id)
    item.state -= 1
    item.save()
    return redirect(f'/lists/{list_id}/')

def delete_item(request, list_id: int, item_id: int):
    item = Item.objects.get(id=item_id)
    item.state = 0
    item.save()
    return redirect(f'/lists/{list_id}/')
