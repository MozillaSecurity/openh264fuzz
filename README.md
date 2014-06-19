OpenH264Fuzz
============

A leightweight fuzzer for the encoder and decoder of OpenH264


###Usage Examples
---


Fuzzing the decoder:

    ./fuzzer.py -decoder -decbin $HOME/dev/repos/openh264/h264dec -worker 4


Fuzzing the encoder:

    ./fuzzer.py -encoder -encbin $HOME/dev/repos/openh264/h264enc -worker 4


Fuzzing the encoder and decoder:

    ./fuzzer.py -encoder -encbin $HOME/dev/repos/openh264/h264enc -decbin $HOME/dev/repos/openh264/h264dec -worker 4



###Help Menu
---

    usage: fuzzer.py [-h] [-decoder] [-encoder] [-decbin path] [-encbin path]
                     [-count #] [-bucket path] [-samples path] [-resources path]
                     [-symbolizer path] [-ubsan] [-log LOGLEVEL] [-worker #]
    
    Fuzzer: OpenH264
    
    optional arguments:
      -h, --help        show this help message and exit
      -decoder
      -encoder
      -decbin path
      -encbin path
      -count #
      -bucket path
      -samples path
      -resources path
      -symbolizer path
      -ubsan
      -log LOGLEVEL
      -worker #

