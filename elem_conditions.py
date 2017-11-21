def get_login_username_tag_conditions():
    tag = "input"
    conditions = [lambda elem: elem.get_attribute("id") == 'myusername']
    return tag, conditions


def get_login_password_tag_conditions():
    tag = "input"
    conditions = [lambda elem: elem.get_attribute("id") == 'mypassword']
    return tag, conditions


def get_login_btn_tag_conditions():
    tag = "input"
    conditions = [lambda elem: elem.get_attribute("id") == 'submit']
    return tag, conditions


def get_move_arrow_tag_conditions():
    return "img", [lambda elem: elem.get_attribute("class") == "activeArrow"]


def get_battle_attack_select_conditions():
    return "input", [lambda elem: elem.get_attribute('name') == 'attack']


def get_battle_wild_tag_conditions():
    return "input", [lambda elem: elem.get_attribute("value") == "Battle!"]


def get_wild_caught_conditions():
    return "p", [lambda elem: 'has been caught.' in elem.text]


def get_map_tile_conditions_f(map_link: str):
    return lambda: (
        "a", [lambda elem: elem.get_attribute("href") is not None and elem.get_attribute("href").endswith(map_link)])
