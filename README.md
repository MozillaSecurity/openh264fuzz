OpenH264Fuzz
============

A lightweight fuzzer for the encoder and decoder of OpenH264


###Usage Examples
---


Fuzzing the decoder:

    % ./fuzzer.py -decoder -decbin $HOME/dev/repos/openh264/h264dec -workers 4


Fuzzing the encoder:

    % ./fuzzer.py -encoder -encbin $HOME/dev/repos/openh264/h264enc -workers 4


Fuzzing the encoder and decoder:

    % ./fuzzer.py -encoder -encbin $HOME/dev/repos/openh264/h264enc -decbin $HOME/dev/repos/openh264/h264dec -workers 4


See fuzzing results:
    
    % ./faults.sh
 
Filter fuzzing results:
    
    % ./faults.sh | ./ignore.sh



###Help Menu
---
    
    usage: fuzzer.py [-decoder] [-encoder] [-decbin path] [-encbin path]
                     [-count #] [-bucket path] [-samples path] [-resources path]
                     [-symbolizer path] [-ubsan] [-loglevel #] [-workers #]
    
    Fuzzer: OpenH264
    
    optional arguments:
      -decoder          fuzz decoder (default: False)
      -encoder          fuzz encoder (default: False)
      -decbin path      (default: ./h264dec)
      -encbin path      (default: ./h264enc)
      -count #
      -bucket path      (default: bucket)
      -samples path     (default: $HOME/dev/projects/fuzzers/openh264/samples/*.*)
      -resources path   (default: $HOME/dev/projects/fuzzers/openh264/resources)
      -symbolizer path  (default: $HOMEdev/projects/fuzzers/openh264/symbolize.py)
      -ubsan            (default: False)
      -loglevel #       (default: 20)
      -workers #        (default: 1)

