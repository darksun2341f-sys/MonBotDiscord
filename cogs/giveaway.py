import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

class GiveawayView(ui.View):
    def __init__(self, bot, giveaway_id):
        super().__init__()
        self.bot = bot
        self.giveaway_id = giveaway_id

    @ui.button(label="Participer", style=discord.ButtonStyle.green, emoji="🎉")
    async def participate(self, interaction: discord.Interaction, button: ui.Button):
        giveaway_file = Path(__file__).parent.parent / "database" / "giveaways.json"
        
        if giveaway_file.exists():
            with open(giveaway_file, 'r', encoding='utf-8-sig') as f:
                giveaways = json.load(f)
        else:
            giveaways = {}
        
        giveaway = giveaways.get(str(self.giveaway_id))
        if not giveaway:
            await interaction.response.send_message("❌ Giveaway introuvable!", ephemeral=True)
            return
        
        if str(interaction.user.id) in giveaway["participants"]:
            await interaction.response.send_message("❌ Vous participez déjà!", ephemeral=True)
            return
        
        giveaway["participants"].append(str(interaction.user.id))
        
        with open(giveaway_file, 'w', encoding='utf-8-sig') as f:
            json.dump(giveaways, f, indent=2)
        
        await interaction.response.send_message(f"✅ Vous participez au giveaway! ({len(giveaway['participants'])} participant(s))", ephemeral=True)

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaway_file = Path(__file__).parent.parent / "database" / "giveaways.json"
        self.giveaway_file.parent.mkdir(exist_ok=True)
        self.check_giveaways.start()

    @app_commands.command(name="giveaway", description="Crée un giveaway")
    @app_commands.describe(
        prize="Le prix du giveaway",
        duration="Durée en minutes",
        winners="Nombre de gagnants"
    )
    async def create_giveaway(self, interaction: discord.Interaction, prize: str, duration: int, winners: int = 1):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        if self.giveaway_file.exists():
            with open(self.giveaway_file, 'r', encoding='utf-8-sig') as f:
                giveaways = json.load(f)
        else:
            giveaways = {}
        
        giveaway_id = len(giveaways) + 1
        end_time = datetime.now() + timedelta(minutes=duration)
        
        giveaway_data = {
            "id": giveaway_id,
            "prize": prize,
            "end_time": end_time.isoformat(),
            "winners_count": winners,
            "participants": [],
            "channel_id": interaction.channel.id,
            "message_id": None
        }
        
        giveaways[str(giveaway_id)] = giveaway_data
        
        with open(self.giveaway_file, 'w', encoding='utf-8-sig') as f:
            json.dump(giveaways, f, indent=2)
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY!",
            description=f"**Prix:** {prize}\n**Gagnants:** {winners}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Fin dans", value=f"{duration} minutes", inline=False)
        embed.set_footer(text=f"ID: {giveaway_id}")
        
        msg = await interaction.response.send_message(embed=embed, view=GiveawayView(self.bot, giveaway_id))
        
        giveaway_data["message_id"] = msg.id
        with open(self.giveaway_file, 'w', encoding='utf-8-sig') as f:
            json.dump(giveaways, f, indent=2)

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        if not self.giveaway_file.exists():
            return
        
        with open(self.giveaway_file, 'r', encoding='utf-8-sig') as f:
            giveaways = json.load(f)
        
        now = datetime.now()
        to_remove = []
        
        for giveaway_id, giveaway in giveaways.items():
            end_time = datetime.fromisoformat(giveaway["end_time"])
            
            if now >= end_time and giveaway.get("finished") != True:
                to_remove.append(giveaway_id)
                
                if giveaway["participants"]:
                    winners = random.sample(giveaway["participants"], min(giveaway["winners_count"], len(giveaway["participants"])))
                    
                    channel = self.bot.get_channel(giveaway["channel_id"])
                    if channel:
                        winners_mentions = ", ".join([f"<@{w}>" for w in winners])
                        embed = discord.Embed(
                            title="🎊 Giveaway Terminé!",
                            description=f"**Gagnants:** {winners_mentions}\n**Prix:** {giveaway['prize']}",
                            color=discord.Color.gold()
                        )
                        await channel.send(embed=embed)
                    
                    giveaway["finished"] = True
        
        with open(self.giveaway_file, 'w', encoding='utf-8-sig') as f:
            json.dump(giveaways, f, indent=2)

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
