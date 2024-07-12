import logging
from redbot.core.bot import Red
from .onepiece import OnePieceBattle

log = logging.getLogger("red.onepiecebattle")

async def setup(bot: Red):
    cog = OnePieceBattle(bot)
    await bot.add_cog(cog)
    log.info("OnePieceBattle cog loaded")
