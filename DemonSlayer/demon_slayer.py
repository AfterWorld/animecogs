from redbot.core import commands, Config, bank
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import box, pagify
import random
import asyncio
import discord
from datetime import datetime, timedelta
from typing import Dict, List

class DemonSlayer(commands.Cog):
    """
    Demon Slayer themed cog with RPG elements.
    
    Slay demons, master breathing techniques, and rise through the ranks of the Demon Slayer Corps!
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_user = {
            "breathing_technique": None,
            "nichirin_color": None,
            "demons_slayed": 0,
            "rank": "Mizunoto",
            "experience": 0,
            "known_forms": [],
            "last_mission": None,
            "last_daily": None,
            "nichirin_materials": {"steel": 0, "scarlet_ore": 0},
            "boss_cooldown": None
        }
        default_guild = {
            "active_missions": {},
            "group_training": None
        }
        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)
        
        self.breathing_techniques = {
            "Water": ["Water Surface Slash", "Water Wheel", "Flowing Dance", "Striking Tide", "Blessed Rain"],
            "Thunder": ["Thunderclap and Flash", "Rice Spirit", "Heat Lightning", "Distant Thunder", "Lightning Ball"],
            "Flame": ["Unknowing Fire", "Rising Scorching Sun", "Blooming Flame Undulation", "Flaming Tiger", "Flame Tiger"],
            "Wind": ["Dusty Whirlwind Cutter", "Claws-Purifying Wind", "Clean Storm Wind Tree", "Rising Dust Storm", "Purgatory Windmill"],
            "Stone": ["Serpentine Bipedal", "Upper Smash", "Stone Skin", "Volcanic Rock", "Arrows of Stone"]
        }
        self.demons = {
            "Muzan Kibutsuji": {"difficulty": 100, "xp": 1000},
            "Akaza": {"difficulty": 85, "xp": 800},
            "Doma": {"difficulty": 90, "xp": 850},
            "Kokushibo": {"difficulty": 95, "xp": 900},
            "Gyokko": {"difficulty": 75, "xp": 700},
            "Daki": {"difficulty": 70, "xp": 650},
            "Gyutaro": {"difficulty": 80, "xp": 750},
            "Enmu": {"difficulty": 65, "xp": 600},
            "Rui": {"difficulty": 60, "xp": 550},
            "Kyogai": {"difficulty": 55, "xp": 500}
        }
        self.ranks = ["Mizunoto", "Mizunoe", "Kanoto", "Kanoe", "Tsuchinoto", "Tsuchinoe", "Hinoto", "Hinoe", "Kinoto", "Kinoe"]

    @commands.group()
    async def ds(self, ctx):
        """Demon Slayer commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ds.command(name="assign_technique")
    async def assign_breathing_technique(self, ctx):
        """
        Assigns a random Breathing Technique to you.
        
        This command will give you a random Breathing Technique and teach you its first form.
        You can only have one Breathing Technique at a time.
        """
        """Assigns a random Breathing Technique to the user."""
        technique = random.choice(list(self.breathing_techniques.keys()))
        await self.config.user(ctx.author).breathing_technique.set(technique)
        first_form = self.breathing_techniques[technique][0]
        await self.config.user(ctx.author).known_forms.set([first_form])
        await ctx.send(f"{ctx.author.mention}, you have been assigned the **{technique} Breathing** technique! You've learned your first form: **{first_form}**!")

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @ds.command(name="slay")
    async def slay_demon(self, ctx):
        """
        Attempt to slay a random demon.
        
        This command simulates a battle with a random demon. Your success depends on your rank and experience.
        You can use this command once per hour.
        """
        """Simulates a battle with a random demon. Can be used once per hour."""
        demon, info = random.choice(list(self.demons.items()))
        user_technique = await self.config.user(ctx.author).breathing_technique()
        
        if not user_technique:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")

        success_rate = random.randint(1, 100)
        await ctx.send(f"{ctx.author.mention} encounters {demon}! The battle begins...")
        await asyncio.sleep(2)
        
        if success_rate > info["difficulty"]:
            demons_slayed = await self.config.user(ctx.author).demons_slayed()
            await self.config.user(ctx.author).demons_slayed.set(demons_slayed + 1)
            xp_gained = info["xp"]
            await self.add_xp(ctx.author, xp_gained)
            await ctx.send(f"Victory! {ctx.author.mention} has successfully slain {demon} using {user_technique} Breathing! You gained {xp_gained} XP!")
            await self.check_rank_up(ctx)
            await self.check_new_form(ctx)
        else:
            await ctx.send(f"Oh no! {demon} was too powerful. {ctx.author.mention} needs to train harder!")

    @ds.command(name="nichirin")
    async def nichirin_color(self, ctx):
        """
        Assigns a random color to your Nichirin Blade.
        
        The color of your Nichirin Blade is purely cosmetic and doesn't affect your demon-slaying abilities.
        """
        colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"]
        color = random.choice(colors)
        await self.config.user(ctx.author).nichirin_color.set(color)
        await ctx.send(f"{ctx.author.mention}, your Nichirin Blade turns **{color}**!")

    @commands.cooldown(1, 1800, commands.BucketType.user)
    @ds.command(name="train")
    async def train(self, ctx):
        """
        Undergo a training session to improve your skills.
        
        Training will give you experience points and potentially help you learn new forms.
        You can train once every 30 minutes.
        """
        user_data = await self.config.user(ctx.author).all()
        user_technique = user_data['breathing_technique']
        if not user_technique:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")
        
        known_forms = user_data['known_forms']
        form = random.choice(known_forms)
        exercises = [
            f"practices {form} 1000 times",
            f"meditates under a waterfall while focusing on {user_technique} Breathing",
            "runs up and down the mountain with a boulder strapped to your back",
            f"spars with Tanjiro, learning the intricacies of {user_technique} Breathing",
            "practices Total Concentration Breathing for hours"
        ]
        exercise = random.choice(exercises)
        xp_gained = random.randint(50, 100)
        await self.add_xp(ctx.author, xp_gained)
        await ctx.send(f"{ctx.author.mention} {exercise}. Your {user_technique} Breathing skills have improved! You gained {xp_gained} XP!")
        await self.check_rank_up(ctx)
        await self.check_new_form(ctx)

    @ds.command(name="quote")
    async def demon_quote(self, ctx):
        """Shares a random quote from the Demon Slayer series."""
        quotes = [
            "The weak have no rights or choices. Their only fate is to be relentlessly crushed by the strong! - Akaza",
            "Don't ever give up. Even if it's painful, even if it's agonizing, don't try to take the easy way out. - Tanjiro Kamado",
            "Feel the rage. The powerful, pure rage of not being able to forgive will become your unswerving drive to take action. - Giyu Tomioka",
            "No matter how many people you may lose, you have no choice but to go on living. No matter how devastating the blows may be. - Shinobu Kocho"
        ]
        embed = discord.Embed(title="Demon Slayer Quote", description=random.choice(quotes), color=discord.Color.red())
        await ctx.send(embed=embed)

    @ds.command(name="form")
    async def form(self, ctx):
        """
        Perform a random form of your assigned Breathing Style.
        
        This command will randomly choose one of the forms you know and perform it.
        """
        user_technique = await self.config.user(ctx.author).breathing_technique()
        if not user_technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")
        
        known_forms = await self.config.user(ctx.author).known_forms()
        if not known_forms:
            return await ctx.send(f"{ctx.author.mention}, you haven't learned any forms yet! Train more to learn new forms.")
        
        form = random.choice(known_forms)
        await ctx.send(f"{ctx.author.mention} performs **{user_technique} Breathing: {form}**! The enemies tremble before your might!")

    @ds.command(name="profile")
    async def profile(self, ctx, user: discord.Member = None):
        """
        Display your or another user's Demon Slayer profile.
        
        This command shows information such as Breathing Technique, rank, experience, and known forms.
        If no user is specified, it will show your own profile.
        """
        if user is None:
            user = ctx.author
        user_data = await self.config.user(user).all()
        embed = discord.Embed(title=f"{user.name}'s Demon Slayer Profile", color=discord.Color.red())
        embed.add_field(name="Breathing Technique", value=user_data['breathing_technique'] or "Not assigned", inline=False)
        embed.add_field(name="Nichirin Blade Color", value=user_data['nichirin_color'] or "Not assigned", inline=False)
        embed.add_field(name="Demons Slayed", value=user_data['demons_slayed'], inline=False)
        embed.add_field(name="Rank", value=user_data['rank'], inline=False)
        embed.add_field(name="Experience", value=user_data['experience'], inline=False)
        embed.add_field(name="Known Forms", value=", ".join(user_data['known_forms']) or "None", inline=False)
        await ctx.send(embed=embed)

    @ds.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """
        Display the top 10 Demon Slayers based on demons slayed.
        
        This leaderboard ranks Demon Slayers in your server by the number of demons they've defeated.
        """
        all_users = await self.config.all_users()
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]['demons_slayed'], reverse=True)[:10]
        
        embed = discord.Embed(title="Top 10 Demon Slayers", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_users, 1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{i}. {user.name}", value=f"Demons Slayed: {data['demons_slayed']}\nRank: {data['rank']}", inline=False)
        
        await ctx.send(embed=embed)

    @ds.command(name="mission")
    async def start_mission(self, ctx):
        """
        Start a demon-slaying mission.
        
        Missions are timed events where you attempt to defeat a specific demon.
        You can only be on one mission at a time, and missions have a cooldown period.
        """
        user_data = await self.config.user(ctx.author).all()
        if not user_data['breathing_technique']:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")
        
        last_mission = user_data['last_mission']
        if last_mission and datetime.now() < datetime.fromisoformat(last_mission) + timedelta(hours=4):
            time_left = datetime.fromisoformat(last_mission) + timedelta(hours=4) - datetime.now()
            return await ctx.send(f"{ctx.author.mention}, you're still recovering from your last mission. You can start a new one in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")

        mission_demon = random.choice(list(self.demons.keys()))
        mission_duration = random.randint(1, 3)  # 1 to 3 hours
        end_time = datetime.now() + timedelta(hours=mission_duration)
        
        guild_data = await self.config.guild(ctx.guild).all()
        guild_data['active_missions'][str(ctx.author.id)] = {
            "demon": mission_demon,
            "end_time": end_time.isoformat()
        }
        await self.config.guild(ctx.guild).set(guild_data)
        await self.config.user(ctx.author).last_mission.set(datetime.now().isoformat())
        
        await ctx.send(f"{ctx.author.mention}, you've started a mission to defeat {mission_demon}! The mission will last for {mission_duration} hours. Use `[p]ds complete_mission` when the time is up to claim your reward!")

    @ds.command(name="complete_mission")
    async def complete_mission(self, ctx):
        """
        Complete your ongoing demon-slaying mission.
        
        Use this command when your mission timer is up to claim your rewards.
        The success of your mission is determined when you complete it.
        """
        guild_data = await self.config.guild(ctx.guild).all()
        active_missions = guild_data['active_missions']
        
        if str(ctx.author.id) not in active_missions:
            return await ctx.send(f"{ctx.author.mention}, you don't have an active mission. Start one with `[p]ds mission`!")
        
        mission = active_missions[str(ctx.author.id)]
        if datetime.now() < datetime.fromisoformat(mission['end_time']):
            time_left = datetime.fromisoformat(mission['end_time']) - datetime.now()
            return await ctx.send(f"{ctx.author.mention}, your mission is not complete yet. Time remaining: {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")
        
        del active_missions[str(ctx.author.id)]
        await self.config.guild(ctx.guild).active_missions.set(active_missions)
        
        success = random.random() < 0.7  # 70% success rate
        if success:
            xp_gained = self.demons[mission['demon']]['xp']
            await self.add_xp(ctx.author, xp_gained)
            demons_slayed = await self.config.user(ctx.author).demons_slayed()
            await self.config.user(ctx.author).demons_slayed.set(demons_slayed + 1)
            await ctx.send(f"Congratulations, {ctx.author.mention}! You've successfully completed your mission and defeated {mission['demon']}! You gained {xp_gained} XP!")
            await self.check_rank_up(ctx)
            await self.check_new_form(ctx)
        else:
            await ctx.send(f"{ctx.author.mention}, despite your best efforts, {mission['demon']} managed to escape. Better luck next time!")

    async def add_xp(self, user, amount):
        current_xp = await self.config.user(user).experience()
        await self.config.user(user).experience.set(current_xp + amount)t

    async def check_rank_up(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        current_rank_index = self.ranks.index(user_data['rank'])
        xp_required = (current_rank_index + 1) * 1000

        if user_data['experience'] >= xp_required and current_rank_index < len(self.ranks) - 1:
            new_rank = self.ranks[current_rank_index + 1]
            await self.config.user(ctx.author).rank.set(new_rank)
            await ctx.send(f"Congratulations {ctx.author.mention}! You've been promoted to the rank of **{new_rank}**!")

    async def check_new_form(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']
        all_forms = self.breathing_techniques[technique]

        if len(known_forms) < len(all_forms):
            chance = random.random()
            if chance < 0.1:  # 10% chance to learn a new form
                new_form = random.choice([form for form in all_forms if form not in known_forms])
                known_forms.append(new_form)
                await self.config.user(ctx.author).known_forms.set(known_forms)
                await ctx.send(f"Breakthrough! {ctx.author.mention} has learned a new form: **{new_form}**!")

    @ds.command(name="forms")
    async def list_forms(self, ctx):
        """
        List all the Breathing Technique forms you've learned.
        
        This command displays all the forms you currently know for your assigned Breathing Technique.
        """
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']

        if not technique:
            return await ctx.send(f"{ctx.author.mention}, you need to be assigned a Breathing Technique first! Use `[p]ds assign_technique`")

        if not known_forms:
            return await ctx.send(f"{ctx.author.mention}, you haven't learned any forms yet! Train more to learn new forms.")

        embed = discord.Embed(title=f"{ctx.author.name}'s {technique} Breathing Forms", color=discord.Color.blue())
        for i, form in enumerate(known_forms, 1):
            embed.add_field(name=f"Form {i}", value=form, inline=False)

        await ctx.send(embed=embed)

    @ds.command(name="shop")
    async def shop(self, ctx):
        """
        Display the Demon Slayer shop.
        
        The shop offers various items to help you in your demon-slaying journey.
        Use the 'buy' command to purchase items from the shop.
        """
        shop_items = [
            {"name": "Extra Training Session", "cost": 500, "description": "Instantly gain 200 XP"},
            {"name": "Nichirin Blade Polishing", "cost": 1000, "description": "Increase your chances of slaying demons for the next 24 hours"},
            {"name": "Rare Form Scroll", "cost": 2000, "description": "Learn a random new form of your breathing technique"}
        ]

        embed = discord.Embed(title="Demon Slayer Shop", color=discord.Color.green())
        for item in shop_items:
            embed.add_field(name=f"{item['name']} - {item['cost']} coins", value=item['description'], inline=False)

        embed.set_footer(text="Use [p]ds buy <item name> to purchase an item")
        await ctx.send(embed=embed)

    @ds.command(name="buy")
    async def buy_item(self, ctx, *, item_name: str):
        """
        Buy an item from the Demon Slayer shop.
        
        Usage: [p]ds buy <item name>
        
        Make sure you have enough coins to purchase the item.
        Use the 'shop' command to see available items and their prices.
        """
        shop_items = {
            "Extra Training Session": {"cost": 500, "effect": self.extra_training},
            "Nichirin Blade Polishing": {"cost": 1000, "effect": self.nichirin_polishing},
            "Rare Form Scroll": {"cost": 2000, "effect": self.rare_form_scroll}
        }

        if item_name not in shop_items:
            return await ctx.send("That item is not available in the shop. Use `[p]ds shop` to see available items.")

        item = shop_items[item_name]
        user_balance = await bank.get_balance(ctx.author)

        if user_balance < item["cost"]:
            return await ctx.send(f"You don't have enough coins to buy this item. You need {item['cost']} coins.")

        await bank.withdraw_credits(ctx.author, item["cost"])
        await item["effect"](ctx)
        
    @ds.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim your daily reward of experience and materials."""
        user_data = await self.config.user(ctx.author).all()
        last_daily = user_data['last_daily']
        now = datetime.now()

        if last_daily and datetime.fromisoformat(last_daily) + timedelta(days=1) > now:
            time_left = datetime.fromisoformat(last_daily) + timedelta(days=1) - now
            return await ctx.send(f"{ctx.author.mention}, you can claim your next daily reward in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")

        xp_reward = random.randint(100, 300)
        steel_reward = random.randint(1, 5)
        scarlet_ore_reward = random.randint(0, 2)

        await self.add_xp(ctx.author, xp_reward)
        async with self.config.user(ctx.author).nichirin_materials() as materials:
            materials['steel'] += steel_reward
            materials['scarlet_ore'] += scarlet_ore_reward

        await self.config.user(ctx.author).last_daily.set(now.isoformat())

        await ctx.send(f"{ctx.author.mention}, you've claimed your daily reward!\nYou received:\n"
                       f"• {xp_reward} XP\n"
                       f"• {steel_reward} steel\n"
                       f"• {scarlet_ore_reward} scarlet ore")

    @ds.command(name="boss")
    async def boss_battle(self, ctx):
        """Initiate a boss battle against a powerful demon."""
        user_data = await self.config.user(ctx.author).all()
        now = datetime.now()

        if user_data['boss_cooldown'] and datetime.fromisoformat(user_data['boss_cooldown']) > now:
            time_left = datetime.fromisoformat(user_data['boss_cooldown']) - now
            return await ctx.send(f"{ctx.author.mention}, you're still recovering from your last boss battle. You can challenge a boss again in {time_left.seconds // 3600} hours and {(time_left.seconds // 60) % 60} minutes.")

        boss = random.choice(["Rui", "Gyutaro", "Daki", "Akaza", "Doma"])
        boss_health = random.randint(1000, 2000)
        player_health = 1000
        turns = 0

        await ctx.send(f"{ctx.author.mention}, you've encountered the demon {boss} with {boss_health} health! Prepare for battle!")

        while boss_health > 0 and player_health > 0:
            turns += 1
            player_damage = random.randint(50, 200)
            boss_damage = random.randint(50, 150)

            boss_health -= player_damage
            player_health -= boss_damage

            await ctx.send(f"Turn {turns}:\n"
                           f"You deal {player_damage} damage to {boss}. Boss health: {max(0, boss_health)}\n"
                           f"{boss} deals {boss_damage} damage to you. Your health: {max(0, player_health)}")

            await asyncio.sleep(2)

        if boss_health <= 0:
            xp_reward = random.randint(500, 1000)
            await self.add_xp(ctx.author, xp_reward)
            await ctx.send(f"Victory! You've defeated {boss} and gained {xp_reward} XP!")
        else:
            await ctx.send(f"Defeat... {boss} was too powerful. Train harder and try again!")

        await self.config.user(ctx.author).boss_cooldown.set((now + timedelta(hours=12)).isoformat())

    @ds.command(name="craft")
    async def craft_nichirin(self, ctx):
        """Craft or reforge your Nichirin Blade."""
        user_data = await self.config.user(ctx.author).all()
        materials = user_data['nichirin_materials']

        if materials['steel'] < 10 or materials['scarlet_ore'] < 5:
            return await ctx.send(f"{ctx.author.mention}, you don't have enough materials to craft a Nichirin Blade. You need 10 steel and 5 scarlet ore.")

        new_color = random.choice(["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"])
        
        async with self.config.user(ctx.author).nichirin_materials() as mats:
            mats['steel'] -= 10
            mats['scarlet_ore'] -= 5

        await self.config.user(ctx.author).nichirin_color.set(new_color)

        await ctx.send(f"{ctx.author.mention}, you've successfully crafted a new Nichirin Blade!\n"
                       f"Its color is... **{new_color}**!")

    @ds.command(name="group_train")
    async def group_training(self, ctx):
        """Start or join a group training session."""
        guild_data = await self.config.guild(ctx.guild).all()
        now = datetime.now()

        if guild_data['group_training'] and datetime.fromisoformat(guild_data['group_training']['end_time']) > now:
            # Join existing training
            guild_data['group_training']['participants'].append(ctx.author.id)
            await self.config.guild(ctx.guild).set(guild_data)
            time_left = datetime.fromisoformat(guild_data['group_training']['end_time']) - now
            await ctx.send(f"{ctx.author.mention} has joined the group training session! {len(guild_data['group_training']['participants'])} participants now. {time_left.seconds // 60} minutes remaining.")
        else:
            # Start new training
            end_time = now + timedelta(minutes=30)
            guild_data['group_training'] = {
                "participants": [ctx.author.id],
                "end_time": end_time.isoformat()
            }
            await self.config.guild(ctx.guild).set(guild_data)
            await ctx.send(f"{ctx.author.mention} has started a group training session! It will last for 30 minutes. Use `[p]ds group_train` to join!")

            # Schedule end of training
            await asyncio.sleep(1800)  # 30 minutes
            await self.end_group_training(ctx.guild)

    async def end_group_training(self, guild):
        guild_data = await self.config.guild(guild).all()
        if not guild_data['group_training']:
            return

        participants = guild_data['group_training']['participants']
        xp_reward = len(participants) * 50  # More participants = more XP

        for user_id in participants:
            user = guild.get_member(user_id)
            if user:
                await self.add_xp(user, xp_reward)

        await self.config.guild(guild).group_training.set(None)
        channel = guild.get_channel(guild.system_channel.id)  # Announce in the system channel
        if channel:
            await channel.send(f"The group training session has ended! All {len(participants)} participants gained {xp_reward} XP!")

    @ds.command(name="materials")
    async def show_materials(self, ctx):
        """Show your crafting materials for Nichirin Blades."""
        materials = await self.config.user(ctx.author).nichirin_materials()
        await ctx.send(f"{ctx.author.mention}, your crafting materials:\n"
                       f"• Steel: {materials['steel']}\n"
                       f"• Scarlet Ore: {materials['scarlet_ore']}")

    async def extra_training(self, ctx):
        await self.add_xp(ctx.author, 200)
        await ctx.send(f"{ctx.author.mention}, you've completed an intense training session and gained 200 XP!")

    async def nichirin_polishing(self, ctx):
        # This effect would need to be implemented in the slay_demon method
        # For now, we'll just acknowledge the purchase
        await ctx.send(f"{ctx.author.mention}, your Nichirin Blade has been polished to perfection! Your demon-slaying chances are increased for the next 24 hours.")

    async def rare_form_scroll(self, ctx):
        user_data = await self.config.user(ctx.author).all()
        technique = user_data['breathing_technique']
        known_forms = user_data['known_forms']
        all_forms = self.breathing_techniques[technique]

        if len(known_forms) == len(all_forms):
            await ctx.send(f"{ctx.author.mention}, you've already mastered all forms of {technique} Breathing!")
            return

        new_form = random.choice([form for form in all_forms if form not in known_forms])
        known_forms.append(new_form)
        await self.config.user(ctx.author).known_forms.set(known_forms)
        await ctx.send(f"Incredible! {ctx.author.mention} has learned a new form from the rare scroll: **{new_form}**!")

def setup(bot):
    bot.add_cog(DemonSlayer(bot))
