from bokeh.core.properties import String, Float, Instance, List
from bokeh.models import Button, ColumnDataSource
import numpy as np

class AudioButton(Button):
    ''' A button that implements client-side audio playback.
    '''
    __implementation__ = "audio_button.ts"

    channels = List(String, help="""
    The list of column names in `source` that identify the audio channels.
    """)
    end = Float(np.Inf, help="""
    The time in seconds of the last sample in `source` for playback.
    """)
    fs = Float(help="""
    The sample rate of the audio signal in `source`.
    """)
    source = Instance(ColumnDataSource, help="""
    A dict of audio signal data, including at least one column of sample
    data and a column of sample times (named 'seconds').
    """)
    start = Float(0.0, help="""
    The time in seconds of the first sample in `source` for playback.
    """)
