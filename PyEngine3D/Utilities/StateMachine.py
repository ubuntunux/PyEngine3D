#---------------------#
# CLASS : StateItem
#---------------------#
class StateItem:
  def __init__(self, stateMgr, name):
    self.stateMgr = stateMgr
    self.name = name

  def onEnter(self):
    """
    override method
    """
    pass

  def onUpdate(self):
    """
    override method
    """
    pass

  def onExit(self):
    """
    override method
    """
    pass

  def getName(self):
      return self.name

  def setState(self, state):
    self.stateMgr.setState(state)


#---------------------#
# CLASS : StateMachine
#---------------------#
class StateMachine(object):
  def __init__(self):
    self.stateCount = 0
    self.stateList = {}
    self.curState = None
    self.oldState = None

  def createState(self, stateName):
    stateItem = StateItem(self, stateName)
    # stateItem is selfKey and value
    self.stateList[stateItem] = stateItem
    self.stateCount = len(self.stateList)
    return stateItem

  def getCount(self):
    return self.stateCount

  def isState(self, state):
    return state == self.curState

  def isStateName(self, stateName):
    return stateName == self.curState.name

  def getState(self):
    return self.curState

  def getStateName(self):
    return self.curState.name

  def setState(self, state, reset=False):
      if state != self.curState:
        self.oldState = self.curState
        self.curState = state
        if self.oldState:
          self.stateList[self.oldState].onExit()
        self.stateList[state].onEnter()
      elif reset:
        self.stateList[state].onEnter()

  def updateState(self, *args):
    if self.curState:
      self.stateList[self.curState].onUpdate()

if __name__ == '__main__':
    import unittest
    class testStateMachine(unittest.TestCase):
        def test(self):
            s = StateMachine()
            state_A = s.createState(stateName="state_A")
            state_B = s.createState(stateName="state_B")

            s.setState(state_A)
            self.assertEqual(state_A, s.getState())
            self.assertEqual("state_A", s.getStateName())

            s.setState(state_B)
            self.assertTrue(s.isState(state_B))
            self.assertTrue(s.isStateName("state_B"))

            self.assertEqual(s.getCount(), 2)
    unittest.main()