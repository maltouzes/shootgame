# -*- coding: utf-8 -*-

from kivy.properties import OptionProperty
from kivy.uix.screenmanager import TransitionBase


class CustomTransition(TransitionBase):
    '''CustomTransition, can be used to show a new screen from any direction:
    left, right, up or down.
    '''

    direction = OptionProperty('left', options=('left', 'right', 'up', 'down'))
    '''Direction of the transition.
    :attr:`direction` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'left'. Can be one of 'left', 'right', 'up' or 'down'.
    '''
    origpos = None

    def on_progress(self, progression):
        a = self.screen_in
        b = self.screen_out
        manager = self.manager
        x, y = manager.pos
        width, height = manager.size
        direction = self.direction
        progression = self.al(progression)

        if direction == 'left':
            a.y = b.y = y
            a.x = x + width * (1 - progression)
            b.x = x - width * progression
        elif direction == 'right':
            a.y = b.y = y
            b.x = x + width * progression
            a.x = x - width * (1 - progression)
        elif direction == 'down':
            a.x = b.x = x
            a.y = y + height * (1 - progression)
            b.y = y - height * progression
        elif direction == 'up':
            a.x = b.x = manager.x
            b.y = y + height * progression
            a.y = y - height * (1 - progression)

        for c in b.children:
            try:
                if 'yellow' in c.source:
                    if not self.origpos:
                        self.origpos = c.pos_hint
                    c.pos_hint = {}
                    c.y += 10
            except (AttributeError, TypeError):
                pass

    def on_complete(self):
        for c in self.screen_out.children:
            try:
                if 'yellow' in c.source:
                    c.pos_hint = self.origpos
            except (AttributeError, TypeError):
                pass
        self.origpos = None
        self.screen_in.pos = self.manager.pos
        self.screen_out.pos = self.manager.pos
        super(CustomTransition, self).on_complete()
