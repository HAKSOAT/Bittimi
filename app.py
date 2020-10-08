import io
import os

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
import time



def load_chrome_driver():
    chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
    opts = ChromeOptions()
    opts.binary_location = chrome_bin
    return webdriver.Chrome(executable_path="chromedriver", chrome_options=opts)


ff = load_chrome_driver()

# options = Options()
# options.headless = True

# ff = webdriver.Firefox(executable_path="../geckodriver.exe", options=options)
delay = 5
actionchains = ActionChains(ff)


def wait_until(driver, by, value):
    refresh = 3
    while refresh:
        try:
            return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, value)))
        except:
            ff.refresh()
            refresh -= 1

def fetch(product_name, amount, payment_method):
    ff.get('https://www.bitrefill.com/buy')
    search_options = wait_until(ff, By.XPATH, "//*[starts-with(@id, 'downshift-')]")

    search_options.clear()

    search_options.send_keys("Worldwide")

    search_options.send_keys(Keys.ENTER)

    search_box = wait_until(ff, By.XPATH, "//*[starts-with(@placeholder, 'Search for products or gift cards')]")

    for i in product_name.split(" ")[0]:
        search_box.send_keys(i)
        actionchains.move_to_element(search_box)
        actionchains.click()

    search_box.click()

    product = wait_until(ff, By.XPATH, "//p[contains(text(), '{}')]".format(product_name))

    product.click()

    price_gbp = amount
    prices_div = wait_until(ff, By.XPATH, "//input[@value='{}']/following-sibling::span[1]".format(price_gbp))
    prices_div.click()


    purchase_gift_button = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/form/div[3]/div[2]/button")
    purchase_gift_button.click()

    recipient_name = "HAKS"
    my_name = "HAKS"
    recipient_email = "test@gmail.com"
    message = "Send me the 200USD"

    design_type = "Blue"
    gift_designs = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[3]")

    r_name_div = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[2]/div[1]/label[1]/input")
    r_name_div.send_keys(recipient_name)

    my_name_div = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[2]/div[2]/label[1]/input")
    my_name_div.send_keys(my_name)

    r_email = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[2]/div[1]/label[2]/input")
    r_email.send_keys(recipient_email)

    message_div = wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[2]/div[2]/label[2]/textarea")
    message_div.send_keys(message)

    design_type='Blue'
    design = wait_until(ff, By.XPATH, "//div[contains(text(), '{}')]".format(design_type))
    design.click()

    add_to_cart =wait_until(ff, By.XPATH, "/html/body/div[1]/div/div[2]/section/div[2]/div[5]/div[2]/div/div/form/div[4]/button[3]")
    add_to_cart.click()

    checkout = wait_until(ff, By.XPATH, "//a[contains(text(), 'Checkout')]")
    checkout.click()

    try:
        possible_form = wait_until(ff, By.TAG_NAME, "form")
        
        email_part = wait_until(ff, By.XPATH, "//input[@type='email']")
        email_part.clear()
        email_part.send_keys("test@gmail.com")
        agree_terms = ff.find_element_by_xpath("//input[@name='agree_terms']/following-sibling::div[1]")
        
        ActionChains(ff).move_to_element(agree_terms).click().perform()

        wait_until(ff, By.XPATH, "//button[contains(text(), 'Continue')]").click()
        
    except:
        pass

    payment_form = wait_until(ff, By.XPATH, "//h2[contains(text(), 'Choose Payment')]/following-sibling::div[1]")

    payment_method = payment_method.capitalize()
    method = wait_until(ff, By.XPATH,"//p[contains(text(), '{}')]".format(payment_method))
    method.click()

    amount = wait_until(ff, By.XPATH, "//span[contains(text(), 'Send this')]/following-sibling::input[1]").get_attribute('value')
    address = wait_until(ff, By.XPATH, "//span[contains(text(), 'To this')]/following-sibling::input[1]").get_attribute('value')
    return amount, address


app = Flask(__name__)

@app.route('/')
def index():
    return jsonify(success="I am up and running")

@app.route('/pull')
def pull():
    product_name = request.json['product_name']
    amount = request.json['amount']
    method = request.json['payment_method']
    amount, address = fetch(product_name, amount, method)

    return jsonify(amount = amount,
                    address=address)


if __name__ == "__main__":
    app.run()