# -*- coding: utf-8 -*-
__version__ = '0.0.1'
###############################################################################
# copyright 2016-2017 Tony Maillefaud <maltouzes@gmail.com>                   #
#                                                                             #
# This file is part of ShootGame                                              #
#                                                                             #
# ShootGame is free software: you can redistribute it and/or modify           #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# ShootGame is distributed in the hope that it will be useful,                #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with ShootGame. If not, see <http://www.gnu.org/licenses/>.           #
###############################################################################

"""
ShootGame is a game
"""

import os
import random
# from datetime import datetime
# from kivy.utils import platform
# from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.core.window import Window
# from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
# from kivy.core.audio import SoundLoader
# from kivy.graphics import Rectangle

Window.size = (800, 480)


class ImgButton(ButtonBehavior, Image):
    pass


class TargetButton(ButtonBehavior, Image):
    touched = False
    killed = False

    def on_press(self):
        print(ShootGame.points)
        if self.touched is True:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_1-ok.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_6-ok.png"
            if self.killed is not True:
                ShootGame.points += 3
            self.killed = True

        else:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_2.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_4.png"
            ShootGame.points += 10

            self.touched = True


class ShootScreen(Screen):
    pass


class StartScreen(Screen):
    def leave(self):
        App.get_running_app().stop()


class ShootGame(App):
    assetpath = os.getcwd() + ("/assets/PNG/")
    cibles = ['DuckBrown_2.png', 'DuckYellow_3.png']

    background = assetpath + ("Background_Orange.png")
    background1 = assetpath + ("Background_Blue.png")
    background2 = assetpath + ("Water.png")
    layout = FloatLayout(size_hint=(1, 1))
    points = 0
    # pause = True

    # startscreen = StartScreen(name='menu')
    shootscreen = ShootScreen(name='game')

    def addButtons(self):
        for x in range(2):

            btn = TargetButton(
                               size_hint=(None, None),
                               source=self.assetpath + self.cibles[x],
                               pos=(
                                   random.uniform(
                                    Window.size[0], Window.size[0] + 300),
                                   random.uniform(
                                    59, Window.size[1]-89)))
            self.layout.add_widget(btn)
            print(btn.pos)

    def moveButtons(self, dt):
        if self.screen_m.current != 'game':
            pass

        else:
            for btn in self.layout.children:
                # print(btn.pos)
                btn.pos[0] -= random.uniform(.1, 4)

    def build(self):
        self.screen_m = ScreenManager()

        self.shootscreen.add_widget(self.layout)

        self.screen_m.add_widget(StartScreen(name='menu'))
        self.screen_m.add_widget(self.shootscreen)

        self.screen_m.current = 'menu'

        Clock.schedule_interval(self.moveButtons, 0.01)
        self.addButtons()
        return self.screen_m

    def on_start(self):
        from kivy.base import EventLoop
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def hook_keyboard(self, window, key, *largs):
        if key == 27 or key == 97 or key == 1001:
            if self.screen_m.current == 'game':
                self.screen_m.current = 'menu'
            elif self.screen_m.current == 'menu':
                self.leave()
            else:
                self.leave()
            return True

    def leave(self):
        App.get_running_app().stop()

    def on_pause(self):
        '''Enable pause on Android'''
        return True

    def on_resume(self):
        '''Resume after on_pause on Android'''
        pass


if __name__ == '__main__':
    shootgame = ShootGame()
    shootgame.run()
