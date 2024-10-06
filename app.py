import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import yt_dlp

load_dotenv()

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Required to process message content
bot = commands.Bot(command_prefix='?', intents=intents)

queues = {}
voice_clients = {}
yt_dl_options = {'format': 'bestaudio/best'}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)
ffmpeg = {'options': '-vn'}


def create_embed(title, description,url=None, uploader=None, upload_date=None, duration=None, thumbnail=None,
                 view_count=None, like_count=None, color=discord.Color.pink()):

    embed = discord.Embed(title=title, color=color, description=description)

    # Add video URL as a field if available
    if url:
        embed.add_field(name="Watch Video", value=f"[Click Here]({url})", inline=False)

    # Add uploader info if available
    if uploader:
        embed.add_field(name="Uploaded by", value=uploader, inline=True)

    # Add upload date if available
    if upload_date:
        embed.add_field(name="Upload Date", value=upload_date, inline=True)

    # Add duration if available
    if duration:
        embed.add_field(name="Duration", value=f"{duration // 60} minutes, {duration % 60} seconds", inline=True)

    # Add view count if available
    if view_count:
        embed.add_field(name="Views", value=f"{view_count:,}", inline=True)

    # Add like count if available
    if like_count:
        embed.add_field(name="Likes", value=f"{like_count:,}", inline=True)

    # Add thumbnail if available
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    embed.set_author(name='Muse',
                     icon_url='https://cdn.discordapp.com/attachments/1292575373434949673/1292575419085881560/c114123eb48fc0712b2482264414d9d7-ezgif.com-crop.gif?ex=67043c2a&is=6702eaaa&hm=59f7f9bb9f2217617a1ce8c7335b247d96705a75855b2fafb8c91e45c1d4f32d&')
    embed.set_footer(text='Prefix - ?, Commands - play,resume,pause,stop',
                     icon_url='https://cdn.discordapp.com/attachments/1292575373434949673/1292575419534544978/giphy-ezgif.com-crop_1.gif?ex=67043c2a&is=6702eaaa&hm=cd0b70dabc51ed875e26b526283f5ba6f33381fc01e613002d9bb62c5cea2084&')

    return embed

@bot.event
async def on_ready():
    print('Muse is ready')

async def play_next(ctx):
    if queues[ctx.guild.id]:  # If there are songs left in the queue
        song = queues[ctx.guild.id].pop(0)  # Get the next song from the queue
        await play(ctx, song['search'], from_queue=True)

@bot.command()
async def play(ctx, *, search: str, from_queue=False):
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        voice_clients[ctx.guild.id] = voice_client

        loop = asyncio.get_event_loop()

        # Check if the input is a URL or a search query
        if search.startswith("http"):  # If it's a URL
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        else:  # If it's a search keyword
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search}", download=False))
            data = data['entries'][0]  # Get the first result from search

        # Retrieve song data
        song_url = data.get('url')
        song_title = data.get('title', 'Unknown Title')  # Fallback to 'Unknown Title' if title is missing
        uploader = data.get('uploader', 'Unknown Uploader')
        upload_date = data.get('upload_date', 'Unknown Date')
        duration = data.get('duration', 0)
        thumbnail = data.get('thumbnail')
        view_count = data.get('view_count', 0)
        like_count = data.get('like_count', 0)

        player = discord.FFmpegOpusAudio(song_url, **ffmpeg)
        voice_clients[ctx.guild.id].play(player)

        # Create embed with all the relevant metadata
        embed = create_embed(
            title=song_title,
            description='',
            url=song_url,
            uploader=uploader,
            upload_date=upload_date,
            duration=duration,
            thumbnail=thumbnail,
            view_count=view_count,
            like_count=like_count,
        )
        await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
        voice_clients[ctx.guild.id].pause()
        embed = create_embed(title = 'Paused', color=discord.Color.yellow(), description = 'Muse has been paused')
        await ctx.send(embed=embed)


@bot.command()
async def resume(ctx):
        voice_clients[ctx.guild.id].resume()
        embed = create_embed("Resumed", "The song has been resumed.", color=discord.Color.green())
        await ctx.send(embed=embed)


@bot.command()
async def stop(ctx):
        voice_clients[ctx.guild.id].stop()
        await voice_clients[ctx.guild.id].disconnect()
        embed = create_embed("Stopped", "The music has been stopped and the bot has disconnected.",
                             color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    latency  = bot.latency*1000
    embed = create_embed("Ping 🛰️", f'Pong! Latency: {latency:.2f} ms',
                         color=discord.Color.blue())
    await ctx.send(embed=embed)

bot.run(TOKEN)