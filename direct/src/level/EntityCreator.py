"""EntityCreator module: contains the EntityCreator class"""

import EntityCreatorBase
import BasicEntities
import DirectNotifyGlobal
import LevelMgr
import ZoneEntity

# some useful constructor functions
# ctor functions must take (level, entId)
def nothing(*args):
    """For entities that don't need to be created by the client"""
    return None

class EntityCreator(EntityCreatorBase.EntityCreatorBase):
    """This class is responsible for creating instances of Entities on the
    client. It can be subclassed to handle more Entity types."""
    
    def __init__(self, level):
        EntityCreatorBase.EntityCreatorBase.__init__(self, level)
        self.level = level
        self.privRegisterTypes({
            'levelMgr': LevelMgr.LevelMgr,
            'logicGate': nothing,
            'nodepath': BasicEntities.NodePathEntity,
            'zone': ZoneEntity.ZoneEntity,
            })

    def doCreateEntity(self, ctor, entId):
        return ctor(self.level, entId)
