from libpandaexpressModules import *
from DirectNotifyGlobal import *
from PythonUtil import *
from MessengerGlobal import *
import time
import fnmatch
import string
import signal

# MRM: Need to make internal task variables like time, name, index
# more unique (less likely to have name clashes)

exit = -1
done = 0
cont = 1

def print_exc_plus():
    """
    Print the usual traceback information, followed by a listing of all the
    local variables in each frame.
    """
    import sys
    import traceback

    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    traceback.print_exc()
    print "Locals by frame, innermost last"
    for frame in stack:
        print
        print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                             frame.f_code.co_filename,
                                             frame.f_lineno)
        for key, value in frame.f_locals.items():
            print "\t%20s = " % key,
            #We have to be careful not to cause a new error in our error
            #printer! Calling str() on an unknown object could cause an
            #error we don't want.
            try:                   
                print value
            except:
                print "<ERROR WHILE PRINTING VALUE>"


# Store the global clock
globalClock = ClockObject.getGlobalClock()


class Task:
    count = 0
    def __init__(self, callback, priority = 0):
        # Unique ID for each task
        self.id = Task.count
        Task.count += 1
        self.__call__ = callback
        self._priority = priority
        self.uponDeath = None
        self.dt = 0.0
        self.maxDt = 0.0
        self.avgDt = 0.0
        self.runningTotal = 0.0
        self.pstats = None

    def getPriority(self):
        return self._priority

    def setPriority(self, pri):
        self._priority = pri

    def setStartTimeFrame(self, startTime, startFrame):
        self.starttime = startTime
        self.startframe = startFrame

    def setCurrentTimeFrame(self, currentTime, currentFrame):
        # Calculate and store this task's time (relative to when it started)
        self.time = currentTime - self.starttime
        self.frame = currentFrame - self.startframe

    def setupPStats(self, name):
        if __debug__:
            import PStatCollector
            self.pstats = PStatCollector.PStatCollector("App:Show code:" + name)

def doLater(delayTime, task, taskName):
    task.name = taskName
    # make a sequence out of the delay and the task
    seq = sequence(pause(delayTime), task)
    return seq

def pause(delayTime):
    def func(self):
        if (self.time < self.delayTime):
            return cont
        else:
            # Time is up, return done
            # TaskManager.notify.debug('pause done: ' + self.name)
            return done
    task = Task(func)
    task.name = 'pause'
    task.delayTime = delayTime
    return task

def sequence(*taskList):
    return make_sequence(taskList)


def make_sequence(taskList):
    def func(self):
        frameFinished = 0
        taskDoneStatus = -1
        while (not frameFinished):
            task = self.taskList[self.index]
            # If this is a new task, set its start time and frame
            if (self.index > self.prevIndex):
                task.setStartTimeFrame(self.time, self.frame)
            self.prevIndex = self.index
            # Calculate this task's time since it started
            task.setCurrentTimeFrame(self.time, self.frame)
            # Execute the current task
            ret = task(task)
            # Check the return value from the task
            # If this current task wants to continue,
            # come back to it next frame
            if (ret == cont):
                taskDoneStatus = cont
                frameFinished = 1
            # If this task is done, increment the index so that next frame
            # we will start executing the next task on the list
            elif (ret == done):
                self.index = self.index + 1
                taskDoneStatus = cont
                frameFinished = 0
            # If this task wants to exit, the sequence exits
            elif (ret == exit):
                taskDoneStatus = exit
                frameFinished = 1

            # If we got to the end of the list, this sequence is done
            if (self.index >= len(self.taskList)):
                # TaskManager.notify.debug('sequence done: ' + self.name)
                frameFinished = 1
                taskDoneStatus = done
                
        return taskDoneStatus 

    task = Task(func)
    task.name = 'sequence'
    task.taskList = taskList
    task.prevIndex = -1
    task.index = 0
    return task

def resetSequence(task):
    # Should this automatically be done as part of spawnTaskNamed?
    # Or should one have to create a new task instance every time
    # one wishes to spawn a task (currently sequences and can
    # only be fired off once
    task.index = 0
    task.prevIndex = -1

def loop(*taskList):
    return make_loop(taskList)

def make_loop(taskList):
    def func(self):
        frameFinished = 0
        taskDoneStatus = -1
        while (not frameFinished):
            task = self.taskList[self.index]
            # If this is a new task, set its start time and frame
            if (self.index > self.prevIndex):
                task.setStartTimeFrame(self.time, self.frame)
            self.prevIndex = self.index
            # Calculate this task's time since it started
            task.setCurrentTimeFrame(self.time, self.frame)
            # Execute the current task
            ret = task(task)
            # Check the return value from the task
            # If this current task wants to continue,
            # come back to it next frame
            if (ret == cont):
                taskDoneStatus = cont
                frameFinished = 1
            # If this task is done, increment the index so that next frame
            # we will start executing the next task on the list
            # TODO: we should go to the next frame now
            elif (ret == done):
                self.index = self.index + 1
                taskDoneStatus = cont
                frameFinished = 0
            # If this task wants to exit, the sequence exits
            elif (ret == exit):
                taskDoneStatus = exit
                frameFinished = 1

            # If we got to the end of the list, wrap back around
            if (self.index >= len(self.taskList)):
                self.prevIndex = -1
                self.index = 0
                frameFinished = 1

        return taskDoneStatus

    task = Task(func)
    task.name = 'loop'
    task.taskList = taskList
    task.prevIndex = -1
    task.index = 0
    return task


class TaskManager:

    notify = None

    def __init__(self):
        self.running = 0
        self.stepping = 0
        self.taskList = []
        self.currentTime, self.currentFrame = self.__getTimeFrame()
        if (TaskManager.notify == None):
            TaskManager.notify = directNotify.newCategory("TaskManager")
        self.taskTimerVerbose = 0
        self.extendedExceptions = 0
        self.fKeyboardInterrupt = 0
        self.interruptCount = 0
        self.pStatsTasks = 0
        self.resumeFunc = None
        self.fVerbose = 0

    def stepping(self, value):
        self.stepping = value

    def setVerbose(self, value):
        self.fVerbose = value
        messenger.send('TaskManager-setVerbose', sentArgs = [value])

    def keyboardInterruptHandler(self, signalNumber, stackFrame):
        self.fKeyboardInterrupt = 1
        self.interruptCount += 1
        if self.interruptCount == 2:
            # The user must really want to interrupt this process
            # Next time around use the default interrupt handler
            signal.signal(signal.SIGINT, signal.default_int_handler)

    def add(self, funcOrTask, name, priority = 0):
        """
        Add a new task to the taskMgr.
        You can add a Task object or a method that takes one argument.
        """
        if isinstance(funcOrTask, Task):
            funcOrTask.setPriority(priority)
            return self.__spawnTaskNamed(funcOrTask, name)
        elif callable(funcOrTask):
            return self.__spawnMethodNamed(funcOrTask, name, priority)
        else:
            self.notify.error('Tried to add a task that was not a Task or a func')

    def remove(self, taskOrName):
        if type(taskOrName) == type(''):
            return self.__removeTasksNamed(taskOrName)
        elif isinstance(taskOrName, Task):
            return self.__removeTask(taskOrName)
        else:
            self.notify.error('remove takes a string or a Task')

    def __spawnMethodNamed(self, func, name, priority=0):
        task = Task(func, priority)
        return self.__spawnTaskNamed(task, name)

    def __spawnTaskNamed(self, task, name):
        if TaskManager.notify.getDebug():
            TaskManager.notify.debug('spawning task named: ' + name)
        task.name = name
        task.setStartTimeFrame(self.currentTime, self.currentFrame)
        # search back from the end of the list until we find a
        # task with a lower priority, or we hit the start of the list
        index = len(self.taskList) - 1
        while (1):
            if (index < 0):
                break
            if (self.taskList[index].getPriority() <= task.getPriority()):
                break
            index = index - 1
        index = index + 1
        self.taskList.insert(index, task)

        if __debug__:
            if self.pStatsTasks and name != "igloop":
                # Get the PStats name for the task.  By convention,
                # this is everything until the first hyphen; the part
                # of the task name following the hyphen is generally
                # used to differentiate particular tasks that do the
                # same thing to different objects.
                hyphen = name.find('-')
                if hyphen >= 0:
                    name = name[0:hyphen]
                task.setupPStats(name)

        if self.fVerbose:
            # Alert the world, a new task is born!
            messenger.send('TaskManager-spawnTask',
                           sentArgs = [task, name, index])
                
        return task

    def doMethodLater(self, delayTime, func, taskName):
        task = Task(func)
        seq = doLater(delayTime, task, taskName)
        seq.laterTask = task
        return self.__spawnTaskNamed(seq, taskName)

    def __removeTask(self, task):
        if TaskManager.notify.getDebug():
            TaskManager.notify.debug('removing task: ' + `task`)
        if task in self.taskList:
            self.taskList.remove(task)
            if task.uponDeath:
                task.uponDeath(task)
            if self.fVerbose:
                # We regret to announce...
                messenger.send('TaskManager-removeTask',
                               sentArgs = [task, task.name])

    def __removeTasksNamed(self, taskName):
        if TaskManager.notify.getDebug():
            TaskManager.notify.debug('removing tasks named: ' + taskName)

        # Find the tasks that match by name and make a list of them
        removedTasks = []
        for task in self.taskList:
           if (task.name == taskName):
               removedTasks.append(task)

        # Now iterate through the tasks we need to remove and remove them
        for task in removedTasks:
            self.__removeTask(task)

        # Return the number of tasks removed
        return len(removedTasks)

    def hasTaskNamed(self, taskName):
        for task in self.taskList:
            if (task.name == taskName):
                return 1
        return 0

    def removeTasksMatching(self, taskPattern):
        """removeTasksMatching(self, string taskPattern)

        Removes tasks whose names match the pattern, which can include
        standard shell globbing characters like *, ?, and [].

        """
        if TaskManager.notify.getDebug():
            TaskManager.notify.debug('removing tasks matching: ' + taskPattern)
        removedTasks = []

        # Find the tasks that match by name and make a list of them
        for task in self.taskList:
            if (fnmatch.fnmatchcase(task.name, taskPattern)):
                removedTasks.append(task)

        # Now iterate through the tasks we need to remove and remove them
        for task in removedTasks:
           self.__removeTask(task)

        # Return the number of tasks removed
        return len(removedTasks)

    def step(self):
        if TaskManager.notify.getDebug():
            TaskManager.notify.debug('step')
        self.currentTime, self.currentFrame = self.__getTimeFrame()
        # Replace keyboard interrupt handler during task list processing
        # so we catch the keyboard interrupt but don't handle it until
        # after task list processing is complete.
        self.fKeyboardInterrupt = 0
        self.interruptCount = 0
        signal.signal(signal.SIGINT, self.keyboardInterruptHandler)
        for task in self.taskList:
            task.setCurrentTimeFrame(self.currentTime, self.currentFrame)

            if not self.taskTimerVerbose:
                # don't record timing info
                ret = task(task)
            else:
                # Run the task and check the return value
                if task.pstats:
                    task.pstats.start()
                startTime = time.clock()
                ret = task(task)
                endTime = time.clock()
                if task.pstats:
                    task.pstats.stop()

                # Record the dt
                dt = endTime - startTime
                task.dt = dt

                # See if this is the new max
                if dt > task.maxDt:
                    task.maxDt = dt

                # Record the running total of all dts so we can compute an average
                task.runningTotal = task.runningTotal + dt
                if (task.frame > 0):
                    task.avgDt = (task.runningTotal / task.frame)
                else:
                    task.avgDt = 0

            # See if the task is done
            if (ret == cont):
                continue
            elif (ret == done):
                self.__removeTask(task)
            elif (ret == exit):
                self.__removeTask(task)
            else:
                raise StandardError, "Task named %s did not return cont, exit, or done" % task.name
        # Restore default interrupt handler
        signal.signal(signal.SIGINT, signal.default_int_handler)
        if self.fKeyboardInterrupt:
            raise KeyboardInterrupt
        return len(self.taskList)

    def run(self):
        # Set the clock to have last frame's time in case we were
        # Paused at the prompt for a long time
        t = globalClock.getFrameTime()
        timeDelta = t - globalClock.getRealTime()
        globalClock.setRealTime(t)

        messenger.send("resetClock", [timeDelta])

        if self.resumeFunc != None:
            self.resumeFunc()
        
        if self.stepping:
            self.step()
        else:
            self.running = 1
            while self.running:
                try:
                    self.step()
                except KeyboardInterrupt:
                    self.stop()
                except:
                    if self.extendedExceptions:
                        self.stop()
                        print_exc_plus()
                    else:
                        raise

    def stop(self):
        # Set a flag so we will stop before beginning next frame
        self.running = 0

    def replaceMethod(self, oldMethod, newFunction):
        import new
        for task in self.taskList:
            method = task.__call__
            if (type(method) == types.MethodType):
                function = method.im_func
            else:
                function = method
            #print ('function: ' + `function` + '\n' +
            #       'method: ' + `method` + '\n' +
            #       'oldMethod: ' + `oldMethod` + '\n' +
            #       'newFunction: ' + `newFunction` + '\n')
            if (function == oldMethod):
                newMethod = new.instancemethod(newFunction,
                                               method.im_self,
                                               method.im_class)
                task.__call__ = newMethod
                # Found it return true
                return 1
        return 0

    def __repr__(self):
        import fpformat
        taskNameWidth = 32
        dtWidth = 7
        priorityWidth = 10
        totalDt = 0
        totalAvgDt = 0
        str = ('taskList'.ljust(taskNameWidth)
               + 'dt(ms)'.rjust(dtWidth)
               + 'avg'.rjust(dtWidth)
               + 'max'.rjust(dtWidth)
               + 'priority'.rjust(priorityWidth)
               + '\n')
        str = str + '---------------------------------------------------------------\n'
        for task in self.taskList:
            totalDt = totalDt + task.dt
            totalAvgDt = totalAvgDt + task.avgDt
            if (self.taskTimerVerbose):
                str = str + (task.name.ljust(taskNameWidth)
                             + fpformat.fix(task.dt*1000, 2).rjust(dtWidth)
                             + fpformat.fix(task.avgDt*1000, 2).rjust(dtWidth)
                             + fpformat.fix(task.maxDt*1000, 2).rjust(dtWidth)
                             + `task.getPriority()`.rjust(priorityWidth)
                             + '\n')
            else:
                str = str + (task.name.ljust(taskNameWidth)
                             + '----'.rjust(dtWidth)
                             + '----'.rjust(dtWidth)
                             + '----'.rjust(dtWidth)
                             + `task.getPriority()`.rjust(priorityWidth)
                             + '\n')
        str = str + '---------------------------------------------------------------\n'
        if (self.taskTimerVerbose):
            str = str + ('total'.ljust(taskNameWidth)
                         + fpformat.fix(totalDt*1000, 2).rjust(dtWidth)
                         + fpformat.fix(totalAvgDt*1000, 2).rjust(dtWidth)
                         + '\n')
        else:
            str = str + ('total'.ljust(taskNameWidth)
                         + '----'.rjust(dtWidth)
                         + '----'.rjust(dtWidth)
                         + '\n')
        return str

    def resetStats(self):
        for task in self.taskList:
            task.dt = 0
            task.avgDt = 0
            task.maxDt = 0
            task.runningTotal = 0
            task.setStartTimeFrame(self.currentTime, self.currentFrame)

    def popupControls(self):
        import TaskManagerPanel
        return TaskManagerPanel.TaskManagerPanel(self)

    def __getTimeFrame(self):
        # WARNING: If you are testing tasks without an igloop,
        # you must manually tick the clock        
        # Ask for the time last frame
        return globalClock.getFrameTime(), globalClock.getFrameCount()

