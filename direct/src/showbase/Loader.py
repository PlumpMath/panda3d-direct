"""Loader module: contains the Loader class"""

from PandaModules import *
from DirectNotifyGlobal import *

# You can specify a phaseChecker callback to check
# a modelPath to see if it is being loaded in the correct
# phase
phaseChecker = None

class Loader:

    """Loader class: contains method to load models, sounds and code"""

    notify = directNotify.newCategory("Loader")
    #notify.setDebug(1)
    
    # special methods
    def __init__(self, base):
        """__init__(self)
        Loader constructor"""
        self.base = base
        self.loader = PandaLoader()
        
    # model loading funcs
    def loadModel(self, modelPath):
        """loadModel(self, string)
        Attempt to load a model from given file path, return
        a nodepath to the model if successful or None otherwise."""
        Loader.notify.debug("Loading model: %s" % (modelPath) )
        if phaseChecker:
            phaseChecker(modelPath)
        node = self.loader.loadSync(Filename(modelPath))
        if (node != None):
            nodePath = self.base.hidden.attachNewNode(node)
        else:
            nodePath = None
        return nodePath

    def loadModelOnce(self, modelPath):
        """loadModelOnce(self, string)
        Attempt to load a model from modelPool, if not present
        then attempt to load it from disk. Return a nodepath to
        the model if successful or None otherwise"""
        Loader.notify.debug("Loading model once: %s" % (modelPath))
        if phaseChecker:
            phaseChecker(modelPath)
        node = ModelPool.loadModel(modelPath)
        if (node != None):
            nodePath = self.base.hidden.attachNewNode(node)
        else:
            nodePath = None
        return nodePath
    
    def loadModelCopy(self, modelPath):
        """loadModelCopy(self, string)
        Attempt to load a model from modelPool, if not present
        then attempt to load it from disk. Return a nodepath to
        a copy of the model if successful or None otherwise"""
        Loader.notify.debug("Loading model copy: %s" % (modelPath))
        if phaseChecker:
            phaseChecker(modelPath)
        node = ModelPool.loadModel(modelPath)
        if (node != None):
            return (NodePath(node).copyTo(self.base.hidden))
        else:
            return None

    def loadModelNode(self, modelPath):
        """loadModelNode(self, string)
        This is like loadModelOnce in that it loads a model from the
        modelPool, but it does not then instance it to hidden and it
        returns a Node instead of a NodePath.  This is particularly
        useful for special models like fonts that you don't care about
        where they're parented to, and you don't want a NodePath
        anyway--it prevents accumulation of instances of the font
        model under hidden.

        However, if you're loading a font, see loadFont(), below.
        """
        
        Loader.notify.debug("Loading model once node: %s" % (modelPath))
        if phaseChecker:
            phaseChecker(modelPath)
        return ModelPool.loadModel(modelPath)

    def unloadModel(self, modelPath):
        """unloadModel(self, string)
        """
        Loader.notify.debug("Unloading model: %s" % (modelPath))
        ModelPool.releaseModel(modelPath)

    # font loading funcs
    def loadFont(self, modelPath, priority = 0):
        """loadFont(self, string)

        This loads a special model that will be sent to a TextNode as
        a "font"--this is a model generated with egg-mkfont (or
        ttf2egg) that consists of a flat hierarchy, with one node per
        each letter of the font.  The TextNode will assemble these
        letters together, given a string.
        """
        Loader.notify.debug("Loading font: %s" % (modelPath))
        if phaseChecker:
            phaseChecker(modelPath)

        # Check the filename extension.
        fn = Filename(modelPath)
        extension = fn.getExtension()

        if extension == "" or extension == "egg" or extension == "bam":
            # A traditional model file is probably an old-style,
            # static font.
            node = ModelPool.loadModel(modelPath)
            # Create a temp node path so you can adjust priorities
            nodePath = hidden.attachNewNode(node)
            nodePath.adjustAllPriorities(priority)
            # Now create text font from the node
            font = StaticTextFont(node)

            # And remove node path
            nodePath.removeNode()
        else:
            # Otherwise, it must be a new-style, dynamic font.  Maybe
            # it's just a TTF file or something.
            font = DynamicTextFont(fn)

        return font

    # texture loading funcs
    def loadTexture(self, texturePath, alphaPath = None):
        """loadTexture(self, string)
        Attempt to load a texture from the given file path using
        TexturePool class. Returns None if not found"""

        if alphaPath == None:
            Loader.notify.debug("Loading texture: %s" % (texturePath) )
            if phaseChecker:
                phaseChecker(texturePath)
            texture = TexturePool.loadTexture(texturePath)
        else:
            Loader.notify.debug("Loading texture: %s %s" % (texturePath, alphaPath) )
            if phaseChecker:
                phaseChecker(texturePath)
            texture = TexturePool.loadTexture(texturePath, alphaPath)
        return texture

    def unloadTexture(self, texture):
        """unloadTexture(self, texture)
        """
        Loader.notify.debug("Unloading texture: %s" % (texture) )
        TexturePool.releaseTexture(texture)

    # sound loading funcs
    def loadSound(self, soundPath):
        """loadSound(self, string)
        Attempt to load a sound from the given file path using
        Cary's sound class. Returns None if not found"""
        Loader.notify.debug("Loading sound: %s" % (soundPath) )
        if phaseChecker:
            phaseChecker(soundPath)
        sound = base.sfxManager.getSound(soundPath)
        return sound

