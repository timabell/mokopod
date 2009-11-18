#!/usr/bin/env python
import gobject,gtk, os, sys
import pickle
import urllib # So we can download files
from time import strftime
from threading import Thread

sys.path.append('/usr/lib/site-python')

from mokopodlib import feedparser
from mokopodlib import playpod

# Requirements on Openmoko: (not complete)
# python-html, python-pickle, python-netclient, mplayer, python-pygtk


class gui:
  def quit(self,target):
    gtk.main_quit(target)
    exit()
  
  def get_active_text(self, combobox):
    model = combobox.get_model()
    active = combobox.get_active()
    if active < 1:
      return None
    return model[active][0]
  
  def showFeed(self, feed):
    #called indirectly when item selected in feed list combo box
    self.feedInfo_label[0].set_label("Name: " + feed.name)
    self.feedInfo_label[1].set_label("URL: " + feed.url)
    self.feedInfo_label[2].set_label("*Latest episode*")
    #self.feedInfo_label[3].set_label("Title: " + feed['episode_title']) #fixme
    #self.feedInfo_label[4].set_label("File: " + feed['episode_path'])#fixme
    #self.feedInfo_label[5].set_label("pubDate: " + strftime("%c", feed['episode_pubDate']))#fixme
    
#    if feed.status=="ready": #fixme
#      self.playpodButton.set_sensitive(True)
#      self.listEpisodesButton.set_sensitive(True)
#    else:
#      self.playpodButton.set_sensitive(False)
#      self.listEpisodesButton.set_sensitive(False)
#    self.feedInfo_removeb.set_sensitive(True)
  
  def yesNoDialog(self, text):
    dialog = gtk.MessageDialog(  
         self.w,
         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
         gtk.MESSAGE_QUESTION,  
         gtk.BUTTONS_YES_NO,  
         text)
    response = dialog.run()
    dialog.destroy()
    return (response==-8)
  def showText(self, text):
    dialog = gtk.MessageDialog(  
         self.w,
         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
         gtk.MESSAGE_QUESTION,  
         gtk.BUTTONS_OK,  
         text)
    response = dialog.run()
    dialog.destroy()
  def showTextNoOk(self, text):
    w = gtk.Window()
    w.set_transient_for(self.w)
    w.set_modal(False)
    w.add(gtk.Label("\n\n\n"+text+"\n\n\n"))
    w.show_all()
    while gtk.events_pending():
      gtk.main_iteration(False)
    return w
  
  def responseToDialog(self, entry, dialog, response):
    dialog.response(response)
  def getText(self, ask_text, default=""):
    dialog = gtk.MessageDialog(
         self.w,
         gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  
         gtk.MESSAGE_QUESTION,  
         gtk.BUTTONS_OK,  
         None)
    dialog.set_markup(ask_text)
    entry = gtk.Entry()
    entry.set_text(default)
    entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
    hbox = gtk.HBox()  
    hbox.pack_start(gtk.Label("Name:"), False, 5, 5)  
    hbox.pack_end(entry)
    dialog.vbox.pack_end(hbox, True, True, 0)  
    dialog.show_all()  
    #go go go  
    dialog.run()  
    text = entry.get_text()  
    dialog.destroy()  
    return text
  
  def clearInfoView(self):
    for i in range(0,6):
      self.feedInfo_label[i].set_label("")
    self.feedInfo_removeb.set_sensitive(False)
    self.playpodButton.set_sensitive(False)
    
  def destroyNewFeedWindow(self,t):
    self.newfeed_window.destroy()
  def newFeedWindow(self):
    w = gtk.Window()
    w.set_transient_for(self.w)
    w.set_modal(True)
    w.set_title("Make new feed")
    w.maximize()
    v = gtk.VBox(False,10)
    
    v.add(gtk.Label("Add new feed"))
    
    h = gtk.HBox(False,3)
    
    h.add(gtk.Label("URL for feed:"))
    self.newfeed_URL = gtk.Entry()
    h.add(self.newfeed_URL)
    v.add(h)
    
    h = gtk.HBox(True,3)
    cancelButton = gtk.Button("\nCancel\n")
    cancelButton.connect('clicked', self.destroyNewFeedWindow)
    h.add(cancelButton)
    self.newfeed_ok_button = gtk.Button("\nDone!\n")
    h.add(self.newfeed_ok_button)
    v.add(h)
    
    w.add(v)
    w.show_all()
    self.newfeed_window = w

  def destroyEpisodeListWindow(self,t):
    self.episodelist_window.destroy()
  def newEpisodeListWindow(self,  feed):
    w = gtk.Window()
    w.set_transient_for(self.w)
    w.set_modal(True)
    w.set_title("Episodes")
    w.maximize()
    v = gtk.VBox(False,10)   
    v.add(gtk.Label("Episode list"))
    updateFeedButton = gtk.Button("Update feed")
    v.add(updateFeedButton)
    closeButton = gtk.Button("Close")
    closeButton.connect('clicked', self.destroyEpisodeListWindow)
    v.add(closeButton)
    w.add(v)
    w.show_all()
    self.episodelist_window = w
    

  def __init__(self):
    self.w = gtk.Window()
    self.w.set_title("Moko do the RSS")
    self.w.connect("destroy", gtk.main_quit) # Makes gtk stop when the window is closed
    
    # Main page
    mainvbox = gtk.VBox(False, 10)
    
    # Add topbar with buttons
    hbox = gtk.HBox(True,10)
    vbox = gtk.VBox(True,10)
    self.configureButton = gtk.Button("Configure")
    vbox.add(self.configureButton)
    self.getNewEpisodesButton = gtk.Button("Get new episodes")
    vbox.add(self.getNewEpisodesButton)
    hbox.add(vbox)
    vbox = gtk.VBox(True,10)
    self.newFeedButton = gtk.Button("Add new podcast")
    vbox.add(self.newFeedButton)
    closeButton = gtk.Button("Close program")
    closeButton.connect('clicked', gtk.main_quit)
    vbox.add(closeButton)
    hbox.add(vbox)
    mainvbox.add(hbox)
    
    # Add list of current feeds
    self.feedCombo = gtk.combo_box_new_text()
    self.feedCombo.append_text("List of feeds:")
    self.feedCombo.set_active(0)
    mainvbox.add(self.feedCombo)
    
    vbox = gtk.VBox(False, 1)
    self.feedInfo_label = []
    for i in range(0,6):
      self.feedInfo_label.append(gtk.Label(""))
      vbox.add(self.feedInfo_label[i])
    self.playpodButton = gtk.Button("Play latest episode")
    self.playpodButton.set_sensitive(False)
    vbox.add(self.playpodButton)
    self.listEpisodesButton = gtk.Button("List episodes")
    self.listEpisodesButton.set_sensitive(False)
    vbox.add(self.listEpisodesButton)
    self.feedInfo_removeb = gtk.Button("Remove feed")
    self.feedInfo_removeb.set_sensitive(False)
    vbox.add(self.feedInfo_removeb)
    mainvbox.add(vbox)
    
    self.w.add(mainvbox)
    #b = gtk.Button('Sure?')
    #b.connect('clicked', self.quit)
    #noteb.append_page(b, gtk.Label("\n    Exit    \n"))
    
  def main(self):
    self.w.show_all()
    gtk.main()


class mokorss:
  class Feed:
    def __init__(self,  url):
      self.url = url
      self.parsedFeed = self.Parse(self.url)
      self.name = self.parsedFeed['feed']['title']
      self.relativeDownloadPath = self.name + "/"

    def Parse(self,url):
      return feedparser.parse(self.url)

    def GetEpisodeLIst():
      #todo match existing entries
      for entry in self.parsedFeed.entries:
        episode = Episode()
        episode.title = entry.title
        episode.pubDate = entry.updated_parsed
        url = entry.enclosures[0].href
        episode.downloadUrl = url
        #extract filename from url
        filename = url.split('/')[-1] #last part of url
        if filename.find("?"):
          filename = filename.split('?')[0] #remove any querystring
        episode.filename = filename
        episode.status = "new"

    class Episode:
      def Download(self, storagePath): #storagePath is the folder that contains all downloads (without the feed name)
        self.status = "downloading"
        self.file = storagePath+self.filename
        urllib.urlretrieve(self.downloadUrl, self.file)
        self.status = "ready"

  class Storage:
    def IntializeDownloadLocation(self):
     self.save_path = self.parent.getPodcastFolder()
     if save_path=="":
       self.parent.setFolderToSaveIn(t)
     if not os.path.exists(save_path):
       os.mkdir(save_path)
     return save_path

  class DownloadEpisodes(Thread):
    def __init__(self,parent):
      Thread.__init__(self)
      self.parent = parent
      
    def run(self):
      # TODO: save shownotes
      # TODO: use new feed class
      popupText = "Downloaded new episodes for:"
      save_path = self.parent.Storage().IntializeDownloadLocation()
      for feed in self.parent.feeds[1::]:
        dialog = self.parent.gui.showTextNoOk("Checking "+feed.name)
        pod_path = save_path + feed.name + "/"
        if not os.path.exists(pod_path):
          os.mkdir(pod_path)
        # TODO: See if feedparser is slowing Openmoko down too much
        parser = feedparser.parse(feed.url)
        feed['episode_title'] = parser.entries[0].title
        old_pubDate = feed['episode_pubDate']
        feed['episode_pubDate'] = parser.entries[0].updated_parsed
        dialog.destroy()
        if feed['episode_pubDate'] > old_pubDate:
          dialog = self.parent.gui.showTextNoOk("Downloading episode from\n"+feed.name)
          filename = parser.entries[0].enclosures[0].href.split('/')[-1]
          if filename.find("?"):
            filename = filename.split('?')[0]
          if os.path.exists(feed['episode_path']):
            os.remove(feed['episode_path'])
          # TODO: Use wget?
          urllib.urlretrieve(parser.entries[0].enclosures[0].href, pod_path+filename)
          popupText = popupText + "\n* " + feed.name
          dialog.destroy()
          feed['episode_path'] = pod_path+filename
          feed['episode_pos'] = 0
      self.parent.saveFeeds()
      self.parent.showFeedInfo(self.parent.gui.feedCombo)
      self.parent.gui.showText(popupText)

  def __init__(self, gui):
    self.storageRoot = os.environ.get('HOME') + "/.mokorss/"
    self.gui = gui
    self.loadFeeds()
    self.redrawFeedCombo()
    gui.feedCombo.connect("changed", self.showFeedInfo)
    gui.playpodButton.connect('clicked', self.playPodcast)
    gui.newFeedButton.connect('clicked', self.newFeedWindow)
    gui.configureButton.connect('clicked', self.setFolderToSaveIn)
    gui.feedInfo_removeb.connect('clicked', self.removeCurrentFeed)
    gui.getNewEpisodesButton.connect('clicked', self.getNewEpisodes)
    gui.listEpisodesButton.connect('clicked', self.newEpisodeListWindow)
  
  def playPodcast(self, t):
    view = playpod.view(self.gui.w, self.feeds[self.currentFeed])
    playpod.control(view, self.feeds[self.currentFeed], self)
  
  def getNewEpisodes(self, t):
    d = self.DownloadEpisodes(self)
    d.start()
    
  def removeCurrentFeed(self, t):
    if self.gui.yesNoDialog("Do you really want to remove\n%s?" % (self.feeds[self.currentFeed]['name'])):
      # Remove files
      if os.path.exists(self.feeds[self.currentFeed]['episode_path']):
        os.remove(self.feeds[self.currentFeed]['episode_path'])
      if os.path.exists(self.getPodcastFolder() + self.feeds[self.currentFeed]['name']):
        os.rmdir(self.getPodcastFolder() + self.feeds[self.currentFeed]['name'])
      # Remove the rest
      self.gui.clearInfoView()
      self.feeds.remove(self.feeds[self.currentFeed])
      self.saveFeeds()
      self.redrawFeedCombo()
    
  def newFeedWindow(self, t):
    self.gui.newFeedWindow()
    self.gui.newfeed_ok_button.connect('clicked',self.parseNewFeed)

  def newEpisodeListWindow(self, t):
    #feed = 
    self.gui.newEpisodeListWindow(feed)
  
  def parseNewFeed(self,t):
    url = self.gui.newfeed_URL.get_text()
    feed = self.Feed(url)
    self.feeds.append(feed)
    self.gui.newfeed_window.destroy()
    self.saveFeeds()
    self.redrawFeedCombo()
    
  def showFeedInfo(self, cb):
    #fired when item selected in feed list combo box
    active = cb.get_active()
    if active < 1:
      self.gui.clearInfoView()
      return None
    self.currentFeed = active
    self.gui.showFeed( self.feeds[active] )
    #cb.set_active(0)
  
  def saveFeeds(self):
    filename = self.storageRoot + "feeds"
    f = open( filename, 'w' )
    pickle.dump(self.feeds, f)
    f.close()
    
  def loadFeeds(self):
    filename = self.storageRoot + "feeds"
    # Does the file feed list exists?
    if not os.path.exists(filename):
      if not os.path.exists(self.storageRoot):
        os.mkdir(self.storageRoot)
      self.feeds = [0]
    else:
      f = open( filename, 'r' )
      self.feeds = pickle.load(f)
      f.close()
  
  def getPodcastFolder(self):
    filename = self.storageRoot + "folder"
    if not os.path.exists(filename):
      return ""
    else:
      f = open( filename, 'r' )
      place = pickle.load(f)
      f.close()
      return place
  
  def setFolderToSaveIn(self,t):
    place = self.gui.getText("Where do you want to save the podcasts?", self.getPodcastFolder())
    if len(place)==0:
      return self.setFolderToSaveIn(t)
    if not place[-1]=="/":
      place = place + "/"
    filename = self.storageRoot + "folder"
    f = open( filename, 'w' )
    pickle.dump(place, f)
    f.close()
  
  def redrawFeedCombo(self):
    number = len(self.gui.feedCombo.get_model())
    for i in range(1,number):
      self.gui.feedCombo.remove_text(1)
    for feed in self.feeds[1::]:
      self.gui.feedCombo.append_text(feed.name)
  
  def net_getFeedName(self, url):
    d = feedparser.parse(url)
    return d['feed']['title']


if __name__ == "__main__":
  #os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
  #gtk.gdk.threads_init()
  #gtk.gdk.threads_enter()

  g = gui()
  app = mokorss(g)
  #start processing screen events
  g.main()
  #gtk.gdk.threads_leave()
