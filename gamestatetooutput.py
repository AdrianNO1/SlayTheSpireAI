import json, anthropic, re, os, sys, openai

dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

with open(os.path.join(dir_path, "cardlist.json"), "r", encoding="utf-8") as f:
    cardlist = json.load(f)

with open(os.path.join(dir_path, "powerlist.json"), "r", encoding="utf-8") as f:
    powerlist = json.load(f)

with open(os.path.join(dir_path, "reliclist.json"), "r", encoding="utf-8") as f:
    reliclist = json.load(f)

with open(os.path.join(dir_path, "potionlist.json"), "r", encoding="utf-8") as f:
    potionlist = json.load(f)


cardlist = {k.lower(): v for k, v in cardlist.items()}
powerlist = {k.lower(): v for k, v in powerlist.items()}
reliclist = {k.lower(): v for k, v in reliclist.items()}
potionlist = {k.lower(): v for k, v in potionlist.items()}

claude_client = anthropic.Client(api_key=os.getenv("CLAUDE_API_KEY"))
openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEYt"))

model = "gpt-4o"

"""
"claude-3-5-sonnet-20240620"
"""

def GPT(messages, model=model):
    if "claude" in model:
        response = claude_client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0,
            messages=messages
        )
        
        return response.content[0].text
    else:
        response = openai_client.chat.completions.create(
            model=model,
            max_tokens=2000,
            temperature=0,
            messages=messages
        )

        return response.choices[0].message.content

def gamestate_to_output(input_json, print, debug_print, messages=[]):
    state = json.loads(input_json.replace(",\n        ...", ""))

    if "in_game" in state:
        if not state["in_game"]:
            debug_print("Not in game")
            return [], False

    keep_messages = False

    if "relics" not in state:
        state = state["game_state"]

    if "choice_list" in state and len(state["choice_list"]) == 1 and state["screen_type"] == "SHOP_ROOM":
        return ["choose 0"], False

    map_dict = {
        "M": "Normal Enemy",
        "E": "Elite Enemy",
        "$": "Shop",
        "?": "?",
        "R": "Rest Site",
        "T": "Treasure",
    }

    potions_str = ""
    for potion in state["potions"]:
        if potion["name"] != "Potion Slot":
            if potion['name'].lower() not in potionlist:
                debug_print("Unknown potion:", potion['name'])
            potions_str += f"{potion['name']}: {potionlist[potion['name'].lower()]}\n"
        else:
            potions_str += "Empty Slot\n"


    relics_str = ""
    for relic in state["relics"]:
        if relic['name'].lower() not in reliclist:
            debug_print("Unknown relic:", relic['name'])
        if relic["counter"] >= -1:
            counter = f" (Counter: {relic['counter']})" if relic["counter"] > -1 else ""
            relics_str += f"{relic['name']}{counter}: {reliclist[relic['name'].lower()]}\n"


    prompt = f"""You are currently playing Slay the Spire as the {state["class"][0] + state["class"].lower()[1:]}. Cards have their energy cost in parenthesis next to them. Only use curly brackets when you perform an action.\nGame state:
Current HP: {state["current_hp"]}
Max HP: {state["max_hp"]}
Gold: {state["gold"]}
Floor: {state["floor"]}
Act: {state["act"]}

Potions:
{potions_str}
Relics:
{relics_str}
"""
    cards_in_deck = []
    if "combat_state" not in state:
        prompt += "Deck:\n"
        for card in state["deck"]:
            if card["name"].lower() not in cardlist:
                debug_print("Unknown card:", card["name"])
            else:
                prompt += f"{card['name']} ({'X' if card['cost'] == -1 else (card['cost'] if card['cost'] != -2 else 'Unplayable')} Energy)\n"
                cards_in_deck.append(card["name"].lower())
    prompt += "\n\n\n\n"

    combat_hand = []
    shop_things = []
    requires_confirm = False
    is_combat_reward = False
    is_combat = False
    is_shop = False

    if "next_nodes" in state["screen_state"]:
        if len(state["choice_list"]) == 1:
            return ["choose 0"], False
        choices = {}
        i = 0
        for node in state["screen_state"]["next_nodes"]:
            if node["symbol"] in map_dict:
                choices[map_dict[node["symbol"]]] = i
            else:
                debug_print("Unknown symbol:", node["symbol"])
            i += 1
        if len(choices) == 1:
            return ["choose 0"], False
        
        prompt += "You are currently at the map screen and you need to choose where to go next. Your choices are: \n- " + "\n- ".join(choices.keys())
        prompt += f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to go to the '{list(choices.keys())[0]}', type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."""
    
    elif state["screen_type"] == "EVENT" or state["screen_type"] == "REST":
        if state["screen_type"] == "REST":
            if state["screen_state"]["has_rested"]:
                return ["proceed"], False
            
        if len(state["choice_list"]) == 1:
            return ["choose 0"], False
        
        choices = []
        if state["screen_type"] == "REST":
            for option in state["choice_list"]:
                choices.append(option)
        else:
            for option in state["screen_state"]["options"]:
                choices.append(option["text"])
        
        event_text = f" The event text is: '{state['screen_state']['body_text']}'." if 'body_text' in state['screen_state'] and state['screen_state']['body_text'] != "" else ""
        prompt += f"""You are currently in an event called '{state["screen_state"]["event_name"] if state["screen_type"] == "EVENT" else "Rest"}'.{event_text} Your choices are:
- """ + "\n- ".join(choices) + f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first option, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."""

    elif state["screen_type"] == "HAND_SELECT":
        requires_confirm = True
        keep_messages = True
        choices = state["choice_list"]
        prompt = "This is a continuation of the previous event. Your choices are:\n- " + "\n- ".join([f"{i}: {choice}" for i, choice in enumerate(choices)]) + f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first option, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."

    elif "combat_state" in state:
        is_combat = True
        if state["screen_type"] == "CARD_REWARD":
            requires_confirm = True
            keep_messages = True
            choices = state["choice_list"]

            prompt = "This is a continuation of the previous event. Please reflect on what you did last time that caused this choice, and what this choice does. Your choices are:\n- " + "\n- ".join([f"{i}: {choice}" for i, choice in enumerate(choices)]) + f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first option, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."
        else:
            unique_cards = set()

            def pile_to_str(pile, fill_combat_hand=False):
                pile_str = ""
                for card in pile:
                    unique_cards.add(card["name"].lower())
                    if fill_combat_hand:
                        combat_hand.append(card["name"])
                    pile_str += f"{card['name']} ({'X' if card['cost'] == -1 else (card['cost'] if card['cost'] != -2 else 'Unplayable')} Energy)\n"
                if pile_str == "":
                    pile_str = "Empty\n"
                return pile_str
            
            draw_pile = pile_to_str(state["combat_state"]["draw_pile"])
            discard_pile = pile_to_str(state["combat_state"]["discard_pile"])
            hand = pile_to_str(state["combat_state"]["hand"], fill_combat_hand=True)

            card_descriptions = ""
            for card in unique_cards:
                if card not in cardlist:
                    debug_print("Unknown card:", card)
                    continue
                card_descriptions += f"{card}: {cardlist[card]}\n"

            monsters = ""
            i = 0
            for monster in state["combat_state"]["monsters"]:
                if not monster["is_gone"]:
                    if monster["intent"] == "ATTACK" or monster["move_base_damage"] > 0:
                        intent = f"""Attack for {monster['move_adjusted_damage']}{f'x{monster["move_hits"]}' if monster['move_hits'] > 1 else ''} damage"""
                    elif monster["intent"] == "DEBUG":
                        intent = "BUFF"
                        debug_print("DEBUG INTENT", i)
                    elif monster["intent"] == "UNKNOWN":
                        intent = "UNKNOWN (not attacking)"
                    else:
                        intent = monster["intent"]
                    intent = intent.lower().capitalize()

                    for power in monster['powers']:
                        if power['name'].lower() not in powerlist:
                            debug_print("Unknown power:", power['name'])
                            monster['powers'].remove(power)

                    monsters += f"""{monster['name']}:\n- Index: {i}\n- {monster['current_hp']}/{monster['max_hp']}HP\n- {monster['block']} block\n- Intent: {intent}\n- Powers: {', '.join([f"{power['amount']} {power['name']} ({powerlist[power['name'].lower()].replace('X', str(power['amount']))})" for power in monster['powers']])}\n\n"""

                i += 1

            player_powers = ""
            for power in state["combat_state"]["player"]["powers"]:
                if power['name'].lower() not in powerlist:
                    debug_print("Unknown power:", power['name'])
                else:
                    player_powers += f"- {power['amount']} {power['name']} ({powerlist[power['name'].lower()].replace('X', str(power['amount']))})\n"
            if player_powers != "":
                player_powers = "\nYour Powers/Effects:\n" + player_powers

            prompt += f"""You are currently in combat.

Card descriptions:
{card_descriptions}
Draw pile:
{draw_pile}
Discard pile:
{discard_pile}
Your hand:
{hand}
Energy: {state["combat_state"]["player"]["energy"]}
{player_powers}
Enemies:
{monsters}

Reflect first on the current and what you should do. The energy cost of each card is next to the name of the card inside parenthesis. It is very important that you look at how much energy you have and if you have enough energy to play the cards you want to play. Please ensure you have enough energy for the cards you want to play. You can ONLY play cards that are currently in your hand. To play a card from your hand, type '{{play}}' with the name of the card and the target index if the card requires a target. For example, if you want to play a 'Strike', type '{{play Strike 0}}'. This will play the strike card against the enemy with index 0. If you want to play a card which does not have a target, like a defend, you don't need to include the target index. To end your turn, type '{{end}}'. To use a potion use the {{potion}} action. For example, if you want to use your first potion, type {{potion use 0}}. 0 is the index of the potion slot with the potion you want to play, so the second potion slot is index 1 and so on. If the potion requires a target enemy, add the index of that enemy after the potion slot index. Write a list of these actions in the order you want to perform them in. If you are playing a special card that requires you to make another choice after playing it, like if you draw a new card and you want to see that card before doing anything else, simply don't do any other actions after that and you will be prompted with the new game state. Ending your turn will end your turn, so you should only do that when you are sure you don't want to do anything else. After thinking through what cards you want to play, double check if you have enough energy to play all those cards by adding together all their energy costs in a math equation. VERY IMPORTANT!!! Do NOT use curly brackets anywhere else except when you are performing an action. If you use curly brackets anywhere else, the action inside the curly brackets will be executed no matter what, so be careful to not use curly brackets when planning your actions."""

    elif state["screen_type"] == "SHOP_SCREEN":
        is_shop = True
        cards = ""
        relics = ""
        potions = ""
        for card in state["screen_state"]["cards"]:
            if card["name"].lower() not in cardlist:
                debug_print("Unknown card:", card["name"])
            cards += f"""{card["name"]} ({card["price"]} gold) (costs {card["cost"]} energy in combat): {cardlist[card["name"].lower()]}\n"""
            shop_things.append(card["name"].lower())
        for relic in state["screen_state"]["relics"]:
            if relic["name"].lower() not in reliclist:
                debug_print("Unknown relic:", relic["name"])
            relics += f"""{relic["name"]} ({relic["price"]} gold) (costs {card["cost"]} energy in combat): {reliclist[relic["name"].lower()]}\n"""
            shop_things.append(relic["name"].lower())
        for potion in state["screen_state"]["potions"]:
            if potion["name"].lower() not in potionlist:
                debug_print("Unknown potion:", potion["name"])
            potions += f"""{potion["name"]} ({potion["price"]} gold) (costs {card["cost"]} energy in combat): {potionlist[potion["name"].lower()]}\n"""
            shop_things.append(potion["name"].lower())
        prompt += f"""You are currently in a shop. Reflect on what you need and what you can afford. To buy an item, type '{{buy}}' with the name of the item. For example, if you want to buy a 'card removal', type '{{buy card removal cardname}}'. If you choose to buy a card removal, include the name of the card you want to remove. To buy a regular card, relic, or potion, it is simply '{{buy name}}'. Write a list of these actions to buy multiple things. If you want to buy a potion, ensure you have an empty potion slot first so you have room to pick it up. If you need room and want to discard a potion, use the action {{potion discard}} followed by the index of the potion slot of the potion you want to discard. For example, to remove ur first potion, type {{potion discard 0}}. After choosing what items you want to buy, check if you have enough gold by adding together their costs in a math equation before making your final decision. VERY IMPORTANT!!! Remember, every time you write an action inside curly brackets it will be executed no matter what, so be careful to not use curly brackets when planning ur actions.

Shop items:
Cards:
{cards}
Relics:
{relics}
Potions:
{potions}
"""
        if state["screen_state"]["purge_available"]:
            prompt += f'Card removal: Choose a card to remove from your deck. Costs {state["screen_state"]["purge_cost"]} gold. Can only be purchased once per shop.'
    
    elif state["screen_type"] == "REST_SITE":
        choices = {}
        for option in state["screen_state"]["options"]:
            choices[option["label"]] = option["choice_index"]
        
        if len(choices) == 1:
            return ["choose 0"], False

        prompt += f"""You are currently at a rest site. Reflect on your current health and what you should do. Your choices are:
- """ + "\n- ".join(choices.keys()) + f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first option, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."""
            
    elif state["screen_type"] == "CARD_REWARD":
        cards = ""
        for card in state["screen_state"]["cards"]:
            if card["name"].lower() not in cardlist:
                debug_print("Unknown card:", card["name"])
            cards += f"{card['name']} ({'X' if card['cost'] == -1 else (card['cost'] if card['cost'] != -2 else 'Unplayable')} Energy): {cardlist[card['name'].lower()]}\n"
        prompt += f"""You are currently being offered a choice of cards. Reflect on what you need and what would be most beneficial. The energy cost of each card is written in parenthesis next to it. Your choices are:
""" + cards + f"\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first card, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on. If you don't think any of the cards are beneficial to your deck, you can choose to skip this reward by typing {{skip}}"""
    
    elif state["screen_type"] == "COMBAT_REWARD":
        is_combat_reward = True
        if len(state["screen_state"]["rewards"]) == 0:
            return ["proceed"], False
        reward_list = []
        for reward in state['screen_state']['rewards']:
            if reward["reward_type"] == "CARD":
                reward_list.append("Card Reward")
            elif reward["reward_type"] == "RELIC":
                if reward["relic"]["name"].lower() not in reliclist:
                    debug_print("Unknown relic:", reward["relic"]["name"])
                else:
                    reward_list.append("Relic: " + reward["relic"]["name"] + " (" + reliclist[reward["relic"]["name"].lower()] + ")")
            elif reward["reward_type"] == "POTION":
                if reward["potion"]["name"].lower() not in potionlist:
                    debug_print("Unknown potion:", reward["potion"]["name"])
                else:
                    reward_list.append("Potion: " + reward["potion"]["name"] + " (" + potionlist[reward["potion"]["name"].lower()] + ")")
            elif reward["reward_type"] == "GOLD":
                reward_list.append(str(reward["gold"]) + " Gold")
            elif reward["reward_type"] == "STOLEN_GOLD":
                reward_list.append(str(reward["gold"]) + " Gold (Stolen)")
            else:
                debug_print("Unknown reward type:", reward["reward_type"])
                reward_list.append(reward["reward_type"])

        rewards = "- " + "\n- ".join(reward_list)
        prompt += f"""You have defeated the enemies and are now being offered rewards. Reflect on what you need and if you need it. ALL the choices are FREE and you can choose as many as you want. This means that you should only not choose something when it may be harmful to the future of your run. Make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first reward, type '{{choose 0}}' as 0 is the index of that reward. The second option is index 1 and so on. If you want to pick up a potion, ensure you have an empty potion slot first so you have room to pick it up. If you need room and want to discard a potion, use the action {{potion discard}} followed by the index of the potion slot of the potion you want to discard. For example, to remove ur first potion, type {{potion discard 0}}. When you choose the card reward by using an action, you will be prompted with the choice to add one of three cards to your deck, or skip it entirely to add no cards. There is no harm in looking. Write a list of all the actions you want to take, if you omit any reward from the action list, it will not be claimed or checked. Your rewards are:
{rewards}"""
        
    elif state["screen_type"] == "GRID":
        requires_confirm = True
        keep_messages = True
        choices = state["choice_list"]

        prompt = "This is a continuation of the previous event. Your choices are:\n- " + "\n- ".join([f"{i}: {choice}" for i, choice in enumerate(choices)]) + f"\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first option, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on."
        if state["screen_state"]["for_upgrade"]:
            prompt += "Since this is a choice for an upgrade, this is how all your cards look like upgraded:\n"
            for card in state["deck"]:
                name = card['name']
                if not name.endswith("+"):
                    name += "+"
                if card["name"].lower() not in cardlist:
                    debug_print("Unknown card:", card["name"])
                else:
                    prompt += f"{name} ({'X' if card['cost'] == -1 else (card['cost'] if card['cost'] != -2 else 'Unplayable')} Energy): {cardlist[name.lower()]}\n"
    
    elif state["screen_type"] == "CHEST":
        if not state["screen_state"]["chest_open"]:
            return ["choose 0"], False
    
    elif state["screen_type"] == "BOSS_REWARD":
        relics = ""
        for relic in state["screen_state"]["relics"]:
            if relic["name"].lower() not in reliclist:
                debug_print("Unknown relic:", relic["name"])
            else:
                relics += f"{relic['name']}: {reliclist[relic['name'].lower()]}\n"
        prompt += f"""You have defeated the boss and are now being offered a boss relic. Reflect on what you need and if you need it. Your choices are:
{relics}
\n\nReflect a little bit first on the current situation and what the consequences of each choice might be. Then, make a choice by typing '{{choose}}' with the choice you want to make. For example, if you want to choose the first relic, type '{{choose 0}}' as 0 is the index of that choice. The second option is index 1 and so on. You can only choose one of these boss relics, so choose wisely. If you don't want any of the relics, you can choose to skip this reward by typing {{skip}}"""
    else:
        debug_print("Unknown screen type:", state["screen_type"])
        return [], False

    if not keep_messages:
        while len(messages) > 0:
            messages.pop()

    print("Generating with prompt:\n" + prompt + "\n\n\n")
    messages.append({"role": "user", "content": prompt})
    response = GPT(messages)
    messages.append({"role": "assistant", "content": response})
    print("Response:\n" + response + "\n\n\n")

    matches = re.findall(r"\{(.*?)\}", response)
    commands = []
    for match in matches:
        command = None
        action = match.split()[0]
        arg = " ".join(match.split()[1:])
        if action == "play":
            target = ""
            if arg.split()[-1].isdigit():
                target = int(arg.split()[-1])
                arg = " ".join(arg.split()[:-1])
            else:
                i = 0
                for m in state["combat_state"]["monsters"]:
                    if not m["is_gone"]:
                        target = i
                        break
                    i += 1
            if arg not in combat_hand:
                debug_print("Could not find card in hand:", arg, "Hand:", combat_hand)

            command = f"play {arg} {target}"
            commands.append(command)
            #combat_hand.remove(arg)

        elif action == "choose":
            commands.append("choose " + arg)
        elif action == "end":
            commands.append(action)
        elif action == "buy":
            if arg.lower() not in shop_things:
                if len(arg.split()) > 2 and arg.split()[0] == "card" and arg.split()[1] == "removal":
                    if " ".join(arg.split()[2:]).lower() not in cardlist:
                        debug_print("Could not find card in cardlist:", " ".join(arg.split()[2:]))
                    elif " ".join(arg.split()[2:]).lower() not in cards_in_deck:
                        debug_print("Could not find card attempted to remove in deck:", " ".join(arg.split()[2:]), "Deck:", cards_in_deck)
                    else:
                        commands.append(f"choose {state['choice_list'].index('purge')}")
                        commands.append(f"choose {cards_in_deck.index(' '.join(arg.split()[2:]).lower())}")
                        commands.append("confirm")
                        state['choice_list'].remove('purge')
                else:
                    debug_print("Could not find item in shop:", arg.lower(), "Shop items:", shop_things)
            else:
                index = [x.lower() for x in state["choice_list"]].index(arg.lower())
                
                command = "choose " + str(index)
                commands.append(command)
                state["choice_list"].pop(index)
                for item in state["screen_state"]["cards"] + state["screen_state"]["relics"] + state["screen_state"]["potions"]:
                    if item["name"].lower() == arg.lower():
                        state["gold"] -= item["price"]
                        break

                for item in state["screen_state"]["cards"] + state["screen_state"]["relics"] + state["screen_state"]["potions"]:
                    if item["name"].lower() in state["choice_list"] and item["price"] > state["gold"]:
                        state["choice_list"].remove(item["name"].lower())

                if "purge" in state["choice_list"] and state["screen_state"]["purge_cost"] > state["gold"]:
                    state["choice_list"].remove("purge")
                    
        elif action == "potion":
            if arg.split()[0] == "use":
                if arg.split()[1].isdigit() and int(arg.split()[1]) < 3:
                    if len(arg.split()) == 2:
                        arg += " 0"
                    commands.append(f"potion use {' '.join(arg.split()[1:])}")
                else:
                    debug_print("Invalid potion slot:", arg.split()[1])
            elif arg.split()[0] == "discard":
                if arg.split()[1].isdigit() and int(arg.split()[1]) < 3:
                    commands.append(f"potion discard {arg.split()[1]}")
                else:
                    debug_print("Invalid potion slot:", arg.split()[1])
        elif action == "skip":
            commands.append("skip")
            commands.append("proceed")
        else:
            debug_print("Unknown action:", action)

    i = 0
    for command in commands:
        if command.split()[0] == "choose" and command.split()[1] == "smith":
            commands[i] = f"choose 1"
        elif command.split()[0] == "choose" and command.split()[1] == "rest":
            commands[i] = f"choose 0"
        i += 1

    if not is_shop and not is_combat:
        commands.sort(key=lambda x: int(x.split()[1]) if x.split()[0] == "choose" else (-999 if x.split()[0] == "potion" else 0))
    if is_combat_reward:
        num_found = 0
        i = 0
        for command in commands:
            if command.split()[0] == "choose":
                commands[i] = f"choose {int(command.split()[1]) - num_found}"
                num_found += 1
            i += 1
        commands.append("proceed")
            
    if requires_confirm:
        commands.append("confirm")
    if is_shop:
        commands.append("leave")
        commands.append("proceed")
    if state["screen_type"] == "BOSS_REWARD":
        commands.append("proceed")

    return commands, is_combat