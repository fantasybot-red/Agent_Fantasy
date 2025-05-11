from discord.abc import Connectable
from mafic import Player, Track, SearchType, Playlist

from classs import AIContext, FClient

class MusicPlayer(Player[FClient]):
    current_track: Track | None
    queue: list[Track]
    history: list[Track]

    def __init__(self, client: FClient, channel: Connectable) -> None:
        super().__init__(client, channel)
        self.current_track = None
        self.queue = []
        self.history = []

    async def play_track(self, track: Track):
        if self.current_track:
            self.queue.append(self.current_track)
            return {
                "success": True,
                "reason": "added track to queue",
                "track_name": track.title,
                "track_url": track.uri,
                "thumbnail": track.artwork_url
            }
        else:
            self.current_track = track
            await self.stop()
            await self.play(track)
            return {
                "success": True,
                "reason": "playing track",
                "current_playing_track": {
                    "title": track.title,
                    "url": track.uri,
                    "thumbnail": track.artwork_url
                }
            }

    async def play_playlist(self, playlist: Playlist):
        if self.current_track:
            self.queue.extend(playlist.tracks)
            return {
                "success": True,
                "reason": "added playlist to queue",
                "playlist_track_length": len(playlist.tracks),
                "playlist_name": playlist.name
            }
        else:
            self.current_track = playlist.tracks[0]
            await self.stop()
            await self.play(self.current_track)
            self.queue.extend(playlist.tracks[1:])
            return {
                "success": True,
                "reason": "playing playlist",
                "playlist_track_length": len(playlist.tracks),
                "playlist_name": playlist.name,
                "current_playing_track": {
                    "title": self.current_track.title,
                    "url": self.current_track.uri,
                    "thumbnail": self.current_track.artwork_url
                }
            }

    async def skip(self):
        if self.queue:
            self.history.append(self.current_track)
            self.current_track = self.queue.pop(0)
            await self.stop()
            await self.play(self.current_track)
            return {
                "success": True,
                "reason": "skipped track",
                "current_playing_track": {
                    "title": self.current_track.title,
                    "url": self.current_track.uri,
                    "thumbnail": self.current_track.artwork_url
                }
            }
        else:
            await self.disconnect()
            return {
                "success": False,
                "reason": "no track to skip bot will disconnect"
            }

    async def previous(self):
        if self.history:
            self.queue.insert(0, self.current_track)
            self.current_track = self.history.pop()
            await self.stop()
            await self.play(self.current_track)
            return {
                "success": True,
                "reason": "playing previous track",
                "current_playing_track": {
                    "title": self.current_track.title,
                    "url": self.current_track.uri,
                    "thumbnail": self.current_track.artwork_url
                }
            }
        else:
            return {
                "success": False,
                "reason": "no previous track to previous"
            }

    @classmethod
    def check_voice_status(cls, ctx: AIContext):
        if not ctx.author.voice:
            return {
                "success": False,
                "reason": "user are not in a voice channel"
            }
        elif ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                return {
                    "success": False,
                    "reason": "user are not in the same voice channel"
                }
        elif ctx.voice_client is None:
            return {
                "success": False,
                "reason": "bot is not connected to a voice channel"
            }
        return None

    @classmethod
    async def resolve(cls, ctx: AIContext, query: str) -> Track:
        if not ctx.author.voice:
            return {
                "success": False,
                "reason": "user are not in a voice channel"
            }
        elif ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                return {
                    "success": False,
                    "reason": "user are not in the same voice channel"
                }
        else:
            ctx.voice_client = await ctx.author.voice.channel.connect(cls=cls)

        track = await ctx.voice_client.fetch_tracks(query, SearchType.YOUTUBE_MUSIC)
        if not track:
            await ctx.voice_client.disconnect()
            return {
                "success": False,
                "reason": "no query found or url is invalid"
            }
        if isinstance(track, Playlist):
            return await ctx.voice_client.play_playlist(track)
        return await ctx.voice_client.play_track(track[0])
