from .kaiju8 import Kaiju8

async def setup(bot):
    await bot.add_cog(Kaiju8(bot))
