import monitor_utils
import elem_conditions
import const

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import time
import re

SLEEP_NAT_CLICK = 0.2
SLEEP_BATTLE_CHECK = 1
BATTLE_DMG_RE = re.compile(r'd+')


def get_login_url():
    return 'https://www.pokemon-vortex.com/login/'


def is_login_page(driver: webdriver.Chrome):
    required_elems = get_login_elements(driver)
    return all(elem is not None for elem in required_elems)


def get_login_elements(driver: webdriver.Chrome):
    """
    tries to find login page elements (username, password, sign up button) and returns them, None if it cannot find any
    one of them
    :param driver:
    :return:
    """
    username_inp = get_single_element(driver=driver,
                                      tag_condition_func=elem_conditions.get_login_username_tag_conditions)
    pwd_inp = get_single_element(driver=driver, tag_condition_func=elem_conditions.get_login_password_tag_conditions)
    login_btn = get_single_element(driver=driver, tag_condition_func=elem_conditions.get_login_btn_tag_conditions)
    return username_inp, pwd_inp, login_btn


def get_battle_info(driver: webdriver.Chrome):
    # below two fetches just try and ensure the page is loaded
    for _ in range(10):
        try:
            no_wild_elem = driver.find_element_by_xpath(r'//*[@id="pkmnappear"]/b')
            break
        except:
            pass
        try:
            appeared_elem = driver.find_element_by_xpath(r'//*[@id="pkmnappear"]/form/center/p')
            break
        except:
            pass

    # checks if there is a battle available and if so retrieves info
    monitor_utils.debug("Checking if battle")
    battle_btn = get_single_element(elem_conditions.get_battle_wild_tag_conditions, driver)
    if battle_btn is None:
        monitor_utils.debug("No fight!")
        return None

    appeared_elem = driver.find_element_by_xpath(r'//*[@id="pkmnappear"]/form/center/p')
    pokemon_name = appeared_elem.text.replace("appeared.", "").replace("Wild", "").strip()
    level_elem = driver.find_element_by_xpath(r'//*[@id="pkmnappear"]/form/p')
    pokemon_level = int(level_elem.text.replace("Level:", "").strip())
    is_captured = True
    driver.implicitly_wait(1)
    try:
        driver.find_element_by_xpath(r'//*[@id="pkmnappear"]/form/center/p/img')
    except:
        is_captured = False
    driver.implicitly_wait(const.IMPLICIT_WAIT_TIME)
    return battle_btn, pokemon_name, pokemon_level, is_captured


def should_capture_pokemon(pokemon_name: str):
    return any(elem in pokemon_name for elem in ["Mystic", "Ancient", "Dark", "Shiny", "Shadow", "Metallic"])


def get_enemy_health_during_battle(driver: webdriver.Chrome):
    return int(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/table/tbody/tr[1]/td[1]/strong')
               .text.replace("HP: ", "").strip())


def get_own_health_during_battle(driver: webdriver.Chrome):
    return int(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/table/tbody/tr[2]/td[2]/strong')
               .text.replace("HP: ", "").strip())


def get_dmg_inflicted_during_battle(driver: webdriver.Chrome):
    return re.findall(BATTLE_DMG_RE, driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/div/strong[2]/p').text)[0]


def get_dmg_received_during_battle(driver: webdriver.Chrome):
    return re.findall(BATTLE_DMG_RE, driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/div/strong[1]/p').text)[0]


def get_single_element(tag_condition_func, driver: webdriver.Chrome):
    poss_elems = get_all_elements(tag_condition_func, driver)

    if len(poss_elems) == 0:
        return None
    elif len(poss_elems) > 1:
        elem_tag, _ = tag_condition_func()
        monitor_utils.warn(
            "Multiple instances detected for single element with tag %s in get_single_element" % elem_tag)
        return None
    return poss_elems[0]


def get_all_elements(tag_condition_func, driver: webdriver.Chrome):
    elem_tag, conditions = tag_condition_func()
    poss_elems = []
    for elem in driver.find_elements_by_tag_name(elem_tag):
        all_true = True
        for condition in conditions:
            try:
                if not condition(elem):
                    all_true = False
                    break
            except:
                all_true = False
                break

        if all_true:
            poss_elems.append(elem)
    return poss_elems


def click_on_element_naturally(elem, driver: webdriver.Chrome):
    ActionChains(driver).move_to_element(elem).click(elem).perform()


def click_by_script(elem, driver: webdriver.Chrome):
    driver.execute_script('arguments[0].click();', elem)


def submit_naturally(submit_btn_elem, driver: webdriver.Chrome):
    ActionChains(driver).move_to_element(submit_btn_elem).perform()
    submit_btn_elem.submit()
