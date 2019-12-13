class StateItem:
    def __init__(self, state_manager, *args, **kargs):
        self.state_manager = state_manager
        self.key = None
        for key in kargs:
            setattr(self, key, kargs[key])

    def on_enter(self, *args, **kargs):
        pass

    def on_update(self, *args, **kargs):
        pass

    def on_exit(self, *args, **kargs):
        pass

    def get_key(self):
        return self.key


class StateMachine:
    def __init__(self):
        self.state_map = {}
        self.current_state = None
        self.previous_state = None

    def add_state(self, state_item_class, state_item_key, *args, **kargs):
        """
        :param state_item_class: a Overrided Class of the StateItem.
        :param state_item_key: key
        """
        state_item = state_item_class(*args, state_manager=self, **kargs)
        state_item.key = state_item_key
        self.state_map[state_item_key] = state_item
        return state_item

    def get_state_keys(self):
        return self.state_map.keys()

    def get_state_count(self):
        return len(self.state_map)

    def is_state(self, state):
        return state == self.current_state

    def is_state_key(self, state_key):
        return state_key == self.current_state.key

    def get_state(self):
        return self.current_state

    def get_state_key(self):
        return self.current_state.key

    def set_state(self, state_key, *args, force=False, **kargs):
        if self.current_state is None or state_key != self.current_state.key:
            if state_key in self.state_map:
                self.previous_state = self.current_state
                self.current_state = self.state_map[state_key]
                if self.previous_state is not None:
                    self.previous_state.on_exit(*args, **kargs)
                self.current_state.on_enter(*args, **kargs)
        elif force and self.current_state is not None:
            self.current_state.on_enter(*args, **kargs)

    def update_state(self, *args, **kargs):
        if self.current_state:
            self.current_state.on_update(*args, **kargs)


if __name__ == '__main__':
    import unittest
    from enum import Enum


    class STATES(Enum):
        A = 0
        B = 1

    class StateItemCustom(StateItem):
        def on_enter(self):
            print(str(self.key) + "::on_enter")

        def on_update(self):
            print(str(self.key) + "::on_update")

        def on_exit(self):
            print(str(self.key) + "::on_exit")

    class TestStateMachine(unittest.TestCase):
        def test(self):
            s = StateMachine()
            state_A = s.add_state(StateItemCustom, STATES.A)
            state_B = s.add_state(StateItemCustom, STATES.B)

            s.set_state(STATES.A)
            self.assertEqual(state_A, s.get_state())
            self.assertEqual(STATES.A, s.get_state_key())

            s.update_state()

            s.set_state(STATES.B)
            self.assertTrue(s.is_state(state_B))
            self.assertTrue(s.is_state_key(STATES.B))

            s.update_state()

            self.assertEqual(s.get_state_count(), 2)

    unittest.main()
