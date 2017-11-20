import site_actions

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

options = webdriver.ChromeOptions()
# options.add_argument('headless')
options.add_argument('window-size=1600x900')
driver = webdriver.Chrome(chrome_options=options)
if site_actions.login("gameburger2", "darealgameburger", driver):
    pass
