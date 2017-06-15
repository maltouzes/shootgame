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
    '''custom button use in kv lang for the gui'''
    pass


class TargetButton(ButtonBehavior, Image):
    '''cibles for shoot'''
    touched = False
    killed = False

    def on_press(self):
        '''check which duck is touched or not'''
        shootgame.shoot.play()
        if self.touched is True:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_1-ok.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_6-ok.png"
            elif 'Bad' in self.source:
                self.source = ShootGame.assetpath + "DuckBad_5.png"
            if self.killed is not True:
                shootgame.points += 5
            self.killed = True

        else:
            if 'Yellow' in self.source:
                self.source = ShootGame.assetpath + "DuckYellow_2.png"
            elif 'Brown' in self.source:
                self.source = ShootGame.assetpath + "DuckBrown_4.png"
            elif 'Bad' in self.source:
                self.source = ShootGame.assetpath + "DuckBad_4.png"
            shootgame.points += 3

            self.touched = True
        print(shootgame.points)


class ShootScreen(Screen):
    '''ingame screen'''
    pass


class PauseScreen(Screen):
    '''when the game is in pause, see kv lang for gui'''
    pass


class WinScreen(Screen):
    '''when the user finish the time mode, see kv lang for gui'''
    pass


class LevelScreen(Screen):
    '''gui for choose the level:
        easy, medium or hard

        see kv lang'''
    pass


class StartScreen(Screen):
    '''first gui displayed, see kv lang'''
    def leave(self):
        '''when the user leave the game'''
        App.get_running_app().stop()


class ShootGame(App):
    '''all the logic of the game'''
    assetpath = os.getcwd() + ("/assets/PNG/")
    cibles = {'easy': 'DuckBrown_2.png', 'medium': 'DuckYellow_3.png',
              'bad': 'DuckBad_3.png', 'gold': 'none'}

    background = assetpath + ("Background_Orange.png")
    background1 = assetpath + ("Background_Blue.png")
    background2 = assetpath + ("Water.png")
    layout = FloatLayout(size_hint=(1, 1))
    points = NumericProperty(0)
    bestscore = 0
    dificulty = 'none'  # easy, medium and hard
    mode = 'none'  # arcade, time
    shoot = SoundLoader.load(os.getcwd() + '/sound/shoot/shotgun.wav')
    timer = NumericProperty(0)

    def addButton(self, ducktype,  num):
        '''add the cibles take a ducktype parameter (easy, medium, bad, gold)
        and add the coresponding duck multiplying the num parameter (number)'''
        for x in range(num):
            btn = TargetButton(
                    size_hint=(None, None),
                    source=self.assetpath + self.cibles[ducktype])

            self.shootscreen.add_widget(btn)

    def resetButtons(self):
        '''reset all the buttons to their original position and their original
        source image'''
        for btn in self.shootscreen.children:
            try:
                if 'Duck' in btn.source:
                    self.resetbutton(btn)
            except AttributeError:
                pass

    def moveButtons(self, dt):
        '''move every buttons (cibles) in the screen according to the dificulty
        and the image source (yellow or brown)'''
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
        '''reset the position,the source image and the status of the button'''
        btn.touched = False
        btn.killed = False
        btn.pos = (
                random.uniform(
                 Window.size[0], Window.size[0] + 600),
                random.uniform(
                 59, Window.size[1]-89))
        if 'Yellow' in btn.source:
            btn.source = self.assetpath + self.cibles['medium']
        elif 'Brown' in btn.source:
            btn.source = self.assetpath + self.cibles['easy']

    def difficultymult(self):
        '''return the dificulty multiplier for move the buttons'''
        if self.dificulty == 'easy':
            return random.uniform(.8, 1)
        elif self.dificulty == 'medium':
            return random.uniform(1, 2)
        elif self.dificulty == 'hard':
            return random.uniform(2, 3)
        else:
            return random.uniform(.1, 2)  # easy

    def build(self):
        '''create a ScreenManager and add all the Screens'''
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
        '''Loop the keyboard input'''
        from kivy.base import EventLoop
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def starteasy(self):
        '''set dificulty'''
        self.dificulty = 'easy'
        self.start()

    def startmedium(self):
        '''set dificulty'''
        self.dificulty = 'medium'
        self.start()

    def starthard(self):
        '''set dificulty'''
        self.dificulty = 'hard'
        self.start()

    def arcademode(self):
        '''remove the timer from the screen'''
        self.shootscreen.ids.timerlabel.text = ''
        self.mode = 'arcade'

    def timemode(self):
        '''initialize the timer'''
        self.shootscreen.ids.timerlabel.text = 'Time ' + str(self.timer)
        self.timer = 16
        self.shootscreen.ids.timerlabel.color = (1, 1, 1, 1)
        self.mode = 'time'

    def endtimemode(self, dt):
        '''check if the timer is ended'''
        if self.screen_m.current != 'game' or self.mode != 'time':
            pass
        else:
            if self.timer < 5:
                self.shootscreen.ids.timerlabel.color = (1, 0, 0, 1)
            if self.timer > 0:
                self.timer -= 1
            else:
                self.screen_m.current = 'win'

    def start(self):
        '''add the button to the screen and reset their position. reset the
        points'''
        self.addButton('easy', 5)
        self.addButton('medium', 5)
        self.addButton('bad', 2)
        self.points = 0
        self.resetButtons()
        self.screen_m.transition = SlideTransition()

    def hook_keyboard(self, window, key, *largs):
        '''hook the back key'''
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
        '''shutdown the game'''
        App.get_running_app().stop()

    def on_pause(self):
        '''Enable pause on Android'''
        return True

    def on_resume(self):
        '''Resume after on_pause on Android'''
        pass

    def savescore(self):
        '''save the score to a file'''
        with open('scores') as f:
            f.write(self.bestscore)

    def loadscore(self):
        '''load a score from a file'''
        if os.path.isfile('score'):
            print('y')
            with open('scores') as f:
                f.read()


if __name__ == '__main__':
    shootgame = ShootGame()
    shootgame.run()
