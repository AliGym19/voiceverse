#!/usr/bin/env python3
"""
Audio Enhancement Filters
Provides audio processing capabilities for TTS output
"""

import os
import io
import wave
import struct
import math
from typing import Optional, Tuple, List
from pathlib import Path


class AudioFilter:
    """
    Base class for audio filters
    """

    def __init__(self):
        self.sample_rate = 24000  # Default OpenAI TTS sample rate

    def read_audio(self, file_path: str) -> Tuple[bytes, int, int]:
        """
        Read audio file and return audio data, sample rate, and channels

        Returns:
            (audio_data, sample_rate, channels)
        """
        with wave.open(file_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            audio_data = wav_file.readframes(wav_file.getnframes())

        return audio_data, sample_rate, channels

    def write_audio(self, file_path: str, audio_data: bytes,
                   sample_rate: int = 24000, channels: int = 1):
        """Write audio data to file"""
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)

    def bytes_to_samples(self, audio_data: bytes) -> List[int]:
        """Convert audio bytes to sample list"""
        num_samples = len(audio_data) // 2
        return list(struct.unpack(f'{num_samples}h', audio_data))

    def samples_to_bytes(self, samples: List[int]) -> bytes:
        """Convert sample list to audio bytes"""
        return struct.pack(f'{len(samples)}h', *samples)


class VolumeFilter(AudioFilter):
    """Adjust audio volume"""

    def apply(self, file_path: str, gain: float = 1.0,
             output_path: Optional[str] = None) -> str:
        """
        Apply volume adjustment

        Args:
            file_path: Input audio file
            gain: Volume multiplier (0.5 = 50%, 2.0 = 200%)
            output_path: Output file path (defaults to input_enhanced.wav)

        Returns:
            Output file path
        """
        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_volume.wav")

        audio_data, sample_rate, channels = self.read_audio(file_path)
        samples = self.bytes_to_samples(audio_data)

        # Apply gain
        adjusted_samples = [
            max(-32768, min(32767, int(sample * gain)))
            for sample in samples
        ]

        adjusted_data = self.samples_to_bytes(adjusted_samples)
        self.write_audio(output_path, adjusted_data, sample_rate, channels)

        return output_path


class NoiseGateFilter(AudioFilter):
    """Remove low-level background noise"""

    def apply(self, file_path: str, threshold: float = 0.02,
             output_path: Optional[str] = None) -> str:
        """
        Apply noise gate

        Args:
            file_path: Input audio file
            threshold: Noise threshold (0.0 to 1.0)
            output_path: Output file path

        Returns:
            Output file path
        """
        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_noisegate.wav")

        audio_data, sample_rate, channels = self.read_audio(file_path)
        samples = self.bytes_to_samples(audio_data)

        # Calculate threshold in sample units
        threshold_value = int(32767 * threshold)

        # Apply noise gate
        gated_samples = [
            sample if abs(sample) > threshold_value else 0
            for sample in samples
        ]

        gated_data = self.samples_to_bytes(gated_samples)
        self.write_audio(output_path, gated_data, sample_rate, channels)

        return output_path


class NormalizeFilter(AudioFilter):
    """Normalize audio to maximum volume without clipping"""

    def apply(self, file_path: str, target_level: float = 0.95,
             output_path: Optional[str] = None) -> str:
        """
        Normalize audio

        Args:
            file_path: Input audio file
            target_level: Target level (0.0 to 1.0)
            output_path: Output file path

        Returns:
            Output file path
        """
        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_normalized.wav")

        audio_data, sample_rate, channels = self.read_audio(file_path)
        samples = self.bytes_to_samples(audio_data)

        # Find peak
        peak = max(abs(s) for s in samples)

        if peak == 0:
            # Silence - no normalization needed
            self.write_audio(output_path, audio_data, sample_rate, channels)
            return output_path

        # Calculate gain to reach target level
        target_peak = int(32767 * target_level)
        gain = target_peak / peak

        # Apply normalization
        normalized_samples = [
            max(-32768, min(32767, int(sample * gain)))
            for sample in samples
        ]

        normalized_data = self.samples_to_bytes(normalized_samples)
        self.write_audio(output_path, normalized_data, sample_rate, channels)

        return output_path


class FadeFilter(AudioFilter):
    """Apply fade in/out effects"""

    def apply(self, file_path: str, fade_in_ms: int = 0, fade_out_ms: int = 0,
             output_path: Optional[str] = None) -> str:
        """
        Apply fade effects

        Args:
            file_path: Input audio file
            fade_in_ms: Fade in duration in milliseconds
            fade_out_ms: Fade out duration in milliseconds
            output_path: Output file path

        Returns:
            Output file path
        """
        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_fade.wav")

        audio_data, sample_rate, channels = self.read_audio(file_path)
        samples = self.bytes_to_samples(audio_data)

        # Calculate fade samples
        fade_in_samples = int(sample_rate * fade_in_ms / 1000)
        fade_out_samples = int(sample_rate * fade_out_ms / 1000)

        # Apply fade in
        for i in range(min(fade_in_samples, len(samples))):
            factor = i / fade_in_samples
            samples[i] = int(samples[i] * factor)

        # Apply fade out
        start_fade_out = len(samples) - fade_out_samples
        for i in range(max(0, start_fade_out), len(samples)):
            factor = (len(samples) - i) / fade_out_samples
            samples[i] = int(samples[i] * factor)

        faded_data = self.samples_to_bytes(samples)
        self.write_audio(output_path, faded_data, sample_rate, channels)

        return output_path


class EqualizerFilter(AudioFilter):
    """Simple equalizer (bass/treble adjustment)"""

    def apply(self, file_path: str, bass: float = 1.0, treble: float = 1.0,
             output_path: Optional[str] = None) -> str:
        """
        Apply simple EQ

        Args:
            file_path: Input audio file
            bass: Bass level multiplier (affects low frequencies)
            treble: Treble level multiplier (affects high frequencies)
            output_path: Output file path

        Returns:
            Output file path

        Note: This is a simplified EQ using a basic high-pass/low-pass approach
        """
        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_eq.wav")

        audio_data, sample_rate, channels = self.read_audio(file_path)
        samples = self.bytes_to_samples(audio_data)

        # Simple moving average for bass (low-pass filter)
        # This is a very basic implementation
        if bass != 1.0:
            window_size = 5
            for i in range(window_size, len(samples) - window_size):
                avg = sum(samples[i-window_size:i+window_size+1]) // (window_size * 2 + 1)
                samples[i] = int(samples[i] + (avg - samples[i]) * (bass - 1.0))

        # High-pass for treble (difference from moving average)
        if treble != 1.0:
            window_size = 3
            for i in range(window_size, len(samples) - window_size):
                avg = sum(samples[i-window_size:i+window_size+1]) // (window_size * 2 + 1)
                diff = samples[i] - avg
                samples[i] = int(samples[i] + diff * (treble - 1.0))

        # Clamp values
        samples = [max(-32768, min(32767, s)) for s in samples]

        eq_data = self.samples_to_bytes(samples)
        self.write_audio(output_path, eq_data, sample_rate, channels)

        return output_path


class AudioEnhancer:
    """
    Combined audio enhancement pipeline
    """

    def __init__(self):
        self.volume = VolumeFilter()
        self.noise_gate = NoiseGateFilter()
        self.normalize = NormalizeFilter()
        self.fade = FadeFilter()
        self.equalizer = EqualizerFilter()

    def enhance(self, file_path: str, output_path: Optional[str] = None,
                options: Optional[dict] = None) -> str:
        """
        Apply enhancement pipeline

        Args:
            file_path: Input audio file
            output_path: Final output path
            options: Dict with enhancement options:
                - volume: Volume gain (default: 1.0)
                - noise_gate: Noise threshold (default: 0.02)
                - normalize: Target level (default: 0.95)
                - fade_in_ms: Fade in duration (default: 0)
                - fade_out_ms: Fade out duration (default: 0)
                - bass: Bass level (default: 1.0)
                - treble: Treble level (default: 1.0)

        Returns:
            Output file path
        """
        if options is None:
            options = {}

        if output_path is None:
            base = Path(file_path).stem
            output_path = str(Path(file_path).parent / f"{base}_enhanced.wav")

        # Work with temporary files
        temp_path = file_path

        # Apply filters in sequence
        if options.get('noise_gate', 0.02) > 0:
            temp_path = self.noise_gate.apply(
                temp_path,
                threshold=options.get('noise_gate', 0.02),
                output_path=f"{temp_path}.tmp1.wav"
            )

        if options.get('volume', 1.0) != 1.0:
            temp_path = self.volume.apply(
                temp_path,
                gain=options.get('volume', 1.0),
                output_path=f"{temp_path}.tmp2.wav"
            )

        if options.get('bass', 1.0) != 1.0 or options.get('treble', 1.0) != 1.0:
            temp_path = self.equalizer.apply(
                temp_path,
                bass=options.get('bass', 1.0),
                treble=options.get('treble', 1.0),
                output_path=f"{temp_path}.tmp3.wav"
            )

        if options.get('fade_in_ms', 0) > 0 or options.get('fade_out_ms', 0) > 0:
            temp_path = self.fade.apply(
                temp_path,
                fade_in_ms=options.get('fade_in_ms', 0),
                fade_out_ms=options.get('fade_out_ms', 0),
                output_path=f"{temp_path}.tmp4.wav"
            )

        # Always normalize as final step
        temp_path = self.normalize.apply(
            temp_path,
            target_level=options.get('normalize', 0.95),
            output_path=output_path
        )

        # Clean up temporary files
        for i in range(1, 5):
            tmp_file = f"{file_path}.tmp{i}.wav"
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

        return output_path

    def get_available_filters(self) -> List[str]:
        """Get list of available filters"""
        return ['volume', 'noise_gate', 'normalize', 'fade', 'equalizer']

    def get_filter_info(self) -> dict:
        """Get information about available filters"""
        return {
            'volume': {
                'description': 'Adjust audio volume',
                'parameters': {'gain': 'Volume multiplier (0.5-2.0)'}
            },
            'noise_gate': {
                'description': 'Remove background noise',
                'parameters': {'threshold': 'Noise threshold (0.0-0.1)'}
            },
            'normalize': {
                'description': 'Maximize volume without clipping',
                'parameters': {'target_level': 'Target level (0.8-1.0)'}
            },
            'fade': {
                'description': 'Apply fade in/out effects',
                'parameters': {
                    'fade_in_ms': 'Fade in duration (ms)',
                    'fade_out_ms': 'Fade out duration (ms)'
                }
            },
            'equalizer': {
                'description': 'Adjust bass and treble',
                'parameters': {
                    'bass': 'Bass level (0.5-2.0)',
                    'treble': 'Treble level (0.5-2.0)'
                }
            }
        }


if __name__ == '__main__':
    # Test audio enhancer
    enhancer = AudioEnhancer()
    print("Audio Enhancer initialized")
    print(f"Available filters: {enhancer.get_available_filters()}")
    print("\nFilter information:")
    for name, info in enhancer.get_filter_info().items():
        print(f"  {name}: {info['description']}")
