
    """
    NodePath-extensions module: contains methods to extend functionality
    of the NodePath class
    """

    def id(self):
        """Returns the bottom node's this pointer as a unique id"""
        return self.arc()

    def getName(self):
        """Returns the name of the bottom node if it exists, or <noname>"""
        from PandaModules import *
        # Initialize to a default value
        name = '<noname>'
        # Get the bottom node
        node = self.node()
        # Is it a named node?, If so, see if it has a name
        if issubclass(node.__class__, NamedNode):
            namedNodeName = node.getName()
            # Is it not zero length?
            if len(namedNodeName) != 0:
                name = namedNodeName
        return name

    def setName(self, name = '<noname>'):
        """Returns the name of the bottom node if it exists, or <noname>"""
        from PandaModules import *
        # Get the bottom node
        node = self.node()
        # Is it a named node?, If so, see if it has a name
        if issubclass(node.__class__, NamedNode):
            node.setName(name)

    # For iterating over children
    def getChildrenAsList(self):
        """Converts a node path's child NodePathCollection into a list"""
        childrenList = []
        for childNum in range(self.getNumChildren()):
            childrenList.append(self.getChild(childNum))
        return childrenList

    def printChildren(self):
        """Prints out the children of the bottom node of a node path"""
        for child in self.getChildrenAsList():
            print child.getName()

    def toggleVis(self):
        """Toggles visibility of a nodePath"""
        if self.isHidden():
            self.show()
        else:
            self.hide()
            
    def showSiblings(self):
        """Show all the siblings of a node path"""
        for sib in self.getParent().getChildrenAsList():
            if sib.node() != self.node():
                sib.show()

    def hideSiblings(self):
        """Hide all the siblings of a node path"""
        for sib in self.getParent().getChildrenAsList():
            if sib.node() != self.node():
                sib.hide()

    def showAllDescendants(self):
        """Show the node path and all its children"""
        if self.hasArcs():
            self.show()
        for child in self.getChildrenAsList():
            child.showAllDescendants()

    def isolate(self):
        """Show the node path and hide its siblings"""
        self.showAllDescendants()
        self.hideSiblings()

    def remove(self):
        """Remove a node path from the scene graph"""
        from PandaObject import *
        # Send message in case anyone needs to do something
        # before node is deleted
        messenger.send('preRemoveNodePath', [self])
        # Remove nodePath
        self.removeNode()

    def reversels(self):
        """Walk up a tree and print out the path to the root"""
        ancestry = self.getAncestry()
        indentString = ""
        for nodePath in ancestry:
            type = nodePath.node().getType().getName()
            name = nodePath.getName()
            print indentString + type + "  " + name
            indentString = indentString + " "

    def getAncestry(self):
        """Get a list of a node path's ancestors"""
        from PandaObject import *
        node = self.node()
        if (self.hasParent()):
            ancestry = self.getParent().getAncestry()
            ancestry.append(self)
            return ancestry
        else:
            return [self]

    # private methods
    
    def __getBlend(self, blendType):
        """__getBlend(self, string)
        Return the C++ blend class corresponding to blendType string
        """
        import LerpBlendHelpers

        if (blendType == "easeIn"):
            return LerpBlendHelpers.LerpBlendHelpers.easeIn
        elif (blendType == "easeOut"):
            return LerpBlendHelpers.LerpBlendHelpers.easeOut
        elif (blendType == "easeInOut"):
            return LerpBlendHelpers.LerpBlendHelpers.easeInOut
        elif (blendType == "noBlend"):
            return LerpBlendHelpers.LerpBlendHelpers.noBlend
        else:
            raise Exception("Error: NodePath.__getBlend: Unknown blend type")

            
    def __lerp(self, functorFunc, duration, blendType, taskName=None):
        """
        __lerp(self, functorFunc, float, string, string)
        Basic lerp functionality used by other lerps.
        Fire off a lerp. Make it a task if taskName given.
        """
        # functorFunc is a function which can be called to create a functor.
        # functor creation is defered so initial state (sampled in functorFunc)
        # will be appropriate for the time the lerp is spawned
        from TaskManagerGlobal import *
        
        # make the task function
        def lerpTaskFunc(task):
            import Lerp
            import Task
            import ClockObject
            if task.init == 1:
                # make the lerp
                functor = task.functorFunc()
                task.lerp = Lerp.Lerp(functor, task.duration, task.blendType)
                task.init = 0
            dt = ClockObject.ClockObject.getGlobalClock().getDt()
            task.lerp.setStepSize(dt)
            task.lerp.step()
            if (task.lerp.isDone()):
                # Reset the init flag, in case the task gets re-used
                task.init = 1
                return(Task.done)
            else:
                return(Task.cont)
        
        # make the lerp task
        lerpTask = Task.Task(lerpTaskFunc)
        lerpTask.init = 1
        lerpTask.functorFunc = functorFunc
        lerpTask.duration = duration
        lerpTask.blendType = self.__getBlend(blendType)
        
        if (taskName == None):
            # don't spawn a task, return one instead
            return lerpTask
        else:
            # spawn the lerp task
            taskMgr.spawnTaskNamed(lerpTask, taskName)
            return lerpTask

    def __autoLerp(self, functorFunc, time, blendType, taskName):
        """_autoLerp(self, functor, float, string, string)
        This lerp uses C++ to handle the stepping. Bonus is
        its more efficient, trade-off is there is less control"""
        import AutonomousLerp
        from ShowBaseGlobal import *

        # make a lerp that lives in C++ land
        functor = functorFunc()
        lerp = AutonomousLerp.AutonomousLerp(functor, time,
                              self.__getBlend(blendType),
                              base.eventHandler)
        lerp.start()
        return lerp


    # user callable lerp methods
    def lerpColor(self, *posArgs, **keyArgs):
        """lerpColor(self, *positionArgs, **keywordArgs)
        determine which lerpColor* to call based on arguments
        """
        if (len(posArgs) == 2):
            return apply(self.lerpColorVBase4, posArgs, keyArgs)
        elif (len(posArgs) == 3):
            return apply(self.lerpColorVBase4VBase4, posArgs, keyArgs)
        elif (len(posArgs) == 5):
            return apply(self.lerpColorRGBA, posArgs, keyArgs)
        elif (len(posArgs) == 9):
            return apply(self.lerpColorRGBARGBA, posArgs, keyArgs)
        else:
            # bad args
            raise Exception("Error: NodePath.lerpColor: bad number of args")

            
    def lerpColorRGBA(self, r, g, b, a, time,
                      blendType="noBlend", auto=None, task=None):
        """lerpColorRGBA(self, float, float, float, float, float,
        string="noBlend", string=none, string=none)
        """
        def functorFunc(self = self, r = r, g = g, b = b, a = a):
            import ColorLerpFunctor
            # just end rgba values, use current color rgba values for start
            startColor = self.getColor()
            functor = ColorLerpFunctor.ColorLerpFunctor(
                self,
                startColor[0], startColor[1],
                startColor[2], startColor[3],
                r, g, b, a)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpColorRGBARGBA(self, sr, sg, sb, sa, er, eg, eb, ea, time,
                          blendType="noBlend", auto=None, task=None):
        """lerpColorRGBARGBA(self, float, float, float, float, float,
        float, float, float, float, string="noBlend", string=none, string=none)
        """
        def functorFunc(self = self, sr = sr, sg = sg, sb = sb, sa = sa,
                        er = er, eg = eg, eb = eb, ea = ea):
            import ColorLerpFunctor
            # start and end rgba values
            functor = ColorLerpFunctor.ColorLerpFunctor(self, sr, sg, sb, sa,
                                                        er, eg, eb, ea)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpColorVBase4(self, endColor, time,
                        blendType="noBlend", auto=None, task=None):
        """lerpColorVBase4(self, VBase4, float, string="noBlend", string=none,
        string=none)
        """
        def functorFunc(self = self, endColor = endColor):
            import ColorLerpFunctor
            # just end vec4, use current color for start
            startColor = self.getColor()
            functor = ColorLerpFunctor.ColorLerpFunctor(
                self, startColor, endColor)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpColorVBase4VBase4(self, startColor, endColor, time,
                          blendType="noBlend", auto=None, task=None):
        """lerpColorVBase4VBase4(self, VBase4, VBase4, float, string="noBlend",
        string=none, string=none)
        """
        def functorFunc(self = self, startColor = startColor,
                        endColor = endColor):
            import ColorLerpFunctor
            # start color and end vec
            functor = ColorLerpFunctor.ColorLerpFunctor(
                self, startColor, endColor)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)
            

    def lerpHpr(self, *posArgs, **keyArgs):
        """lerpHpr(self, *positionArgs, **keywordArgs)
        Determine whether to call lerpHprHPR or lerpHprVBase3
        based on first argument
        """
        # check to see if lerping with
        # three floats or a VBase3
        if (len(posArgs) == 4):
            return apply(self.lerpHprHPR, posArgs, keyArgs)
        elif(len(posArgs) == 2):
            return apply(self.lerpHprVBase3, posArgs, keyArgs)
        else:
            # bad args
            raise Exception("Error: NodePath.lerpHpr: bad number of args")
    
    def lerpHprHPR(self, h, p, r, time, other=None,
                   blendType="noBlend", auto=None, task=None):
        """lerpHprHPR(self, float, float, float, float, string="noBlend",
        string=none, string=none, NodePath=none)
        Perform a hpr lerp with three floats as the end point
        """
        def functorFunc(self = self, h = h, p = p, r = r, other = other):
            import HprLerpFunctor
            # it's individual hpr components
            if (other != None):
                # lerp wrt other
                startHpr = self.getHpr(other)
                functor = HprLerpFunctor.HprLerpFunctor(
                    self,
                    startHpr[0], startHpr[1], startHpr[2],
                    h, p, r, other)
            else:
                startHpr = self.getHpr()
                functor = HprLerpFunctor.HprLerpFunctor(
                    self,
                    startHpr[0], startHpr[1], startHpr[2],
                    h, p, r)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)
    
    def lerpHprVBase3(self, hpr, time, other=None,
                      blendType="noBlend", auto=None, task=None):
        """lerpHprVBase3(self, VBase3, float, string="noBlend", string=none,
        string=none, NodePath=None)
        Perform a hpr lerp with a VBase3 as the end point
        """
        def functorFunc(self = self, hpr = hpr, other = other):
            import HprLerpFunctor
            # it's a vbase3 hpr
            if (other != None):
                # lerp wrt other
                functor = HprLerpFunctor.HprLerpFunctor(
                    self, (self.getHpr(other)), hpr, other)
            else:
                functor = HprLerpFunctor.HprLerpFunctor(
                    self, (self.getHpr()), hpr)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)
        

    def lerpPos(self, *posArgs, **keyArgs):
        """lerpPos(self, *positionArgs, **keywordArgs)
        Determine whether to call lerpPosXYZ or lerpPosPoint3
        based on the first argument
        """
        # check to see if lerping with three
        # floats or a Point3
        if (len(posArgs) == 4):
            return apply(self.lerpPosXYZ, posArgs, keyArgs)
        elif(len(posArgs) == 2):
            return apply(self.lerpPosPoint3, posArgs, keyArgs)
        else:
            # bad number off args
            raise Exception("Error: NodePath.lerpPos: bad number of args")
        
    def lerpPosXYZ(self, x, y, z, time, other=None,
                   blendType="noBlend", auto=None, task=None):
        """lerpPosXYZ(self, float, float, float, float, string="noBlend",
        string=None, NodePath=None)
        Perform a pos lerp with three floats as the end point
        """
        def functorFunc(self = self, x = x, y = y, z = z, other = other):
            import PosLerpFunctor
            if (other != None):
                # lerp wrt other
                startPos = self.getPos(other)
                functor = PosLerpFunctor.PosLerpFunctor(self,
                                         startPos[0], startPos[1], startPos[2],
                                         x, y, z, other)
            else:
                startPos = self.getPos()
                functor = PosLerpFunctor.PosLerpFunctor(self, startPos[0],
                                         startPos[1], startPos[2], x, y, z)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return  self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpPosPoint3(self, pos, time, other=None,
                      blendType="noBlend", auto=None, task=None):
        """lerpPosPoint3(self, Point3, float, string="noBlend", string=None,
        string=None, NodePath=None)
        Perform a pos lerp with a Point3 as the end point
        """
        def functorFunc(self = self, pos = pos, other = other):
            import PosLerpFunctor
            if (other != None):
                #lerp wrt other
                functor = PosLerpFunctor.PosLerpFunctor(
                    self, (self.getPos(other)), pos, other)
            else:
                functor = PosLerpFunctor.PosLerpFunctor(
                    self, (self.getPos()), pos)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)


    def lerpPosHpr(self, *posArgs, **keyArgs):
        """lerpPosHpr(self, *positionArgs, **keywordArgs)
        Determine whether to call lerpPosHprXYZHPR or lerpHprPoint3VBase3
        based on first argument
        """
        # check to see if lerping with
        # six floats or a Point3 and a VBase3
        if (len(posArgs) == 7):
            return apply(self.lerpPosHprXYZHPR, posArgs, keyArgs)
        elif(len(posArgs) == 3):
            return apply(self.lerpPosHprPoint3VBase3, posArgs, keyArgs)
        else:
            # bad number off args
            raise Exception("Error: NodePath.lerpPosHpr: bad number of args")

    def lerpPosHprPoint3VBase3(self, pos, hpr, time, other=None,
                               blendType="noBlend", auto=None, task=None):
        """lerpPosHprPoint3VBase3(self, Point3, VBase3, string="noBlend",
        string=none, string=none, NodePath=None)
        """
        def functorFunc(self = self, pos = pos, hpr = hpr, other = other):
            import PosHprLerpFunctor
            if (other != None):
                # lerp wrt other
                startPos = self.getPos(other)
                startHpr = self.getHpr(other)
                functor = PosHprLerpFunctor.PosHprLerpFunctor(
                    self, startPos, pos,
                    startHpr, hpr, other)
            else:
                startPos = self.getPos()
                startHpr = self.getHpr()
                functor = PosHprLerpFunctor.PosHprLerpFunctor(
                    self, startPos, pos,
                    startHpr, hpr)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpPosHprXYZHPR(self, x, y, z, h, p, r, time, other=None,
                         blendType="noBlend", auto=None, task=None):
        """lerpPosHpr(self, float, string="noBlend", string=none,
        string=none, NodePath=None)
        """
        def functorFunc(self = self, x = x, y = y, z = z,
                        h = h, p = p, r = r, other = other):
            import PosHprLerpFunctor
            if (other != None):
                # lerp wrt other
                startPos = self.getPos(other)
                startHpr = self.getHpr(other)
                functor = PosHprLerpFunctor.PosHprLerpFunctor(self,
                                            startPos[0], startPos[1],
                                            startPos[2], x, y, z,
                                            startHpr[0], startHpr[1],
                                            startHpr[2], h, p, r,
                                            other)
            else:
                startPos = self.getPos()
                startHpr = self.getHpr()
                functor = PosHprLerpFunctor.PosHprLerpFunctor(self,
                                            startPos[0], startPos[1],
                                            startPos[2], x, y, z,
                                            startHpr[0], startHpr[1],
                                            startHpr[2], h, p, r)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)


    def lerpPosHprScale(self, pos, hpr, scale, time, other=None,
                        blendType="noBlend", auto=None, task=None):
        """lerpPosHpr(self, Point3, VBase3, float, float, string="noBlend",
        string=none, string=none, NodePath=None)
        Only one case, no need for extra args. Call the appropriate lerp
        (auto, spawned, or blocking) based on how(if) a task name is given
        """
        def functorFunc(self = self, pos = pos, hpr = hpr,
                        scale = scale, other = other):
            import PosHprScaleLerpFunctor
            if (other != None):
                # lerp wrt other
                startPos = self.getPos(other)
                startHpr = self.getHpr(other)
                startScale = self.getScale(other)
                functor = PosHprScaleLerpFunctor.PosHprScaleLerpFunctor(self,
                                                 startPos, pos,
                                                 startHpr, hpr,
                                                 startScale, scale, other)
            else:
                startPos = self.getPos()
                startHpr = self.getHpr()
                startScale = self.getScale()
                functor = PosHprScaleLerpFunctor.PosHprScaleLerpFunctor(self,
                                                 startPos, pos,
                                                 startHpr, hpr,
                                                 startScale, scale)

            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)


    def lerpScale(self, *posArgs, **keyArgs):
        """lerpSclae(self, *positionArgs, **keywordArgs)
        Determine whether to call lerpScaleXYZ or lerpScaleaseV3
        based on the first argument
        """
        # check to see if lerping with three
        # floats or a Point3
        if (len(posArgs) == 4):
            return apply(self.lerpScaleXYZ, posArgs, keyArgs)
        elif(len(posArgs) == 2):
            return apply(self.lerpScaleVBase3, posArgs, keyArgs)
        else:
            # bad number off args
            raise Exception("Error: NodePath.lerpScale: bad number of args")

    def lerpScaleVBase3(self, scale, time, other=None,
                        blendType="noBlend", auto=None, task=None):
        """lerpPos(self, VBase3, float, string="noBlend", string=none,
        string=none, NodePath=None)
        """
        def functorFunc(self = self, scale = scale, other = other):
            import ScaleLerpFunctor
            if (other != None):
                # lerp wrt other
                functor = ScaleLerpFunctor.ScaleLerpFunctor(self,
                                           (self.getScale(other)),
                                           scale, other)
            else:
                functor = ScaleLerpFunctor.ScaleLerpFunctor(self,
                                           (self.getScale()), scale)

            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)

    def lerpScaleXYZ(self, sx, sy, sz, time, other=None,
                     blendType="noBlend", auto=None, task=None):
        """lerpPos(self, float, float, float, float, string="noBlend",
        string=none, string=none, NodePath=None)
        """
        def functorFunc(self = self, sx = sx, sy = sy, sz = sz, other = other):
            import ScaleLerpFunctor
            if (other != None):
                # lerp wrt other
                startScale = self.getScale(other)
                functor = ScaleLerpFunctor.ScaleLerpFunctor(self,
                                           startScale[0], startScale[1],
                                           startScale[2], sx, sy, sz, other)
            else:
                startScale = self.getScale()
                functor = ScaleLerpFunctor.ScaleLerpFunctor(self,
                                           startScale[0], startScale[1],
                                           startScale[2], sx, sy, sz)
            return functor
        #determine whether to use auto, spawned, or blocking lerp
        if (auto != None):
            return self.__autoLerp(functorFunc, time, blendType, auto)
        elif (task != None):
            return self.__lerp(functorFunc, time, blendType, task)
        else:
            return self.__lerp(functorFunc, time, blendType)
            














