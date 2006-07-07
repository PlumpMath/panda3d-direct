from direct.directnotify.DirectNotifyGlobal import directNotify

class DoHierarchy:
    """
    This table has been a source of memory leaks, with DoIds getting left in the table indefinitely.
    DoHierarchy guards access to the table and ensures correctness.
    """
    notify = directNotify.newCategory("DoHierarchy")

    def __init__(self):
        # parentId->zoneId->set(child DoIds)
        self._table = {}
        self._allDoIds = set()

    def isEmpty(self):
        assert ((len(self._table) == 0) == (len(self._allDoIds) == 0))
        return len(self._table) == 0 and len(self._allDoIds) == 0

    def __len__(self):
        return len(self._allDoIds)

    def clear(self):
        assert self.notify.debugCall()
        self._table = {}
        self._allDoIds = set()

    def getDoIds(self, parentId, zoneId=None, classType=None):
        """
        Moved from DoCollectionManager
        ==============================
        parentId is any distributed object id.
        zoneId is a uint32, defaults to None (all zones).  Try zone 2 if
            you're not sure which zone to use (0 is a bad/null zone and
            1 has had reserved use in the past as a no messages zone, while
            2 has traditionally been a global, uber, misc stuff zone).
        dclassType is a distributed class type filter, defaults
            to None (no filter).

        If dclassName is None then all objects in the zone are returned;
        otherwise the list is filtered to only include objects of that type.
        """
        parent=self._table.get(parentId)
        if parent is None:
            return []
        if zoneId is None:
            r = []
            for zone in parent.values():
                for obj in zone:
                    r.append(obj)
        else:
            r = parent.get(zoneId, [])
        if classType is not None:
            a = []
            for doId in r:
                obj = self.getDo(doId)
                if isinstance(obj, classType):
                    a.append(doId)
            r = a
        return r

    def storeObjectLocation(self, doId, parentId, zoneId):
        assert self.notify.debugCall()
        assert doId not in self._allDoIds
        parentZoneDict = self._table.setdefault(parentId, {})
        zoneDoSet = parentZoneDict.setdefault(zoneId, set())
        zoneDoSet.add(doId)
        self._allDoIds.add(doId)

    def deleteObjectLocation(self, doId, parentId, zoneId):
        assert self.notify.debugCall()
        assert doId in self._allDoIds
        parentZoneDict = self._table.get(parentId)
        if parentZoneDict is not None:
            zoneDoSet = parentZoneDict.get(zoneId)
            if zoneDoSet is not None:
                if doId in zoneDoSet:
                    zoneDoSet.remove(doId)
                    self._allDoIds.remove(doId)
                    if len(zoneDoSet) == 0:
                        del parentZoneDict[zoneId]
                        if len(parentZoneDict) == 0:
                            del self._table[parentId]
                else:
                    self.notify.error(
                        "deleteObjectLocation: objId: %s not found" % doId)
            else:
                self.notify.error(
                    "deleteObjectLocation: zoneId: %s not found" % zoneId)
        else:
            self.notify.error(
                "deleteObjectLocation: parentId: %s not found" % parentId)
