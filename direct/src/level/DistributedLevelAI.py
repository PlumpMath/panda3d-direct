"""DistributedLevelAI.py: contains the DistributedLevelAI class"""

from ClockDelta import *
import DistributedObjectAI
import Level
import DirectNotifyGlobal
import EntityCreatorAI
import WeightedChoice

class DistributedLevelAI(DistributedObjectAI.DistributedObjectAI,
                         Level.Level):
    """DistributedLevelAI"""
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLevelAI')

    def __init__(self, air, zoneId):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        Level.Level.__init__(self)
        self.uberZoneId = zoneId

    def generate(self, spec):
        self.notify.debug('generate')
        DistributedObjectAI.DistributedObjectAI.generate(self)

        self.initializeLevel(spec)

        self.sendUpdate('setZoneIds', [self.zoneIds])
        self.sendUpdate('setStartTimestamp', [self.startTimestamp])
        self.sendUpdate('setScenarioIndex', [self.scenarioIndex])

    def delete(self):
        self.notify.debug('delete')
        self.destroyLevel()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def initializeLevel(self, spec):
        # record the level's start time so that we can sync the clients
        self.startTime = globalClock.getRealTime()
        self.startTimestamp = globalClockDelta.localToNetworkTime(
            self.startTime, bits=32)

        # choose a scenario
        wc = WeightedChoice.WeightedChoice(spec['scenarios'], 1)
        scenario = wc.choose()
        scenarioIndex = spec['scenarios'].index(scenario)

        Level.Level.initializeLevel(self, self.doId,
                                    spec, scenarioIndex)

    def createEntityCreator(self):
        """Create the object that will be used to create Entities.
        Inheritors, override if desired."""
        return EntityCreatorAI.EntityCreatorAI(self.air, level=self)

    def getEntityZoneId(self, entId):
        """figure out what network zoneId an entity is in"""
        # this func is called before the entity has been created; look
        # into the spec data, since we can't yet get a handle on the
        # object itself at this point
        spec = self.entId2spec[entId]
        type = spec['type']
        if type == 'zone':
            if not hasattr(self, 'zoneNum2zoneId'):
                # we haven't even started creating our zone entities yet;
                # we have no idea yet which zoneNums map to which
                # network zoneIds. just return None.
                return None
            # If the entity *is* the zone, it will not yet be in the
            # table; but since zone entities are currently not distributed,
            # it's fine to return None.
            return self.zoneNum2zoneId.get(spec['modelZoneNum'])
        if not spec.has_key('parent'):
            return None
        return self.getEntityZoneId(spec['parent'])

    if __debug__:
        # level editors should call this func to tweak attributes of level
        # entities
        def setAttribChange(self, entId, attribName, value):
            # send a copy to the client-side level obj
            self.sendUpdate('setAttribChange',
                            [entId, attribName, repr(value)])
            
            entity = self.getEntity(entId)
            entity.handleAttribChange(attribName, value)

            # send a copy of the entire spec for any new users that
            # might come in
            ##self.sendUpdate('setSpecOverride', [repr(self.spec)])

        def getCurrentSpec(self):
            """returns the complete, current spec, including any edits"""
            return self.spec

        """
        def getSpecOverride(self):
            # This is the value we'll send until someone actually edits
            # the level
            return repr(None)
        """
