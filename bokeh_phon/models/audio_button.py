from bokeh.core.properties import String, Float, Instance, List
from bokeh.models import Button, ColumnDataSource
from bokeh.util.compiler import TypeScript
import numpy as np

TS_CODE='''
import {Button, ButtonView} from "models/widgets/button"
import {ColumnDataSource} from "models/sources/column_data_source"
import {ButtonClick} from "core/bokeh_events"
import * as p from "core/properties"

export class AudioButtonView extends ButtonView {
  model: AudioButton

  click(): void {
    this.play()
    this.model.trigger_event(new ButtonClick())
    super.click()
  }

  private _time2idx(time: number, attr: string): number {
    let idx: number = Math.round(time * this.model.fs)
    if (attr == "start" && idx < 0) {
      idx = 0
    }
    else if (attr == "end") {
      const names: Array<string> = this.model.channels
      const name: string = names[0]
      const sig = this.model.source.data[name]
      const maxidx = sig.length
      if (idx > maxidx) {
        idx = maxidx
      }
    }
    return idx
  }

  public play(): void {
    const sidx = this._time2idx(this.model.start, "start")
    const eidx = this._time2idx(this.model.end, "end")

    // For more on AudioBuffer usage see
    // https://developer.mozilla.org/en-US/docs/Web/API/AudioBuffer
    //
    let audioCtx = new AudioContext()

    // Create an empty mono buffer at the signal sample rate.
    let myArrayBuffer = audioCtx.createBuffer(
        this.model.channels.length,
        eidx - sidx + 1,
        this.model.fs
    )

    // Fill the buffer with mysig.
    // This would be cleaner if mysig were of type Float32Array
    // so we could use copyToChannel().
    //myArrayBuffer.copyToChannel(mysig, chan);
    // This gives us the actual array that contains the data
    const names: Array<string> = this.model.channels
    for (let channel = 0; channel < myArrayBuffer.numberOfChannels; channel++) {
      let nowBuffering = myArrayBuffer.getChannelData(channel)
      const name: string = names[channel]
      const sig = this.model.source.data[name]
      for (let i = 0; i < myArrayBuffer.length; i++) {
        nowBuffering[i] = sig[sidx + i]
      }
    }

    // Get an AudioBufferSourceNode.
    // This is the AudioNode to use when we want to play an AudioBuffer
    let source = audioCtx.createBufferSource()
    source.buffer = myArrayBuffer
    source.connect(audioCtx.destination)
    // Start the source playing.
    source.start()
  }

}

export namespace AudioButton {
  export type Attrs = p.AttrsOf<Props>

  export type Props = Button.Props & {
    channels: p.Property<string[]>
    end: p.Property<number>
    fs: p.Property<number>
    source: p.Property<ColumnDataSource>
    start: p.Property<number>
   }
}

export interface AudioButton extends AudioButton.Attrs {}

export class AudioButton extends Button {
  properties: AudioButton.Props
  __view_type__: AudioButtonView

  constructor(attrs?: Partial<AudioButton.Attrs>) {
    super(attrs)
  }

  static init_AudioButton(): void {
    this.prototype.default_view = AudioButtonView

    this.define<AudioButton.Props>({
      channels: [ p.Array, [] ],
      end:    [ p.Number, Infinity ],
      fs:     [ p.Number ],
      source: [ p.Instance ],
      start:  [ p.Number, 0.0 ],
     })

    this.override({
      label: "",
    })
  }
}
'''

class AudioButton(Button):
    ''' A button that implements client-side audio playback.
    '''

    # TODO: Figure out why installation fails when the TypeScript code
    # is  included as a separate .ts file. It isn't copied along with
    # the .py file.
    #__implementation__ = 'audio_button.ts'
    __implementation__ = TypeScript(TS_CODE)

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
