from classs import Module, tool, MusicPlayer
from classs.AIContext import AIContext

class MusicControl(Module):


    @tool(
        query="Search query for music or music URL",
    )
    async def play_music(self, ctx: AIContext, query: str):
        """
        Play music from a given query or URL.
        - Support YouTube, Spotify, SoundCloud, and other music platforms.
        - This function will play the music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        return await MusicPlayer.resolve(ctx, query)

    @tool()
    async def pause_music(self, ctx: AIContext):
        """
        Pause the current music.
        - This function will pause the music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        if not ctx.voice_client.paused:
            await ctx.voice_client.pause()
            return {
                "success": True,
                "reason": "paused music",
                "current_playing_track": {
                    "title": ctx.voice_client.current_track.title,
                    "url": ctx.voice_client.current_track.uri,
                    "thumbnail": ctx.voice_client.current_track.artwork_url
                }
            }
        else:
            return {
                "success": False,
                "reason": "music is already paused"
            }

    @tool()
    async def resume_music(self, ctx: AIContext):
        """
        Resume the current music.
        - This function will resume the music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        if ctx.voice_client.paused:
            await ctx.voice_client.resume()
            return {
                "success": True,
                "reason": "resumed music",
                "current_playing_track": {
                    "title": ctx.voice_client.current_track.title,
                    "url": ctx.voice_client.current_track.uri,
                    "thumbnail": ctx.voice_client.current_track.artwork_url
                }
            }
        else:
            return {
                "success": False,
                "reason": "music is not paused"
            }

    @tool()
    async def stop_music(self, ctx: AIContext):
        """
        Stop the current music and disconnect the bot.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        await ctx.voice_client.disconnect()
        return {
            "success": True,
            "reason": "stopped music and disconnected bot"
        }

    @tool()
    async def skip_music(self, ctx: AIContext):
        """
        Skip the current music.
        - This function will skip the music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        return await ctx.voice_client.skip()

    @tool()
    async def previous_music(self, ctx: AIContext):
        """
        Play the previous music.
        - This function will play the previous music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        return await ctx.voice_client.previous()

    @tool()
    async def current_playing(self, ctx: AIContext):
        """
        Get the current playing music.
        - This function will get the current playing music in the voice channel.
        - You MUST embed `current_playing_track` to display.
        - You should give all information to user.
        """
        check = MusicPlayer.check_voice_status(ctx)
        if check:
            return check
        return {
            "success": True,
            "reason": "current playing track",
            "current_playing_track": {
                "title": ctx.voice_client.current_track.title,
                "url": ctx.voice_client.current_track.uri,
                "thumbnail": ctx.voice_client.current_track.artwork_url
            }
        }

async def setup(client):
    await client.add_module(MusicControl(client))
