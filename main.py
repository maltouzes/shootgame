# -*- coding: utf-8 -*-
__version__ = '0.0.22'
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
# from customtransition import CustomTransition
# from kivy.uix.screenmanager import AnimationTransition
# from datetime import datetime
# from kivy.utils import platform
from kivy.uix.label import Label
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.behaviors import ButtonBehavior
# from kivy.uix.image import AsyncImage
from kivy.uix.image import Image
from kivy.core.window import Window
# from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
# from kivy.graphics import Rectangle
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import SlideTransition
from kivy.animation import Animation
from kivy.lang import Builder
try:
    from plyer import vibrator
except ImportError:
    pass

Window.size = (800, 460)


class ImgButton(ButtonBehavior, Image):
    '''custom button use in kv lang for the gui'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size_hint = 0.3, 0.3

    def on_press(self):
        shootgame.soundbtn.play()


class Duck():
    '''handle all variables, TargetButton use composition for use Duck'''
    def __init__(self, targettype, ducktype, normalpoints, hurtpoints,
                 rapidity, normalimg, hurtimg, deadimg,
                 timespawn=[4, 8], timehere=[8, 13], nbr_img=2):
        '''initialize all variables'''
        self.targettype = targettype
        self.normalimg = normalimg
        self.hurtimg = hurtimg
        self.deadimg = deadimg
        self.rapidity = rapidity
        self.normalpts = normalpoints
        self.hurtpts = hurtpoints
        self.ducktype = ducktype
        self.velocity_x = None
        self.velocity_y = None
        self.timespawn = timespawn
        self.timeheredefault = timehere
        self.timebeforespawn = 1000
        self.timehere = 0
        self.nbr_img = nbr_img
        self.index = 0

    def update_img(self):
        if self.index < self.nbr_img:
            self.index += 1
        else:
            self.index = 0


class Hen(Duck):
    def __init__(self, eggs, *args, **kwargs):
        self.eggs = eggs
        super().__init__(*args, **kwargs)


class TargetButton(ButtonBehavior, Image):
    '''cibles for shoot, is composed of the Duck class'''
    def __init__(self, duck, *args, **kwargs):
        '''initialize the Duck class parameter as duck (composition),
        then use super() for parent class. see the MRO for details'''
        self.duck = duck
        super().__init__(*args, **kwargs)
    '''the above parameters must be a part of TargetButton and not a part of
    Duck, because all TargetButton share the same Duck instance'''
    touched = False  # keep this here
    killed = False   # heep this here
    falling = False

    def on_press(self):
        '''check which duck is touched or not'''
        # print(self.last_touch)
        # print(self.texture_size)
        # print(self.pos)
        if isinstance(self.duck, Hen):
            self.duck.eggs -= 1
        shootgame.shoot.play()
        ptsmulti = shootgame.dificultypts
        if self.touched is True and self.killed is not True:
            self.source = ShootGame.assetpath + self.duck.deadimg
            ptswin = self.duck.hurtpts * ptsmulti
            self.shoot_type(self.source)
            ptswinmult = ptswin*self.mult_pts_type()
            shootgame.points += ptswinmult
            self.display_pts_win(ptswinmult)
            self.score_to_time()
            self.combo()

            self.killed = True

        elif self.touched is False:
            self.source = ShootGame.assetpath + self.duck.hurtimg
            ptswin = self.duck.normalpts * ptsmulti
            shootgame.points += ptswin
            self.display_pts_win(ptswin)
            self.score_to_time()

            self.touched = True

    def combo(self):
        combo = shootgame.shootscreen.ids.combolabel
        if self.mult_pts_type() == 1:
            combo.text = ''
        else:
            combo.text = 'Combo X' + str(self.mult_pts_type())

    @staticmethod
    def mult_pts_type():
        if shootgame.multshoot_type < 4:
            return shootgame.multshoot_type
        else:
            return 3

    def shoot_type(self, source):
        if self.source == shootgame.lastshoot_type:
            shootgame.multshoot_type += 1
        else:
            shootgame.multshoot_type = 1
            shootgame.lastshoot_type = self.source

    def score_to_time(self):
        '''transform pts to time'''
        pointup = shootgame.points - shootgame.lstscorebeforeaddtime
        pointupdif = pointup/shootgame.dificultypts
        if ((pointupdif >= shootgame.score_to_time)
                and 'time' in shootgame.mode):
            pointbyhundred = (round(pointup/100)*100)
            scoreremain = pointupdif - pointbyhundred
            timeadded = \
                (shootgame.timeadd *
                 int(round(pointupdif/shootgame.score_to_time)))
            shootgame.timer += timeadded
            shootgame.lstscorebeforeaddtime = shootgame.points - scoreremain

    def display_pts_win(self, pts):
        if pts < 0:
            try:
                vibrator.vibrate(0.1)
            except NameError:
                pass
            if 'time' in shootgame.mode:
                shootgame.timer -= 2
                shootgame.pointsdisplay += pts
        for w in shootgame.shootscreen.children:
            if isinstance(w, ScoreLabel):
                x = self.pos[0] / Window.size[0]
                y = self.pos[1] / Window.size[1]
                w.pos_hint = {'center_x':  x, 'center_y': y}
                w.text = str(pts)
                w.timehere = 2
                w.color = (1, 1, 1, 1)

    def dead_anim(self):
        animation = Animation(pos=(
            self.pos[0] - self.size[0]/2, self.pos[1] + self.size[1]/2),
            t='linear',
            duration=.3)

        animation += Animation(pos=(
            self.pos[0] - self.size[0]/1.8, self.pos[1] + self.size[1]/1.8),
            t='linear',
            duration=.1)

        animation += Animation(pos=(
            self.pos[0] - self.size[0], - self.size[1]),
            t='in_quad')

        animation.start(self)


class ScoreLabel(Label):
    timehere = 0


class ShootScreen(Screen):
    '''ingame screen'''

    def on_touch_down(self, touch):
        if super(ShootScreen, self).on_touch_down(touch):
            return True
        if not self.collide_point(touch.x, touch.y):
            return False
        shootgame.shoot.play()
        shootgame.points -= 1
        # if shootgame.points < 0:
        # shootgame.points = 0
        return True

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
    assetpath = os.getcwd() + ("/assets/")
    cibles = {'easy': 'DuckBrown_2.png', 'medium': 'DuckYellow_3.png',
              'bad': 'DuckBad_3.png', 'gold': 'none'}

    background1 = assetpath + ("background/2.png")
    background2 = assetpath + ("background/1.png")
    background3 = assetpath + ("background/4.png")

    layout = FloatLayout(size_hint=(1, 1))
    points = NumericProperty(0)
    bestscore = NumericProperty()
    newrecord = StringProperty('')
    dificulty = 'none'  # easy, medium and hard
    dificultypts = 1
    mode = 'none'  # arcade, time
    shoot = SoundLoader.load(os.getcwd() + '/sound/shotgun.wav')
    soundbtn = SoundLoader.load(os.getcwd() + '/sound/push.ogg')
    timer = NumericProperty(0)
    pointsdisplay = NumericProperty(0)
    scorelabel = ScoreLabel(text='', font_size='25sp')
    lstscorebeforeaddtime = 0
    score_to_time = 100  # pts = timeadd
    timeadd = 1  # sec added
    lastshoot_type = None
    multshoot_type = 1

    def ducks_init(self):
        '''Initialize the cibles, with their
        :param type: easy, medium, hard or bad
        :type: normalpts: int
        :type: hurtpts: int
        :param rapidity: movement of the duck = rapidity * dificulty
        :param normalimg: img of the duck
        :param hurtmalimg: img of the duck is hurted
        :param deadimg: img when the duck is dead
        '''
        self.dkeasy = Duck('Bird', 'easy', 30, 50, 1,  # pts, pts and rapidity
                           # 'birds/BirdGreen-idle.zip',
                           # 'birds/BirdGreen-hit.zip',
                           # 'birds/BirdGreen-hit.zip')
                           # ('atlas://' + self.assetpath +
                           #  'atlas/myatlas/BirdGreen-idle-0'),
                           # ('atlas://' + self.assetpath +
                           #  'atlas/myatlas/BirdGreen-idle-0'))
                           'atlas/myatlas/BirdGreen-idle-0',
                           'atlas/myatlas/BirdGreen-idle-0',
                           'atlas/myatlas/BirdGreen-idle-0')

        self.dkmedium = Duck('Bird', 'medium', 40, 100, 1.3,
                             'birds/BirdYellow-idle.zip',
                             'birds/BirdYellow-hit.zip',
                             'birds/BirdYellow-hit.zip')

        self.dkhard = Duck('Bird', 'hard', 10, 300, 2,  # pts, pts and rapidity
                           'birds/BirdPurple-idle.zip',
                           'birds/BirdPurple-hit.zip',
                           'birds/BirdPurple-hit.zip')

        self.dkbonus = Duck('Bird', 'crasy', 1000, 0, 3,
                            'birds/BirdGrey1-idle.zip',
                            'birds/BirdGrey1-hit.zip',
                            'birds/BirdGrey1-hit.zip',
                            [13, 16],
                            [2, 3])

        self.dkbad = Duck('bomb', 'bad', -300, 0, 2,  # pts, pts and rapidity
                          'PNG/bomb_6.png',
                          'PNG/bomb_dead.zip',
                          'PNG/bomb_dead.zip')

        self.dkcrasy = Duck('Bird', 'crasy', -300, 0, 2,
                            'birds/BirdSkull2-idle.zip',
                            'birds/BirdSkull2-hit.zip',
                            'birds/BirdSkull2-hit.zip',
                            [13, 16])

        self.dkhen = Hen(3, 'Bird', 'hen', 0, 0, 1,
                         'birds/BirdHen-idle.zip',
                         'targets/BirdHen-hit.zip',
                         'targets/BirdHen-hit.zip')

    def add_targets(self, duck, num):
        '''add the cibles take a duck parameter
        and add the coresponding duck multiplying the num parameter (number)'''

        for x in range(num):
            btn = TargetButton(
                    duck,
                    size_hint=(None, None),
                    # source=self.assetpath + duck.hurtimg)
                    # source=(duck.normalimg))
                    # source=('atlas://' + self.assetpath + duck.normalimg))
                    # source=(('atlas://' + atl)))
                    source=('atlas://' + self.assetpath +
                            'atlas/myatlas/BirdGreen-idle-0'))

            if 'bomb' in btn.duck.targettype:
                btn.anim_loop = 1

            self.shootscreen.add_widget(btn)
            # btn.source = self.assetpath + duck.deadimg  # load all img
            # btn.source = self.assetpath + duck.normalimg  # load all img

    def reset_buttons(self):
        '''reset all the buttons to their original position and their original
        source image'''
        for btn in self.shootscreen.children:
            if isinstance(btn, TargetButton):  # and
                    # 'crasy' not in btn.duck.ducktype):
                try:
                    # if 'Bird' in btn.source or 'bomb' in btn.source:
                    if ('Bird' in btn.duck.targettype or
                            'bomb' in btn.duck.targettype):
                        self.reset_btn(btn)
                except AttributeError:
                    pass

    def move_buttons(self, dt):
        '''move every buttons (cibles) in the screen according to the dificulty
        and the rapidity of the cibles'''
        if self.screen_m.current != 'game':
            pass
        else:
            for btn in self.shootscreen.children:
                try:
                    if btn.duck.ducktype == 'crasy':
                        self.move_btn_crasy(btn)
                    # elif 'Bird' in btn.source or 'bomb' in btn.source:
                    elif ('Bird' in btn.duck.targettype or
                            'bomb' in btn.duck.targettype):
                        # if 'bonus' in btn.source
                        if btn.killed and not btn.falling:
                            btn.falling = True
                            if 'bomb' not in btn.duck.targettype:
                                btn.dead_anim()
                        else:
                            btn.pos[0] += (btn.duck.rapidity *
                                           self.diffic_mult())

                            if btn.duck.ducktype == 'medium':
                                self.move_diagonal(btn)

                        if ((btn.pos[0] > Window.size[0] + 490 or
                            btn.pos[1] < 0 - btn.texture.size[1] or
                                btn.pos[1] > (Window.size[1] +
                                              btn.texture.size[1])) and 'crasy'
                                not in btn.duck.ducktype):
                                self.reset_btn(btn)
                except AttributeError:
                    pass

    def move_diagonal(self, btn):
        btn.pos[1] += btn.velocity_y

        if (btn.pos[1] < 0 or
                btn.pos[1] >
                (Window.size[1]
                    - btn.texture.size[1]/1.5)):
            btn.velocity_y *= -1

    def move_btn_crasy(self, btn):
        if btn.duck.timehere < 0:
            btn.pos[0] += btn.velocity_x
            btn.pos[1] += btn.velocity_y

        else:
            if btn.pos[0] < 0:
                btn.pos[0] += (btn.duck.rapidity *
                               self.diffic_mult())

            btn.pos[0] += btn.velocity_x
            btn.pos[1] += btn.velocity_y
            if btn.touched:
                btn.killed = True
            if not btn.touched:
                if btn.pos[0] < 0 or btn.pos[0] > (Window.size[0] -
                                                   btn.texture.size[0]/1.5):
                    btn.velocity_x *= -1
                if btn.pos[1] < 0 or btn.pos[1] > (Window.size[1] -
                                                   btn.texture.size[1]/1.5):
                    btn.velocity_y *= -1

    def move_button_dead(self):
        pass

    def diffic_mult(self):
        '''return the dificulty multiplier for move the buttons'''
        if self.dificulty == 'easy':
            self.dificultypts = 1
            return random.uniform(1, 2)
        elif self.dificulty == 'medium':
            self.dificultypts = 2
            return random.uniform(2, 3)
        elif self.dificulty == 'hard':
            self.dificultypts = 3
            return random.uniform(3, 4)
        else:
            self.dificultypts = 1
            return random.uniform(1, 2)  # easy

    def build(self):
        '''create a ScreenManager and add all the Screens'''
        filename = (os.getcwd() + '/shootgamebuild.kv')

        with open(filename, encoding='utf-8') as f:
            Builder.load_string(f.read())

        self.soundbtn.volume = 0.5
        self.screen_m = ScreenManager()
        self.screen_m.transition.direction = 'left'

        self.shootscreen = ShootScreen(name='game')
        self.screen_m.add_widget(StartScreen(name='menu'))
        self.screen_m.add_widget(LevelScreen(name='level'))
        self.screen_m.add_widget(PauseScreen(name='pause'))
        self.screen_m.add_widget(WinScreen(name='win'))
        self.screen_m.add_widget(self.shootscreen)

        self.ducks_init()

        # self.shootscreen.add_widget(ScoreLabel(text='', font_size='25sp'))
        self.shootscreen.add_widget(self.scorelabel)
        self.add_targets(self.dkeasy, 5)
        # self.add_targets(self.dkmedium, 3)
        # s elf.add_targets(self.dkhard, 1)
        # self.add_targets(self.dkbad, 3)
        # self.add_targets(self.dkbonus, 1)
        # self.add_targets(self.dkcrasy, 1)
        # self.add_targets(self.dkhen, 1)

        self.screen_m.current = 'menu'
        Clock.schedule_interval(self.endtime_mode, 1)
        Clock.schedule_interval(self.move_buttons, 0.01)
        Clock.schedule_interval(self.reset_label, 0.01)
        Clock.schedule_interval(self.gif, 0.2)
        self.load_score()

        return self.screen_m

    def gif(self, dt):
        if self.screen_m.current != 'game':
            pass
        else:
            for btn in self.shootscreen.children:
                if isinstance(btn, TargetButton):
                    btn.source = ('atlas://' +
                                  self.assetpath +
                                  'atlas/myatlas/BirdGreen-idle-{}'.format(
                                      btn.duck.index))

                    btn.duck.update_img()

    def on_start(self):
        '''Loop the keyboard input'''
        from kivy.base import EventLoop
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)

    def start_easy(self):
        '''set dificulty'''
        self.dificulty = 'easy'
        self.start()

    def start_medium(self):
        '''set dificulty'''
        self.dificulty = 'medium'
        self.start()

    def start_hard(self):
        '''set dificulty'''
        self.dificulty = 'hard'
        self.start()

    def arcade_mode(self):
        '''remove the timer from the screen'''
        # self.screen_m.transition = SlideTransition()

        self.shootscreen.ids.timerlabel.text = ''

        # self.screen_m.transition = CustomTransition()
        # self.screen_m.transition.al = AnimationTransition.out_quad
        # self.screen_m.transition.duration = .4
        self.screen_m.transition.direction = 'left'
        self.mode = 'arcade'

    def time_mode(self):
        '''initialize the timer'''
        self.screen_m.transition = SlideTransition()
        self.screen_m.transition.direction = 'left'
        self.shootscreen.ids.timerlabel.text = 'Time ' + str(self.timer)
        self.timer = 21
        self.shootscreen.ids.timerlabel.color = (0, 0, 0, 1)
        self.mode = 'time'

    def reset_btn(self, btn, pos_x=10000, crasy=False):
        '''reset the position,the source image and the status of the button'''
        btn.velocity_x = btn.duck.rapidity * self.diffic_mult()
        btn.velocity_y = btn.duck.rapidity * self.diffic_mult()
        btn.touched = False
        btn.killed = False
        btn.falling = False
        btn.duck.timehere = random.randrange(btn.duck.timeheredefault[0],
                                             btn.duck.timeheredefault[1])
        btn.duck.timebeforespawn = \
            (btn.duck.timehere +
             random.randrange(btn.duck.timespawn[0], btn.duck.timespawn[1]))
        btn.pos = (
                random.uniform(
                 -btn.texture.size[0], 0 - 600),
                random.uniform(
                 0+btn.texture.size[1], Window.size[1]-btn.texture.size[1]))
        # btn.source = self.assetpath + btn.duck.normalimg
        btn.source = ('atlas://' + self.assetpath +
                      'atlas/myatlas/BirdGreen-idle-0')

        if btn.duck.ducktype == 'crasy':
            a = (btn.duck.rapidity * self.diffic_mult())
            b = (btn.duck.rapidity * - self.diffic_mult())
            # btn.velocity_y = (random.choice([a, b]))
            btn.velocity_y = (random.uniform(a, b))
            btn.pos = (
                    0 - pos_x,
                    random.uniform(
                        btn.texture.size[1],
                        Window.size[1] - btn.texture.size[1]))

    def reset_label(self, dt):
        if self.screen_m.current != 'game':
            return

        if self.pointsdisplay < self.points:
            if self.pointsdisplay + 100 < self.points:
                self.pointsdisplay += random.randint(5, 9) * self.dificultypts
            else:
                self.pointsdisplay += random.randint(1, 5)
        else:  # self.pointsdisplay > self.points:
            self.pointsdisplay = self.points

        # bt_crasy = None
        for btn in self.shootscreen.children:
            '''implement crasy duck clock'''
            if isinstance(btn, ScoreLabel) and btn.color[3] > 0:
                btn.color[3] -= dt
                if btn.color[3] < 0:
                    btn.color[3] = 0

    def endtime_mode(self, dt):
        '''check if the timer is ended'''
        if self.screen_m.current != 'game':
            return

        # bt_crasy = None
        for btn in self.shootscreen.children:
            '''implement crasy duck clock'''
            if isinstance(btn, TargetButton) and 'crasy' in btn.duck.ducktype:
                # bt_crasy = btn
                btn.duck.timebeforespawn -= 1

                if btn.duck.timebeforespawn < 0:
                    self.reset_btn(btn, btn.texture.size[0], True)

                btn.duck.timehere -= 1
                if btn.duck.timehere < 0:
                    pass

        # if bt_crasy.duck.timebeforespawn > 200:
        # bt_crasy.duck.timebeforespawn = 12

        if self.screen_m.current != 'game' or self.mode != 'time':
            pass
        else:

            if self.timer < 5:
                self.shootscreen.ids.timerlabel.color = (1, 0, 0, 1)
            if self.timer > 0:
                self.timer -= 1
            else:
                if self.points > self.bestscore:
                    self.bestscore = self.points
                    self.newrecord = 'New Record !!!'
                else:
                    self.newrecord = ''
                self.screen_m.current = 'win'

    def start(self):
        '''add the button to the screen and reset their position. reset the
        points'''
        shootgame.shootscreen.ids.combolabel.text = ''
        self.lastshoot_type = None
        self.multshoot_type = 1

        self.lstscorebeforeaddtime = 0
        self.points = self.pointsdisplay = 0
        self.scorelabel.text = ''
        self.reset_buttons()
        self.screen_m.transition = SlideTransition()
        self.screen_m.transition.direction = 'up'

    def hook_keyboard(self, window, key, *largs):
        '''hook the back key'''
        if key == 27 or key == 97 or key == 1001:
            if self.screen_m.current == 'game':
                self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'pause'
            elif self.screen_m.current == 'menu':
                self.leave()
            else:
                self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'menu'
            return True

    def leave(self):
        '''shutdown the game'''
        App.get_running_app().stop()

    def on_pause(self):
        '''Enable pause on Android'''
        self.save_score()
        return True

    def on_stop(self):
        '''save score when the app stop'''
        self.save_score()

    def on_resume(self):
        '''Resume after on_pause on Android'''
        pass

    def save_score(self):
        '''save the score to a file'''
        with open('scores', 'w') as f:
            f.write(str(self.bestscore))

    def load_score(self):
        '''load a score from a file'''
        if os.path.isfile('scores'):
            try:
                with open('scores', 'r') as f:
                    self.bestscore = float(f.readline())
            except ValueError:
                self.bestscore = 0


if __name__ == '__main__':
    # import sys
    # print('SYS.GETFILESYSTEMENCODING()')
    # print(sys.getfilesystemencoding())
    shootgame = ShootGame()
    shootgame.run()
