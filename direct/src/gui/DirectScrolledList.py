from DirectFrame import *
from DirectButton import *
import Task

class DirectScrolledList(DirectFrame):
    def __init__(self, parent = aspect2d, **kw):

        self.index = 0
        self.forceHeight = None

        """ If one were to want a scrolledList that makes and adds its items
           as needed, simply pass in an items list of strings (type 'str')
           and when that item is needed, itemMakeFunction will be called
           with the text, the index, and itemMakeExtraArgs.  If itemMakeFunction
           is not specified, it will create a DirectFrame with the text."""

        # if 'items' is a list of strings, make a copy for our use
        # so we can modify it without mangling the user's list
        if kw.has_key('items'):
            for item in kw['items']:
                if type(item) != type(''):
                    break
            else:
                # we get here if every item in 'items' is a string
                # make a copy
                kw['items'] = kw['items'][:]

        self.nextItemID = 10
        
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('items',              [],        None),
            ('command',            None,      None),
            ('extraArgs',          [],        None),
            ('itemMakeFunction',   None,      None),
            ('itemMakeExtraArgs',  [],        None),
            ('numItemsVisible',    1,         self.setNumItemsVisible),
            ('scrollSpeed',        8,         self.setScrollSpeed),
            ('forceHeight',        None,      self.setForceHeight),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)

        # Initialize superclasses
        DirectFrame.__init__(self, parent)

        self.incButton = self.createcomponent("incButton", (), None,
                                              DirectButton, (self,),
                                              )
        self.incButton.bind(B1PRESS, self.__incButtonDown)
        self.incButton.bind(B1RELEASE, self.__buttonUp)
        self.decButton = self.createcomponent("decButton", (), None,
                                              DirectButton, (self,),
                                              )
        self.decButton.bind(B1PRESS, self.__decButtonDown)
        self.decButton.bind(B1RELEASE, self.__buttonUp)
        self.itemFrame = self.createcomponent("itemFrame", (), None,
                                              DirectFrame, (self,),
                                              )
        for item in self["items"]:
            if item.__class__.__name__ != 'str':
                item.reparentTo(self.itemFrame)
            
        self.initialiseoptions(DirectScrolledList)
        self.recordMaxHeight()
        #if len(self["items"]) > 0:
        #    self.scrollTo(0)
        self.scrollTo(0)
        
    def setForceHeight(self):
        self.forceHeight = self["forceHeight"]

    def recordMaxHeight(self):
        if self.forceHeight is not None:
            self.maxHeight = self.forceHeight
            return
        
        self.maxHeight = 0.0
        for item in self["items"]:
            if item.__class__.__name__ != 'str':
                self.maxHeight = max(self.maxHeight, item.getHeight())
        return
        
    def setScrollSpeed(self):
        # Items per second to move
        self.scrollSpeed = self["scrollSpeed"]
        if self.scrollSpeed <= 0:
            self.scrollSpeed = 1

    def setNumItemsVisible(self):
        # Items per second to move
        self.numItemsVisible = self["numItemsVisible"]

    def destroy(self):
        taskMgr.remove(self.taskName("scroll"))
        DirectFrame.destroy(self)

    def scrollBy(self, delta):
        # print "scrollBy[",delta,"]"
        return self.scrollTo(self.index + delta)

    def getItemIndexForItemID(self, itemID):
        #for i in range(len(self["items"])):
        #    print "buttontext[",i,"]",self["items"][i]["text"]

        for i in range(len(self["items"])):
            if(self["items"][i].itemID == itemID):
                return i
        print "warning: getItemIndexForItemID: item not found!"
        return 0

    def scrollToItemID(self, itemID, centered=0):
        self.scrollTo(self.getItemIndexForItemID(itemID), centered)

    """ scrolls list so selected index is at top, or centered in box"""
    def scrollTo(self, index, centered=0):
        # print "scrollTo[",index,"] called, len(self[items])=",len(self["items"])," self[numItemsVisible]=",self["numItemsVisible"]

        numItemsVisible=self["numItemsVisible"]
        numItemsTotal = len(self["items"])
        if(centered):
            self.index = index - (numItemsVisible/2)
        else:
            self.index = index

        # Not enough items to even worry about scrolling,
        # just disable the buttons and do nothing
        if (len(self["items"]) <= numItemsVisible):
            self.incButton['state'] = DISABLED
            self.decButton['state'] = DISABLED
            # Hmm.. just reset self.index to 0 and bail out
            self.index = 0
            ret = 0
        else:
            if (self.index <= 0):
                self.index = 0
                self.decButton['state'] = DISABLED
                self.incButton['state'] = NORMAL
                ret = 0
            elif (self.index >= (numItemsTotal - numItemsVisible)):
                self.index = numItemsTotal - numItemsVisible
                # print "at list end, ",len(self["items"]),"  ",self["numItemsVisible"]
                self.incButton['state'] = DISABLED
                self.decButton['state'] = NORMAL
                ret = 0
            else:
                self.incButton['state'] = NORMAL
                self.decButton['state'] = NORMAL
                ret = 1

        # print "self.index set to ",self.index

        # Hide them all
        for item in self["items"]:
            if item.__class__.__name__ != 'str':
                item.hide()
                
        # Then show the ones in range, and stack their positions 
        upperRange = min(numItemsTotal, numItemsVisible)
        for i in range(self.index, self.index + upperRange):
            item = self["items"][i]
            #print "stacking buttontext[",i,"]",self["items"][i]["text"]
            # If the item is a 'str', then it has not been created (scrolled list is 'as needed')
            #  Therefore, use the the function given to make it or just make it a frame
            if item.__class__.__name__ == 'str':
                if self['itemMakeFunction']:
                    # If there is a function to create the item
                    item = apply(self['itemMakeFunction'], (item, i, self['itemMakeExtraArgs']))
                else:
                    item = DirectFrame(text = item, relief = None)
                #print "str stacking buttontext[",i,"]",self["items"][i]["text"]
                # Then add the newly formed item back into the normal item list
                self["items"][i] = item
                item.reparentTo(self.itemFrame)
                self.recordMaxHeight()
                
            item.show()
            item.setPos(0,0,  -(i-self.index) * self.maxHeight)
       
        if self['command']:
            # Pass any extra args to command
            apply(self['command'], self['extraArgs'])    
        return ret

    def __scrollByTask(self, task):
        if ((task.time - task.prevTime) < task.delayTime):
            return Task.cont
        else:
            ret = self.scrollBy(task.delta)
            task.prevTime = task.time
            if ret:
                return Task.cont
            else:
                return Task.done
            
    def __incButtonDown(self, event):
        task = Task.Task(self.__scrollByTask)
        task.delayTime = (1.0 / self.scrollSpeed)
        task.prevTime = 0.0
        task.delta = 1
        self.scrollBy(task.delta)
        taskMgr.add(task, self.taskName("scroll"))
        

    def __decButtonDown(self, event):
        task = Task.Task(self.__scrollByTask)
        task.delayTime = (1.0 / self.scrollSpeed)
        task.prevTime = 0.0
        task.delta = -1
        self.scrollBy(task.delta)
        taskMgr.add(task, self.taskName("scroll"))

    def __buttonUp(self, event):
        taskMgr.remove(self.taskName("scroll"))

    def addItem(self, item, refresh=1):
        """
        Add this string and extraArg to the list
        """
        item.itemID = self.nextItemID
        self.nextItemID += 1
        self['items'].append(item)
        if type(item) != type(''):
            item.reparentTo(self.itemFrame)
        if refresh:
            self.refresh()
        return item.itemID  # to pass to scrollToItemID

    def removeItem(self, item, refresh=1):
        """
        Remove this item from the panel
        """
        #print "remove item called", item
        #print "items list", self['items']
        if item in self["items"]:
            #print "removing item", item
            self["items"].remove(item)
            if type(item) != type(''):
                item.reparentTo(hidden)
            self.refresh()
            return 1
        else:
            return 0
        
    def refresh(self):
        """
        Update the list - useful when adding or deleting items
        or changing properties that would effect the scrolling
        """
        self.recordMaxHeight()
        #print "refresh called"
        self.scrollTo(self.index)
        
    def getSelectedIndex(self):
        return self.index

    def getSelectedText(self):
        return self['items'][self.index]['text']
    
