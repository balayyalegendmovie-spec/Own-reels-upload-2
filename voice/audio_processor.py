"""
Audio Processor V4

Humanizes TTS voice with broadcast-quality audio processing.
Uses FFmpeg filters for EQ warmth, compression, and loudness normalization.
Avoids artificial echo.
"""
import ffmpeg
import logging
import os

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        pass

    def humanize_voice(self, input_path: str, output_path: str):
        """
        Apply production-quality audio processing to TTS voice.
        
        Chain:
          1. highpass=f=80       → Remove rumble/DC offset
          2. bass=g=2            → Subtle warmth
          3. equalizer           → Presence boost at 200Hz
          4. acompressor         → Soft dynamic range compression
          5. loudnorm            → Broadcast loudness normalization
          6. volume              → Final level adjustment
          
        NO artificial echo. Goal: natural young woman recording on a phone mic.
        """
        logger.info(f"Processing audio: {input_path}")
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input audio not found: {input_path}")
            
        try:
            stream = ffmpeg.input(input_path)
            
            # 1. High-pass filter to remove rumble
            stream = ffmpeg.filter_(stream, 'highpass', f=80)
            
            # 2. Subtle bass warmth (not boomy, just warm)
            stream = ffmpeg.filter_(stream, 'bass', g=2, f=150)
            
            # 3. Presence EQ
            stream = ffmpeg.filter_(stream, 'equalizer', f=200, t='q', width=1.0, g=2)
            
            # 4. Soft compression
            stream = ffmpeg.filter_(stream, 'acompressor',
                                    threshold=0.02, ratio=2, attack=10, release=200)
            
            # 5. Loudness normalization (EBU R128)
            stream = ffmpeg.filter_(stream, 'loudnorm',
                                    I=-16, LRA=11, TP=-1.5)
            
            # 6. Final volume
            stream = ffmpeg.filter_(stream, 'volume', 1.1)
            
            out, err = (
                ffmpeg
                .output(stream, output_path)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Successfully processed audio to {output_path}")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode('utf8')}")
            raise

    def mix_with_ducking(self, voice_path: str, music_path: str, output_path: str, music_volume: float = 0.2):
        """
        Mixes voice and music, applying sidechain compression to the music track 
        so it ducks (lowers volume) when the voice speaks.
        """
        logger.info(f"Mixing voice and music with ducking: {voice_path} + {music_path} -> {output_path}")
        
        if not os.path.exists(voice_path) or not os.path.exists(music_path):
            raise FileNotFoundError("Voice or music file not found for mixing.")
            
        try:
            voice = ffmpeg.input(voice_path)
            # Adjust music volume initially before ducking
            music = ffmpeg.input(music_path).filter('volume', music_volume)
            
            # Apply sidechaincompress
            # music is input 0, voice is input 1 (sidechain)
            # But ffmpeg-python sidechaincompress syntax needs inputs in correct order
            # The syntax is sidechaincompress=threshold=xxx...
            
            # Using amix or aformat... 
            # Simple fallback to ensure it works in basic setups:
            # We can use sidechaincompress: 
            compressed_music = ffmpeg.filter([music, voice], 'sidechaincompress', threshold=0.01, ratio=4.0, attack=20, release=200)
            
            # Then mix the compressed music with the original voice
            mixed = ffmpeg.filter([compressed_music, voice], 'amix', inputs=2, duration='first', dropout_transition=2)
            
            (
                ffmpeg
                .output(mixed, output_path)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Successfully mixed audio to {output_path}")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error in mix_with_ducking: {e.stderr.decode('utf8')}")
            raise
