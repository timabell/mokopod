#!/usr/bin/env python
import gobject,gtk, os, sys
import pickle
import urllib # So we can download files
import shutil
from time import strftime
from threading import Thread

sys.path.append('/usr/lib/site-python')

from mokopodlib import feedparser
from mokopodlib import playpod

# Requirements on Openmoko: (not complete)
# python-html, python-pickle, python-netclient, mplayer, python-pygtk

#TODO: playlist
#TODO: separate adding feed url from download and parse of xml
#TODO: background long running operations
#TODO: download progress indicator
#TODO: ability to cancel long running operations
#TODO: continue partial downloads
#TODO: save shownotes
#TODO: update the episode list after get/delete
#TODO: any kind of error handling and notification. eg out of disk space, connection failures
#TODO: opml import/export
#TODO: prevent duplication of feeds

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
    self.listEpisodesButton.set_sensitive(True)
    self.updateFeedButton.set_sensitive(True)
    self.feedInfo_removeb.set_sensitive(True)
    if feed.episodes:
      latest = feed.episodes[0]
      self.feedInfo_label[2].set_label("*Latest episode* - %s" % latest.status)
      self.feedInfo_label[3].set_label("Title: " + latest.title)
      self.feedInfo_label[4].set_label("File: " + latest.filename)
      self.feedInfo_label[5].set_label("Date: " + strftime("%c",latest.pubDate))
  
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
    self.listEpisodesButton.set_sensitive(False)
    self.updateFeedButton.set_sensitive(False)
    self.feedInfo_removeb.set_sensitive(False)
    self.getLatestEpisodeButton.set_sensitive(False)

  def destroyNewFeedWindow(self,t):
    self.newfeed_window.destroy()
  def newFeedWindow(self):
    w = gtk.Window()
    w.set_transient_for(self.w)
    w.set_modal(True)
    w.set_title("Make new feed")
    w.maximize()
    v = gtk.VBox(False,10)
    
    v.add(gtk.Label("Add new feed(s) - separate urls with spaces"))
    
    h = gtk.HBox(False,3)
    
    h.add(gtk.Label("URL(s) for feed(s):"))
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

  def busyWindow(self, message):
    w = gtk.Window()
    w.set_transient_for(self.w)
    w.set_modal(True)
    w.set_title("Busy...")
    w.maximize()
    v=gtk.HBox(False, 0)
    v.add(gtk.Label(message))
    w.add(v)
    w.show_all()
    while gtk.events_pending():
      gtk.main_iteration(False)
    return w

  def showEpisodeList(self,  feed, downloadCallback,  playCallback,  deleteCallback):
    self.clearWindow()
    v = gtk.VBox(False,10)   
    v.pack_start(gtk.Label(feed.name), False, False, 0)
    v.pack_start(gtk.Label("%s items" % len(feed.episodes)), False, False, 0)
    list = gtk.VBox(True,  3)
    for episode in feed.episodes:
      item = gtk.HBox(False, 5)
      downloadButton = gtk.Button("get")
      downloadButton.connect('clicked',  lambda t,  selectedEpisode=episode: downloadCallback(selectedEpisode))
      item.pack_start(downloadButton, False, False, 0)
      playButton = gtk.Button("play")
      playButton.connect('clicked',  lambda t,  selectedEpisode=episode: playCallback(selectedEpisode))
      item.pack_start(playButton, False, False, 0)
      text = gtk.Label(episode.status + ", " + episode.title)
      text.set_alignment(0, 0.5)
      item.pack_start(text, False, True, 0)
      deleteButton = gtk.Button("delete")
      deleteButton.connect('clicked',  lambda t,  selectedEpisode=episode: deleteCallback(selectedEpisode))
      item.pack_start(deleteButton, False, False, 5)
      list.add(item)
    listScroller = gtk.ScrolledWindow() 
    listScroller.set_policy(gtk.POLICY_AUTOMATIC,  gtk.POLICY_AUTOMATIC)
    listScroller.add_with_viewport(list)
    v.pack_start(listScroller, True, True, 0)
    closeButton = gtk.Button("Close")
    closeButton.connect('clicked', self.showFrontPage)
    v.pack_end(closeButton, False, False, 0)
    self.w.add(v)
    self.w.show_all() #refresh display

  def __init__(self):
    self.w = gtk.Window()
    self.w.set_title("Moko do the RSS")
    self.w.connect("destroy", gtk.main_quit) # Makes gtk stop when the window is closed
    self.frontPageVBox = self.createFrontPage()
    self.showFrontPage(None)

  def clearWindow(self):
    #remove everything from the main window before displaying a different screen
    for x in self.w:
      self.w.remove(x)

  def showFrontPage(self, t):
    self.clearWindow()
    self.w.add(self.frontPageVBox)
    self.w.show_all()

  def createFrontPage(self):
    # Main page
    mainvbox = gtk.VBox(False, 10)
    # Add topbar with buttons
    hbox = gtk.HBox(False,10)
    self.configureButton = gtk.Button("Settings...")
    hbox.add(self.configureButton)
    self.updateAllButton = gtk.Button("Update all")
    hbox.add(self.updateAllButton)
    self.newFeedButton = gtk.Button("Add...")
    hbox.add(self.newFeedButton)
    mainvbox.pack_start(hbox, False, False, 0)
    # Add list of current feeds
    self.feedCombo = gtk.combo_box_new_text()
    self.feedCombo.append_text("List of feeds:")
    self.feedCombo.set_active(0)
    mainvbox.pack_start(self.feedCombo, False, False, 0)
    #feed info
    vbox = gtk.VBox(False, 1)
    self.feedInfo_label = []
    for i in range(0,6):
      self.feedInfo_label.append(gtk.Label(""))
      vbox.pack_start(self.feedInfo_label[i], False, False, 0)
    hbox = gtk.HBox(True,  5)
    self.updateFeedButton = gtk.Button("Update feed")
    self.updateFeedButton.set_sensitive(False)
    hbox.add(self.updateFeedButton)
    self.listEpisodesButton = gtk.Button("Episodes...")
    self.listEpisodesButton.set_sensitive(False)
    hbox.add(self.listEpisodesButton)
    vbox.pack_start(hbox, True, True, 0)
    self.feedInfo_removeb = gtk.Button("Remove feed and files")
    self.feedInfo_removeb.set_sensitive(False)
    vbox.pack_end(self.feedInfo_removeb, False, False, 0)
    mainvbox.add(vbox)
    return mainvbox

  def main(self):
    self.w.show_all()
    gtk.main()


class mokorss:
  def IntializeDownloadLocation(self):
   self.save_path = self.getPodcastFolder()
   if not os.path.exists(self.save_path):
     os.mkdir(self.save_path)

  def __init__(self, gui):
    self.storageRoot = os.environ.get('HOME') + "/.mokorss/"
    if not os.path.exists(self.storageRoot):
      os.mkdir(self.storageRoot)
    self.feedListFile = self.storageRoot + "feedlist"
    self.downloadFolderFile = self.storageRoot + "downloadfolder"
    self.gui = gui
    self.loadFeeds()
    self.redrawFeedCombo()
    gui.feedCombo.connect("changed", self.showFeedInfo)
    gui.newFeedButton.connect('clicked', self.newFeedWindow)
    gui.configureButton.connect('clicked', self.setFolderToSaveIn)
    gui.updateAllButton.connect('clicked',  self.updateAll)
    gui.feedInfo_removeb.connect('clicked', self.removeCurrentFeed)
    gui.listEpisodesButton.connect('clicked', self.newEpisodeListWindow)
    gui.updateFeedButton.connect('clicked', self.updateFeed)
  
  def playLatestEpisode(self, t):
    feed = self.feeds[self.gui.feedCombo.get_active()]
    view = playpod.view(self.gui.w, feed.episodes[0],  feed.name)
    playpod.control(view, feed.episodes[0], self)
  
  def playEpisode(self,  episode):
    view = playpod.view(self.gui.w, episode,  "fixme - feed title here")
    playpod.control(view, episode, self)

  def deleteEpisode(self, episode):
    if self.gui.yesNoDialog("Really delete episode?\n%s" % (episode.title)):
      if os.path.exists(episode.file):
        os.remove(episode.file)
      episode.status="deleted"
      self.saveFeeds() #to save the new state of this episode

  def getLatestEpisode(self, t):
    self.downloadEpisode(self.feeds[self.currentFeed].episodes[0])
    self.gui.showFeed() #update displayed feed info, and enable play button

  def removeCurrentFeed(self, t):
    if self.gui.yesNoDialog("Do you really want to remove\n%s?" % (self.feeds[self.currentFeed].name)):
      # Remove files
      folder=self.getPodcastFolder()+self.feeds[self.currentFeed].relativeDownloadPath
      if os.path.exists(folder):
        shutil.rmtree(folder) #remove episode files and folder
      # Remove the rest
      self.gui.clearInfoView()
      self.feeds.remove(self.feeds[self.currentFeed])
      self.saveFeeds()
      self.redrawFeedCombo()
    
  def newFeedWindow(self, t):
    self.gui.newFeedWindow()
    self.gui.newfeed_ok_button.connect('clicked',self.addNewFeeds)

  def newEpisodeListWindow(self, t):
    feed = self.feeds[self.gui.feedCombo.get_active()]
    self.gui.showEpisodeList(feed, self.downloadEpisode,  self.playEpisode,  self.deleteEpisode)

  def downloadEpisode(self, episode):
    waitWindow=self.gui.busyWindow("downloading...")
    self.IntializeDownloadLocation()
    episode.Download(self.save_path)
    self.saveFeeds() #to save the new state of this episode
    waitWindow.destroy()
    self.gui.showText("downloaded")

  def updateAll(self, t):
    waitWindow=self.gui.busyWindow("updating...")
    for feed in self.feeds:
      feed.Update()
    self.saveFeeds()
    self.gui.showFeed(self.feeds[self.currentFeed]) #update displayed feed info
    self.redrawFeedCombo()
    waitWindow.destroy()
    self.gui.showText("updated")

  def updateFeed(self, t):
    waitWindow=self.gui.busyWindow("updating...")
    feed = self.feeds[self.gui.feedCombo.get_active()]
    feed.Update()
    self.saveFeeds()
    self.gui.showFeed(self.feeds[self.currentFeed]) #update displayed feed info
    self.redrawFeedCombo()
    waitWindow.destroy()
    self.gui.showText("updated")

  def addNewFeeds(self,  t):
    text = self.gui.newfeed_URL.get_text()
    self.gui.newfeed_window.destroy()
    for url in text.split(" "): #multiple urls separated by spaces (works for single url too)
      if url!="":
        self.feeds.append(Feed(url))
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
    f = open(self.feedListFile, 'w' )
    pickle.dump(self.feeds, f)
    f.close()

  def loadFeeds(self):
    # Does the file feed list exists?
    if not os.path.exists(self.feedListFile):
      self.feeds = []
    else:
      f = open(self.feedListFile, 'r' )
      self.feeds = pickle.load(f)
      f.close()
  
  def getPodcastFolder(self):
    if not os.path.exists(self.downloadFolderFile):
      return self.storageRoot + "downloads/"
    else:
      f = open( self.downloadFolderFile, 'r' )
      place = pickle.load(f)
      f.close()
      return place
  
  def setFolderToSaveIn(self, t):
    place = self.gui.getText("Where do you want to save the podcasts?", self.getPodcastFolder())
    if len(place)==0:
      return
    if not place[-1]=="/":
      place = place + "/"
    f = open( self.downloadFolderFile, 'w' )
    pickle.dump(place, f)
    f.close()
  
  def redrawFeedCombo(self):
    selected=self.gui.feedCombo.get_active()
    number = len(self.gui.feedCombo.get_model())
    for i in range(1,number):
      self.gui.feedCombo.remove_text(1)
    for feed in self.feeds[1::]:
      self.gui.feedCombo.append_text(feed.name)
    self.gui.feedCombo.set_active(selected)
  
  def net_getFeedName(self, url):
    d = feedparser.parse(url)
    return d['feed']['title']

class Feed:
  def __init__(self,  url):
    self.url = url
    self.name = url # temporary name till first update
    self.episodes=[]

  def Update(self):
    parsedFeed = self.Parse(self.url)
    self.name = parsedFeed['feed']['title']
    self.relativeDownloadPath = self.name + "/"
    self.EnumerateEpisodes(parsedFeed)

  def Parse(self,url):
    return feedparser.parse(self.url)

  def EnumerateEpisodes(self, parsedFeed):
    #todo match existing entries
    for entry in parsedFeed.entries:
      if self.FindEpisodeById(entry.id):
        return #ignore already seen item
      episode = Episode()
      episode.id = entry.id #unique id for this episode
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
      episode.parentFeed=self
      self.episodes.append(episode);

  def FindEpisodeById(self, id):
    for episode in self.episodes:
      if episode.id==id:
        return episode

class Episode:
  def Download(self, storagePath): #storagePath is the folder that contains all downloads (without the feed name)
    self.status = "downloading"
    folder=storagePath+self.parentFeed.relativeDownloadPath
    if not os.path.exists(folder):
      os.mkdir(folder)
    self.file = folder+self.filename
    urllib.urlretrieve(self.downloadUrl, self.file)
    self.status = "ready"
    self.position = 0 #where the user stopped playing this episode

if __name__ == "__main__":
  #os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
  #gtk.gdk.threads_init()
  #gtk.gdk.threads_enter()

  g = gui()
  app = mokorss(g)
  #start processing screen events
  g.main()
  #gtk.gdk.threads_leave()
