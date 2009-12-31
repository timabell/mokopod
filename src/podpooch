#!/usr/bin/env python

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



import gobject,gtk, os, sys
import pickle
import urllib # So we can download files
import shutil
from time import strftime
from threading import Thread

sys.path.append('/usr/lib/site-python')

from podpoochlib import feedparser
from podpoochlib import playpod

# Requirements on Openmoko: (not complete)
# python-html, python-pickle, python-netclient, mplayer, python-pygtk

class gui:
  def quit(self,target):
    gtk.main_quit(target)
    exit()
  
  def get_active_text(self, combobox):
    model = combobox.get_model()
    active = combobox.get_active()-1
    if active < 1:
      return None
    return model[active][0]
  
  def showFeed(self, feed):
    #called indirectly when item selected in feed list combo box
    self.listEpisodesButton.set_sensitive(True)
    self.updateFeedButton.set_sensitive(True)
    self.feedInfo_removeb.set_sensitive(True)
    self.feedInfo_label[1].set_label("URL: " + feed.url)
    if feed.name==None: #no data to display yet
      return
    self.feedInfo_label[0].set_label("Name: " + feed.name)
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
    self.listEpisodesButton.set_sensitive(False)
    self.updateFeedButton.set_sensitive(False)
    self.feedInfo_removeb.set_sensitive(False)

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
    list = gtk.VBox(True,  10)
    for episode in feed.episodes:
      item = gtk.HBox(False, 5)
      downloadButton = gtk.Button("get")
      downloadButton.connect('clicked',  lambda t,  e=episode: downloadCallback(e))
      item.pack_start(downloadButton, False, False, 5)
      playButton = gtk.Button("play")
      playButton.connect('clicked',  lambda t,  e=episode: playCallback(e))
      item.pack_start(playButton, False, False, 0)
      text = gtk.Label(episode.status + ", " + episode.title)
      text.set_alignment(0, 0.5)
      item.pack_start(text, False, True, 0)
      deleteButton = gtk.Button("delete")
      deleteButton.connect('clicked',  lambda t,  e=episode: deleteCallback(e))
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
    self.w.set_title("Pod Pooch")
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
    mainvbox = gtk.VBox(False, 5)
    # Add topbar with buttons
    globalButtonsHBox = gtk.HBox(True, 5)
    self.configureButton = gtk.Button("Settings...")
    globalButtonsHBox.add(self.configureButton)
    self.updateAllButton = gtk.Button("Update all")
    globalButtonsHBox.add(self.updateAllButton)
    self.newFeedButton = gtk.Button("Add...")
    globalButtonsHBox.add(self.newFeedButton)
    mainvbox.pack_start(globalButtonsHBox, True, True, 0)
    # Add list of current feeds
    self.feedCombo = gtk.combo_box_new_text()
    self.feedCombo.append_text("List of feeds:")
    self.feedCombo.set_active(0)
    mainvbox.pack_start(self.feedCombo, True, True, 0)
    #feed info
    feedInfoVBox = gtk.VBox(False, 1)
    self.feedInfo_label = []
    for i in range(0,6):
      self.feedInfo_label.append(gtk.Label(""))
      feedInfoVBox.pack_start(self.feedInfo_label[i], False, False, 0)
    mainvbox.pack_start(feedInfoVBox, False, False, 0)
    #feed buttons
    feedButtonsHBox = gtk.HBox(True,  5)
    self.updateFeedButton = gtk.Button("Update feed")
    self.updateFeedButton.set_sensitive(False)
    feedButtonsHBox.add(self.updateFeedButton)
    self.listEpisodesButton = gtk.Button("Episodes...")
    self.listEpisodesButton.set_sensitive(False)
    feedButtonsHBox.add(self.listEpisodesButton)
    mainvbox.pack_start(feedButtonsHBox, True, True, 0)
    #remove feed button
    self.feedInfo_removeb = gtk.Button("Remove feed and files")
    self.feedInfo_removeb.set_sensitive(False)
    mainvbox.pack_end(self.feedInfo_removeb, False, False, 0)
    return mainvbox

  def main(self):
    self.w.show_all()
    gtk.main()


class mokorss:
  def __init__(self, gui):
    self.feeds = []
    self.storageRoot = os.environ.get('HOME') + "/.mokorss/"
    self.feedListFile = self.storageRoot + "feedlist"
    self.downloadFolderFile = self.storageRoot + "downloadfolder"
    self.initStorageRoot()
    self.save_path = self.getPodcastFolder()
    self.gui = gui
    self.loadFeeds()
    #ui events
    gui.feedCombo.connect("changed", self.showFeedInfo)
    gui.newFeedButton.connect('clicked', self.newFeedWindow)
    gui.configureButton.connect('clicked', self.setFolderToSaveIn)
    gui.updateAllButton.connect('clicked',  self.updateAll)
    gui.feedInfo_removeb.connect('clicked', self.removeCurrentFeed)
    gui.listEpisodesButton.connect('clicked', self.newEpisodeListWindow)
    gui.updateFeedButton.connect('clicked', self.updateFeed)

  def initStorageRoot(self):
    try:
      if not os.path.exists(self.storageRoot):
        os.mkdir(self.storageRoot)
    except BaseException, err:
      self.gui.showText("failed to create storage root!\n'%s'\n%s\n%s" %  (self.storageRoot, err.__class__.__name__,  err.args))
  
  def playEpisode(self,  episode):
    try:
      episode.position = self.getPosition(episode)
      view = playpod.view(self.gui.w, episode)
      playpod.control(view, episode, self)
    except BaseException, err:
      self.gui.showText("playEpisode failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
      raise

  def getPosition(self,  episode):
    try:
      positionFile=self.save_path + episode.parentFeed.relativeDownloadPath + episode.filename + '.position'
      if not os.path.exists(positionFile):
        return 0
      else:
        f = open(positionFile, 'r' )
        line=f.read()
        f.close()
        return int(line)
    except BaseException, err:
      self.gui.showText("failed to load playback position!\n%s\n%s" %  (err.__class__.__name__,  err.args))

  def savePosition(self,  episode,  position):
    try:
      positionFile=self.save_path + episode.parentFeed.relativeDownloadPath + episode.filename + '.position'
      f = open(positionFile, 'w' )
      f.write(str(position))
      f.close()
    except BaseException, err:
      self.gui.showText("failed to save playback position!\n%s\n%s" %  (err.__class__.__name__,  err.args))

  def deleteEpisode(self, episode):
    if self.gui.yesNoDialog("Really delete episode?\n%s" % (episode.title)):
      try:
        if os.path.exists(episode.file):
          os.remove(episode.file)
      except BaseException, err:
        self.gui.showText("deleteEpisode failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
        return
      episode.status="deleted"
      self.saveFeeds() #to save the new state of this episode

  def removeCurrentFeed(self, t):
    if self.gui.yesNoDialog("Do you really want to remove\n%s?" % (self.feeds[self.currentFeed].name)):
      # Remove files
      folder=self.getPodcastFolder()+self.feeds[self.currentFeed].relativeDownloadPath
      try:
        if os.path.exists(folder):
          shutil.rmtree(folder) #remove episode files and folder
      except BaseException, err:
        self.gui.showText("removeCurrentFeed failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
        return
      # Remove the rest
      self.gui.clearInfoView()
      self.feeds.remove(self.feeds[self.currentFeed])
      self.saveFeeds()
      self.redrawFeedCombo()
    
  def newFeedWindow(self, t):
    self.gui.newFeedWindow()
    self.gui.newfeed_ok_button.connect('clicked',self.addNewFeeds)

  def newEpisodeListWindow(self, t):
    feed = self.feeds[self.gui.feedCombo.get_active()-1]
    self.gui.showEpisodeList(feed, self.downloadEpisode,  self.playEpisode,  self.deleteEpisode)

  def downloadEpisode(self, episode):
    waitWindow=self.gui.busyWindow("downloading...")
    try:
      episode.Download(self.save_path)
    except BaseException, err:
      waitWindow.destroy()
      self.gui.showText("download failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
      return
    self.saveFeed(episode.parentFeed) #to save the new state of this episode
    waitWindow.destroy()
    self.gui.showText("downloaded")

  def updateAll(self, t):
    failed=[]
    total=len(self.feeds)
    succeeded=0
    progress=0
    episodes=0
    lastUpdateResult=""
    for feed in self.feeds:
      progress+=1
      waitWindow=self.gui.busyWindow("updating %s...\nfeed %i of %i. %i failed feeds.\n%s\n%i total new episodes" % (feed.name, progress, total, len(failed), lastUpdateResult, episodes))
      try:
        feed.Update()
        succeeded+=1
        episodes+=feed.countNewest()
      except BaseException, err:
        waitWindow.destroy()
        failed.append("%s error:\n%s\n%s" %  (feed.name, err.__class__.__name__,  err.args))
        lastUpdateResult="Previous feed failed:\n%s" % feed.name
        continue
      self.saveFeedList()  #update saved feed name
      self.saveFeed(feed)
      waitWindow.destroy()
      lastUpdateResult="Previous feed:\n%s\n%i new episodes" % (feed.name, feed.countNewest())
    self.redrawFeedCombo()
    finalStatus="%i feeds updated\n%i new episodes" % (succeeded, episodes)
    if len(failed):
      self.gui.showText("%s\n%i failures:\n%s" % (finalStatus, len(failed), '\n'.join(failed)))
    else:
      self.gui.showText(finalStatus)

  def updateFeed(self, t):
    waitWindow=self.gui.busyWindow("updating...")
    feed = self.feeds[self.gui.feedCombo.get_active()-1]
    try:
      feed.Update()
    except BaseException, err:
      waitWindow.destroy()
      self.gui.showText("update failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
      return
    self.saveFeedList()  #update saved feed name
    self.saveFeed(feed)
    self.gui.showFeed(self.feeds[self.currentFeed]) #update displayed feed info
    self.redrawFeedCombo()
    waitWindow.destroy()
    self.gui.showText("updated\n%i new episodes" % feed.countNewest())

  def addNewFeeds(self,  t):
    text = self.gui.newfeed_URL.get_text()
    self.gui.newfeed_window.destroy()
    for url in text.split(" "): #multiple urls separated by spaces (works for single url too)
      if url!="":
        feed=Feed(url)
        self.feeds.append(feed)
    self.saveFeedList()
    self.redrawFeedCombo()

  def showFeedInfo(self, cb):
    #fired when item selected in feed list combo box
    active = cb.get_active()-1
    if active < 0:
      self.gui.clearInfoView()
      return None
    self.currentFeed = active
    self.gui.showFeed( self.feeds[active] )

  def saveFeedList(self):
    self.feedInfo = FeedInfo()
    for feed in self.feeds:
      self.feedInfo.feedInfoList.append({"name":feed.name,  "folder":feed.relativeDownloadPath,  "url":feed.url})
    try:
      f = open(self.feedListFile, 'w' )
      pickle.dump(self.feedInfo, f)
      f.close()
    except BaseException, err:
      self.gui.showText("saveFeedList failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))

  def loadFeeds(self):
    try:
      if not os.path.exists(self.feedListFile): # Does the file feed list exists?
        return # nothing to load
      else:
        f = open(self.feedListFile, 'r' )
        self.feedInfo = pickle.load(f)
        f.close()
    except BaseException, err:
      self.gui.showText("loadFeedList failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
    #load saved data for each feed
    for feedInfo in self.feedInfo.feedInfoList:
      if feedInfo["folder"]: #folder only available after feed parsed for first time as based on feed title
        feed = self.loadFeed(self.save_path + feedInfo["folder"])
        if feed==None: #load feed stub instead as no feed data found
          feed=Feed(feedInfo["url"])
        self.feeds.append(feed)
      else:
        self.feeds.append(Feed(feedInfo["url"]))
    self.redrawFeedCombo()

  def saveFeed(self,  feed):
    #save feed state to file in feed folder
    feedPath = self.save_path + feed.relativeDownloadPath
    try:
      if not os.path.exists(self.save_path):
        os.mkdir(self.save_path)
      if not os.path.exists(feedPath):
        os.mkdir(feedPath)
      f = open(feedPath + 'pickledFeedData', 'w' )
      pickle.dump(feed, f)
      f.close()
    except BaseException, err:
      self.gui.showText("saveFeed for %s failed!\n%s\n%s" %  (feed.name, err.__class__.__name__,  err.args))

  def loadFeed(self, feedFolder):
    try:
      feedFile = feedFolder + "pickledFeedData"
      if not os.path.exists(feedFile): # Does the feed data file exists?
        return None# nothing to load
      else:
        f = open(feedFile, 'r' )
        feed = pickle.load(f)
        f.close()
      return feed
    except BaseException, err:
      self.gui.showText("loadFeed for %s failed!\n%s\n%s" %  (feedFolder, err.__class__.__name__,  err.args))
    return None #failed
  
  def getPodcastFolder(self):
    try:
      if not os.path.exists(self.downloadFolderFile):
        return self.storageRoot + "downloads/"
      else:
        f = open( self.downloadFolderFile, 'r' )
        place = pickle.load(f)
        f.close()
        return place
    except BaseException, err:
      self.gui.showText("getPodcastFolder failed!\n%s\n%s" %  (err.__class__.__name__,  err.args))
  
  def setFolderToSaveIn(self, t):
    place = self.gui.getText("Where do you want to save the podcasts?", self.getPodcastFolder())
    if len(place)==0:
      return
    if not place[-1]=="/":
      place = place + "/"
    try:
      f = open( self.downloadFolderFile, 'w' )
      pickle.dump(place, f)
      f.close()
    except BaseException, err:
      self.gui.showText("failed to save storage config!\n'%s'\n%s\n%s" %  (self.downloadFolderFile, err.__class__.__name__,  err.args))

  def redrawFeedCombo(self):
    #remember which was already selected
    selected=self.gui.feedCombo.get_active()
    number = len(self.gui.feedCombo.get_model())
    for i in range(1,number): #remove all but title entry
      self.gui.feedCombo.remove_text(1)
    for feed in self.feeds: #add each feed
      #name, total (excluding deleted), newest, downloaded
      if feed.name:
        self.gui.feedCombo.append_text("%s||%inew|%igot|%itotal)" % (feed.name[:26],  feed.countNewest(),  feed.countDownloaded(), feed.count()))
      else: #no data for feed yet
        self.gui.feedCombo.append_text(feed.url)
    self.gui.feedCombo.set_active(selected)
  
  def net_getFeedName(self, url):
    d = feedparser.parse(url)
    return d['feed']['title']

class Feed:
  def __init__(self,  url):
    self.url = url
    self.name = url # temporary name till first update
    self.episodes=[]
    self.relativeDownloadPath=None
    self.name=None

  def count(self):
    newest = filter(lambda episode: episode.status!="deleted",  self.episodes)
    return len(newest)

  def countNewest(self):
    newest = filter(lambda episode: episode.status=="newest",  self.episodes)
    return len(newest)

  def countDownloaded(self):
    newest = filter(lambda episode: episode.status=="ready",  self.episodes)
    return len(newest)

  def Update(self):
    parsedFeed = self.Parse(self.url)
    self.name = parsedFeed['feed']['title']
    self.relativeDownloadPath = self.name + "/"
    self.EnumerateEpisodes(parsedFeed)

  def Parse(self,url):
    return feedparser.parse(self.url)

  def EnumerateEpisodes(self, parsedFeed):
    #run through backwards, feeds are usually supplied with new entries first, 
    #and we would have to create our final list newest first.
    #Eg. previous feed provided episodes feb, mar, april, (oldest to newest) 
    #which would have been supplied in reverse order as april, mar, feb (newest to oldest), 
    #we would already have this stored as (april, mar, feb)
    #we update and get supplied june, may, april (one existing, two new, newest first)
    #processing in reverse order - april is matched, may is prepended to existing list, 
    #june is prepended to existing list, giving us the desired list of june, may, april, mar, feb, ready for display in the episode list.
    parsedFeed.entries.reverse() #sort list to be oldest to newest
    for entry in parsedFeed.entries:
      existing = self.FindEpisodeById(entry.id)
      if existing:
        if existing.status=="newest":
          existing.status="new" #no longer newest item
        continue #ignore already seen item
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
      episode.status = "newest"
      episode.parentFeed=self
      self.episodes.insert(0, episode); #prepend

  def FindEpisodeById(self, id):
    for episode in self.episodes:
      if episode.id==id:
        return episode

class Episode:
  # possible episode states:
  # newest - added in last feed update, not downloaded yet
  # new - no longer newest (ie, the feed has been read since the first time this was seen), not downloaded yet
  # ready - audio file downloaded and ready to play
  # deleted - audio file deleted (i.e. user no longer interested in this episode), still displayed in episode list
  def Download(self, storagePath): #storagePath is the folder that contains all downloads (without the feed name)
    self.status = "downloading"
    folder=storagePath+self.parentFeed.relativeDownloadPath
    if not os.path.exists(folder):
      os.mkdir(folder)
    self.file = folder+self.filename
    urllib.urlretrieve(self.downloadUrl, self.file)
    self.status = "ready"

class FeedInfo:
  #minimum info needed to rest of feed info from disk
  def __init__(self):
    self.feedInfoList = []
  

if __name__ == "__main__":
  #os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
  #gtk.gdk.threads_init()
  #gtk.gdk.threads_enter()

  g = gui()
  app = mokorss(g)
  #start processing screen events
  g.main()
  #gtk.gdk.threads_leave()
