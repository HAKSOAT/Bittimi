import os
import random
import string
import json
import traceback
import re
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains

from config import redis

timeout = 1500


def validate(data):
    errors = {}
    new_data = {}
    must_haves = ['slug', 'amount', 'rec_email', 'rec_name']

    if data is None:
        errors['message'] = 'No parameters passed'
    else:
        for i in must_haves:
            if not data.get(i, None):
                errors[i] = 'Key is missing'

    if errors:
        return errors, None

    slug = data.get('slug', None)
    try:
        product_data = requests.get('https://www.bitrefill.com/api/product/{}'.format(slug))
        status_code = product_data.status_code
        product_name = product_data.json().get('name', None)
        if not len(slug):
            errors['slug'] = 'Should contain at least one character'
        elif not product_name:
            errors['slug'] = 'Does not have a product name'
        else:
            new_data['product_name'] = product_name
    except:
        errors['slug'] = 'Something went wrong during data retrieval'


    if status_code == 200:
        amounts = [package.get('amount', None) for package in product_data.json().get('packages', None)]
        amount = data.get('amount')
        if amount not in amounts:
            errors['amount'] = 'Invalid amount, supported amounts are: {}'.format(', '.join(map(str, amounts)))
        else:
            new_data['amount'] = amount

    color = data.get('color', 'blue').lower()
    allowed_colors = ['green', 'blue', 'red']
    if color not in allowed_colors:
        errors['color'] = 'Invalid color, can only use {}'.format(', '.join(allowed_colors))
    else:
        new_data['color'] = color

    payment = data.get('payment', 'bitcoin').lower()
    allowed_payments = ['bitcoin', 'lightning', 'ethereum', 'litecoin', 'dogecoin', 'dash']
    if payment not in allowed_payments:
        errors['payment'] = 'Invalid payment method, can only use {}'.format(', '.join(allowed_colors))
    else:
        new_data['payment'] = payment

    rec_email = data.get('rec_email', '')
    if not re.match("[^@]+@[^@]+\.[^@]+", rec_email):
        errors['rec_email'] = 'Invalid email address'
    else:
        new_data['rec_email'] = rec_email

    new_data['rec_name'] = data.get('rec_name', None)
    new_data['sender'] = data.get('sender', 'Sendcash')
    new_data['message'] = data.get('message', 'Sending you a gift')
    
    return errors, new_data


def generate_id():
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))


def load_chrome_driver():
    chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
    opts = ChromeOptions()
    opts.binary_location = chrome_bin
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--start-maximized")
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument("user-data-dir=selenium") 
    return webdriver.Chrome(executable_path="chromedriver", chrome_options=opts)


def wait_until(driver, by, value, multiple=False, refresh=3):
    if multiple:
        checker = EC.presence_of_all_elements_located
    else:
        checker = EC.presence_of_element_located

    refresh = refresh + 1
    delay = 5
    while refresh:
        try:
            return WebDriverWait(driver, delay).until(checker((by, value)))
        except:
            refresh -= 1

        if refresh:
            driver.refresh()


def login(driver):
    # CHANGE LOGIN
    # CHANGE LOGIN
    # CHANGE LOGIN
    # CHANGE LOGIN
    # CHANGE LOGIN
    # CHANGE LOGIN
    email = 'Shopejuh@gmail.com'
    login_email_input = wait_until(driver, By.XPATH, "//input[@type='email']", refresh=0)
    ActionChains(driver).move_to_element(login_email_input).click().perform()
    login_email_input.send_keys(email)

    login_password_input = wait_until(driver, By.XPATH, "//input[@type='password']", refresh=0)
    ActionChains(driver).move_to_element(login_password_input).click().perform()
    login_password_input.send_keys('G96WJfGAQftH392')

    code_input = wait_until(ff, By.XPATH, "//input[@type='text' and @name='code']", refresh=0)
    if code_input:
        login_code = 'login_code'
        code = redis.get(login_code, None)
        while not code:
            code = redis.get(login_code, None)
        redis.delete(login_code)

        ActionChains(driver).move_to_element(code_input).click().perform()
        code_input.send_keys(code)

    login_submit = wait_until(driver, By.XPATH, "//button[@type='submit']", refresh=0)
    ActionChains(driver).move_to_element(login_submit).click().perform()
    
    email_display = wait_until(driver, By.XPATH, "//div[contains(text(), '{}')]".format(email.lower()), refresh=0)
    if email_display:
        return driver


def clear_cart(driver):
    cart = wait_until(driver, By.XPATH, "//span[contains(text(), 'Cart')]")
    ActionChains(driver).move_to_element(cart).click().perform()
    items = wait_until(driver, By.XPATH, "//button[contains(text(), '×')]", multiple=True, refresh=0)
    if items:
        for item in items:
            ActionChains(driver).move_to_element(item).click().perform()
    return driver


def fetch(id_, product_name, amount, payment, sender, message, color, rec_email, rec_name):
    login_error = True
    try:
        ff = load_chrome_driver()
        ff.get('https://www.bitrefill.com/login')

        current_url = ff.current_url
        attempts = 3
        while current_url != 'https://www.bitrefill.com/buy':
            print("TRYING TO LOGIN")
            temp = login(ff)
            if temp:
                current_url = temp.current_url

            attempts -= 1
            if not attempts:
                break

        if ff:
            login_error = False
            print("SUCCESSFULLY LOGGED IN")

        cookies = driver.get_cookies()
        cookies = {i['name']: i['value'] for i in cookies}
        redis.set('cookies', json.dumps(cookies), ex=86400)
            
        print('Starting extraction for process: {} with product name: {}'.format(id_, product_name))

        ff = clear_cart(ff)

        ff.get('https://www.bitrefill.com/buy/worldwide/?hl=en&q={}'.format(product_name.split()[0]))
        

        product = wait_until(ff, By.XPATH, "//p[contains(text(), '{}')]".format(product_name))
        product.click()

        amount_div = wait_until(ff, By.XPATH, "//input[@value='{}']/following-sibling::span[1]".format(amount))
        amount_div.click()

        number = '09026746381'
        number_input = wait_until(ff, By.XPATH, "//input[@name='recipient']")
        ActionChains(ff).move_to_element(number_input).click().perform()
        number_input.send_keys(number)

        purchase_gift_button = wait_until(ff, By.XPATH, "//span[contains(text(), 'Purchase as gift')]")
        purchase_gift_button.click()

        rec_name_input = wait_until(ff, By.XPATH, "//input[@name='gift_recipient_name']")
        ActionChains(ff).move_to_element(rec_name_input).click().perform()
        rec_name_input.send_keys(rec_name)

        senders_name_input = wait_until(ff, By.XPATH, "//input[@name='gift_sender_name']")
        ActionChains(ff).move_to_element(senders_name_input).click().perform()
        senders_name_input.send_keys(sender)

        rec_email_input = wait_until(ff, By.XPATH, "//input[@name='gift_recipient_email']")
        ActionChains(ff).move_to_element(rec_email_input).click().perform()
        rec_email_input.send_keys(rec_email)

        message_input = wait_until(ff, By.XPATH, "//textarea[@name='gift_message']")
        ActionChains(ff).move_to_element(message_input).click().perform()
        message_input.send_keys(message)

        color_div = wait_until(ff, By.XPATH, "//div[contains(text(), '{}')]".format(color.capitalize()))
        ActionChains(ff).move_to_element(color_div).click().perform()

        add_to_cart = ff.find_element_by_xpath("//button[contains(text(), 'Add to cart')]")
        ActionChains(ff).move_to_element(add_to_cart).click().perform()

        checkout = wait_until(ff, By.XPATH, "//a[contains(text(), 'Checkout')]")
        checkout.click()

        payment_form = wait_until(ff, By.XPATH, "//h2[contains(text(), 'Choose Payment')]/following-sibling::div[1]")
        method = wait_until(ff, By.XPATH,"//p[contains(text(), '{}')]".format(payment.capitalize()))
        method.click()

        amount = wait_until(ff, By.XPATH, "//span[contains(text(), 'Send this')]/following-sibling::input[1]").get_attribute('value')
        address = wait_until(ff, By.XPATH, "//span[contains(text(), 'To this')]/following-sibling::input[1]").get_attribute('value')

        values = {'amount': amount, 'address': address}
        redis.set(id_, json.dumps(values), ex=timeout)
        print('Finishing extraction for process: {} with product name: {}'.format(id_, product_name))

        invoiceid = re.search('checkout/([^\/]+)', ff.current_url).group(1)
        redis.set('{}_invoiceid'.format(id_), ff.current_url, ex=timeout)

    except Exception as e:
        traceback.print_exc()
        if login_error:
            error = 'There was an issue with login'
        else:
            error = 'Something went wrong'
        redis.set(id_, json.dumps(
                {'error': error}), ex=timeout)
    ff.close()


def find(invoice_id, items):
    for item in items:
        if item['invoice_id'] == invoiceid:
            return True


def status(id_):
    invoiceid = redis.get('{}_invoiceid'.format(id_))
    cookies = redis.get('cookies')
    if not cookies:
        return False

    cookies = json.loads(cookies)

    orders = requests.get('https://www.bitrefill.com/api/accounts/orders?page=1&page_size=500', cookies=cookies)
    items = orders['items']
    if find(invoice_id, items):
        return True
    else:
        page_count = orders['pageCount']
        for i in range(2, page_count + 1):
            orders = requests.get('https://www.bitrefill.com/api/accounts/orders?page={}&page_size=500'.format(i), cookies=cookies)
            items = orders['items']
            if find(invoice_id, items):
                return True
    return False



