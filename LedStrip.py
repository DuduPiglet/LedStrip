from enum import Enum
import time
import board
import neopixel
import utils
import moonracker_api

class Mode(Enum):
  MODE_INIT = 0
  MODE_OFF  = 1
  MODE_LNTR = 2
  MODE_TMLP = 3
  MODE_PROG = 4
  MODE_FAIL = 5

class LedStrip():

  def __init__(self, len=10, pin=board.D10, bright=1.0, moonraker_host='localhost', moonraker_port=7125):
    self.__enables = {
      'init': False,
      'lntr': False,
      'tmlp': False,
      'prog': False,
      'fail': False,
    }
    self.__mode = Mode.MODE_INIT
    self.__modeLast = Mode.MODE_INIT
    self.__colorConf = {
      'init': {
        'r' : 255,
        'g' : 255,
        'b' : 255,
      },
      'lntr': {
        'r' : 255,
        'g' : 255,
        'b' : 255,
      },
      'tmlp': {
        'r' : 255,
        'g' : 255,
        'b' : 255,
      },
      'prog': {
        'r' : 0,
        'g' : 255,
        'b' : 0,
      },
      'fail': {
        'r' : 255,
        'g' : 0,
        'b' : 0,
      }
    }
    self.__printProg = 0.0
    self.__printFail = False
    self.__moonraker_host = moonraker_host
    self.__moonraker_port = moonraker_port
    self.__strip_len = len
    self.__strip_pin = pin
    self.__strip_br = utils.check_saturation(bright, 0, 1)
    self.__pixels = neopixel.NeoPixel(self.__strip_pin, self.__strip_len, brightness=self.__strip_br)
    self.__pixels.fill((0, 0, 0))
    self.__moonraker_api = moonracker_api.MoonrakerAPI(self.__moonraker_host, self.__moonraker_port)

  def __SetAllPixels(self, r, g, b):
    self.__pixels.fill((r, g, b))
  
  def __SetSpecificPixel(self, ix, r, g, b):
    self.__pixels[ix] = (r, g, b)

  def __UpdateMode(self):
    self.__mode = Mode.MODE_OFF
    if (self.__enables['tmlp']):
      self.__mode = Mode.MODE_TMLP
    elif (self.__enables['lntr']):
      self.__mode = Mode.MODE_LNTR
    elif (self.__enables['fail'] and self.__printFail):
      self.__mode = Mode.MODE_FAIL
    elif (self.__enables['prog']):
      self.__mode = Mode.MODE_PROG

  def __AnimBreath(self, T):
    t = 0 # [ms]
    while (t <= T):
      self.__pixels.fill((int(self.__colorConf['init']['r'] * t / T), int(self.__colorConf['init']['r'] * t / T), int(self.__colorConf['init']['r'] * t / T)))
      t = t + 1
      time.sleep(0.001)

  def __ProcessInit(self):
    if self.__enables['init']:
      self.__AnimBreath(1000)

  def __TurnOff(self):
    self.__SetAllPixels(0, 0, 0)
    pass

  def __TurnOnLntr(self):
    self.__SetAllPixels(self.__colorConf['lntr']['r'], self.__colorConf['lntr']['g'], self.__colorConf['lntr']['b'])

  def __TurnOnTmlp(self):
    self.__SetAllPixels(self.__colorConf['tmlp']['r'], self.__colorConf['tmlp']['g'], self.__colorConf['tmlp']['b'])

  def __TurnOnFail(self):
    self.__SetAllPixels(self.__colorConf['fail']['r'], self.__colorConf['fail']['g'], self.__colorConf['fail']['b'])

  def __ProcessProg(self):
    prog_leds = int(self.__strip_len * self.__printProg / 100)
    for led in prog_leds:
      self.__SetSpecificPixel(led, self.__colorConf['prog']['r'], self.__colorConf['prog']['g'], self.__colorConf['prog']['b'])
    pass
  
  def __updatePrinterState(self):
    self.__printFail = False
    printer_state = self.__moonraker_api.printer_state()
    if (printer_state == 'printing'):
      printing_stats = self.__moonraker_api.printing_stats()
      self.__printProg = printing_stats['printing']['done_percent']
    elif (printer_state == 'error'):
      self.__printFail = True
    else:
      # Do nothing.
      pass

  def Process(self):
    self.__updatePrinterState()
    if (self.__mode == Mode.MODE_INIT):
      self.__ProcessInit()
    elif (self.__mode == Mode.MODE_PROG):
      self.__ProcessProg()
    self.__UpdateMode()

    if (self.__mode != self.__modeLast):
      if (self.__mode == Mode.MODE_INIT):
        self.__TurnOff()
      elif (self.__mode == Mode.MODE_OFF):
        self.__TurnOff()
      elif (self.__mode == Mode.MODE_LNTR):
        self.__TurnOnLntr()
      elif (self.__mode == Mode.MODE_TMLP):
        self.__TurnOnTmlp()
      elif (self.__mode == Mode.MODE_PROG):
        self.__TurnOff()
      elif (self.__mode == Mode.MODE_FAIL):
        self.__TurnOnFail()
    
    self.__modeLast = self.__mode

  def SetColorConf(self, mode, r, g, b, br):
    self.__colorConf[mode] = {
      'r' : utils.check_saturation(int(r * br), 0, 255),
      'g' : utils.check_saturation(int(g * br), 0, 255),
      'b' : utils.check_saturation(int(b * br), 0, 255)
    }
  
  def SetModeEn(self, mode, en):
    self.__enables[mode] = en
