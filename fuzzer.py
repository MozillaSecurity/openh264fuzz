#!/usr/bin/env python
# coding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
import glob
import time
import random
import shutil
import struct
import logging
import tempfile
import argparse
import subprocess
import multiprocessing


ROOT = os.path.dirname(os.path.abspath(__file__))


class Random(object):

  @staticmethod
  def init(seed=None):
    if not seed:
      seed = random.random()
    random.seed(seed)
    return seed

  @staticmethod
  def number(start, stop=None, step=1):
    return random.randrange(start, stop + 1, step)

  @staticmethod
  def index(seq):
    return random.choice(seq)

  @staticmethod
  def key(o):
    return Random.index(o.keys())

  @staticmethod
  def shuffle(seq):
    seq = random.shuffle(seq)

  @staticmethod
  def chance(limit):
    return Random.number(limit) == 1

  @staticmethod
  def weighted(choices):
      total = sum(w for c, w in choices)
      r = random.uniform(0, total)
      upto = 0
      for c, w in choices:
          if upto + w > r:
              return c
          upto += w
      assert False, choices

  @staticmethod
  def pick(o):
    if o is None: 
      return o
    if callable(o):
      return Random.pick(o())
    if isinstance(o, list):
      return Random.pick(Random.index(o))
    if isinstance(o, (int, long, float)):
      return o
    if isinstance(o, str):
      return o
    if isinstance(o, dict):
      return Random.pick(o[Random.key(o)])
    assert False, type(o)


class DatatypeMutator(object):

  values = {
    'h': [-32768, 32767],
    'H': [65535],
    'i': [-2147483648, 2147483647],
    'I': [4294967295],
    'q': [ -9223372036854775808, 9223372036854775807],
    'Q': [18446744073709551615]
  }

  def __init__(self):
    self.max_mutations = 4
    self.endian = Random.pick(["<", ">"])

  def mutate(self, data):
    for _ in xrange(1, Random.number(2, self.max_mutations)):
      fmt = Random.key(self.values)
      val = Random.pick(self.values[fmt])
      value = struct.pack(self.endian + fmt, val)
      offset = Random.number(0, len(data))
      data = data[:offset] + value + data[offset + len(value):]
    return data


class RandomByteMutator(object):

  def __init__(self):
    self.max_mutations = 4
    self.max_length = 2

  def mutate(self, data):
    for _ in xrange(1, Random.number(2, self.max_mutations)):
      length = Random.number(1, self.max_length)
      value = ''.join([chr(Random.number(0, 255)) for _ in xrange(length)])
      offset = Random.number(0, len(data))
      data = data[:offset] + value + data[offset + len(value):]
    return data


class Fuzzer(object):

  def __init__(self):
    self.mutators = []

  def add_mutator(self, mutator):
    self.mutators.append(mutator)

  def mutate(self, data):
    for mutator in self.mutators:
      data = mutator.mutate(data)
    return data

  def open_sample(self, path):
    path = Random.index(glob.glob(path))
    with open(path) as fo:
      data = fo.read()
    return data

  def symbolize(self, script, callstack):
    callstack = "".join(callstack)
    if sys.platform == 'darwin':
      p1 = subprocess.Popen(["echo", callstack], 
                            stdout=subprocess.PIPE)
      p2 = subprocess.Popen([script], 
                            stdin=p1.stdout, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.STDOUT)
      callstack = p2.communicate()[0] or ""
      p1.stdout.close()
      p2.stdout.close()
    elif sys.platform == 'linux2':
      p1 = subprocess.Popen(["echo", callstack], 
                            stdout=subprocess.PIPE)
      p2 = subprocess.Popen([script], 
                            stdin=p1.stdout, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.STDOUT)
      p3 = subprocess.Popen(["c++filt"], 
                            stdin=p2.stdout, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.STDOUT)
      callstack = p3.communicate()[0] or ""
      p1.stdout.close()
      p2.stdout.close()
      p3.stdout.close()
    return callstack

  def make_bucket(self, base):
    path = os.path.join(base, str(format(time.time())))
    os.makedirs(path)
    return path


class OpenH264(Fuzzer):

  def __init__(self, **kwargs):
    super(OpenH264, self).__init__()
    self.__dict__.update(kwargs)

  def generate_configs(self):
    self.temp_folder = tempfile.mkdtemp(dir=tempfile.gettempdir())
    self.output_file = os.path.join(self.temp_folder, "success.264")
    self.wels_config = os.path.join(self.temp_folder, "welsenc_fuzz.cfg")
    self.layer_config = os.path.join(self.temp_folder, "layer_config.cfg")

    w  = "OutputFile\t%s\n" % self.output_file
    w += "MaxFrameRate\t%d\n" % Random.number(0, 30, 3)
    w += "FramesToBeEncoded\t%d\n" % Random.index([-1])
    w += "SourceSequenceInRGB24\t%d\n" % Random.number(0, 1)
    w += "GOPSize\t%d\n" % Random.index([1, 2, 4, 8, 16, 32, 64])
    w += "IntraPeriod\t%d\n" % Random.index([0, 320])
    w += "EnableSpsPpsIDAddition\t%d\n" % Random.number(0, 1)
    w += "EnableScalableSEI\t%d\n" % Random.number(0, 1)
    w += "EnableFrameCropping\t%d\n" % Random.number(0, 1)
    w += "LoopFilterDisableIDC\t%d\n" % Random.number(0, 6)
    w += "LoopFilterAlphaC0Offset\t%d\n" % Random.number(-6, 6)
    w += "LoopFilterBetaOffset\t%d\n" % Random.number(-6, 6)
    w += "InterLayerLoopFilterDisableIDC\t%d\n" % Random.number(0, 6)
    w += "InterLayerLoopFilterAlphaC0Offset\t%d\n" % Random.number(-6, 6)
    w += "InterLayerLoopFilterBetaOffset\t%d\n" % Random.number(-6, 6)
    w += "MultipleThreadIdc\t%d\n" % Random.index([0, 1, 4])
    EnableRC = Random.number(0, 1)
    w += "EnableRC\t%d\n" % EnableRC
    w += "RCMode\t%d\n" % Random.number(0, 1)
    TargetBitrate = Random.index([5000])
    w += "TargetBitrate\t%d\n" % TargetBitrate
    w += "EnableDenoise\t%d\n" % Random.number(0, 1)
    w += "EnableSceneChangeDetection\t%d\n" % Random.number(0, 1)
    w += "EnableBackgroundDetection\t%d\n" % Random.number(0, 1)
    w += "EnableAdaptiveQuantization\t%d\n" % Random.number(0, 1)
    w += "EnableLongTermReference\t%d\n" % Random.number(0, 1)
    w += "LtrMarkPeriod\t%d\n" % Random.index([30])
    w += "NumLayers\t%d\n" % Random.index([1])
    w += "LayerCfg\t%s\n" % self.layer_config
    w += "PrefixNALAddingCtrl\t%d\n" % Random.number(0, 1)

    with open(self.wels_config, "wb") as fo:
      fo.write(w)

    l  = "SourceWidth\t%d\n" % Random.number(0, 150)
    l += "SourceHeight\t%d\n" % Random.number(0, 64)
    l += "FrameRateIn\t%d\n" % 12
    l += "FrameRateOut\t%d\n" % 12
    InputFile = Random.index(glob.glob(os.path.join(self.resources, "*.yuv")))
    l += "InputFile\t%s\n" % InputFile
    ReconFile = Random.index(glob.glob(os.path.join(self.resources, "*.yuv")))
    l += "ReconFile\t%s\n" % ReconFile
    l += "ProfileIdc\t%d\n" % Random.index([11, 83])
    l += "FRExt\t%d\n" % 0
    if EnableRC:
      SpatialBitrate = Random.index([2000])
    else:
      SpatialBitrate = Random.index([100])
    l += "SpatialBitrate\t%d\n" % SpatialBitrate
    l += "InitialQP\t%d\n" % Random.index([24, 26])
    l += "SliceMode\t%d\n" % Random.number(0, 4)
    l += "SliceSize\t%d\n" % Random.index([1000, 1500])
    l += "SliceNum\t%d\n" % 1
    l += "SlicesAssign0\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign1\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign2\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign3\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign4\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign5\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign6\t%d\n" % Random.number(0, 35)
    l += "SlicesAssign7\t%d\n" % Random.number(0, 35)

    with open(self.layer_config, "wb") as fo:
      fo.write(l)

  def fuzz_decoder(self, path, count=None):
    count = self.count if count is None else count
    while count > 0:
      sample_buffer = self.open_sample(path)
      fuzzed_buffer = self.mutate(sample_buffer)
      testcase = tempfile.NamedTemporaryFile()
      testcase.write(fuzzed_buffer)
      yuv = tempfile.NamedTemporaryFile()
      p = subprocess.Popen([self.decbin, testcase.name, yuv.name],
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT)
      stdout = p.communicate()[0]
      logging.debug("ExitCode: %d" % p.returncode)
      logging.debug("DecoderOutput:\n%s" % stdout)
      if p.returncode != 0 or ("runtime error" in stdout and self.ubsan):
        logging.info("Crash detected!")
        bucket = self.make_bucket(self.bucket)
        shutil.copy(testcase.name, os.path.join(bucket, "testcase.264"))
        with open(os.path.join(bucket, "callstack.txt"), "wb") as fo:
          fo.write(self.symbolize(self.symbolizer, stdout))
      testcase.close()
      yuv.close()
      count -= 1

  def fuzz_encoder(self, count=None):
    count = self.count if count is None else count
    while count > 0:
      self.generate_configs()
      p = subprocess.Popen([self.encbin, self.wels_config], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT)
      stdout = p.communicate()[0]
      logging.debug("ExitCode: %d" % p.returncode)
      logging.debug("EncoderOutput:\n%s" % stdout)
      #  1 = initialize failed
      #  0 = success
      # -6 = assertion failure
      if p.returncode < 0:
        logging.info("Crash detected!")
        bucket = self.make_bucket(self.bucket)
        shutil.move(self.wels_config, bucket)
        shutil.move(self.layer_config, bucket)
        with open(os.path.join(bucket, "callstack.txt"), "w") as fo:
          fo.write(self.symbolize(self.symbolizer, stdout))
      if p.returncode == 0:
        self.fuzz_decoder(self.output_file, 10)
      shutil.rmtree(self.temp_folder)
      count -= 1

def main(args):
  logging.basicConfig(
    format='[OpenH264] %(asctime)s %(levelname)s: %(message)s',
    level=args.loglevel)

  fuzzer = OpenH264(**vars(args))

  m1 = DatatypeMutator()
  m1.max_mutations = 4
  
  m2 = RandomByteMutator()
  m2.max_length = 4
  m2.max_mutations = 8
  
  fuzzer.add_mutator(m1)
  #fuzzer.add_mutator(m2)
  Random.shuffle(fuzzer.mutators)
  
  if args.decoder and args.samples:
    fuzzer.fuzz_decoder(os.path.expanduser(args.samples))

  if args.encoder:
    fuzzer.fuzz_encoder()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Fuzzer: OpenH264',
                                   prefix_chars='-',
                                   add_help=False,
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-decoder', action='store_true', default=False, help="fuzz decoder")
  parser.add_argument('-encoder', action='store_true', default=False, help="fuzz encoder")
  parser.add_argument('-decbin', metavar='path', default='./h264dec', help=" ")
  parser.add_argument('-encbin', metavar='path', default='./h264enc', help=" ")
  parser.add_argument('-count', metavar='#', type=int, default=sys.maxint, help="")
  parser.add_argument('-bucket', metavar='path', default='bucket', help=" ")
  parser.add_argument('-samples', metavar='path', default=os.path.join(ROOT, "samples/*.*"), help=" ")
  parser.add_argument('-resources', metavar='path', default=os.path.join(ROOT, "resources"), help=" ")
  parser.add_argument('-symbolizer', metavar='path', default=os.path.join(ROOT, 'symbolize.py'), help=" ")
  parser.add_argument('-ubsan', action='store_true', default=False, help=" ")
  parser.add_argument('-loglevel', metavar="#", type=int, default=20, help=" ")
  parser.add_argument('-workers', metavar='#', type=int, default=1, help=" ")
  parser.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
  parser.add_argument('-version', action='version', version='%(prog)s 1.0', help=argparse.SUPPRESS)
  args = parser.parse_args()

  for _ in range(args.workers):
    p = multiprocessing.Process(target=main, args=(args,))
    p.start()
