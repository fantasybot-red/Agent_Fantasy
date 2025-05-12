from typing import Literal

from discord.abc import Connectable
from mafic import Player, Track, SearchType, Playlist

from classs import AIContext, FClient


class MusicPlayer(Player[FClient]):
    current_track: Track | None
    queue: list[Track]
    history: list[Track]
    volume: int
    loop_mode: Literal["off", "track", "all"]

    def __init__(self, client: FClient, channel: Connectable) -> None:
        super().__init__(client, channel)
        self.current_track = None
        self.queue = []
        self.history = []
        self.volume = 100
        self.loop_mode = "off"

    async def play(
            self,
            track: Track | str, **kwargs: dict[str, str]
    ) -> None:
        # update status and do more
        await super().play(track, **kwargs)

    async def set_volume(self, volume: int, /) -> None:
        """
        Set the volume of the player.
        :param volume: Volume level (0-100)
        """
        self.volume = volume
        await super().set_volume(volume)

    async def play_track(self, track: Track):
        if self.current_track:
            self.queue.append(self.current_track)
            return {
                "success": True,
                "reason": "added track to queue",
                "track_name": track.title,
                "track_url": track.uri,
                "thumbnail": track.artwork_url,
                "player_info": self.get_player_status_short()
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
                },
                "player_info": self.get_player_status_short()
            }

    async def play_playlist(self, playlist: Playlist):
        if self.current_track:
            self.queue.extend(playlist.tracks)
            return {
                "success": True,
                "reason": "added playlist to queue",
                "playlist_track_length": len(playlist.tracks),
                "playlist_name": playlist.name,
                "player_info": self.get_player_status_short()
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
                },
                "player_info": self.get_player_status_short()
            }

    async def skip(self):
        if self.loop_mode == "track":
            await self.stop()
            await self.play(self.current_track)

        elif self.loop_mode == "all":
            if not self.queue:
                self.queue, self.history = self.history, []
            self.history.append(self.current_track)
            self.current_track = self.queue.pop(0)
            await self.stop()
            await self.play(self.current_track)

        elif self.queue:
            self.history.append(self.current_track)
            self.current_track = self.queue.pop(0)
            await self.stop()
            await self.play(self.current_track)

        else:
            await self.disconnect()
            return {"success": False, "reason": "no track to skip bot will disconnect"}

        return {
            "success": True,
            "reason": "skipped track",
            "current_playing_track": {
                "title": self.current_track.title,
                "url": self.current_track.uri,
                "thumbnail": self.current_track.artwork_url
            },
            "player_info": self.get_player_status_short()
        }


    async def previous(self):
        if self.loop_mode == "track":
            return {
                "success": False,
                "reason": "loop mode is track, cannot previous"
            }

        if self.history or (self.loop_mode == "all" and self.queue):
            self.queue.insert(0, self.current_track)
            self.current_track = self.history.pop() if self.history else self.queue.pop()
            await self.stop()
            await self.play(self.current_track)
            return {
                "success": True,
                "reason": "playing previous track",
                "current_playing_track": {
                    "title": self.current_track.title,
                    "url": self.current_track.uri,
                    "thumbnail": self.current_track.artwork_url
                },
                "player_info": self.get_player_status_short()
            }

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

    def loop(self, mode: Literal["off", "track", "all"]):
        """
        Set the loop mode of the player.
        :param mode: Loop mode (off, track, all)
        """
        if mode not in ["off", "track", "all"]:
            return {
                "success": False,
                "reason": "invalid loop mode"
            }
        self.loop_mode = mode
        return {
            "success": True,
            "reason": f"loop mode set to {mode}"
        }

    def get_status(self, success: bool, reason: str):
        return {
            "success": success,
            "reason": reason,
            "current_playing_track": {
                "title": self.current_track.title,
                "url": self.current_track.uri,
                "thumbnail": self.current_track.artwork_url
            },
            "player_info": self.get_player_status()
        }

    def get_player_status(self):
        position = self._fomart_ms(self.position)
        song_len = self._fomart_ms(self.current_track.length)
        data = self.get_player_status_short()
        data["track_length"] = song_len
        data["current_time"] = position
        return data

    def get_player_status_short(self):
        return {
            "volume": self.volume,
            "loop_mode": self.loop_mode,
        }

    def _fomart_ms(self, ms: int) -> str:
        """
        Fomart ms to mm:ss
        """
        seconds = (ms // 1000) % 60
        minutes = (ms // (1000 * 60)) % 60
        hours = (ms // (1000 * 60 * 60)) % 24
        return f"{hours}:{minutes}:{seconds}" if hours > 0 else f"{minutes}:{seconds}"
