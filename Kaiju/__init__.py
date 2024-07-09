from .kaiju8game import Kaiju8Game

async def setup(bot):
    await bot.add_cog(Kaiju8Game(bot))
