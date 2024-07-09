from redbot.core import commands
import random
import asyncio

class DemonSlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.breathing_techniques = [
            "Water Breathing", "Thunder Breathing", "Flame Breathing",
            "Wind Breathing", "Stone Breathing", "Sound Breathing",
            "Love Breathing", "Mist Breathing", "Flower Breathing",
            "Serpent Breathing", "Insect Breathing"
        ]
        self.demons = [
            "Muzan Kibutsuji", "Akaza", "Doma", "Kokushibo", "Gyokko",
            "Daki", "Gyutaro", "Enmu", "Rui", "Kyogai"
        ]

    @commands.command()
    async def breathing_technique(self, ctx):
        """Assigns a random Breathing Technique to the user."""
        technique = random.choice(self.breathing_techniques)
        await ctx.send(f"{ctx.author.mention}, your Breathing Technique is: **{technique}**!")

    @commands.command()
    async def slay_demon(self, ctx):
        """Simulates a battle with a random demon."""
        demon = random.choice(self.demons)
        success = random.choice([True, False])
        
        await ctx.send(f"{ctx.author.mention} encounters {demon}! The battle begins...")
        await asyncio.sleep(2)
        
        if success:
            await ctx.send(f"Victory! {ctx.author.mention} has successfully slain {demon}!")
        else:
            await ctx.send(f"Oh no! {demon} was too powerful. {ctx.author.mention} needs to train harder!")

    @commands.command()
    async def nichirin_color(self, ctx):
        """Assigns a random color to the user's Nichirin Blade."""
        colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet", "Black", "White"]
        color = random.choice(colors)
        await ctx.send(f"{ctx.author.mention}, your Nichirin Blade turns **{color}**!")

    @commands.command()
    async def train(self, ctx):
        """Simulates a training session to improve your skills."""
        exercises = ["swings your sword 1000 times", "practices Water Breathing forms",
                     "meditates under a waterfall", "runs up and down the mountain",
                     "spars with Tanjiro", "practices Total Concentration Breathing"]
        exercise = random.choice(exercises)
        await ctx.send(f"{ctx.author.mention} {exercise}. Your skills have improved!")

    @commands.command()
    async def demon_quote(self, ctx):
        """Shares a random quote from the Demon Slayer series."""
        quotes = [
            "The weak have no rights or choices. Their only fate is to be relentlessly crushed by the strong! - Akaza",
            "Don't ever give up. Even if it's painful, even if it's agonizing, don't try to take the easy way out. - Tanjiro Kamado",
            "Feel the rage. The powerful, pure rage of not being able to forgive will become your unswerving drive to take action. - Giyu Tomioka",
            "No matter how many people you may lose, you have no choice but to go on living. No matter how devastating the blows may be. - Shinobu Kocho"
        ]
        await ctx.send(random.choice(quotes))

    @commands.command()
    async def form(self, ctx, breathing_style: str):
        """Perform a random form of the specified Breathing Style."""
        forms = {
            "water": ["First Form: Water Surface Slash", "Second Form: Water Wheel", "Third Form: Flowing Dance", "Tenth Form: Constant Flux"],
            "thunder": ["First Form: Thunderclap and Flash", "Second Form: Rice Spirit", "Fifth Form: Heat Lightning", "Seventh Form: Honoikazuchi no Kami"],
            "flame": ["First Form: Unknowing Fire", "Second Form: Rising Scorching Sun", "Fourth Form: Blooming Flame Undulation", "Ninth Form: Rengoku"]
        }
        breathing_style = breathing_style.lower()
        if breathing_style in forms:
            form = random.choice(forms[breathing_style])
            await ctx.send(f"{ctx.author.mention} performs **{form}**! The enemies tremble before your might!")
        else:
            await ctx.send(f"Sorry, I don't know any forms for {breathing_style.capitalize()} Breathing. Try water, thunder, or flame!")

def setup(bot):
    bot.add_cog(DemonSlayer(bot))