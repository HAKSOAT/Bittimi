import os
import random
import string
import json
import traceback

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains

from config import redis


def validate(data):
    errors = {}
    new_data = {}
    must_haves = ['product_name', 'amount', 'payment']

    for i in must_haves:
        if not data.get(i, None):
            errors[i] = 'Key is missing'

    if errors:
        return errors, None

    product_name = data.get('product_name')
    if not len(product_name):
        errors['product_name'] = 'Should contain at least one character'
    else:
        new_data['product_name'] = product_name

    amount = int(data.get('amount'))
    allowed_amounts = [10, 30, 60]
    if amount not in allowed_amounts:
        errors['amount'] = 'Invalid amount, can only use {}'.format(', '.join(allowed_amounts))
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
    return webdriver.Chrome(executable_path="chromedriver", chrome_options=opts)


def wait_until(driver, by, value):
    refresh = 3
    delay = 5
    while refresh:
        try:
            return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, value)))
        except:
            driver.refresh()
            refresh -= 1


def fetch(id_, product_name, amount, payment, sender, message, color):
    is_product_valid = False
    res_email = "john@doe.com"
    res_name = "John Doe"
    try:
        ff = load_chrome_driver()
        ff.delete_all_cookies()
        actionchains = ActionChains(ff)
        print('Starting extraction for process: {} with product name: {}'.format(id_, product_name))

        ff.get('https://www.bitrefill.com/buy/worldwide/?hl=en&q={}'.format(product_name.split()[0]))

        product = wait_until(ff, By.XPATH, "//p[contains(text(), '{}')]".format(product_name))
        product.click()

        is_product_valid = True

        amount_div = wait_until(ff, By.XPATH, "//input[@value='{}']/following-sibling::span[1]".format(amount))
        amount_div.click()

        purchase_gift_button = wait_until(ff, By.XPATH, "//span[contains(text(), 'Purchase as gift')]")
        purchase_gift_button.click()

        res_name_input = wait_until(ff, By.XPATH, "//input[@name='gift_recipient_name']")
        ActionChains(ff).move_to_element(res_name_input).click().perform()
        res_name_input.send_keys(res_name)

        senders_name_input = wait_until(ff, By.XPATH, "//input[@name='gift_sender_name']")
        ActionChains(ff).move_to_element(senders_name_input).click().perform()
        senders_name_input.send_keys(sender)

        res_email_input = wait_until(ff, By.XPATH, "//input[@name='gift_recipient_email']")
        ActionChains(ff).move_to_element(res_email_input).click().perform()
        res_email_input.send_keys(res_email)

        message_input = wait_until(ff, By.XPATH, "//textarea[@name='gift_message']")
        ActionChains(ff).move_to_element(message_input).click().perform()
        message_input.send_keys(message)

        color_div = wait_until(ff, By.XPATH, "//div[contains(text(), '{}')]".format(color.capitalize()))
        ActionChains(ff).move_to_element(color_div).click().perform()

        add_to_cart = ff.find_element_by_xpath("//button[contains(text(), 'Add to cart')]")
        ActionChains(ff).move_to_element(add_to_cart).click().perform()

        checkout = wait_until(ff, By.XPATH, "//a[contains(text(), 'Checkout')]")
        checkout.click()

        #Status updates section
        email_part = wait_until(ff, By.XPATH, "//input[@type='email']")
        email_part.clear()
        email_part.send_keys(res_email)
        agree_terms = ff.find_element_by_xpath("//input[@name='agree_terms']/following-sibling::div[1]")
        ActionChains(ff).move_to_element(agree_terms).click().perform()
        wait_until(ff, By.XPATH, "//button[contains(text(), 'Continue')]").click()
            

        payment_form = wait_until(ff, By.XPATH, "//h2[contains(text(), 'Choose Payment')]/following-sibling::div[1]")
        method = wait_until(ff, By.XPATH,"//p[contains(text(), '{}')]".format(payment.capitalize()))
        method.click()

        amount = wait_until(ff, By.XPATH, "//span[contains(text(), 'Send this')]/following-sibling::input[1]").get_attribute('value')
        address = wait_until(ff, By.XPATH, "//span[contains(text(), 'To this')]/following-sibling::input[1]").get_attribute('value')

        values = {'amount': amount, 'address': address}
        redis.set(id_, json.dumps(values))
        print('Finishing extraction for process: {} with product name: {}'.format(id_, product_name))

    except Exception as e:
        traceback.print_exc()
        if not is_product_valid:
            redis.set(id_, json.dumps(
                {'error': 'Invalid product name: {}'.format(product_name)}))
        else:
            redis.set(id_, json.dumps(
                {'error': 'Something went wrong'}))
    ff.close()
