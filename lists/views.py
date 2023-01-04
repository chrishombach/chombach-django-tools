from django.shortcuts import render, redirect
from django.http import HttpResponse
from lists.models import Item, List

# Create your views here.
def home_page(request):
    lists = List.objects.all()
    return render(request, 'home.html', {'lists': lists})

def view_list(request, list_id: int):
    list_ = List.objects.get(id=list_id)
    open_items = list_.item_set.filter(state=3)
    filtered_items = [list_.item_set.filter(state=_state) for _state in
                      range(1,4)]
    states = ['Open','In Progress','Done']
    filtered_items = dict(zip(states, filtered_items))
    return render(request, 'list.html', {'list': list_, 
                                         'filtered_items': filtered_items,
                                         'states': states})

def new_list_form(request):
    if request.GET.get('new_list_submit'):
        return redirect('/lists/new')
    return render(request, 'new_form_list.html')

def new_list(request):
    list_ = List.objects.create(name=request.POST['list_name'])
    return redirect(f'/lists/{list_.id}/')

def add_item_form(request, list_id: int):
    if request.GET.get('add_item_submit'):
        return redirect(f'/lists/{list_id}/add_item')
    return render(request, 'new_form_item.html', {'list_id': list_id})

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
