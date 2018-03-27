#!/usr/bin/python
# Program for recording a wave file until either enter is pressed or an interrupt
# (ctrl+c / SIGINT) is caught.
# The arguments used for this program are based on the Linux ALSA 'arecord' program.
# This module is also importable.

from pyaudio import PyAudio, paFloat32, paInt32, paInt24, paInt16, paInt8, paUInt8, \
    paCustomFormat
import wave
import time
import sys
import argparse
from threading import Thread


class RecordingThread(Thread):
    """
    Thread that records audio until the `stop_recording` method is called, then
    writes the recorded audio into a wave file, by default 'output.wav'.
    """
    def __init__(self, args):
        parser = argparse.ArgumentParser(
            prog="pa_record",
            description="Record audio into a .wav file using pyaudio.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("--output", default="output.wav",
                            help="Output .wav file path.")
        parser.add_argument("--rate", type=int, default=8000,
                            help="Sampling rate in Hertz.")

        # Valid PortAudio sample formats
        formats = {
            "paFloat32": paFloat32,            # 32 bit float
            "paInt32": paInt32,                # 32 bit int
            "paInt24": paInt24,                # 24 bit int
            "paInt16": paInt16,                # 16 bit int
            "paInt8": paInt8,                  # 8 bit int
            "paUInt8": paUInt8,                # 8 unsigned bit int
            "paCustomFormat": paCustomFormat,  # a custom data format
        }

        def pa_sample_format(s):
            # If the specified format is invalid, raise a ValueError so that a usage
            # message is displayed and the program exits.
            if s not in formats:
                raise ValueError
            return formats[s]
        
        parser.add_argument("--format", help="PortAudio sample format to use.",
                            type=pa_sample_format, default="paUInt8",
                            dest="pa_format")
        parser.add_argument("--device", type=int, default=-1, help="Index of the "
                            "input device to use. If unspecified or less than zero, "
                            "the default input device will be used.")
        parser.add_argument("--channels", type=int, default=1,
                            help="The number of channels to use.")
        parser.add_argument("--chunk", type=int, default=1024,
                            help="The size of frames read from the stream.")

        # TODO Make shell autocompletion work using argcomplete:
        # https://argcomplete.readthedocs.io/en/latest/
        # argcomplete.autocomplete(parser)

        # Parse args if it isn't None or empty or use sys.argv instead
        if args:
            self.args = parser.parse_args(args)
        else:
            self.args = parser.parse_args()

        self._recording = False
        super(RecordingThread, self).__init__()

    def stop_recording(self):
        self._recording = False

    def run(self):
        # Get data from the parsed arguments
        CHUNK = self.args.chunk
        FORMAT = self.args.pa_format
        CHANNELS = self.args.channels
        RATE = self.args.rate
        DEVICE_INDEX = self.args.device
        if DEVICE_INDEX < 0:
            DEVICE_INDEX = None
        WAVE_OUTPUT_FILENAME = self.args.output

        # Initialise a PyAudio connection and open a stream.
        p = PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=DEVICE_INDEX,
                        frames_per_buffer=CHUNK)

        # Set up the output wave file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)

        # Record into the specified file (or stdout) until interrupted.
        self._recording = True
        while self._recording:
            wf.writeframes(stream.read(CHUNK))
            time.sleep(0.05)  # not sure if we need this

        # Stop and close the stream, close the file and terminate the PyAudio
        # connection.
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()


def record(args):
    """
    Record from an audio device until enter or ctrl+c is pressed.
    :param args: argument list
    """
    t = RecordingThread(args)
    t.start()
    try:
        read = raw_input
    except NameError:
        read = input

    # Wait until enter is pressed or an interrupt is caught (ctrl+c), then
    # stop recording and write the .wav file.
    try:
        read()
    except KeyboardInterrupt:
        t.stop_recording()
    else:
        t.stop_recording()


if __name__ == "__main__":
    # Record and let argparse use sys.argv for arguments
    record(sys.argv[1:])
