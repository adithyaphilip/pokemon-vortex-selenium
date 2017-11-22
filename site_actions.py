import monitor_utils
import site_utils
import elem_conditions
import pokemon_const
import inventory_const
import const

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import time
import random

SLEEP_SEARCH_POKEMON = 1
SLEEP_GO_MAP = 1
SLEEP_LOGIN_ENTRY = 1
SLEEP_BATTLE_ACTIONS = 2

caught_ctr = 0
caught_failed_ctr = 0
battled_ctr = 0
avg_caught_hp = 0
avg_caught_failed_hp = 0
login_ctr = 0


def login(username, password, driver: webdriver.Chrome):
    """
        assumes we want to do a fresh login and navigates to the login page
        returns true on successful login, false otherwise
    """
    global login_ctr
    login_ctr += 1
    driver.get(site_utils.get_login_url())
    if not site_utils.is_login_page(driver):
        monitor_utils.error("Login page no longer contains required login elements. Login failed!")
        return False

    # is a login page
    username_inp, pwd_inp, login_btn = site_utils.get_login_elements(driver)
    username_inp.send_keys(username)
    pwd_inp.send_keys(password)
    time.sleep(SLEEP_LOGIN_ENTRY)
    login_btn.click()
    if any(username in elem.text for elem in driver.find_elements_by_tag_name("a")):
        monitor_utils.debug("Login successful!")
        return True
    monitor_utils.debug("Login failed!")
    return False
    pass


def move_to_map(map_tile_num: int, driver: webdriver.Chrome):
    monitor_utils.debug("Beginning map change")
    map_link = '/map/%d' % map_tile_num
    maps_tab = driver.find_element_by_id("mapsTab")
    ActionChains(driver).move_to_element(maps_tab).perform()
    time.sleep(1)  # let the tab show up
    monitor_utils.debug("Looking for tile with num %d" % map_tile_num)
    map_tile_elem = site_utils.get_single_element(elem_conditions.get_map_tile_conditions_f(map_link), driver)
    if map_tile_elem is None:
        monitor_utils.error("Failed to find tile with number %d" % map_tile_num)
        return False
    time.sleep(SLEEP_GO_MAP)
    map_tile_elem.click()
    return True


def search_pokemon(driver: webdriver.Chrome):
    time.sleep(SLEEP_SEARCH_POKEMON)
    # assumes we are already on the map screen
    arrows = site_utils.get_all_elements(elem_conditions.get_move_arrow_tag_conditions, driver)
    if len(arrows) == 0:
        monitor_utils.error(
            "Looks like we aren't on the map for some reason (no clickable arrows were found) and search_pokemon was called!")
        return False
    chosen_arrow = random.choice(arrows)
    site_utils.click_by_script(chosen_arrow, driver)
    return True


def execute_random_attack(driver: webdriver.Chrome):
    for _ in range(10):
        attack_elems = site_utils.get_all_elements(elem_conditions.get_battle_attack_select_conditions, driver)
        if len(attack_elems) != 0:
            break
        time.sleep(SLEEP_BATTLE_ACTIONS)

    chosen_att_elem = random.choice(attack_elems)
    site_utils.click_by_script(chosen_att_elem, driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)
    site_utils.submit_naturally(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input[10]'), driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)


def try_catch_pokemon(driver: webdriver.Chrome, ball_val: int):
    ball_elem = driver.find_element_by_xpath(inventory_const.BALL_XPATH_DICT[ball_val])
    site_utils.click_by_script(ball_elem, driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)
    ball_elem.submit()
    time.sleep(SLEEP_BATTLE_ACTIONS)
    caught_elem = site_utils.get_single_element(elem_conditions.get_wild_caught_conditions, driver)
    driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input').submit()
    return caught_elem is not None


def do_actual_battle(driver: webdriver.Chrome, pokemon_name: str, pokemon_level: int, is_captured: bool):
    time.sleep(SLEEP_BATTLE_ACTIONS)
    # we assume to start at the choose your pokemon screen
    # click on "Continue" to enter the battle.
    site_utils.submit_naturally(driver.find_element_by_xpath(r'//*[@id="battleForm"]/p/input'), driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)

    # click on "Attack!"
    # driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input[10]').submit()
    # time.sleep(SLEEP_BATTLE_ACTIONS)
    enemy_health = site_utils.get_enemy_health_during_battle(driver)
    own_health = site_utils.get_own_health_during_battle(driver)
    while True:
        # if enemy_health == 0 or own_health == 0:
        #     break
        # to "Continue" after an attack
        # site_utils.submit_naturally(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input'), driver)
        # time.sleep(SLEEP_BATTLE_ACTIONS)

        # try and catch before next attack
        if enemy_health <= pokemon_const.CAPTURE_HP_LIMIT and not is_captured and site_utils.should_capture_pokemon(
                pokemon_name):
            for _ in range(pokemon_const.CAPTURE_TIMES_LIMIT):
                global caught_ctr
                global caught_failed_ctr
                global avg_caught_hp
                global avg_caught_failed_hp
                if try_catch_pokemon(driver, inventory_const.ULTRA_BALL):
                    caught_ctr += 1
                    avg_caught_hp = (avg_caught_hp * (caught_ctr - 1) + enemy_health) / caught_ctr
                    monitor_utils.debug("Caught Level %d %s at %d HP" % (pokemon_level, pokemon_name, enemy_health))
                    # to return to map at the end of a fight
                    site_utils.click_on_element_naturally(driver.find_element_by_xpath(r'//*[@id="ajax"]/ul/li[1]/a'),
                                                          driver)
                    return True
                else:
                    monitor_utils.debug("Failed capture at Level %d %s at %d HP"
                                        % (pokemon_level, pokemon_name, enemy_health))
                    caught_failed_ctr += 1
                    avg_caught_failed_hp = (avg_caught_failed_hp * (caught_failed_ctr - 1)
                                            + enemy_health) / caught_failed_ctr
                    own_health = site_utils.get_own_health_during_battle(driver)
                    if own_health == 0:
                        # our pokemon died while trying to catch this one
                        return do_actual_battle(driver, pokemon_name, pokemon_level, is_captured)

        # click on "Attack!"
        execute_random_attack(driver)
        enemy_health = site_utils.get_enemy_health_during_battle(driver)
        own_health = site_utils.get_own_health_during_battle(driver)
        if own_health == 0 or enemy_health == 0:
            break
        # to "Continue" after an attack
        while True:
            try:
                site_utils.submit_naturally(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input'), driver)
                break
            except Exception as e:
                monitor_utils.error("Weird, got error for clicking on continue after an attack: " + str(e))

        time.sleep(SLEEP_BATTLE_ACTIONS)

    # to "Continue" at the end of a fight
    site_utils.submit_naturally(driver.find_element_by_xpath(r'//*[@id="battleForm"]/div/input'), driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)

    if enemy_health == 0:
        # we won! Return to map
        site_utils.click_on_element_naturally(driver.find_element_by_xpath(r'//*[@id="ajax"]/ul/li[1]/a'), driver)
    else:
        # we lost :( continue the good fight
        do_actual_battle(driver, pokemon_name, pokemon_level, is_captured)
    return True


def do_battle_if_exists(driver: webdriver.Chrome):
    battle_info = site_utils.get_battle_info(driver)
    if battle_info is None:
        monitor_utils.debug("No battle!")
        return False
    global battled_ctr
    battled_ctr += 1
    monitor_utils.debug("Battle detected!")
    battle_btn, pokemon_name, pokemon_level, is_captured = battle_info
    monitor_utils.debug("Fighting %s at Level %d" % (pokemon_name, pokemon_level))
    site_utils.submit_naturally(battle_btn, driver)
    time.sleep(SLEEP_BATTLE_ACTIONS)

    do_actual_battle(driver, pokemon_name, pokemon_level, is_captured)
    return True


if __name__ == '__main__':
    # for testing only
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    options.add_argument('window-size=1600x900')
    driver2 = webdriver.Chrome(chrome_options=options)
    driver2.implicitly_wait(const.IMPLICIT_WAIT_TIME)
    while True:
        # try:
        login("gameburger2", "darealgameburger", driver2)
        while not move_to_map(18, driver2):
            login("gameburger2", "darealgameburger", driver2)
        while True:
            monitor_utils.debug(
                "Battled: %d Caught: %d Catch Failed: %d Avg. Catch HP: %f Avg. Catch Fail HP: %f Logged in: %d"
                % (battled_ctr, caught_ctr, caught_failed_ctr, avg_caught_hp, avg_caught_failed_hp, login_ctr))
            if not do_battle_if_exists(driver2):
                search_pokemon(driver2)
                # except Exception as e:
                #     print(e)
    pass
