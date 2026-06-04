#TRPG OOP System


import random
from abc import ABC, abstractmethod


# DICE ROLLER
class DiceRoller:
    """Utility class for dice"""

    @staticmethod
    def roll(sides: int, count: int = 1) -> list[int]:
        return [random.randint(1, sides) for _ in range(count)]

    @staticmethod
    def roll_with_modifier(sides: int, modifier: int = 0) -> int:
        return random.randint(1, sides) + modifier

    @staticmethod
    def advantage_roll(sides: int) -> int:
        return max(random.randint(1, sides), random.randint(1, sides))

    @staticmethod
    def disadvantage_roll(sides: int) -> int:
        return min(random.randint(1, sides), random.randint(1, sides))


# ITEMS
class Item(ABC):
    """Abstract base class for items"""

    def __init__(self, name: str, weight: float, value: int):
        self._name = name
        self._weight = weight
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def weight(self):
        return self._weight

    @property
    def value(self):
        return self._value

    @abstractmethod
    def use(self, target) -> str:
        pass

    def __str__(self):
        return f"{self._name} (value: {self._value}g)"


class Weapon(Item):
    def __init__(self, name: str, damage_dice: int, damage_sides: int,
                 weight: float, value: int, weapon_type: str = "melee"):
        super().__init__(name, weight, value)
        self._damage_dice = damage_dice
        self._damage_sides = damage_sides
        self._weapon_type = weapon_type

    def roll_damage(self) -> int:
        return sum(DiceRoller.roll(self._damage_sides, self._damage_dice))

    def use(self, target) -> str:
        dmg = self.roll_damage()
        target.take_damage(dmg)
        return f"{self._name} deals {dmg} damage to {target.name}!"

    def __str__(self):
        return (f"{self._name} [{self._weapon_type}] "
                f"{self._damage_dice}d{self._damage_sides}")


class Armor(Item):
    def __init__(self, name: str, defense: int, weight: float, value: int):
        super().__init__(name, weight, value)
        self._defense = defense

    @property
    def defense(self):
        return self._defense

    def use(self, target) -> str:
        return f"{self._name} provides {self._defense} defense."

    def __str__(self):
        return f"{self._name} [Armor] DEF+{self._defense}"


class Potion(Item):
    def __init__(self, name: str, heal_amount: int, value: int):
        super().__init__(name, 0.5, value)
        self._heal_amount = heal_amount

    def use(self, target) -> str:
        target.heal(self._heal_amount)
        return f"{target.name} drinks {self._name} and recovers {self._heal_amount} HP!"


# SKILLS
class Skill(ABC):
    def __init__(self, name: str, mp_cost: int, description: str):
        self._name = name
        self._mp_cost = mp_cost
        self._description = description

    @property
    def name(self):
        return self._name

    @property
    def mp_cost(self):
        return self._mp_cost

    @abstractmethod
    def activate(self, user, target) -> str:
        pass

    def __str__(self):
        return f"{self._name} (MP: {self._mp_cost}) — {self._description}"


class AttackSkill(Skill):
    def __init__(self, name: str, mp_cost: int, damage: int, description: str):
        super().__init__(name, mp_cost, description)
        self._damage = damage

    def activate(self, user, target) -> str:
        if not user.spend_mp(self._mp_cost):
            return f"{user.name} doesn't have enough MP!"
        total = self._damage + DiceRoller.roll(6)[0]
        target.take_damage(total)
        return f"{user.name} uses {self._name}! {target.name} takes {total} damage."


class HealSkill(Skill):
    def __init__(self, name: str, mp_cost: int, heal: int, description: str):
        super().__init__(name, mp_cost, description)
        self._heal = heal

    def activate(self, user, target) -> str:
        if not user.spend_mp(self._mp_cost):
            return f"{user.name} doesn't have enough MP!"
        target.heal(self._heal)
        return f"{user.name} uses {self._name}! {target.name} recovers {self._heal} HP."


class BuffSkill(Skill):
    def __init__(self, name: str, mp_cost: int, stat: str,
                 amount: int, description: str):
        super().__init__(name, mp_cost, description)
        self._stat = stat
        self._amount = amount

    def activate(self, user, target) -> str:
        if not user.spend_mp(self._mp_cost):
            return f"{user.name} doesn't have enough MP!"
        target.apply_buff(self._stat, self._amount)
        return (f"{user.name} uses {self._name}! "
                f"{target.name}'s {self._stat} +{self._amount} for this battle.")


# CHARACTERS
class Character(ABC):
    """Abstract base class for all characters."""

    def __init__(self, name: str, max_hp: int, max_mp: int,
                 strength: int, agility: int, intelligence: int):
        self._name = name
        self._max_hp = max_hp
        self._hp = max_hp
        self._max_mp = max_mp
        self._mp = max_mp
        self._strength = strength
        self._agility = agility
        self._intelligence = intelligence
        self._buffs: dict[str, int] = {}
        self._inventory: list[Item] = []
        self._weapon: Weapon | None = None
        self._armor: Armor | None = None
        self._skills: list[Skill] = []

    @property
    def name(self):
        return self._name

    @property
    def hp(self):
        return self._hp

    @property
    def mp(self):
        return self._mp

    @property
    def is_alive(self):
        return self._hp > 0

    def effective_strength(self):
        return self._strength + self._buffs.get("strength", 0)

    def effective_defense(self):
        base = self._armor.defense if self._armor else 0
        return base + self._buffs.get("defense", 0)

    # Combat
    def take_damage(self, amount: int):
        reduced = max(0, amount - self.effective_defense())
        self._hp = max(0, self._hp - reduced)

    def heal(self, amount: int):
        self._hp = min(self._max_hp, self._hp + amount)

    def spend_mp(self, amount: int) -> bool:
        if self._mp >= amount:
            self._mp -= amount
            return True
        return False

    def apply_buff(self, stat: str, amount: int):
        self._buffs[stat] = self._buffs.get(stat, 0) + amount

    def basic_attack(self, target: "Character") -> str:
        if self._weapon:
            return self._weapon.use(target)
        dmg = DiceRoller.roll_with_modifier(6, self.effective_strength())
        target.take_damage(dmg)
        return f"{self._name} punches {target.name} for {dmg} damage!"

    def use_skill(self, skill_index: int, target: "Character") -> str:
        if skill_index < 0 or skill_index >= len(self._skills):
            return "Invalid skill!"
        return self._skills[skill_index].activate(self, target)

    # Equipment & Inventory
    def equip_weapon(self, weapon: Weapon):
        self._weapon = weapon

    def equip_armor(self, armor: Armor):
        self._armor = armor

    def add_to_inventory(self, item: Item):
        self._inventory.append(item)

    def learn_skill(self, skill: Skill):
        self._skills.append(skill)

    @abstractmethod
    def class_bonus(self) -> str:
        """Each subclass provides a unique passive description."""
        pass

    def status(self) -> str:
        weapon_str = str(self._weapon) if self._weapon else "Unarmed"
        armor_str = str(self._armor) if self._armor else "No Armor"
        skills_str = ", ".join(s.name for s in self._skills) or "None"
        return (
            f"{'='*40}\n"
            f"  {self._name}\n"
            f"{'='*40}\n"
            f"  HP : {self._hp}/{self._max_hp}\n"
            f"  MP : {self._mp}/{self._max_mp}\n"
            f"  STR: {self._strength}  AGI: {self._agility}  INT: {self._intelligence}\n"
            f"  Weapon : {weapon_str}\n"
            f"  Armor  : {armor_str}\n"
            f"  Skills : {skills_str}\n"
            f"  Passive: {self.class_bonus()}\n"
            f"{'='*40}"
        )

    def __str__(self):
        return f"{self._name} (HP:{self._hp}/{self._max_hp})"


class Warrior(Character):
    """High HP & STR. Passive: reduces all incoming damage by 2."""

    def __init__(self, name: str):
        super().__init__(name, max_hp=120, max_mp=30,
                         strength=8, agility=4, intelligence=2)

    def take_damage(self, amount: int):
        # Passive: extra damage reduction
        super().take_damage(max(0, amount - 2))

    def class_bonus(self) -> str:
        return "Iron Skin — reduces all incoming damage by 2"


class Mage(Character):
    """High INT & MP. Passive: spell damage boosted by INT modifier."""

    def __init__(self, name: str):
        super().__init__(name, max_hp=70, max_mp=100,
                         strength=2, agility=5, intelligence=10)

    def use_skill(self, skill_index: int, target: "Character") -> str:
        result = super().use_skill(skill_index, target)
        # Passive: extra INT-based damage already in skill design
        return result

    def class_bonus(self) -> str:
        return "Arcane Mastery — spell costs reduced by 1 MP"

    def spend_mp(self, amount: int) -> bool:
        return super().spend_mp(max(0, amount - 1))


class Rogue(Character):
    """High AGI. Passive: 20% chance to dodge attacks entirely."""

    def __init__(self, name: str):
        super().__init__(name, max_hp=85, max_mp=50,
                         strength=5, agility=10, intelligence=4)

    def take_damage(self, amount: int):
        if random.random() < 0.20:
            print(f"  >> {self._name} dodges the attack!")
            return
        super().take_damage(amount)

    def class_bonus(self) -> str:
        return "Shadow Step — 20% chance to dodge incoming attacks"


# ENEMYS
class Enemy(Character):
    def __init__(self, name: str, max_hp: int, strength: int,
                 agility: int, intelligence: int, reward_xp: int):
        super().__init__(name, max_hp=max_hp, max_mp=20,
                         strength=strength, agility=agility,
                         intelligence=intelligence)
        self._reward_xp = reward_xp

    @property
    def reward_xp(self):
        return self._reward_xp

    def class_bonus(self) -> str:
        return "Monster — no special passive"

    def ai_action(self, target: "Character") -> str:
        """Simple AI: uses skill if MP allows, else basic attack."""
        if self._skills and self._mp >= self._skills[0].mp_cost:
            return self.use_skill(0, target)
        return self.basic_attack(target)


# BATTLE SYSTEM
class BattleSystem:
    def __init__(self, player: Character, enemy: Enemy):
        self._player = player
        self._enemy = enemy
        self._log: list[str] = []

    def _log_line(self, msg: str):
        self._log.append(msg)
        print(msg)

    def run(self) -> list[str]:
        self._log_line(f"\n{'*'*45}")
        self._log_line(f"  ⚔  BATTLE: {self._player.name} vs {self._enemy.name}")
        self._log_line(f"{'*'*45}")

        turn = 1
        while self._player.is_alive and self._enemy.is_alive:
            self._log_line(f"\n--- Round {turn} ---")

            # Player turn
            if self._player._skills and self._player.mp >= self._player._skills[0].mp_cost:
                msg = self._player.use_skill(0, self._enemy)
            else:
                msg = self._player.basic_attack(self._enemy)
            self._log_line(f"  [Player] {msg}")
            self._log_line(f"  {self._enemy.name} HP: {self._enemy.hp}/{self._enemy._max_hp}")

            if not self._enemy.is_alive:
                break

            # Enemy turn
            msg = self._enemy.ai_action(self._player)
            self._log_line(f"  [Enemy ] {msg}")
            self._log_line(f"  {self._player.name} HP: {self._player.hp}/{self._player._max_hp}")

            turn += 1

        self._log_line(f"\n{'*'*45}")
        if self._player.is_alive:
            self._log_line(f"  🏆 {self._player.name} WINS! (+{self._enemy.reward_xp} XP)")
        else:
            self._log_line(f"  💀 {self._player.name} was defeated...")
        self._log_line(f"{'*'*45}\n")
        return self._log


def run_demo():
    random.seed(42)
    print("\n" + "="*45)
    print("   TRPG OOP SYSTEM — DEMO")
    print("="*45)

    # Create player characters
    warrior = Warrior("P1_warrior")
    mage    = Mage("P2_mage")
    rogue   = Rogue("P3_rogue")

    # Equipment
    sword        = Weapon("Sword",    2, 6, 3.0, 150)
    staff        = Weapon("Staff",  1, 8, 1.5, 200, "magic")
    dagger       = Weapon("Dagger", 1, 6, 0.8, 100)
    plate_armor  = Armor("Plate Armor",    5, 15.0, 500)
    leather      = Armor("Leather Armor",  2,  5.0, 100)
    health_potion   = Potion("Health Potion", 30, 50)

    warrior.equip_weapon(sword)
    warrior.equip_armor(plate_armor)
    warrior.add_to_inventory(health_potion)

    mage.equip_weapon(staff)
    mage.equip_armor(leather)

    rogue.equip_weapon(dagger)

    # Skills
    warrior.learn_skill(BuffSkill("Battle Cry", 5, "strength", 3,
                                  "Boosts own STR for battle"))
    mage.learn_skill(AttackSkill("Fireball", 15, 20,
                                 "Hurls a ball of fire at the enemy"))
    mage.learn_skill(HealSkill("Mend", 10, 25,
                               "Restores HP to target"))
    rogue.learn_skill(AttackSkill("Backstab", 8, 15,
                                  "Strikes from the shadows for bonus damage"))

    # Print character statuses
    for hero in [warrior, mage, rogue]:
        print(hero.status())

    # Create enemies
    goblin = Enemy("Goblin Scout", max_hp=40, strength=4,
                   agility=6, intelligence=1, reward_xp=50)
    dragon = Enemy("Ancient Dragon", max_hp=200, strength=12,
                   agility=3, intelligence=8, reward_xp=500)
    dragon.learn_skill(AttackSkill("Dragon Breath", 10, 30,
                                   "Breathes scorching fire"))

    battle1 = BattleSystem(warrior, goblin)
    log1 = battle1.run()

    battle2 = BattleSystem(mage, dragon)
    log2 = battle2.run()

    return log1, log2


if __name__ == "__main__":
    run_demo()
