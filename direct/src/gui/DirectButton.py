from PandaObject import *
import OnscreenText
from PGTop import *
from PGButton import *
from PGItem import *
from PGFrameStyle import *
import types
import __builtin__

NORMAL = 'normal'
DISABLED = 'disabled'

FLAT = PGFrameStyle.TFlat
RAISED = PGFrameStyle.TBevelOut
SUNKEN = PGFrameStyle.TBevelIn

# Constant used to indicate that an option can only be set by a call
# to the constructor.
INITOPT = ['initopt']

# Symbolic constants for the indexes into an optionInfo list.
_OPT_DEFAULT         = 0
_OPT_VALUE           = 1
_OPT_FUNCTION        = 2

__builtin__.guiTop = aspect2d.attachNewNode(PGTop('DirectGuiTop'))
guiTop.node().setMouseWatcher(base.mouseWatcher.node())

class DirectGuiObject(PandaObject):
    def __init__(self, optiondefs, dynamicGroups, **kw):
        # Default id of all gui object, subclasses should override this
        self.guiId = 'guiObject'
	# Mapping from each megawidget option to a list of information
	# about the option
	#   - default value
	#   - current value
	#   - function to call when the option is initialised in the
	#     call to initialiseoptions() in the constructor or
	#     modified via configure().  If this is INITOPT, the
	#     option is an initialisation option (an option that can
	#     be set by the call to the constructor but can not be
	#     used with configure).
	# This mapping is not initialised here, but in the call to
	# defineoptions() which precedes construction of this base class.
	#
	# self._optionInfo = {}

	# Mapping from each component name to a tuple of information
	# about the component.
	#   - component widget instance
	#   - configure function of widget instance
	#   - the class of the widget (Frame, EntryField, etc)
	#   - cget function of widget instance
	#   - the name of the component group of this component, if any
	self.__componentInfo = {}

	# Mapping from alias names to the names of components or
	# sub-components.
	self.__componentAliases = {}

	# Contains information about the keywords provided to the
	# constructor.  It is a mapping from the keyword to a tuple
	# containing:
	#    - value of keyword
	#    - a boolean indicating if the keyword has been used.
	# A keyword is used if, during the construction of a megawidget,
	#    - it is defined in a call to defineoptions() or addoptions(), or
	#    - it references, by name, a component of the megawidget, or
	#    - it references, by group, at least one component
	# At the end of megawidget construction, a call is made to
	# initialiseoptions() which reports an error if there are
	# unused options given to the constructor.
	#
	# self._constructorKeywords = {}

        # List of dynamic component groups.  If a group is included in
        # this list, then it not an error if a keyword argument for
        # the group is given to the constructor or to configure(), but
        # no components with this group have been created.
        # self._dynamicGroups = ()

        self.defineoptions(kw, optiondefs, dynamicGroups)
        
    def defineoptions(self, keywords, optionDefs, dynamicGroups = ()):
	# Create options, providing the default value and the method
	# to call when the value is changed.  If any option created by
	# base classes has the same name as one in <optionDefs>, the
	# base class's value and function will be overriden.
        
	# This should be called before the constructor of the base
	# class, so that default values defined in the derived class
	# override those in the base class.
	if not hasattr(self, '_constructorKeywords'):
	    tmp = {}
	    for option, value in keywords.items():
		tmp[option] = [value, 0]
            self._constructorKeywords = tmp
	    self._optionInfo = {}
        # Initialize dictionary of dynamic groups
        if not hasattr(self, '_dynamicGroups'):
            self._dynamicGroups = ()
        self._dynamicGroups = self._dynamicGroups + tuple(dynamicGroups)
        # Reconcile command line and default options
        self.addoptions(optionDefs)
        
    def addoptions(self, optionDefs):
	# Add additional options, providing the default value and the
	# method to call when the value is changed.  See
	# "defineoptions" for more details
        
	# optimisations:
	optionInfo = self._optionInfo
	optionInfo_has_key = optionInfo.has_key
	keywords = self._constructorKeywords
	keywords_has_key = keywords.has_key
	FUNCTION = _OPT_FUNCTION
        
	for name, default, function in optionDefs:
	    if '_' not in name:
                # The option will already exist if it has been defined
                # in a derived class.  In this case, do not override the
                # default value of the option or the callback function
                # if it is not None.
                if not optionInfo_has_key(name):
                    if keywords_has_key(name):
                        # Overridden by keyword, use keyword value
                        value = keywords[name][0]
                        optionInfo[name] = [default, value, function]
                        del keywords[name]
                    else:
                        # Use optionDefs value
                        optionInfo[name] = [default, default, function]
                elif optionInfo[name][FUNCTION] is None:
                    # Override function
                    optionInfo[name][FUNCTION] = function
	    else:
		# This option is of the form "component_option".  If this is
		# not already defined in self._constructorKeywords add it.
		# This allows a derived class to override the default value
		# of an option of a component of a base class.
		if not keywords_has_key(name):
		    keywords[name] = [default, 0]
                
    def initialiseoptions(self, myClass):
	if self.__class__ is myClass:
	    unusedOptions = []
	    keywords = self._constructorKeywords
	    for name in keywords.keys():
                print name
		used = keywords[name][1]
		if not used:
                    # This keyword argument has not been used.  If it
                    # does not refer to a dynamic group, mark it as
                    # unused.
                    index = string.find(name, '_')
                    if index < 0 or name[:index] not in self._dynamicGroups:
                        unusedOptions.append(name)
	    self._constructorKeywords = {}
	    if len(unusedOptions) > 0:
		if len(unusedOptions) == 1:
		    text = 'Unknown option "'
		else:
		    text = 'Unknown options "'
		raise KeyError, text + string.join(unusedOptions, ', ') + \
			'" for ' + myClass.__name__
            
	    # Call the configuration callback function for every option.
	    FUNCTION = _OPT_FUNCTION
	    for info in self._optionInfo.values():
		func = info[FUNCTION]
		if func is not None and func is not INITOPT:
		    func()
                    
    def isinitoption(self, option):
	return self._optionInfo[option][_OPT_FUNCTION] is INITOPT
    
    def options(self):
	options = []
	if hasattr(self, '_optionInfo'):
	    for option, info in self._optionInfo.items():
		isinit = info[_OPT_FUNCTION] is INITOPT
		default = info[_OPT_DEFAULT]
		options.append((option, default, isinit))
	    options.sort()
	return options
    
    def configure(self, option=None, **kw):
	# Query or configure the megawidget options.
	#
	# If not empty, *kw* is a dictionary giving new
	# values for some of the options of this gui item
	# For options defined for this widget, set
	# the value of the option to the new value and call the
	# configuration callback function, if any.
	#
	# If *option* is None, return all gui item configuration
	# options and settings.  Options are returned as standard 3
	# element tuples
	#
	# If *option* is a string, return the 3 element tuple for the
	# given configuration option.
        
	# First, deal with the option queries.
	if len(kw) == 0:
	    # This configure call is querying the values of one or all options.
	    # Return 3-tuples:
	    #     (optionName, default, value)
	    if option is None:
		rtn = {}
		for option, config in self._optionInfo.items():
		    rtn[option] = (option,
                                   config[_OPT_DEFAULT],
                                   config[_OPT_VALUE])
		return rtn
	    else:
		config = self._optionInfo[option]
		return (option, config[_OPT_DEFAULT], config[_OPT_VALUE])
            
	# optimizations:
	optionInfo = self._optionInfo
	optionInfo_has_key = optionInfo.has_key
	componentInfo = self.__componentInfo
	componentInfo_has_key = componentInfo.has_key
	componentAliases = self.__componentAliases
	componentAliases_has_key = componentAliases.has_key
	VALUE = _OPT_VALUE
	FUNCTION = _OPT_FUNCTION
        
	# This will contain a list of options in *kw* which
	# are known to this gui item.
	directOptions = []
        
	# This will contain information about the options in
	# *kw* of the form <component>_<option>, where
	# <component> is a component of this megawidget.  It is a
	# dictionary whose keys are the configure method of each
	# component and whose values are a dictionary of options and
	# values for the component.
	indirectOptions = {}
	indirectOptions_has_key = indirectOptions.has_key

	for option, value in kw.items():
	    if optionInfo_has_key(option):
		# This is one of the options of this gui item. 
		# Check it is an initialisation option.
		if optionInfo[option][FUNCTION] is INITOPT:
		    raise KeyError, \
			    'Cannot configure initialisation option "' \
			    + option + '" for ' + self.__class__.__name__
		optionInfo[option][VALUE] = value
		directOptions.append(option)
            else:
		index = string.find(option, '_')
		if index >= 0:
		    # This option may be of the form <component>_<option>.
		    component = option[:index]
		    componentOption = option[(index + 1):]

		    # Expand component alias
		    if componentAliases_has_key(component):
			component, subComponent = componentAliases[component]
			if subComponent is not None:
			    componentOption = subComponent + '_' \
				    + componentOption

			# Expand option string to write on error
			option = component + '_' + componentOption

                    # Does this component exist
		    if componentInfo_has_key(component):
			# Get the configure func for the named component
			componentConfigFuncs = [componentInfo[component][1]]
		    else:
			# Check if this is a group name and configure all
			# components in the group.
			componentConfigFuncs = []
			for info in componentInfo.values():
			    if info[4] == component:
			        componentConfigFuncs.append(info[1])

                        if len(componentConfigFuncs) == 0 and \
                                component not in self._dynamicGroups:
			    raise KeyError, 'Unknown option "' + option + \
				    '" for ' + self.__class__.__name__

		    # Add the configure method(s) (may be more than
		    # one if this is configuring a component group)
		    # and option/value to dictionary.
		    for componentConfigFunc in componentConfigFuncs:
			if not indirectOptions_has_key(componentConfigFunc):
			    indirectOptions[componentConfigFunc] = {}
			indirectOptions[componentConfigFunc][componentOption] \
				= value
		else:
		    raise KeyError, 'Unknown option "' + option + \
			    '" for ' + self.__class__.__name__

	# Call the configure methods for any components.
	map(apply, indirectOptions.keys(),
		((),) * len(indirectOptions), indirectOptions.values())
            
	# Call the configuration callback function for each option.
	for option in directOptions:
	    info = optionInfo[option]
	    func = info[_OPT_FUNCTION]
	    if func is not None:
	      func()
              
    # Allow index style references
    def __setitem__(self, key, value):
        apply(self.configure, (), {key: value})
        
    def cget(self, option):
	# Get current configuration setting.
        
	# Return the value of an option, for example myWidget['font']. 
	if self._optionInfo.has_key(option):
	    return self._optionInfo[option][_OPT_VALUE]
	else:
	    index = string.find(option, '_')
	    if index >= 0:
		component = option[:index]
		componentOption = option[(index + 1):]

		# Expand component alias
		if self.__componentAliases.has_key(component):
		    component, subComponent = self.__componentAliases[
                        component]
		    if subComponent is not None:
			componentOption = subComponent + '_' + componentOption

		    # Expand option string to write on error
		    option = component + '_' + componentOption

		if self.__componentInfo.has_key(component):
		    # Call cget on the component.
		    componentCget = self.__componentInfo[component][3]
		    return componentCget(componentOption)
		else:
		    # If this is a group name, call cget for one of
		    # the components in the group.
		    for info in self.__componentInfo.values():
			if info[4] == component:
			    componentCget = info[3]
			    return componentCget(componentOption)

        # Option not found
	raise KeyError, 'Unknown option "' + option + \
		'" for ' + self.__class__.__name__
    
    # Allow index style refererences
    __getitem__ = cget
    
    def createcomponent(self, componentName, componentAliases, componentGroup,
                        widgetClass, *widgetArgs, **kw):
	"""Create a component (during construction or later)."""
        # Check for invalid component name
	if '_' in componentName:
	    raise ValueError, \
                    'Component name "%s" must not contain "_"' % componentName
        # Get construction keywords
	if hasattr(self, '_constructorKeywords'):
	    keywords = self._constructorKeywords
	else:
	    keywords = {}

	for alias, component in componentAliases:
	    # Create aliases to the component and its sub-components.
	    index = string.find(component, '_')
	    if index < 0:
		self.__componentAliases[alias] = (component, None)
	    else:
		mainComponent = component[:index]
		subComponent = component[(index + 1):]
		self.__componentAliases[alias] = (mainComponent, subComponent)

	    # Remove aliases from the constructor keyword arguments by
	    # replacing any keyword arguments that begin with *alias*
	    # with corresponding keys beginning with *component*.

	    alias = alias + '_'
	    aliasLen = len(alias)
	    for option in keywords.keys():
		if len(option) > aliasLen and option[:aliasLen] == alias:
		    newkey = component + '_' + option[aliasLen:]
		    keywords[newkey] = keywords[option]
		    del keywords[option]

        # Find any keyword arguments for this component
	componentPrefix = componentName + '_'
	nameLen = len(componentPrefix)
	for option in keywords.keys():
	    if len(option) > nameLen and option[:nameLen] == componentPrefix:
		# The keyword argument refers to this component, so add
		# this to the options to use when constructing the widget.
		kw[option[nameLen:]] = keywords[option][0]
                # And delete it from main construction keywords
		del keywords[option]
	    else:
		# Check if this keyword argument refers to the group
		# of this component.  If so, add this to the options
		# to use when constructing the widget.  Mark the
		# keyword argument as being used, but do not remove it
		# since it may be required when creating another
		# component.
		index = string.find(option, '_')
		if index >= 0 and componentGroup == option[:index]:
		    rest = option[(index + 1):]
		    kw[rest] = keywords[option][0]
		    keywords[option][1] = 1

        # Return None if no widget class is specified
	if widgetClass is None:
	    return None
        # Get arguments for widget constructor
        if len(widgetArgs) == 1 and type(widgetArgs[0]) == types.TupleType:
            # Arguments to the constructor can be specified as either
            # multiple trailing arguments to createcomponent() or as a
            # single tuple argument.
            widgetArgs = widgetArgs[0]
        # Create the widget
	widget = apply(widgetClass, widgetArgs, kw)
	componentClass = widget.__class__.__name__
	self.__componentInfo[componentName] = (widget, widget.configure,
		componentClass, widget.cget, componentGroup)
	return widget

    def component(self, name):
	# Return a component widget of the megawidget given the
	# component's name
	# This allows the user of a megawidget to access and configure
	# widget components directly.

	# Find the main component and any subcomponents
	index = string.find(name, '_')
	if index < 0:
	    component = name
	    remainingComponents = None
	else:
	    component = name[:index]
	    remainingComponents = name[(index + 1):]

	# Expand component alias
	if self.__componentAliases.has_key(component):
	    component, subComponent = self.__componentAliases[component]
	    if subComponent is not None:
		if remainingComponents is None:
		    remainingComponents = subComponent
		else:
		    remainingComponents = subComponent + '_' \
			    + remainingComponents

	widget = self.__componentInfo[component][0]
	if remainingComponents is None:
	    return widget
	else:
	    return widget.component(remainingComponents)

    def components(self):
	# Return a list of all components.
	names = self.__componentInfo.keys()
	names.sort()
	return names

    def hascomponent(self, component):
        return component in self.__componentInfo.keys()

    def destroycomponent(self, name):
	# Remove a megawidget component.
	# This command is for use by megawidget designers to destroy a
	# megawidget component.
	self.__componentInfo[name][0].destroy()
	del self.__componentInfo[name]

    def destroy(self):
        # Clean up optionInfo in case it contains circular references
        # in the function field, such as self._settitle in class
        # MegaToplevel.

	self._optionInfo = {}

    def bind(self, sequence, command):
        self.accept(sequence + '-' + self.guiId, command)
        
    def unbind(self, sequence):
        self.ignore(sequence + '-' + self.guiId)

class DirectButton(DirectGuiObject, NodePath):
    def __init__(self, parent = guiTop, **kw):
        # Pass in a background texture, and/or a geometry object,
        # and/or a text string to be used as the visible
        # representation of the button, or pass in a list of geometry
        # objects, one for each state (normal, rollover, pressed,
        # disabled)
        # Bounding box to be used in button/mouse interaction
        # If None, use bounding box of actual button geometry
        # Otherwise, you can pass in:
        #  - a list of [L,R,B,T] (in aspect2d coords)
        #  - a VBase4(L,R,B,T)
        #  - a bounding box object
        optiondefs = (
            ('image',         None,       self.setImage),
            ('geom',          None,       self.setGeom),
            ('text',          '',         self.setText),
            ('command',       None,       self.setCommand),
            ('relief',        FLAT,       self.setRelief),
            ('frameColor',    (1,1,1,1),  self.setFrameColor),
            ('borderWidth',   (.1,.1),    self.setBorderWidth),
            ('frameSize',     None,       self.setFrameSize),
            ('pressEffect',   1,          None),
            ('padSX',         1.2,        None),
            ('padSZ',         1.1,        None),
            ('pos',           None,       None),
            ('scale',         None,       None),
            ('state',         NORMAL,     self.setState),
            ('rolloverSound', None,       None),
            ('clickSound',    None,       None),
            )
        # Update options to reflect keyword parameters
        apply(DirectGuiObject.__init__, (self, optiondefs, ('text',)), kw)
        # Initialize the superclass
        NodePath.__init__(self)
        # Create a button
        self.guiItem = PGButton()
        self.guiId = self.guiItem.getId()
        # Attach button to parent and make that self
        self.assign(parent.attachNewNode( self.guiItem ) )
        # Set up names
        self.guiItem.setName(self.guiId)
        self.setName(self.guiId + 'NodePath')
        self.stateNodePath = []
        for i in range(4):
            self.stateNodePath.append(NodePath(self.guiItem.getStateDef(i)))
        if self['pressEffect']:
            np = self.stateNodePath[1].attachNewNode('pressEffect')
            np.setScale(0.98)
            self.stateNodePath[1] = np
        # Initialize frame style
        self.frameStyle = []
        for i in range(4):
            self.frameStyle.append(PGFrameStyle())
        # For holding bounds info
        self.ll = Point3(0)
        self.ur = Point3(0)
        # Call initialization functions if necessary
        # To avoid doing things redundantly
        self.fInit = 1
        self.initialiseoptions(DirectButton)
        self.fInit = 0
        # Allow changes to take effect
        self.updateFrameStyle()
        if not self['frameSize']:
            self.setFrameSize()
        # Update pose
        if self['pos']:
            if type(self['pos']) == type(()):
                apply(self.setPos, self['pos'])
            else:
                apply(self.setPos, (self['pos'],))
        if self['scale']:
            if type(self['scale']) == type(()):
                apply(self.setScale, self['scale'])
            else:
                apply(self.setScale, (self['scale'],))

    def updateFrameStyle(self):
        for i in range(4):
            self.guiItem.setFrameStyle(i, self.frameStyle[i])

    def setRelief(self, fSetStyle = 1):
        print 'setting Frame'
        relief = self['relief']
        if relief == None:
            for i in range(4):
                self.frameStyle[i].setType(PGFrameStyle.TNone)
        elif (relief == FLAT) or (relief == 'flat'):
            for i in range(4):
                self.frameStyle[i].setType(FLAT)
        elif (relief == RAISED) or (relief == 'raised'):
            for i in (0,2,3):
                self.frameStyle[i].setType(RAISED)
            self.frameStyle[1].setType(SUNKEN)
        elif (relief == SUNKEN) or (relief == 'sunken'):
            for i in (0,2,3):
                self.frameStyle[i].setType(SUNKEN)
            self.frameStyle[1].setType(RAISED)
        if not self.fInit:
            self.updateFrameStyle()

    def resetFrameSize(self):
        self.setFrameSize(fClearFrame = 1)
        
    def setFrameSize(self, fClearFrame = 0):
        if self['frameSize']:
            # Use user specified bounds
            bounds = self['frameSize']
        else:
            # Use ready state to compute bounds
            frameType = self.frameStyle[0].getType()
            if fClearFrame and (frameType != PGFrameStyle.TNone):
                self.frameStyle[0].setType(PGFrameStyle.TNone)
                self.guiItem.setFrameStyle(0, self.frameStyle[0])
                # To force an update of the button
                self.guiItem.getStateDef(0)
            # Clear out frame before computing bounds
            self.stateNodePath[0].calcTightBounds(self.ll, self.ur)
            # Scale bounds to give a pad around graphics
            bounds = (self.ll[0] * self['padSX'], self.ur[0] * self['padSX'],
                      self.ll[2] * self['padSZ'], self.ur[2] * self['padSZ'])
            # Restore frame style if necessary
            if (frameType != PGFrameStyle.TNone):
                self.frameStyle[0].setType(frameType)
                self.guiItem.setFrameStyle(0, self.frameStyle[0])
        # Set frame to new dimensions
        self.guiItem.setFrame(bounds[0], bounds[1],bounds[2], bounds[3])

    def setFrameColor(self):
        color = self['frameColor']
        for i in range(4):
            self.frameStyle[i].setColor(color[0], color[1], color[2], color[3])
        if not self.fInit:
            self.updateFrameStyle()

    def setBorderWidth(self):
        width = self['borderWidth']
        for i in range(4):
            self.frameStyle[i].setWidth(width[0], width[1])
        if not self.fInit:
            self.updateFrameStyle()

    def setText(self):
        if not self['text']:
            print "No Text"
            return
        else:
            print "SetText"
        if ((type(self['text']) == type(())) or
            (type(self['text']) == type([]))):
            text = self['text']
        else:
            text = (self['text'],) * 4
        for i in range(4):
            component = 'text' + `i`
            if not self.hascomponent(component):
                self.createcomponent(
                    component, (), 'text',
                    OnscreenText.OnscreenText,
                    (), parent = self.stateNodePath[i],
                    text = text[i], scale = 1,
                    mayChange = 1)
            else:
                self[component + '_text'] = text[i]

    def setGeom(self):
        if not self['geom']:
            print "No Geom"
            return
        else:
            print "SetGeom"
        if ((type(self['geom']) == type(())) or
            (type(self['geom']) == type([]))):
            geom = self['geom']
        else:
            geom = (self['geom'],) * 4
        for i in range(4):
            component = 'geom' + `i`
            if not self.hascomponent(component):
                self.createcomponent(
                    component, (), 'geom',
                    OnscreenGeom,
                    (), parent = self.stateNodePath[i],
                    geom = geom[i], scale = 1)
            else:
                self[component + '_geom'] = geom[i]

    def setImage(self):
        if not self['image']:
            print "No Image"
            return
        else:
            print "SetImage"
        if ((type(self['image']) == type(())) or
            (type(self['image']) == type([]))):
            if len(self['image']) == 4:
                image = self['image']
            else:
                image = (self['image'],) * 4
        for i in range(4):
            component = 'image' + `i`
            if not self.hascomponent(component):
                self.createcomponent(
                    component, (), 'image',
                    OnscreenImage,
                    (), parent = self.stateNodePath[i],
                    image = image[i], scale = 1)
            else:
                self[component + '_image'] = image[i]

    def setState(self):
        if type(self['state']) == type(0):
            self.guiItem.setActive(self['state'])
        elif (self['state'] == NORMAL) or (self['state'] == 'normal'):
            self.guiItem.setActive(1)
        else:
            self.guiItem.setActive(0)

    def setCommand(self):
        self.unbind('click')
        if self['command']:
            self.bind('click', self['command'])
            
class DirectLabel(DirectGuiObject, PGItem):
    def __init__(self, parent = None, **kw):
        # Pass in a background texture, and/or a geometry object,
        # and/or a text string to be used as the visible
        # representation of the label
        optiondefs = (
            ('image',         None,       self.setImage),
            ('geom',          None,       self.setGeom),
            ('text',          None,       self.setText),
            ('pos',           (0,0,0),    self.setPos),
            ('scale',         (1,1,1),    self.setScale),
            ('bounds',        None,       self.setBounds),
            ('imagePos',      (0,0,0),    self.setImagePos),
            ('imageScale',    (1,1,1),    self.setImagePos),
            ('geomPos',       (0,0,0),    self.setGeomPos),
            ('geomScale',     (1,1,1),    self.setGeomPos),
            ('textPos',       (0,0,0),    self.setTextPos),
            ('textScale',     (1,1,1),    self.setTextPos),
            )
        apply(DirectGuiObject.__init__, (self, optiondefs, ()), kw)            
        self.initialiseoptions(DirectLabel)

    def setImage(self):
        pass
    def setGeom(self):
        pass
    def setText(self):
        pass
    def setPos(self):
        pass
    def setScale(self):
        pass
    def setBounds(self):
        pass
    def setImagePos(self):
        pass
    def setImagePos(self):
        pass
    def setGeomPos(self):
        pass
    def setGeomPos(self):
        pass
    def setTextPos(self):
        pass
    def setTextPos(self):
        pass
    def setState(self):
        pass


class OnscreenGeom(PandaObject, NodePath):
    def __init__(self, geom = None,
                 pos = None,
                 hpr = None,
                 scale = None,
                 color = None,
                 parent = aspect2d):
        """__init__(self, ...)

        Make a geom node from string or a node path,
        put it into the 2d sg and set it up with all the indicated parameters.

        The parameters are as follows:

          geom: the actual geometry to display or a file name.
                This may be omitted and specified later via setGeom()
                if you don't have it available.

          pos: the x, y, z position of the geometry on the screen.
               This maybe a 3-tuple of floats or a vector.
               y should be zero

          hpr: the h,p,r of the geometry on the screen.
               This maybe a 3-tuple of floats or a vector.

          scale: the size of the geometry.  This may either be a single
                 float, a 3-tuple of floats, or a vector, specifying a
                 different x, y, z scale.  y should be 1

          color: the (r, g, b, a) color of the geometry.  This is
                 normally a 4-tuple of floats or ints.

          parent: the NodePath to parent the geometry to initially.
        """
        # We ARE a node path.  Initially, we're an empty node path.
        NodePath.__init__(self)
        # Assign geometry
        if isinstance(geom, NodePath):
            self.assign(geom.copyTo(parent))
        elif type(geom) == type(''):
            self.assign(loader.loadModelCopy(geom))
            self.reparentTo(parent)

        # Adjust pose
        # Set pos
        if (isinstance(pos, types.TupleType) or
            isinstance(pos, types.ListType)):
            apply(self.setPos, pos)
        elif isinstance(pos, VBase3):
            self.setPos(pos)
        # Hpr
        if (isinstance(hpr, types.TupleType) or
            isinstance(hpr, types.ListType)):
            apply(self.setHpr, hpr)
        elif isinstance(hpr, VBase3):
            self.setPos(hpr)
        # Scale
        if (isinstance(scale, types.TupleType) or
            isinstance(scale, types.ListType)):
            apply(self.setScale, scale)
        elif isinstance(scale, VBase3):
            self.setPos(scale)
        elif (isinstance(scale, types.FloatType) or
              isinstance(scale, types.IntType)):
            self.setScale(scale)

        # Set color
        if color:
            # Set color, if specified
            self.setColor(color[0], color[1], color[2], color[3])

    def setGeom(self, geom):
        # Assign geometry
        self.removeNode()
        # Assign geometry
        if isinstance(geom, NodePath):
            self.assign(geom.copyTo(parent))
        elif type(geom) == type(''):
            self.assign(loader.loadModelCopy(geom))
            self.reparentTo(parent)

    def getGeom(self):
        return self
    
    def configure(self, option=None, **kw):
	for option, value in kw.items():
            # Use option string to access setter function
            try:
                setter = eval('self.set' +
                              string.upper(option[0]) + option[1:])
                if (((setter == self.setPos) or
                     (setter == self.setHpr) or
                     (setter == self.setScale)) and
                    (isinstance(value, types.TupleType) or
                     isinstance(value, types.ListType))):
                    apply(setter,value)
                else:
                    setter(value)
            except AttributeError:
                print 'OnscreenText.configure: invalid option:', option

    # Allow index style references
    def __setitem__(self, key, value):
        apply(self.configure, (), {key: value})
        
    def cget(self, option):
	# Get current configuration setting.
        # This is for compatability with DirectGui functions
        getter = eval('self.get' + string.upper(option[0]) + option[1:])
        return getter()

    # Allow index style refererences
    __getitem__ = cget
    


class OnscreenImage(PandaObject, NodePath):
    def __init__(self, image = None,
                 pos = None,
                 hpr = None,
                 scale = None,
                 color = None,
                 parent = aspect2d):
        """__init__(self, ...)

        Make a image node from string or a node path,
        put it into the 2d sg and set it up with all the indicated parameters.

        The parameters are as follows:

          image: the actual geometry to display or a file name.
                This may be omitted and specified later via setImage()
                if you don't have it available.

          pos: the x, y, z position of the geometry on the screen.
               This maybe a 3-tuple of floats or a vector.
               y should be zero

          hpr: the h,p,r of the geometry on the screen.
               This maybe a 3-tuple of floats or a vector.

          scale: the size of the geometry.  This may either be a single
                 float, a 3-tuple of floats, or a vector, specifying a
                 different x, y, z scale.  y should be 1

          color: the (r, g, b, a) color of the geometry.  This is
                 normally a 4-tuple of floats or ints.

          parent: the NodePath to parent the geometry to initially.
        """
        # We ARE a node path.  Initially, we're an empty node path.
        NodePath.__init__(self)
        # Assign geometry
        if isinstance(image, NodePath):
            self.assign(image.copyTo(parent))
        elif type(image) == type(()):
            model = loader.loadModelOnce(image[0])
            self.assign(model.find(image[1]))
            self.reparentTo(parent)
            model.removeNode()

        # Adjust pose
        # Set pos
        if (isinstance(pos, types.TupleType) or
            isinstance(pos, types.ListType)):
            apply(self.setPos, pos)
        elif isinstance(pos, VBase3):
            self.setPos(pos)
        # Hpr
        if (isinstance(hpr, types.TupleType) or
            isinstance(hpr, types.ListType)):
            apply(self.setHpr, hpr)
        elif isinstance(hpr, VBase3):
            self.setPos(hpr)
        # Scale
        if (isinstance(scale, types.TupleType) or
            isinstance(scale, types.ListType)):
            apply(self.setScale, scale)
        elif isinstance(scale, VBase3):
            self.setPos(scale)
        elif (isinstance(scale, types.FloatType) or
              isinstance(scale, types.IntType)):
            self.setScale(scale)

        # Set color
        if color:
            # Set color, if specified
            self.setColor(color[0], color[1], color[2], color[3])

    def setImage(self, image):
        # Assign geometry
        self.removeNode()
        if isinstance(image, NodePath):
            self.assign(image.copyTo(parent))
        elif type(image) == type(()):
            model = loader.loadModelOnce(image[0])
            self.assign(model.find(image[1]))
            self.reparentTo(parent)
            model.removeNode()

    def getImage(self):
        return self
    
    def configure(self, option=None, **kw):
	for option, value in kw.items():
            # Use option string to access setter function
            try:
                setter = eval('self.set' +
                              string.upper(option[0]) + option[1:])
                if (((setter == self.setPos) or
                     (setter == self.setHpr) or
                     (setter == self.setScale)) and
                    (isinstance(value, types.TupleType) or
                     isinstance(value, types.ListType))):
                    apply(setter,value)
                else:
                    setter(value)
            except AttributeError:
                print 'OnscreenText.configure: invalid option:', option

    # Allow index style references
    def __setitem__(self, key, value):
        apply(self.configure, (), {key: value})
        
    def cget(self, option):
	# Get current configuration setting.
        # This is for compatability with DirectGui functions
        getter = eval('self.get' + string.upper(option[0]) + option[1:])
        return getter()

    # Allow index style refererences
    __getitem__ = cget
    


"""
EXAMPLE CODE
import DirectButton
smiley = loader.loadModel('models/directmodels/smiley')
db = DirectButton.DirectButton(geom = smiley, text = 'hi',
                               scale = .15, relief = 'raised')
db['text_pos'] = (.8, -.8)
db['text_scale'] = .5
db['geom1_color'] = VBase4(1,0,0,1)
db['text2_text'] = 'bye'

def dummyCmd():
    print 'Amazing!'

db['command'] = dummyCmd

rolloverSmiley = db.component('geom2')
def shrink():
    rolloverSmiley.setScale(1)
    rolloverSmiley.lerpScale(.1,.1,.1, 1.0, blendType = 'easeInOut',
                             task = 'shrink')
db.bind('enter', shrink)
"""
