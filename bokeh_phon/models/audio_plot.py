from bokeh.models import BoxAnnotation, ColumnDataSource, CustomJS
from bokeh.plotting import Figure
from bokeh.core.properties import Any, Float, String
from bokeh.util.compiler import TypeScript

import numpy as np

class AudioPlot(Figure):
    '''
A mono waveform plot and associated callbacks for client-side audio playback.

The `js_playxr_cb`, `js_playsel_cb`, and `js_playall_cb` play portions of
the plot data via javascript based on current plot attributes--the data in
the currently displayed x range, the currently selected indices, or all
data, respectively.

The `range_sel_cb` callback is a Python callback for changing the background
fill color of the selected plot range.

Note: The presence of the `range_sel_cb` callback requires that AudioPlot be
instantiated in a Bokeh app context. See example below.

Parameters
----------

samples: array
A numpy array of sample data. Will be cast to float32 values.

fs: num
The sample rate of the sampled data. Will be cast to float32.

Remaining arguments are passed to the base `Figure()` class that AudioPlot
inherits from.


Examples    
--------

```python
from bokeh_phon.models.audio_plot import AudioPlot
from bokeh.models import Button
from bokeh.io import show, output_notebook
from bokeh.layouts import column
import parselmouth
import numpy as np
output_notebook()

def myapp(doc):
    snd = parselmouth.Sound('myaudio.wav')
    ap = AudioPlot(
        samples=np.squeeze(snd.values),
        fs=snd.sampling_frequency,
        # Remaining arguments are passed to Figure().
        plot_height=200,
        toolbar_location='left'
    )
    playbtn = Button(label='Play all')
    playbtn.js_on_event('button_click', ap.js_playall_cb)
    col = column(playbtn, ap)
    doc.add_root(col)
    return doc
show(myapp)
```
    '''

    __implementation__ = TypeScript("""
import {Plot, PlotView} from "models/plots/plot"
import * as p from "core/properties"

export class AudioPlotView extends PlotView {
  model: AudioPlot

  render(): void {
    super.render()
    this.el.classList.add("bk-wav-plot")
  }
}

export namespace AudioPlot {
  export type Attrs = p.AttrsOf<Props>

  export type Props = Plot.Props & {
    fs: p.Property<number>
    xcol: p.Property<string | null>
    ycol: p.Property<string | null>
  }
}

export interface AudioPlot extends AudioPlot.Attrs {
  width: number | null
  height: number | null
}

export class AudioPlot extends Plot {
  properties: AudioPlot.Props

/*
This function plays any audio passed to it. Ideally we would
play the plot's own data automatically based on indexes passed
to its callback, but so far I have not been able to access some
AudioPlot attributes in a callback function. The data is
accessible via this.renderers[0].data_source.data, but .fs is
undefined.

TODO: figure out why model attributes are not available in js.
*/
  public playsig(sig: number[], fs: number): void {
    // For more on AudioBuffer usage see
    // https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer
    //
    let audioCtx = new AudioContext()

    // Create an empty mono buffer at the signal sample rate.
    let myArrayBuffer = audioCtx.createBuffer(1, sig.length, fs)

    const chan = 0
    // Fill the buffer with mysig.
    // This would be cleaner if mysig were of type Float32Array
    // so we could use copyToChannel().
    //myArrayBuffer.copyToChannel(mysig, chan);
    // This gives us the actual array that contains the data
    let nowBuffering = myArrayBuffer.getChannelData(chan)
    for (let i = 0; i < myArrayBuffer.length; i++) {
      nowBuffering[i] = sig[i]
    }

    // Get an AudioBufferSourceNode.
    // This is the AudioNode to use when we want to play an AudioBuffer
    let source = audioCtx.createBufferSource()
    source.buffer = myArrayBuffer
    source.connect(audioCtx.destination)
    // Start the source playing.
    source.start()
  }

  static init_AudioPlot(): void {
    this.prototype.default_view = AudioPlotView

    this.define<AudioPlot.Props>({
      fs:   [ p.Number ],
      xcol:   [ p.String    ],
      ycol:   [ p.String    ],
    })

    this.override({
      background_fill_alpha: 0.8,
      border_fill_alpha: 0.0,
    })
  }
}
""")

    fs = Float
    xcol = String('times')
    ycol = String('samples')
    wav = Any
    selbox = Any
    js_playall_cb = Any
    js_playsel_cb = Any
    js_playxr_cb = Any

    def range_sel_cb(self, attr, old, new):
        '''Handle data range selection event.''' 
        a = np.array(new)
        self.selbox.left = a.min() / self.fs
        self.selbox.right = a.max() / self.fs
        self.selbox.visible = True

    def __init__(self, samples=None, fs=None, *arg, **kwarg):
        if 'tools' not in kwarg:
            kwarg['tools'] = [
                'xbox_zoom', 'xbox_select', 'xwheel_zoom', 'xwheel_pan', 'reset'
            ]
        kwopts = {
            'toolbar_location': 'above'
        }
        kwopts.update(kwarg)
        super().__init__(*arg, **kwopts)
        self.toolbar.logo = None
        self.fs = np.float32(fs)
        data = {
            self.xcol: (np.arange(len(samples)) / self.fs).astype(np.float32),
            self.ycol: samples.astype(np.float32)
        }
        self.wav = self.line(
            self.xcol, self.ycol, source=ColumnDataSource(data), name='wav'
        )
        self.selbox = BoxAnnotation(
            visible=False, name='selbox'
        )
        self.add_layout(self.selbox)
        self.js_playall_cb = CustomJS(
            args=dict(plot=self, fs=self.fs, xcol=self.xcol, ycol=self.ycol),
            code='''
    const data = plot.renderers[0].data_source.data[ycol]
    if (data.length > 2) {
        plot.playsig(data, fs)
    }
'''
        )
        self.js_playsel_cb = CustomJS(
            args=dict(plot=self, fs=self.fs, xcol=self.xcol, ycol=self.ycol),
            code='''
    const data = plot.renderers[0].data_source.data[ycol]
    const indices = plot.renderers[0].data_source.selected.indices
    let s_idx = data.length;
    let e_idx = 0;
    for (let i = 0; i < data.length; i++) {
        if (indices[i] < s_idx) { s_idx = indices[i]; }
        if (indices[i] > e_idx) { e_idx = indices[i]; }
    }
    if (e_idx - s_idx > 2) {
        plot.playsig(data.slice(s_idx, e_idx), fs)
    }
'''
        )
        self.js_playxr_cb = CustomJS(
            args=dict(plot=self, fs=self.fs, xcol=self.xcol, ycol=self.ycol),
            code='''
    const data = plot.renderers[0].data_source.data[ycol]
    let s_idx = Math.round(plot.x_range.start * fs)
    if (s_idx < 0) { s_idx = 0 }
    let e_idx = Math.round(plot.x_range.end * fs)
    if (e_idx > data.length) { e_idx = data.length }
    if (e_idx - s_idx > 2) {
        plot.playsig(data.slice(s_idx, e_idx), fs)
    }
'''
        )
        self.wav.data_source.selected.on_change(
            'indices', self.range_sel_cb
        )

