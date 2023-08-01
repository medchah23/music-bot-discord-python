import discord
from discord.ext import commands
import youtube_dl
import logging

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='§', intents=intents)

current_song = None

# Set up custom logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use §tnbot_help for a list of commands.")


@bot.command(name="play")
async def play(ctx, *, query):
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None
    if not voice_channel:
        await ctx.send("Vous n'êtes pas connecté à un salon vocal.")
        return

    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
    elif not voice_client:
        voice_client = await voice_channel.connect()

    voice_client.stop()

    ydl_opts = {
    "format": "bestaudio/best",
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "verbose": True  # Add this line to enable verbose output
}


    async with ctx.typing():
        try:
            # Use youtube_dl to extract the direct audio stream URL
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = await bot.loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch:{query}", download=False)
                )
                url = info["formats"][0]["url"]
                title = info["title"]
                global current_song
                current_song = title
        except Exception as e:
            await ctx.send("Une erreur s'est produite lors de la récupération de l'audio.")
            print(e)  # Print the exception
            return

    ffmpeg_options = {
        "options": "-vn",
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    }

    voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options))
    channel = ctx.channel
    await channel.send(f"En train de jouer : **{title}**")


@bot.command(name='pause')
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Song paused.")
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='resume')
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Song resumed.")
    else:
        await ctx.send("The bot is not paused. Use the 'play' command to start playing a song.")


@bot.command(name="leave")
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name="stop")
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Song stopped.")
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='bot_help')
async def help_command(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available commands", color=discord.Color.blue())

    commands_list = [
        ("§play <search>", "Joins the voice channel and plays the audio from the provided search query in YouTube"),
        ("§pause", "Pauses the currently playing audio"),
        ("§resume", "Resumes the paused audio"),
        ("§leave", "Leaves the voice channel"),
        ("§stop", "Stops the currently playing audio"),
        ("§bot_help", "Displays this help message")
    ]

    for command, description in commands_list:
        embed.add_field(name=command, value=description, inline=False)

    embed.set_footer(text="Use §help <command> for more information about a specific command.")

    await ctx.send(embed=embed)


@bot.command(name='i')
async def increase_volume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        max_volume = 5.0  # Maximum volume limit
        if voice_client.source.volume < max_volume:
            voice_client.source.volume = max_volume
        await ctx.send(f"Volume set to maximum: {voice_client.source.volume}")
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='d')
async def decrease_volume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        if voice_client.source.volume > 2.0:
            voice_client.source.volume -= 0.1
        await ctx.send(f"Volume decreased to {voice_client.source.volume}")
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.event
async def on_ready():
    print(f"Logged in as: {bot.user.name.encode('unicode_escape').decode()}")
    print(f"ID: {bot.user.id}")
    global current_song
    if current_song:
        print(f"Now playing: {current_song}")


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and not after.channel:
        # Bot has been disconnected from the voice channel
        print("Bot has been disconnected from the voice channel.")


bot.run("MTEyNTk2MzkyOTAwMTE1MjUxMg.G8s8UP.Ad5sLW0ZZqttVP58Y4soCjGIkzJpMiJswuvx2g")
