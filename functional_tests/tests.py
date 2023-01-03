from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import unittest

MAX_WAIT = 10

class NewVisitorTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()

    def tearDown(self):
        self.browser.quit()

    def wait_for_browser_action(browser_action):
        def inner_function(*args, **kwargs):
            start_time = time.time()
            while True:
                try:
                    browser_action(*args, **kwargs)
                    return
                except (AssertionError, WebDriverException) as e:
                    if time.time() - start_time > MAX_WAIT:
                        raise e
                    time.sleep(0.5)
        return inner_function

    @wait_for_browser_action
    def check_for_header_in_list_table(self, row_text):
        table = self.browser.find_element(By.ID, 'id_list_table')
        rows = table.find_elements(By.TAG_NAME,'h2')
        self.assertIn(row_text, [row.text for row in rows])

    @wait_for_browser_action
    def check_for_row_in_list_table(self, row_text):
        table = self.browser.find_element(By.ID, 'id_list_table')
        rows = table.find_elements(By.TAG_NAME,'td')
        self.assertIn(row_text, [row.text for row in rows])

    @wait_for_browser_action
    def check_for_row_in_list_overview(self, row_text, tag_name='td'):
        list_overview = self.browser.find_element(By.ID, 'id_list_overview_table')
        rows = list_overview.find_elements(By.TAG_NAME,tag_name)
        self.assertIn(row_text, [row.text for row in rows])


    def test_can_start_a_list_and_retrieve_it_later(self):
        # Edith has heard about a cool new online to-do app. She goes to check out its
        # homepage
        self.browser.get(self.live_server_url)

        # She notices the page titel and header mention to-do lists
        self.assertIn('To-Do', self.browser.title)
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('To-Do', header_text)
        # She sees a list with all existing lists and it has at least a header
        # row
        self.check_for_row_in_list_overview('To-Do Lists','th')

        # By entering the name of the new list, she adds a new list.
        inputbox = self.browser.find_element(By.ID,'id_new_list')
        self.assertEqual(
            inputbox.get_attribute('placeholder'),
            'Enter a new to-do list'
        )
        inputbox.send_keys('Flyfishing List')

        # When she hits enter, she is directed to the lists page with no items
        # in it. The name of the list appears in the pages Headerline.
        inputbox.send_keys(Keys.ENTER)
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('Flyfishing List', header_text)

        # The tags "Open", "In Progress" and "Done" are shown.
        self.check_for_header_in_list_table('Open')
        self.check_for_header_in_list_table('In Progress')
        self.check_for_header_in_list_table('Done')

        # She is invited to enter a to-do item straight away.
        inputbox = self.browser.find_element(By.ID,'id_new_item')
        self.assertEqual(
            inputbox.get_attribute('placeholder'),
            'Enter a to-do item'
        )

        # She types "Buy peacock feathers" into a text box (Edith's hobby is tying
        # fly-fishing lures)
        inputbox.send_keys('Buy peacock feathers')
        # When she hits enter, the page updates, and now the page lists 
        # "1: Buy peacock feathers" as an item in a to-do list table
        inputbox.send_keys(Keys.ENTER)
        self.check_for_row_in_list_table('Buy peacock feathers')
        # There is still a text box inviting her to add another item. She
        # enters "Use peacock feathers to make a fly" (Edith is very
        # methodical)
        inputbox = self.browser.find_element(By.ID,'id_new_item')
        inputbox.send_keys('Use peacock feathers to make a fly')
        inputbox.send_keys(Keys.ENTER)

        # The page updates again, and now shows both items on her list
        self.check_for_row_in_list_table('Use peacock feathers to make a fly')
        self.check_for_row_in_list_table('Buy peacock feathers')

        # She navigates back to the home page
        self.browser.find_element(By.ID, 'nav_home').click()
        header_text = self.browser.find_element(By.TAG_NAME,'h1').text
        self.assertIn('To-Do', header_text)

        # Here she can find that her new list is listed in the overview table
        self.check_for_row_in_list_overview('Flyfishing List')
        # She can finds a link to her table and the two items are still shown
        self.browser.find_element(By.ID, 'link_lists_1').click()
        self.check_for_row_in_list_table('Use peacock feathers to make a fly')
        self.check_for_row_in_list_table('Buy peacock feathers')
        # Satisfied, she goes back to sleep

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # Edith starts a new to-do list
        self.browser.get(self.live_server_url)
        inputbox = self.browser.find_element(By.ID,'id_new_list')
        inputbox.send_keys('Flyfishing List')
        inputbox.send_keys(Keys.ENTER)
        inputbox = self.browser.find_element(By.ID,'id_new_item')
        inputbox.send_keys('Buy peacock feathers')
        inputbox.send_keys(Keys.ENTER)
        self.check_for_row_in_list_table('Buy peacock feathers')

        # She notices that her list has a unique URL
        edith_list_url = self.browser.current_url
        self.assertRegex(edith_list_url, '/lists/.+')
        # now a new user, Francis, comes along to the site.

        ## We use a new browser session to make sure that no information of
        ## Edith's is coming through from cookies, etc.
        self.browser.quit()
        self.browser = webdriver.Chrome()

        # Francis vistis the homepage. There is no sign of Edith's list
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertNotIn('make a fly', page_text)

        # Francis starts a new list by entering a new item. He is less
        # interesting than Edith
        inputbox = self.browser.find_element(By.ID,'id_new_list')
        inputbox.send_keys('Francises List')
        inputbox.send_keys(Keys.ENTER)
        inputbox = self.browser.find_element(By.ID, 'id_new_item')
        inputbox.send_keys('Buy milk')
        inputbox.send_keys(Keys.ENTER)
        self.check_for_row_in_list_table('Buy milk')

        # Francis gets his own unique URL
        francis_list_url = self.browser.current_url
        self.assertRegex(francis_list_url, '/lists/.+')
        self.assertNotEqual(francis_list_url, edith_list_url)

        # Again, there is no trace of Edith's list
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertIn('Buy milk', page_text)

        # Satisfied, they go both to sleep
    def test_layout_and_styling(self):
       # Edith goes to the home page
       self.browser.get(self.live_server_url)
       self.browser.set_window_size(1024, 768)

       # She notices the input box is nicely centerd
       inputbox = self.browser.find_element(By.ID,'id_new_list')
       self.assertAlmostEqual(
            inputbox.location['x'] + inputbox.size['width'] / 2,
           512,
           delta=30)
       # She starts a new list and sees the input is nicely centered there too
       inputbox.send_keys('Flyfishing List')
       inputbox.send_keys(Keys.ENTER)
       inputbox = self.browser.find_element(By.ID, 'id_new_item')
       inputbox.send_keys('testing')
       inputbox.send_keys(Keys.ENTER)
       self.check_for_row_in_list_table('testing')
       inputbox = self.browser.find_element(By.ID, 'id_new_item')
       self.assertAlmostEqual(
            inputbox.location['x'] + inputbox.size['width'] / 2,
           512,
           delta=30)

    def find_and_validate_state(self, item_index, state_id):
        state_to_compare = {0: 'Deleted',
                            1: 'Open',
                            2: 'In Progress',
                            3: 'Done'}[state_id]
        state = self.browser.find_element(By.ID,
                                          f'id_item_{item_index}_{state_id}_state').text
        self.assertEqual(state, state_to_compare)

    def test_item_state_and_workflow(self):
        # Edith starts a new to-do list and enters two items
        self.browser.get(self.live_server_url)
        inputbox = self.browser.find_element(By.ID,'id_new_list')
        inputbox.send_keys('Flyfishing List')
        inputbox.send_keys(Keys.ENTER)
        item_texts = ['Buy peacock feathers', 'comb peacock feathers']
        for i, item_text in enumerate(item_texts):
            inputbox = self.browser.find_element(By.ID,'id_new_item')
            inputbox.send_keys(item_text)
            inputbox.send_keys(Keys.ENTER)
            item_index = i + 1
            self.check_for_row_in_list_table(f'{item_text}')

        # The new items are in the open state
        for i in range(1,3):
            self.find_and_validate_state(i, 1)
        # She starts buying feathers and sets the first item to "In
        # Progress"
        self.browser.find_element(By.ID, 'id_item_1_1_state_up').click()
        self.find_and_validate_state(1, 2)
        # She leaves the shop and sets the item to "Done"
        self.browser.find_element(By.ID, 'id_item_1_2_state_up').click()
        self.find_and_validate_state(1, 3)
        # After that she cannot find an icon to increase the state further
        with self.assertRaises(NoSuchElementException) as context:
            self.browser.find_element(By.ID, 'id_item_1_3_state_up').click()
        self.assertTrue('Unable to locate element' in str(context.exception))
        # She now goes back to the shop since these have not been the right
        # feathers and sets the state to In Progress again
        self.browser.find_element(By.ID, 'id_item_1_3_state_down').click()
        self.find_and_validate_state(1, 2)
        # She returns the feathers and decides to buy them again later. She
        # sets the state to Open
        self.browser.find_element(By.ID, 'id_item_1_2_state_down').click()
        self.find_and_validate_state(1, 1)
        # Finally, she decides that she does not need any feathers at all and
        # deletes the item -> It is not shown anymore!

        self.browser.find_element(By.ID, 'id_item_1_1_delete_item').click()
        #self.find_and_validate_state(1, 0)
