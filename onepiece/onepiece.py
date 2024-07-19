import discord
from redbot.core import commands, Config
import random
import asyncio

class OnePieceBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        
        default_user = {
            "name": "",
            "epithet": "",
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "attack": 10,
            "defense": 5,
            "speed": 5,
            "haki": {"observation": 0, "armament": 0, "conqueror": 0},
            "devil_fruit": None,
            "bounty": 0,
            "belly": 0,
            "skills": ["Punch"],
            "crew": None
        }
        
        self.config.register_user(**default_user)

        self.enemies = {
            "Marine Recruit": {"hp": 60, "attack": 8, "defense": 5, "speed": 5, "exp": 15, "belly": 1000},
            "Pirate Rookie": {"hp": 70, "attack": 12, "defense": 3, "speed": 7, "exp": 20, "belly": 1500},
            "Sea King": {"hp": 100, "attack": 15, "defense": 10, "speed": 3, "exp": 30, "belly": 2000},
            "Shichibukai": {"hp": 150, "attack": 20, "defense": 15, "speed": 10, "exp": 50, "belly": 5000},
            "Yonko Commander": {"hp": 200, "attack": 25, "defense": 20, "speed": 15, "exp": 100, "belly": 10000}
        }

        self.devil_fruits = {
            "Gomu Gomu no Mi": {"type": "Paramecia", "skill": "Gum-Gum Pistol"},
            "Mera Mera no Mi": {"type": "Logia", "skill": "Fire Fist"},
            "Hie Hie no Mi": {"type": "Logia", "skill": "Ice Age"},
            "Ope Ope no Mi": {"type": "Paramecia", "skill": "Room"},
            "Gura Gura no Mi": {"type": "Paramecia", "skill": "Quake Punch"}
        }

        self.skills = {
            "Punch": {"damage": 1.0, "accuracy": 95},
            "Sword Slash": {"damage": 1.2, "accuracy": 90},
            "Gum-Gum Pistol": {"damage": 1.5, "accuracy": 85, "fruit": "Gomu Gomu no Mi"},
            "Fire Fist": {"damage": 1.8, "accuracy": 80, "fruit": "Mera Mera no Mi"},
            "Ice Age": {"damage": 1.6, "accuracy": 75, "fruit": "Hie Hie no Mi"},
            "Room": {"damage": 1.4, "accuracy": 100, "fruit": "Ope Ope no Mi", "effect": "defense_down"},
            "Quake Punch": {"damage": 2.0, "accuracy": 70, "fruit": "Gura Gura no Mi"},
            "Observation Haki": {"damage": 0.8, "accuracy": 100, "effect": "dodge_up"},
            "Armament Haki": {"damage": 1.3, "accuracy": 90, "effect": "defense_up"},
            "Conqueror's Haki": {"damage": 1.0, "accuracy": 50, "effect": "stun"}
        }

    @commands.group()
    async def op(self, ctx):
        """One Piece Battle commands"""
        pass

    @op.command()
    async def start(self, ctx, name: str, epithet: str):
        """Start your pirate journey"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["name"]:
            await ctx.send("You've already started your journey!")
            return

        user_data["name"] = name
        user_data["epithet"] = epithet
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"{ctx.author.mention}, welcome to the world of One Piece, {name} '{epithet}'!")

    @op.command()
    async def profile(self, ctx):
        """View your pirate profile"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use `op start <name> <epithet>` to begin.")
            return

        embed = discord.Embed(title=f"{user_data['name']} '{user_data['epithet']}'", color=discord.Color.blue())
        embed.add_field(name="Level", value=user_data["level"])
        embed.add_field(name="EXP", value=user_data["exp"])
        embed.add_field(name="HP", value=f"{user_data['hp']}/{user_data['max_hp']}")
        embed.add_field(name="Attack", value=user_data["attack"])
        embed.add_field(name="Defense", value=user_data["defense"])
        embed.add_field(name="Speed", value=user_data["speed"])
        embed.add_field(name="Bounty", value=f"{user_data['bounty']:,} ฿")
        embed.add_field(name="Belly", value=f"{user_data['belly']:,} ฿")
        embed.add_field(name="Devil Fruit", value=user_data["devil_fruit"] or "None")
        haki_info = ", ".join([f"{k.capitalize()}: {v}" for k, v in user_data["haki"].items()])
        embed.add_field(name="Haki", value=haki_info)
        embed.add_field(name="Skills", value=", ".join(user_data["skills"]), inline=False)
        embed.add_field(name="Crew", value=user_data["crew"] or "None")
        await ctx.send(embed=embed)

    @op.command()
    async def battle(self, ctx, opponent: discord.Member = None):
        """Battle an enemy or another player"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use `op start <name> <epithet>` to begin.")
            return

        if opponent:
            return await self.pvp_battle(ctx, opponent)

        enemy_name = random.choice(list(self.enemies.keys()))
        enemy = self.enemies[enemy_name].copy()
        enemy["name"] = enemy_name

        embed = discord.Embed(title="⚔️ Battle Begins ⚔️", color=discord.Color.red())
        embed.add_field(name=user_data["name"], value=f"HP: {user_data['hp']}/{user_data['max_hp']}", inline=True)
        embed.add_field(name=enemy["name"], value=f"HP: {enemy['hp']}/{enemy['hp']}", inline=True)
        battle_msg = await ctx.send(embed=embed)
        
        while user_data["hp"] > 0 and enemy["hp"] > 0:
            if user_data["speed"] >= enemy["speed"]:
                await self.battle_turn(ctx, user_data, enemy, battle_msg, is_player=True)
                if enemy["hp"] <= 0:
                    break
                await self.battle_turn(ctx, enemy, user_data, battle_msg, is_player=False)
            else:
                await self.battle_turn(ctx, enemy, user_data, battle_msg, is_player=False)
                if user_data["hp"] <= 0:
                    break
                await self.battle_turn(ctx, user_data, enemy, battle_msg, is_player=True)

        if user_data["hp"] > 0:
            exp_gain = enemy["exp"]
            belly_gain = enemy["belly"]
            bounty_gain = enemy["exp"] * 10
            user_data["exp"] += exp_gain
            user_data["belly"] += belly_gain
            user_data["bounty"] += bounty_gain
            
            result_embed = discord.Embed(title="🏆 Victory! 🏆", color=discord.Color.green())
            result_embed.add_field(name="Rewards", value=f"EXP: {exp_gain}\nBelly: {belly_gain} ฿\nBounty Increase: {bounty_gain} ฿")
            await ctx.send(embed=result_embed)

            await self.check_level_up(ctx, user_data)
        else:
            user_data["hp"] = user_data["max_hp"]  # Restore HP after losing
            defeat_embed = discord.Embed(title="☠️ Defeat ☠️", color=discord.Color.dark_red())
            defeat_embed.description = "You were defeated. Better luck next time!"
            await ctx.send(embed=defeat_embed)

        await self.config.user(ctx.author).set(user_data)

    async def battle_turn(self, ctx, attacker, defender, battle_msg, is_player=True):
        if is_player:
            skill = await self.get_player_skill(ctx, attacker)
        else:
            skill = random.choice(["Punch", "Kick", "Slam"])  # Basic enemy skills

        skill_data = self.skills.get(skill, {"damage": 1.0, "accuracy": 90})
        accuracy_check = random.randint(1, 100)
        
        embed = discord.Embed(title="⚔️ Battle in Progress ⚔️", color=discord.Color.blue())
        
        if accuracy_check <= skill_data["accuracy"]:
            base_damage = attacker["attack"] * skill_data["damage"]
            damage = max(1, int(base_damage - defender["defense"] / 2))
            defender["hp"] -= damage

            effect_msg = ""
            if "effect" in skill_data:
                effect_msg = self.apply_skill_effect(attacker, defender, skill_data["effect"])

            embed.description = f"{attacker['name']} used {skill} and dealt {damage} damage!{effect_msg}"
        else:
            embed.description = f"{attacker['name']} used {skill} but missed!"

        embed.add_field(name=attacker["name"], value=f"HP: {attacker['hp']}/{attacker['max_hp'] if 'max_hp' in attacker else attacker['hp']}", inline=True)
        embed.add_field(name=defender["name"], value=f"HP: {defender['hp']}/{defender['max_hp'] if 'max_hp' in defender else defender['hp']}", inline=True)
        
        await battle_msg.edit(embed=embed)
        await asyncio.sleep(2)

    def apply_skill_effect(self, attacker, defender, effect):
        if effect == "defense_up":
            attacker["defense"] += 2
            return f"\n{attacker['name']} raised their defense!"
        elif effect == "defense_down":
            defender["defense"] = max(0, defender["defense"] - 2)
            return f"\n{defender['name']}'s defense was lowered!"
        elif effect == "dodge_up":
            attacker["speed"] += 2
            return f"\n{attacker['name']} became more evasive!"
        elif effect == "stun" and random.random() < 0.3:
            return f"\n{defender['name']} was stunned and can't move next turn!"
        return ""

    @op.command()
    async def eat_devil_fruit(self, ctx):
        """Eat a random Devil Fruit"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["devil_fruit"]:
            await ctx.send("You've already eaten a Devil Fruit!")
            return

        fruit = random.choice(list(self.devil_fruits.keys()))
        user_data["devil_fruit"] = fruit
        user_data["skills"].append(self.devil_fruits[fruit]["skill"])
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've eaten the {fruit}! You can now use the skill: {self.devil_fruits[fruit]['skill']}")

    @op.command()
    async def create_crew(self, ctx, crew_name: str):
        """Create a pirate crew"""
        user_data = await self.config.user(ctx.author).all()
        if user_data["crew"]:
            await ctx.send("You're already in a crew!")
            return

        user_data["crew"] = crew_name
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've formed the {crew_name} pirate crew!")

    async def pvp_battle(self, ctx, opponent):
        player_data = await self.config.user(ctx.author).all()
        opponent_data = await self.config.user(opponent).all()

        if not opponent_data["name"]:
            await ctx.send(f"{opponent.mention} hasn't started their journey yet!")
            return

        battle_msg = await ctx.send(f"⚔️ {player_data['name']} vs {opponent_data['name']} ⚔️\nBattle starting...")

        while player_data["hp"] > 0 and opponent_data["hp"] > 0:
            if player_data["speed"] >= opponent_data["speed"]:
                await self.battle_turn(ctx, player_data, opponent_data, battle_msg, is_player=True)
                if opponent_data["hp"] <= 0:
                    break
                await self.battle_turn(ctx, opponent_data, player_data, battle_msg, is_player=True)
            else:
                await self.battle_turn(ctx, opponent_data, player_data, battle_msg, is_player=True)
                if player_data["hp"] <= 0:
                    break
                await self.battle_turn(ctx, player_data, opponent_data, battle_msg, is_player=True)

        if player_data["hp"] > 0:
            winner, loser = player_data, opponent_data
            winner_user, loser_user = ctx.author, opponent
        else:
            winner, loser = opponent_data, player_data
            winner_user, loser_user = opponent, ctx.author

        exp_gain = int(loser["level"] * 10)
        belly_gain = int(loser["belly"] * 0.1)
        bounty_gain = int(loser["bounty"] * 0.05)
        winner["exp"] += exp_gain
        winner["belly"] += belly_gain
        winner["bounty"] += bounty_gain
        loser["belly"] -= belly_gain

        await ctx.send(f"{winner['name']} won! Gained {exp_gain} EXP, {belly_gain} ฿, and bounty increased by {bounty_gain} ฿!")

        await self.check_level_up(ctx, winner)

        winner["hp"] = winner["max_hp"]
        loser["hp"] = loser["max_hp"]

        await self.config.user(winner_user).set(winner)
        await self.config.user(loser_user).set(loser)

    @op.command()
    async def train(self, ctx, stat: str):
        """Train a specific stat (attack, defense, speed, or haki)"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use `op start <name> <epithet>` to begin.")
            return

        valid_stats = ["attack", "defense", "speed", "haki"]
        if stat.lower() not in valid_stats:
            await ctx.send(f"Invalid stat. Please choose one of: {', '.join(valid_stats)}")
            return

        training_cost = user_data["level"] * 100
        if user_data["belly"] < training_cost:
            await ctx.send(f"You need {training_cost} ฿ to train. You only have {user_data['belly']} ฿.")
            return

        user_data["belly"] -= training_cost
        gain = random.randint(1, 3)

        if stat.lower() == "haki":
            haki_type = random.choice(["observation", "armament", "conqueror"])
            user_data["haki"][haki_type] += gain
            await ctx.send(f"You've trained your {haki_type.capitalize()} Haki and gained {gain} points!")
        else:
            user_data[stat.lower()] += gain
            await ctx.send(f"You've trained your {stat.capitalize()} and gained {gain} points!")

        user_data["exp"] += random.randint(10, 30)
        await self.check_level_up(ctx, user_data)
        await self.config.user(ctx.author).set(user_data)

    @op.command()
    async def shop(self, ctx):
        """View the item shop"""
        items = {
            "Den Den Mushi": {"cost": 5000, "effect": "Allows communication with crew members"},
            "Log Pose": {"cost": 10000, "effect": "Increases EXP gain by 10%"},
            "Eternal Pose": {"cost": 50000, "effect": "Allows you to set a 'home' location for quick travel"},
            "Vivre Card": {"cost": 100000, "effect": "Create a Vivre Card for yourself or a crew member"}
        }

        embed = discord.Embed(title="One Piece Item Shop", color=discord.Color.gold())
        for item, data in items.items():
            embed.add_field(name=f"{item} - {data['cost']} ฿", value=data['effect'], inline=False)
        embed.set_footer(text="Use 'op buy <item>' to purchase an item")
        await ctx.send(embed=embed)

    @op.command()
    async def buy(self, ctx, *, item: str):
        """Buy an item from the shop"""
        items = {
            "Den Den Mushi": {"cost": 5000, "effect": "Allows communication with crew members"},
            "Log Pose": {"cost": 10000, "effect": "Increases EXP gain by 10%"},
            "Eternal Pose": {"cost": 50000, "effect": "Allows you to set a 'home' location for quick travel"},
            "Vivre Card": {"cost": 100000, "effect": "Create a Vivre Card for yourself or a crew member"}
        }

        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use `op start <name> <epithet>` to begin.")
            return

        if item not in items:
            await ctx.send("That item doesn't exist in the shop.")
            return

        if user_data["belly"] < items[item]["cost"]:
            await ctx.send(f"You don't have enough Belly to buy this item. You need {items[item]['cost']} ฿.")
            return

        user_data["belly"] -= items[item]["cost"]
        user_data.setdefault("inventory", []).append(item)
        await self.config.user(ctx.author).set(user_data)
        await ctx.send(f"You've purchased a {item}! It has been added to your inventory.")

    @op.command()
    async def inventory(self, ctx):
        """View your inventory"""
        user_data = await self.config.user(ctx.author).all()
        if not user_data["name"]:
            await ctx.send("You haven't started your journey yet! Use `op start <name> <epithet>` to begin.")
            return

        inventory = user_data.get("inventory", [])
        if not inventory:
            await ctx.send("Your inventory is empty.")
            return

        embed = discord.Embed(title=f"{user_data['name']}'s Inventory", color=discord.Color.green())
        for item in set(inventory):
            count = inventory.count(item)
            embed.add_field(name=item, value=f"Quantity: {count}", inline=False)
        await ctx.send(embed=embed)

    @op.command()
    async def wanted_poster(self, ctx, user: discord.Member = None):
        """View your or another user's wanted poster"""
        target = user or ctx.author
        user_data = await self.config.user(target).all()
        if not user_data["name"]:
            await ctx.send(f"{target.mention} hasn't started their journey yet!")
            return

        embed = discord.Embed(title="WANTED", color=discord.Color.red())
        embed.add_field(name="Name", value=f"{user_data['name']} '{user_data['epithet']}'", inline=False)
        embed.add_field(name="Bounty", value=f"{user_data['bounty']:,} ฿", inline=False)
        embed.set_thumbnail(url=target.avatar_url)
        embed.set_footer(text="Dead or Alive")
        await ctx.send(embed=embed)
        
    @op.command()
    @checks.is_owner()
    async def wipe(self, ctx, user: discord.Member):
        """Wipe a user's data (Owner only)"""
        await self.config.user(user).clear()
        await ctx.send(f"{user.mention}'s data has been wiped.")

def setup(bot):
    bot.add_cog(OnePieceBattle(bot))
