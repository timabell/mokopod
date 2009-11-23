#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gobject,gtk, os, sys, dbus
import pymplayer, signal
from time import strftime
import pickle

class view:
  def __init__(self, parent_window, episode):
    self.w = gtk.Window()
    self.w.set_modal(True)
    self.w.set_title("Playing podcast...")
    #self.w.set_decorated(False)
    #self.w.set_geometry_hints(None, 1000, 1000)
    self.w.maximize()
    
    # Main page
    mainvbox = gtk.VBox(False, 10)
    mainvbox.add(gtk.Label(episode.parentFeed.name))
    mainvbox.add(gtk.Label(episode.title))
    mainvbox.add(gtk.Label(strftime("%c", episode.pubDate)))
    
    self.positionLabel = gtk.Label("")
    mainvbox.add(self.positionLabel)
    
    self.scroll = gtk.HScrollbar(gtk.Adjustment(0,0,100,5,5,10))
    mainvbox.add(self.scroll)
    
    hbox = gtk.HBox(True, 5)
    self.backButton = gtk.Button("-5 sec")
    hbox.add(self.backButton)
    self.forwardButton = gtk.Button("+5 sec")
    hbox.add(self.forwardButton)
    mainvbox.add(hbox)
    
    hbox = gtk.HBox(True, 5)
    self.backButton30 = gtk.Button("-30 sec")
    hbox.add(self.backButton30)
    self.forwardButton30 = gtk.Button("+30 sec")
    hbox.add(self.forwardButton30)
    mainvbox.add(hbox)
    
    self.stopButton = gtk.Button("Stop")
    mainvbox.add(self.stopButton)
    
    self.w.add(mainvbox)
    self.w.show_all()

class control:
  stateFileLoad = "/usr/share/openmoko/scenarios/stereoouthead.state"
  volumeFile = os.environ.get('HOME') + "/.mokorss/volume"
  def __init__(self, gui, episode, parent):
    try:
      bus = dbus.SystemBus()
      # Tell FSO we will use CPU
      usage_obj = bus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
      usage_obj.RequestResource("CPU")
    except:
      pass
    if os.path.exists(self.stateFileLoad):
      restorePath = os.environ.get('HOME') + "/.mokorss/restore.state"
      os.system("alsactl -f "+restorePath+" store")
      os.system("alsactl -f "+self.stateFileLoad+" restore")
    if os.path.exists(self.volumeFile):
      f = open( self.volumeFile, 'r' )
      volume = pickle.load(f)
      f.close()
      gui.scroll.set_value(volume)
    else:
      gui.scroll.set_value(100)
      volume=100
    gui.stopButton.connect('clicked', self.stop)
    gui.w.connect("destroy", self.quit)
    gui.scroll.connect('value-changed', self.changeVolume)
    gui.backButton.connect('clicked', self.goBack, -5.0)
    gui.forwardButton.connect('clicked', self.goForward, 5.0)
    gui.backButton30.connect('clicked', self.goBack, -30.0)
    gui.forwardButton30.connect('clicked', self.goForward, 30.0)
    self.running = True
    self.gui = gui
    self.episode = episode
    self.parent = parent
    
    def handle_data(data):
      pass
    
    self.player = pymplayer.MPlayer()
    self.player.args = [episode.file]
    self.player.stdout.attach(handle_data)
    if self.player.start()==False:
      raise Exception("mplayer failed to start. :-(")
    self.player.command('volume', volume, 1)
    self.player.command('seek', episode.position, 2)
    signal.signal(signal.SIGTERM, lambda s, f: player.quit())
    signal.signal(signal.SIGINT, lambda s, f: player.quit())
    
    self.updateTime()
    
    #pymplayer.loop()
  
  def goForward(self, t, time):
    self.seekSec(time)
  def goBack(self, t, time):
    self.seekSec(time)
  
  def changeVolume(self, t):
    volume = self.gui.scroll.get_value()
    self.player.command('volume', volume, 1)
    f = open(self.volumeFile , 'w' )
    pickle.dump(volume, f)
    f.close()
  
  def seekSec(self, sec):
    self.player.command('seek', sec)
    self.updateTime(False)
  
  def updateTime(self, addTimeout = True):
    if self.running:
      if addTimeout:
        gobject.timeout_add (1000, self.updateTime)
      pos = self.player.query('get_time_pos')
      if pos==None:
        return
      pos = int(pos)
      if pos < 5:
        self.episode.position = 0
      else:
        self.episode.position = pos - 5
      length = int(self.player.query('get_time_length'))
      posStr = "%d:%02d / %d:%02d" % (int(pos/60), (pos % 60), int(length/60), (length % 60))
      self.gui.positionLabel.set_text(posStr)
      print "saving position as %i" % pos
      self.parent.savePosition(self.episode,  pos)
  
  def stop(self, t):
    self.gui.w.destroy()
    self.quit(t)
  
  def quit(self, t):
    #gtk.main_quit(t)
    self.player.quit()
    self.running = False
    if os.path.exists(self.stateFileLoad):
      restorePath = os.environ.get('HOME') + "/.mokorss/restore.state"
      os.system("alsactl -f "+restorePath+" restore")
    try:
      bus = dbus.SystemBus()
      usage_obj = bus.get_object('org.freesmartphone.ousaged', '/org/freesmartphone/Usage')
      usage_obj.ReleaseResource("CPU")
    except:
      pass
    try:
      del self.gui
    except:
      pass
    
