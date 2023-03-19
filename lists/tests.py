from django.http import HttpRequest
from django.test import TestCase
from django.urls import resolve

from lists.models import Item, List

# Create your tests here.
class HomePageTest(TestCase):

    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

class ListAndItemModelsTest(TestCase):
    def test_saving_and_retrieving_items(self):
        list_ = List()
        list_.name = 'New List'
        list_.save()
        first_item = Item()
        first_item.text = 'The first (ever) item'
        first_item.list = list_
        first_item.save()

        second_item = Item()
        second_item.text = 'Item the second'
        second_item.list = list_
        second_item.save()

        saved_list = List.objects.first()
        self.assertEqual(saved_list.name, 'New List')
        self.assertEqual(saved_list, list_)
        saved_items = Item.objects.all()
        self.assertEqual(saved_items.count(), 2)

        first_saved_item = saved_items[0]
        second_saved_item = saved_items[1]
        self.assertEqual(first_saved_item.text, 'The first (ever) item')
        self.assertEqual(first_saved_item.list, list_)
        self.assertEqual(second_saved_item.text,'Item the second')
        self.assertEqual(second_saved_item.list, list_)

class ListViewTest(TestCase):

    def test_uses_list_template(self):
        list_ = List.objects.create(name='List')
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_all_items(self):
        correct_list = List.objects.create(name='Correct List')
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create(name='Other List')
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 2')

    def test_passes_correct_list_to_template(self):
        other_list = List.objects.create(name='Other List')
        correct_list = List.objects.create(name='Correct List')
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertEqual(response.context['list'], correct_list)

class NewListTest(TestCase):
    def test_new_list_form_returns_correct_html(self):
        response = self.client.get('/lists/new_form')
        self.assertTemplateUsed(response, 'new_form_list.html')


    def test_can_create_new_list(self):
        self.client.post('/lists/new', data={'list_name' : 'A new list'})
        self.assertEqual(List.objects.count(), 1)
        new_list = List.objects.first()
        self.assertEqual(new_list.name, 'A new list')

    def test_can_save_a_POST_request(self):
        self.client.post('/lists/new', data={'list_name' : 'A new list'})
        self.client.post('/lists/1/add_item', 
                         data={'item_text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_redirects_after_POST(self):
        response = self.client.post('/lists/new',
                                    data={'list_name' : 'A new list'})
        new_list = List.objects.first()
        self.assertRedirects(response, f'/lists/{new_list.id}/')

class ItemTest(TestCase):

    def add_new_item_to_existing_list(self, list_):
        return self.client.post(
            f'/lists/{list_.id}/add_item',
            data={'item_text':'A new item for an existing list'}
        )

    def get_new_list_and_new_item(self):
        list_ = List.objects.create(name='Other List')
        self.add_new_item_to_existing_list(list_)
        new_item = Item.objects.first()
        return list_, new_item

class NewItemTest(ItemTest):

    def test_new_item_form_returns_correct_html(self):
        list_ = List.objects.create(name='New List')
        response = self.client.get(f'/lists/{list_.id}/add_item_form')
        self.assertTemplateUsed(response, 'new_form_item.html')

    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create(name='Other List')
        correct_list = List.objects.create(name='Correct List')
        self.add_new_item_to_existing_list(correct_list)

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)

    def test_redirects_to_list_view(self):
        other_list = List.objects.create(name='Other List')
        correct_list = List.objects.create(name='Correct List')

        response = self.add_new_item_to_existing_list(correct_list)
        self.assertRedirects(response, f'/lists/{correct_list.id}/')

class ItemStateTest(ItemTest):
    def test_new_item_has_open_state(self):
        _, new_item = self.get_new_list_and_new_item()
        self.assertEqual(new_item.state, 1) 
        self.assertEqual(new_item.state_text, 'Open')

    def test_increase_state(self):
        new_list, new_item = self.get_new_list_and_new_item()
        for state, state_text in ((2, 'In Progress'), (3, 'Done')):
            self.client.post(f'/lists/{new_list.id}/{new_item.id}/state_up')
            ## Need to call new_item again, as current new_item is a copy of the
            ## database item and not a pointer to it.
            new_item = Item.objects.get(id = new_item.id)
            self.assertEqual(new_item.state, state) 
            self.assertEqual(new_item.state_text, state_text)

    def test_item_cannot_extend_highest_state(self):
        new_list, new_item = self.get_new_list_and_new_item()
        new_item.state = 3
        new_item.save()
        self.assertRaises(KeyError, self.client.post, f'/lists/{new_list.id}/{new_item.id}/state_up')

    def test_redirect_after_increase_state(self):
        new_list, new_item = self.get_new_list_and_new_item()
        response = self.client.post(f'/lists/{new_list.id}/{new_item.id}/state_up')
        self.assertRedirects(response, f'/lists/{new_list.id}/')

    def test_decrease_state(self):
        new_list, new_item = self.get_new_list_and_new_item()
        new_item.state = 3
        new_item.save()
        for state, state_text in ((2, 'In Progress'), (1, 'Open')):
            self.client.post(f'/lists/{new_list.id}/{new_item.id}/state_down')
            ## Need to call new_item again, as current new_item is a copy of the
            ## database item and not a pointer to it.
            new_item = Item.objects.get(id = new_item.id)
            self.assertEqual(new_item.state, state) 
            self.assertEqual(new_item.state_text, state_text)

    def test_item_cannot_extend_lowest(self):
        new_list, new_item = self.get_new_list_and_new_item()
        new_item.state = 0
        new_item.save()
        self.assertRaises(KeyError, self.client.post,
                          f'/lists/{new_list.id}/{new_item.id}/state_down')

    def test_redirect_after_decrease_state(self):
        new_list, new_item = self.get_new_list_and_new_item()
        response = self.client.post(f'/lists/{new_list.id}/{new_item.id}/state_down')
        self.assertRedirects(response, f'/lists/{new_list.id}/')

    def test_delete_item(self):
        new_list, new_item = self.get_new_list_and_new_item()
        self.client.post(f'/lists/{new_list.id}/{new_item.id}/delete_item')
        new_item = Item.objects.get(id = new_item.id)
        self.assertEqual(new_item.state, 0) 
        self.assertEqual(new_item.state_text, 'Deleted')

    def test_redirect_after_delete_item(self):
        new_list, new_item = self.get_new_list_and_new_item()
        response = self.client.post(f'/lists/{new_list.id}/{new_item.id}/delete_item')
        self.assertRedirects(response, f'/lists/{new_list.id}/')

class ItemPrioTest(ItemTest):
    def test_new_item_has_prio_low(self):
        _, new_item = self.get_new_list_and_new_item()
        self.assertEqual(new_item.prio, 1)
        self.assertEqual(new_item.prio_text, 'Low')

    def test_possible_prios(self):
        _, new_item = self.get_new_list_and_new_item()
        for i, prio in ((0, 'Very Low'),
                        (1, 'Low'),
                        (2, 'High'),
                        (3, 'Very High'),
                        (4, 'Urgent')):
           new_item.prio = i
           new_item.save()
           self.assertEqual(new_item.prio_text, prio)
