import os
import unittest
import json
import time

from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


class CraxSeleniumTests(unittest.TestCase):
    executable = os.environ.get('CRAX_GECKO_EXECUTABLE', '/usr/bin/')
    delay = os.environ.get('CRAX_TEST_DELAY', 2)

    if executable.startswith('/'):
        executable = f'{executable}geckodriver'
    else:
        executable = f'{executable}/geckodriver'

    def test_sel(self):
        self.start_url = "http://127.0.0.1:8000"

        driver = webdriver.Firefox(executable_path=self.executable)
        driver.get(self.start_url)
        driver.get(f'{self.start_url}/v1/cart')
        first_address = driver.find_element_by_xpath('//*[@id="first_field"]')
        first_address.clear()
        first_address.send_keys('Test text one')
        second_address = driver.find_element_by_xpath('//*[@id="second_field"]')
        second_address.clear()
        second_address.send_keys('Test text two')
        file_input = driver.find_element_by_xpath('//*[@id="pic"]')
        if os.path.isfile('static/python_logo.png'):
            file_input.send_keys(os.path.abspath("static/python_logo.png"))
        send_request = driver.find_element_by_xpath('//*[@class="customer_button"]')
        send_request.click()
        time.sleep(int(self.delay))
        response_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="response_details"]')))
        ret = '{"firstField":"Test text one","secondField":"Test text two"}'
        self.assertEqual(response_details.get_attribute("value"), ret)
        self.assertEqual('python_logo.png' in os.listdir('../'), True)

        driver.get(f'{self.start_url}/v1/customer/2/')
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        time.sleep(int(self.delay))
        ret = '{"id":2,"name":"Liberty Day Discount"}'
        self.assertEqual(customer_details.get_attribute("value"), ret)

        driver.get(f'{self.start_url}/v1/customers')
        get_customers_list = driver.find_element_by_xpath('//*[@id="get_customers_list"]')
        get_customers_list.click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        new_customers = [
            {"username": f'{x["username"]}_new', "first_name": x["first_name"],
             "last_name": x["last_name"], "password": "password", "bio": x["bio"]}
            for x in json.loads(customer_details_text)
        ]

        customer_details.clear()
        customer_details.send_keys(json.dumps(new_customers))
        create_customers = driver.find_element_by_xpath('//*[@id="create_customers"]')
        create_customers.click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"success":"Created"}')

        driver.get(f'{self.start_url}/v1/discounts/')
        get_field = driver.find_element_by_xpath('//*[@id="get_field"]')
        get_field.send_keys('1')
        get_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Get Discount')]")
        get_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"name":"Liberty Day Discount","percent":15}')
        new_discount = json.loads(customer_details_text)
        new_discount['percent'] = 35
        customer_details.clear()
        customer_details.send_keys(json.dumps(new_discount))
        create_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Create Discount')]")
        create_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"success":"Created"}')

        get_field = driver.find_element_by_xpath('//*[@id="get_field"]')
        get_field.clear()
        get_field.send_keys('2')
        get_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Get Discount')]")
        get_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"name":"Liberty Day Discount","percent":35}')
        customer_details.clear()
        new_discount = json.loads(customer_details_text)
        new_discount['percent'] = 55
        customer_details.send_keys(json.dumps(new_discount))
        update_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Update Discount')]")
        update_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"success":"Updated"}')

        first_field = driver.find_element_by_xpath('//*[@id="first_field"]')
        first_field.clear()
        first_field.send_keys('2')
        update_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Delete Discount')]")
        update_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, '{"success":"Deleted"}')
        get_discount = driver.find_elements_by_xpath("//*[contains(text(), 'Get Discount')]")
        get_discount[0].click()
        time.sleep(int(self.delay))
        customer_details = WebDriverWait(driver, 2).until(ec.element_to_be_clickable(
            (By.XPATH, '//*[@id="customer_details"]')))
        customer_details_text = customer_details.get_attribute("value")
        self.assertEqual(customer_details_text, 'null')


class SeleniumThreads(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.sel = CraxSeleniumTests()

    def run(self):
        self.sel.test_sel()


class Runner:
    def __init__(self, threads):
        self.threads = threads
        self.start_url = "http://127.0.0.1:8000"

    def start_tests(self):
        for i in range(self.threads - 1):
            my_thread = SeleniumThreads()
            my_thread.start()
            time.sleep(1)


if __name__ == '__main__':
    thread = os.environ.get('CRAX_TEST_THREADS', 1)
    Runner(threads=int(thread)).start_tests()

    unittest.main()
