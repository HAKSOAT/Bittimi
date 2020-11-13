import os
import json
import traceback
import re
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains

from config import redis


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
        amounts = [package.get('amount', None)
                   for package in product_data.json().get('packages', None)]
        amount = data.get('amount')
        if amount not in amounts:
            errors['amount'] = 'Invalid amount, supported amounts are: {}'\
                .format(', '.join(map(str, amounts)))
        else:
            new_data['amount'] = amount

    color = data.get('color', 'blue').lower()
    allowed_colors = ['green', 'blue', 'red']
    if color not in allowed_colors:
        errors['color'] = 'Invalid color, can only use {}'\
            .format(', '.join(allowed_colors))
    else:
        new_data['color'] = color

    payment = data.get('payment', 'bitcoin').lower()
    allowed_payments = {
        'bitcoin': 'Bitcoin (BTC)', 'lightning': 'Lightning (BTC)',
        'ethereum': 'Ethereum (ETH)', 'litecoin': 'Litecoin (LTC)',
        'dogecoin': 'Dogecoin (DOGE)', 'dash': 'Dash (DASH)'}
    
    if payment not in allowed_payments.keys():
        errors['payment'] = 'Invalid payment method, can only use {}'\
            .format(', '.join(allowed_colors))
    else:
        new_data['payment'] = allowed_payments[payment]

    rec_email = data.get('rec_email', '')
    if not re.match(r"[^@]+@[^@]+\.[^@]+", rec_email):
        errors['rec_email'] = 'Invalid email address'
    else:
        new_data['rec_email'] = rec_email

    new_data['rec_name'] = data.get('rec_name', None)
    new_data['sender'] = data.get('sender', 'Sendcash')
    new_data['message'] = data.get('message', 'Sending you a gift')
    
    return errors, new_data


def load_chrome_driver():
    chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
    opts = ChromeOptions()
    opts.binary_location = chrome_bin
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--start-maximized")
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(
        executable_path="chromedriver", chrome_options=opts)

    # Loading in stored cookies if they exist
    driver.get('https://www.bitrefill.com/buy')
    cookies = redis.get('cookies')
    if cookies:
        cookies = json.loads(cookies)
        cookies = [{'name': str(name), 'value': str(value)}
                   for name, value in cookies.items()]
        for cookie in cookies:
            driver.add_cookie(cookie)
    return driver


def wait_until(driver, by, value, refresh=0, multiple=False, delay=10):
    """
    Fetches an element from the page.
    Returns None if element is not found.

    :param driver:
    :param by: Selector tool
    :param value: Value to be passed into the selector tool specified in the `by` argument
    :param refresh: Number of times page is refreshed if element is not found
    :param multiple: Fetches only the first match if true, otherwise, fetches all
    :param delay: Period to wait for element to appear
    :return:
    """
    if multiple:
        checker = EC.presence_of_all_elements_located
    else:
        checker = EC.presence_of_element_located

    refresh = refresh + 1
    while refresh:
        try:
            return WebDriverWait(driver, delay).until(checker((by, value)))
        except:
            refresh -= 1

        if refresh:
            driver.refresh()


def login(driver):
    """
    Logs into the web page using login details set as environment variables
    BITREFILL_EMAIL, BITREFILL_PASSWORD.

    Returns the driver if login is successful, otherwise returns None.

    :param driver:
    :return: driver
    """
    email = os.getenv('BITREFILL_EMAIL', None)
    password = os.getenv('BITREFILL_PASSWORD', None)

    email_input = wait_until(driver, By.XPATH, "//input[@type='email']")
    ActionChains(driver).move_to_element(email_input).click().perform()
    email_input.send_keys(email)

    password_input = wait_until(driver, By.XPATH,
                                "//input[@type='password']")
    ActionChains(driver).move_to_element(password_input).click().perform()
    password_input.send_keys(password)

    submit = wait_until(driver, By.XPATH, "//button[@type='submit']")
    ActionChains(driver).move_to_element(submit).click().perform()

    # Bitrefill may request a login code on some occasions
    # This is dependent on a Zapier-Gmail integration, which should send in
    # the login code.
    code_input = wait_until(driver, By.XPATH,
                            "//input[@type='text' and @name='code']")
    if code_input:
        login_code = 'login_code'
        code = redis.get(login_code)
        for _ in range(10):
            if code:
                break
            time.sleep(30)
            code = redis.get(login_code)
        redis.delete(login_code)

        ActionChains(driver).move_to_element(code_input).click().perform()
        code_input.send_keys(code.decode("utf-8"))
        submit = wait_until(driver, By.XPATH, "//button[@type='submit']")
        ActionChains(driver).move_to_element(submit).click().perform()

    # Checking the top right of the web page to see if the email is displayed
    # Serves as confirmation of a successful login
    email_display = wait_until(
        driver, By.XPATH,
        "//div[contains(text(), '{}')]".format(email.lower()))
    if email_display:
        cookies = driver.get_cookies()
        cookies = {i['name']: i['value'] for i in cookies}
        redis.set('cookies', json.dumps(cookies))
        print("Login successful")
        return driver


def clear_cart(driver):
    """
    Clears the user cart.

    Returns the driver if successful, otherwise returns None.

    :param driver:
    :return:
    """
    try:
        cart = wait_until(driver, By.XPATH, "//span[contains(text(), 'Cart')]")
        ActionChains(driver).move_to_element(cart).click().perform()
        items = wait_until(driver, By.XPATH, "//button[contains(text(), '×')]",
                           multiple=True, refresh=0)
        if items:
            for item in items:
                ActionChains(driver).move_to_element(item).click().perform()
        return driver
    except Exception as e:
        print(e)


def place_order(id_, product_name, amount, payment, sender, message, color,
                rec_email, rec_name):
    """
    Places an order for a product.

    :param id_:
    :param product_name:
    :param amount:
    :param payment:
    :param sender:
    :param message:
    :param color:
    :param rec_email:
    :param rec_name:
    :return: None
    """
    login_error = True
    attempts = 3
    try:
        ff = load_chrome_driver()
        ff.get('https://www.bitrefill.com/login')

        current_url = ff.current_url
        for i in range(attempts):
            if current_url == 'https://www.bitrefill.com/buy':
                break
            temp = login(ff)
            if temp:
                current_url = temp.current_url
            else:
                ff.get('https://www.bitrefill.com/login')

        if ff:
            login_error = False
            
        print('Starting extraction for process: {} with product name: {}'.format(id_, product_name))

        # It is important to clear the cart before placing a new order
        # Otherwise the new order gets added to a non-empty cart
        temp = clear_cart(ff)
        for i in range(attempts):
            if temp:
                break
            else:
                ff.get('https://www.bitrefill.com/buy')
                temp = clear_cart(ff)

        ff.get('https://www.bitrefill.com/buy/worldwide/?hl=en&q={}'.format(
            product_name.split()[0]))
        product = wait_until(
            ff, By.XPATH,
            "//p[contains(text(), '{}')]".format(product_name), 3)
        product.click()

        # Placing an order on desired product
        for i in range(attempts):
            try:
                amount_div = wait_until(
                    ff, By.XPATH,
                    "//input[@value='{}']/following-sibling::span[1]".format(amount))
                if not amount_div:
                    amount_div = wait_until(
                        ff, By.XPATH,
                        "//select/option[@value='{}']".format(amount))
                amount_div.click()

                purchase_gift_button = wait_until(
                    ff, By.XPATH, "//span[contains(text(), 'Purchase as gift')]")
                purchase_gift_button.click()

                rec_name_input = wait_until(
                    ff, By.XPATH, "//input[@name='gift_recipient_name']")
                ActionChains(ff).move_to_element(rec_name_input).click().perform()
                rec_name_input.send_keys(rec_name)

                senders_name_input = wait_until(
                    ff, By.XPATH, "//input[@name='gift_sender_name']")
                ActionChains(ff).move_to_element(senders_name_input).click().perform()
                senders_name_input.send_keys(sender)

                rec_email_input = wait_until(
                    ff, By.XPATH, "//input[@name='gift_recipient_email']")
                ActionChains(ff).move_to_element(rec_email_input).click().perform()
                rec_email_input.send_keys(rec_email)

                message_input = wait_until(
                    ff, By.XPATH, "//textarea[@name='gift_message']")
                ActionChains(ff).move_to_element(message_input).click().perform()
                message_input.send_keys(message)

                color_div = wait_until(
                    ff, By.XPATH, "//div[contains(text(), '{}')]".format(color.capitalize()))
                ActionChains(ff).move_to_element(color_div).click().perform()

                add_to_cart = ff.find_element_by_xpath(
                    "//button[contains(text(), 'Add to cart')]")
                ActionChains(ff).move_to_element(add_to_cart).click().perform()
                break
            except Exception as e:
                print(e)
                ff.refresh()

        # Checking out the item.
        # For some reason, the checkout button may not be directly clickable.
        checkout = wait_until(
            ff, By.XPATH, "//a[contains(text(), 'Checkout')]")
        for i in range(attempts):
            if checkout:
                break
            cart = wait_until(
                ff, By.XPATH, "//span[contains(text(), 'Cart')]", 3)
            ActionChains(ff).move_to_element(cart).click().perform()
            checkout = wait_until(
                ff, By.XPATH, "//a[contains(text(), 'Checkout')]")
        checkout.click()

        # Choosing the payment method
        for i in range(attempts):
            try:
                method = wait_until(
                    ff, By.XPATH, "//p[text()='{}']".format(payment))
                method.click()
                break
            except Exception as e:
                print(e)
                ff.refresh()

        crypto_amount = wait_until(ff, By.XPATH,
                            "//span[contains(text(), 'Send this')]/following-sibling::input[2]", 3)
        crypto_amount = crypto_amount.get_attribute('value')
        crypto_address = wait_until(ff, By.XPATH,
                             "//div[contains(text(), 'To this')]/parent::span/following-sibling::input[2]", 3)
        crypto_address = crypto_address.get_attribute('value')

        values = {'amount': crypto_amount, 'address': crypto_address}
        redis.set(id_, json.dumps(values))
        print('Finishing extraction for process: {} with product name: {}'.format(id_, product_name))

        invoiceid = re.search(r'checkout/([^/]+)', ff.current_url).group(1)
        redis.set('{}_invoiceid'.format(id_), invoiceid)

    except Exception:
        traceback.print_exc()
        if login_error:
            error = 'There was an issue with login'
        else:
            error = 'Something went wrong'
        redis.set(id_, json.dumps({'error': error}))
    ff.close()


def find(invoiceid, items):
    """
    Checks if an order exists in a list of items using the invoice id.

    :param invoiceid:
    :param items:
    :return:
    """
    for item in items:
        if item['invoice_id'] == invoiceid:
            return True


def get_status(id_):
    """
    Fetches the status of an order.

    :param id_:
    :return:
    """
    invoiceid = redis.get('{}_invoiceid'.format(id_)).decode("utf-8")
    cookies = json.loads(redis.get('cookies'))

    if not cookies:
        return False

    orders = requests.get(
        'https://www.bitrefill.com/api/accounts/orders?page=1&page_size=500',
        cookies=cookies).json()

    items = orders.get('items', None)
    if find(invoiceid, items):
        return True
    else:
        page_count = orders['pageCount']
        for i in range(2, page_count + 1):
            orders = requests.get(
                'https://www.bitrefill.com/api/accounts/orders?page={}&page_size=500'.format(i),
                cookies=cookies).json()
            items = orders.get('items', None)
            if find(invoiceid, items):
                return True
    return False



