import aiohttp, asyncio, random

COLOR_ORANGE = "\033[38;5;214m"
COLOR_BLUE = "\033[34m"
COLOR_GREEN = "\033[32m"
COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"


async def fetch_pokemon_chunk(offset: int, limit: int, session: aiohttp.ClientSession):
    async with session.get(f"/api/v2/pokemon?offset={offset}&limit={limit}") as response:
        data = await response.json()
        return data["results"]


async def read_pokemons(chunk_size: int = 100):
    pokemons = []
    async with aiohttp.ClientSession(base_url="https://pokeapi.co/api/v2/") as session:

        async with session.get("/api/v2/pokemon?offset=0&limit=1") as response:
            data = await response.json()
            total_count = data["count"]

        tasks = []
        for offset in range(0, total_count, chunk_size):
            tasks.append(fetch_pokemon_chunk(offset, chunk_size, session))

        chunks = await asyncio.gather(*tasks)
        for chunk in chunks:
            pokemons.extend(chunk)

    return pokemons


async def fetch_pokemon_details(url: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        return await response.json()


async def get_pokemon_data(pokemon_list):
    detailed_pokemon = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_pokemon_details(pokemon["url"], session) for pokemon in pokemon_list]
        detailed_pokemon = await asyncio.gather(*tasks)
    return detailed_pokemon


async def parse_pokemon_data(data):
    name = data.get("name", "Unknown")

    stats = {stat["stat"]["name"]: stat["base_stat"] for stat in data.get("stats", [])}

    hp = stats.get("hp", 0)
    attack = stats.get("attack", 0)
    defense = stats.get("defense", 0)
    speed = stats.get("speed", 0)

    return {
        "name": name,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "speed": speed
    }


class Pokemon:
    def __init__(self, name, hp, attack, defense, speed):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    def is_alive(self):
        return self.hp > 0

    def attack_pokemon(self, other):
        damage = max(1, self.attack - other.defense)
        critical = random.random() < 0.1  # 10% chance of critical hit
        if critical:
            damage *= 2
        other.take_damage(damage)
        return damage, critical


async def pokemon_battle(pokemon1, pokemon2):
    battle_log = []

    while pokemon1.is_alive() and pokemon2.is_alive():
        if pokemon1.speed >= pokemon2.speed:
            attacker, defender = pokemon1, pokemon2
        else:
            attacker, defender = pokemon2, pokemon1

        # Attacker bites
        damage, critical = attacker.attack_pokemon(defender)
        battle_log.append(
            f"{COLOR_ORANGE if attacker == pokemon1 else COLOR_BLUE}{attacker.name}{COLOR_RESET} attacked {COLOR_ORANGE if defender == pokemon1 else COLOR_BLUE}{defender.name}{COLOR_RESET} for {damage} damage"
            + (" (Critical!)" if critical else "")
        )
        await asyncio.sleep(0.1)

        if not defender.is_alive():
            battle_log.append(f"{COLOR_RED}{defender.name} down!")
            break

        # Defender bites back
        damage, critical = defender.attack_pokemon(attacker)
        battle_log.append(
            f"{COLOR_ORANGE if defender == pokemon1 else COLOR_BLUE}{defender.name}{COLOR_RESET} attacked {COLOR_ORANGE if attacker == pokemon1 else COLOR_BLUE}{attacker.name}{COLOR_RESET} for {damage} damage"
            + (" (Critical!)" if critical else "")
        )
        await asyncio.sleep(0.1)

        if not attacker.is_alive():
            battle_log.append(f"{COLOR_RED}{attacker.name} down!")

    winner = pokemon1 if pokemon1.is_alive() else pokemon2
    battle_log.append(f"{COLOR_GREEN}The winner is {winner.name}!{COLOR_RESET}")
    return battle_log


async def main():
    pokemons = await read_pokemons()
    print(f"Fetched {len(pokemons)} Pokémon:\n")
    for pokemon in pokemons:
        print(pokemon)
    print("\nDetails of 10 random Pokemons:\n")
    # Get detailed data for 10 random Pokemon
    random_pokemon = random.sample(pokemons, 10)
    detailed_pokemons = await get_pokemon_data(random_pokemon)

    parsed_pokemons = [await parse_pokemon_data(data) for data in detailed_pokemons]

    for parsed_pokemon in parsed_pokemons:
        print(parsed_pokemon)

    # choose two random Pokemon
    pokemon1, pokemon2 = random.sample(parsed_pokemons, 2)
    print(f"\nFight {pokemon1['name']} vs {pokemon2['name']}")

    print(f"{pokemon1}\n{pokemon2}")

    p1 = Pokemon(**pokemon1)
    p2 = Pokemon(**pokemon2)

    battle_log = await pokemon_battle(p1, p2)

    for event in battle_log:
        print(event)
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    asyncio.run(main())
