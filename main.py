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
from kivy.properties import NumericProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.core.window import Window
# from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
# from kivy.graphics import Rectangle
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import SlideTransition

Window.size = (800, 480)


class ImgButton(ButtonBehavior, Image):
    pass


class TargetButton(ButtonBehavior, Image):
    touched = False
    killed = False

    def on_press(self):
        shootgame.shoot.play()
        if self.touched is True:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_1-ok.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_6-ok.png"
            if self.killed is not True:
                shootgame.points += 3
            self.killed = True

        else:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_2.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_4.png"
            shootgame.points += 10

            self.touched = True
        print(shootgame.points)


class ShootScreen(Screen):
    pass


class PauseScreen(Screen):
    pass


class WinScreen(Screen):
    pass


class LevelScreen(Screen):
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
    points = NumericProperty(0)
    dificulty = 'none'  # easy, medium and hard
    mode = 'none'  # arcade, time
    shoot = SoundLoader.load(os.getcwd() + '/sound/shoot/shotgun.wav')
    timer = NumericProperty(0)
    # pause = True

    def addButtons(self, num):
        for x in range(num):
            self.addButton()

    def addButton(self):
        for x in range(2):

            btn = TargetButton(
                               size_hint=(None, None),
                               source=self.assetpath + self.cibles[x])
            self.shootscreen.add_widget(btn)

    def resetButtons(self):
        for btn in self.shootscreen.children:
            try:
                if 'Duck' in btn.source:
                    self.resetbutton(btn)
            except AttributeError:
                pass

    def moveButtons(self, dt):
        if self.screen_m.current != 'game':
            pass
        else:
            for btn in self.shootscreen.children:
                try:
                    if 'Duck' in btn.source:
                        if 'Yellow' in btn.source:
                            btn.pos[0] -= 1 * self.difficultymult()
                        elif 'Brown' in btn.source:
                            btn.pos[0] -= 1.3 * self.difficultymult()
                        else:
                            btn.pos[0] -= 1 * self.difficultymult()  # easy
                    if btn.pos[0] < -80:
                        self.resetbutton(btn)
                except AttributeError:
                    pass

    def resetbutton(self, btn):
        btn.touched = False
        btn.killed = False
        btn.pos = (
                random.uniform(
                 Window.size[0], Window.size[0] + 600),
                random.uniform(
                 59, Window.size[1]-89))
        if 'Yellow' in btn.source:
            btn.source = self.assetpath + self.cibles[1]
        elif 'Brown' in btn.source:
            btn.source = self.assetpath + self.cibles[0]

    def difficultymult(self):
        if self.dificulty == 'easy':
            return random.uniform(.8, 1)
        elif self.dificulty == 'medium':
            return random.uniform(1, 2)
        elif self.dificulty == 'hard':
            return random.uniform(2, 3)
        else:
            return random.uniform(.1, 2)  # easy

    def build(self):
        self.screen_m = ScreenManager()
        self.screen_m.transition.direction = 'up'

        self.shootscreen = ShootScreen(name='game')
        self.screen_m.add_widget(StartScreen(name='menu'))
        self.screen_m.add_widget(LevelScreen(name='level'))
        self.screen_m.add_widget(PauseScreen(name='pause'))
        self.screen_m.add_widget(WinScreen(name='win'))
        self.screen_m.add_widget(self.shootscreen)

        self.screen_m.current = 'menu'
        Clock.schedule_interval(self.endtimemode, 1)
        Clock.schedule_interval(self.moveButtons, 0.01)

        return self.screen_m

    def on_start(self):
        from kivy.base import EventLoop
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def starteasy(self):
        self.dificulty = 'easy'
        self.start()

    def startmedium(self):
        self.dificulty = 'medium'
        self.start()

    def starthard(self):
        self.dificulty = 'hard'
        self.start()

    def arcademode(self):
        self.shootscreen.ids.timerlabel.text = ''
        self.mode = 'arcade'

    def timemode(self):
        self.shootscreen.ids.timerlabel.text = 'Time ' + str(self.timer)
        self.timer = 20
        self.mode = 'time'

    def endtimemode(self, dt):
        if self.screen_m.current != 'game' or self.mode != 'time':
            pass
        else:
            print(self.timer)
            if self.timer > 0:
                self.timer -= 1
            else:
                self.screen_m.current = 'win'

    def start(self):
        self.addButtons(5)
        self.points = 0
        self.resetButtons()
        self.screen_m.transition = SlideTransition()

    def hook_keyboard(self, window, key, *largs):
        if key == 27 or key == 97 or key == 1001:
            if self.screen_m.current == 'game':
                self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'pause'
            elif self.screen_m.current == 'menu':
                self.leave()
            else:
                self.screen_m.current = 'menu'
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
