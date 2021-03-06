# -*- coding: utf-8 -*-
__version__ = '0.0.61'
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

from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
import csv
import operator
import os
import random
# from customtransition import CustomTransition
# from kivy.uix.screenmanager import AnimationTransition
# from datetime import datetime
# from kivy.utils import platform
from kivy.animation import Animation
from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
# from kivy.uix.screenmanager import FadeTransition
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
# from kivy.uix.screenmanager import SlideTransition
# from kivy.uix.image import AsyncImage
# from kivy.uix.gridlayout import GridLayout
# from kivy.graphics import Rectangle
try:
    from plyer import vibrator
except ImportError:
    pass

Window.size = (800, 460)
MAX_TIMER = 25


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
                 nbr_img=1, nbr_img_hit=1, timespawn=[4, 8], timehere=[8, 13]):
        '''initialize all variables'''
        self.targettype = targettype
        self.normalimg = normalimg
        self.hurtimg = hurtimg
        self.deadimg = deadimg
        self.rapidity = rapidity
        self.normalpts = normalpoints
        self.hurtpts = hurtpoints
        self.ducktype = ducktype
        self.velocity_x = None  # belong to TargetButton
        self.velocity_y = None  # belong to TargetButton
        self.timespawn = timespawn
        self.timeheredefault = timehere
        self.timebeforespawn = 1000
        self.timehere = 0
        self.nbr_img = nbr_img
        self.nbr_img_hit = nbr_img_hit
        self.index = 0


class Hen(Duck):
    '''Bonus when timer ending'''
    def __init__(self, eggs, *args, **kwargs):
        self.eggs = eggs
        super().__init__(*args, **kwargs)


class Gif():
    '''Implement gif behaviour for btn'''
    def __init__(self, img='BirdYellow-idle-', imgindexmax=0):
        self.img = img
        self.imgindexmax = imgindexmax


class GifButton(ButtonBehavior, Image, Gif):
    '''Just a gif btn'''
    def __init__(self, *args, **kwargs):
        self.index = 0
        super().__init__(*args, **kwargs)


class TargetButton(ButtonBehavior, Image):
    '''target for shoot, is composed of the Duck class'''
    def __init__(self, duck, *args, **kwargs):
        '''initialize the Duck class parameter as duck (composition),
        then use super() for parent class. see the MRO for details'''
        self.duck = duck
        self.index = 0
        self.nbr_img = self.duck.nbr_img
        self.nbr_img_hit = self.duck.nbr_img_hit
        super().__init__(*args, **kwargs)
    '''the above parameters must be a part of TargetButton and not a part of
    Duck, because all TargetButton share the same Duck instance'''
    touched = False  # keep this here
    killed = False   # heep this here
    falling = False
    animation = None

    def on_press(self):
        '''check which duck is touched or not'''
        if isinstance(self.duck, Hen):
            self.duck.eggs -= 1
        if (self.duck.ducktype == 'bad' and
                shootgame.end_anim):
            shootgame.finish()

        shootgame.shoot.play()
        if self.touched is True and self.killed is not True:
            self.source = (shootgame.ASSETPATH +
                           self.duck.deadimg + str(0))

            ptswin = self.duck.hurtpts
            self.shoot_type(self.source)
            ptswinmult = ptswin*self.mult_pts_type()
            shootgame.points += ptswinmult
            self.display_pts_win(ptswinmult)
            self.score_to_time()
            self.combo()

            self.killed = True

        elif self.touched is False:
            self.source = (shootgame.ASSETPATH +
                           self.duck.hurtimg + str(0))
            ptswin = self.duck.normalpts
            shootgame.points += ptswin
            self.display_pts_win(ptswin)
            self.score_to_time()

            self.touched = True

    def combo(self):
        '''Display combo on screen'''
        combo = shootgame.shootscreen.ids.combolabel
        if self.mult_pts_type() == 1:
            combo.text = ''
        else:
            combo.color = (0, 0, 0, 1)
            combo.text = 'Combo X' + str(self.mult_pts_type())

    @staticmethod  # maybe use property instead
    def mult_pts_type():
        '''return the combo multiplicator according to multshoot_type'''
        if shootgame.multshoot_type < 6:
            return shootgame.multshoot_type
        else:
            return 5

    def shoot_type(self, source):
        '''remember the lastshoot_type and increase multshoot_type
        this is a part of all combo implementation'''
        shootgame.multshoot_time = 3
        if self.source == shootgame.lastshoot_type:
            shootgame.multshoot_type += 1
        else:
            shootgame.multshoot_type = 1
            shootgame.lastshoot_type = self.source

    def score_to_time(self):
        '''transform pts to time'''
        pointup = shootgame.points - shootgame.lstscorebeforeaddtime
        if ((pointup >= shootgame.score_to_time)
                and 'time' in shootgame.mode):
            pointbyhundred = (round(pointup/100)*100)
            scoreremain = pointup - pointbyhundred
            timeadded = \
                (shootgame.timeadd *
                 int(round(pointup/shootgame.score_to_time)))
            shootgame.timer += timeadded
            shootgame.lstscorebeforeaddtime = shootgame.points - scoreremain

    def display_pts_win(self, pts):
        '''when the user click on a target:
            display the btn's points on the screen using ScoreLabel'''
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

    def hen_anim(self):
        if not shootgame.end_anim:
            shootgame.end_anim = True
            win = Window.size

            pos = (win[0]/2-self.size[0]/2, win[1]/2)
            self.animation = Animation(
                    pos=pos,
                    t='linear',
                    duration=3)

            for x in range(2):
                self.animation += Animation(
                        pos=(pos),
                        t='linear',
                        duration=2)

                self.animation += Animation(
                        pos=pos,
                        t='linear',
                        duration=3)

            self.animation.start(self)

    def hen_stop_anim(self):
        self.animation.stop(self)

    def dead_anim(self, op=operator.sub):
        '''anim when btn killed is True'''
        animation = Animation(pos=(
            op(self.pos[0], self.size[0]/2), self.pos[1] + self.size[1]/2),
            t='linear',
            duration=.3)

        animation += Animation(pos=(
            op(self.pos[0], self.size[0]/1.8), self.pos[1] + self.size[1]/1.8),
            t='linear',
            duration=.1)

        animation += Animation(pos=(
            op(self.pos[0], self.size[0]), - self.size[1]),
            t='in_quad')

        animation.start(self)

    def coin_anim(self, op=operator.sub):
        pos_x = random.uniform(0, self.size[0]*3)

        animation = Animation(pos=(
            op(self.pos[0], pos_x*1.2),
            self.pos[1] + self.size[1]),
            t='linear',
            duration=0.8)

        animation += Animation(pos=(
            op(self.pos[0], random.uniform(pos_x*1.2, pos_x*1.4)),
            self.pos[1]),
            t='linear',
            duration=0.8)

        animation += Animation(pos=(
            op(self.pos[0], random.uniform(pos_x, pos_x*1.2)),
            -self.size[1]),
            t='in_quad',
            duration=0.8)

        animation.start(self)


class ScoreLabel(Label):
    '''Label used to display btn points on the screen'''
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


class CreditsScreen(Screen):
    def __init__(self, *args, **kwargs):
        self.parse()
        super().__init__(*args, **kwargs)

    def parse(self):
        try:
            with open('CREDITS', 'r') as f:
                self.txt = "\n" + f.read()
                import re
                self.txt = re.sub(r'https?://[\w]*\.[\w]*\.?[\w]*\/?[\w]*',
                                  '',
                                  self.txt)
        except FileNotFoundError:
            self.txt = (
                "\nCREDITS\n\n"
                "Please visit:\n\n"
                "http://valstudiogame.maltouzes.win/shootgame.php")


class PauseScreen(Screen):
    '''when the game is in pause, see kv lang for gui'''
    pass


class OptionsScreen(Screen):
    def change_volume(self, checkbox):
        if not checkbox.active:
            shootgame.sound_game.volume = 0
            shootgame.music_volume = 0
        else:
            shootgame.music_volume = \
                shootgame.optionsscreen.ids.slider_volume.value_normalized
            shootgame.sound_game.volume = shootgame.music_volume

    def checkbox(self, value):
        check = shootgame.optionsscreen.ids.checkbox_volume
        if value == 0:
            check.active = False
        else:
            check.active = True


class MyCheckbox(CheckBox):
    def __init__(self, *args, **kwargs):
        self.background_checkbox_normal = (
                shootgame.ASSETPATH + 'yellow_boxCross')
        self.background_checkbox_down = (
                shootgame.ASSETPATH + 'yellow_boxCheckmark')

        super().__init__(*args, **kwargs)


class ScoresScreen(Screen):
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
    ASSETPATH = 'atlas://atlas/birdsatlas/'
    MASTER_MUSIC_VOLUME = 0  # standard music volume default: 0.2
    music_volume = MASTER_MUSIC_VOLUME  # useful for on_resume()

    background1 = ASSETPATH + ("2")
    background2 = ASSETPATH + ("1")
    background3 = ASSETPATH + ("4")

    layout = FloatLayout(size_hint=(1, 1))
    points = NumericProperty(0)
    bestscore = DictProperty({'easy': 0, 'medium': 0, 'hard': 0})
    newrecord = StringProperty('')
    dificulty = 'none'  # easy, medium and hard
    mode = 'none'  # arcade, time
    soundbtn = SoundLoader.load(os.getcwd() +
                                '/sound/push.ogg')
    sound_game_menu = SoundLoader.load(os.getcwd() +
                                       '/sound/happy.ogg')
    sound_game_1 = SoundLoader.load(os.getcwd() +
                                    '/sound/copycat(revised)_syncopika.ogg')
    sound_game = sound_game_menu
    sound_game.loop = True
    shoot = soundbtn
    timer = NumericProperty(0)
    pointsdisplay = NumericProperty(0)
    scorelabel = ScoreLabel(text='', font_size='25sp')
    lstscorebeforeaddtime = 0
    score_to_time = 100  # pts = timeadd
    timeadd = 1  # sec added
    lastshoot_type = None
    multshoot_type = 1
    multshoot_time = 3
    end_anim = False
    henpos = None
    hen_stopped = False

    def ducks_init(self):
        '''Initialize the target, with their
        :param type: easy, medium, hard or bad
        :type: normalpts: int
        :type: hurtpts: int
        :param rapidity: movement of the duck = rapidity * dificulty
        :param normalimg: img of the duck
        :param hurtmalimg: img of the duck is hurted
        :param deadimg: img when the duck is dead
        '''
        self.dkeasy = Duck('Bird', 'easy', 10, 30, 1,
                           'BirdGreen-idle-',
                           'BirdGreen-hit-',
                           'BirdGreen-hit-',
                           2, 2)

        self.dkmedium = Duck('Bird', 'medium', 20, 50, 1.3,
                             'BirdYellow-idle-',
                             'BirdYellow-hit-',
                             'BirdYellow-hit-',
                             8, 2)

        self.dkhard = Duck('Bird', 'hard', 10, 200, 2,  # pts, pts and rapidity
                           'BirdPurple-idle-',
                           'BirdPurple-hit-',
                           'BirdPurple-hit-',
                           2, 2)

        self.dkbonus = Duck('Bird', 'crasy', 600, 0, 3,
                            'BirdRed-idle-',
                            'BirdRed-hit-',
                            'BirdRed-hit-',
                            2, 2,
                            [13, 16],
                            [2, 3])

        self.dkbad = Duck('bomb', 'bad', -300, 0, 2,  # pts, pts and rapidity
                          'bomb-',
                          'bomb_dead-',
                          '/bomb_dead-',
                          1, 7)

        self.dkcrasy = Duck('Bird', 'crasy', -300, 0, 2,
                            'BirdSkull2-idle-',
                            'BirdSkull2-hit-',
                            'BirdSkull2-hit-',
                            2, 2,
                            [13, 16])

        self.dkhen = Hen(3, 'Bird', 'hen', 0, 0, 1,
                         'BirdHen-idle-',
                         'BirdHen-hit-',
                         'BirdHen-hit-',
                         4, 2)

        self.dkegg = Duck('Bird', 'egg', 50, 0, 1,
                          'coin-',
                          'coin-',
                          'coin-',
                          4, 2)

    def add_targets(self, duck, num, size_hx=None, size_hy=None):
        '''add the target take a duck parameter
        and add the coresponding duck multiplying the num parameter (number)'''

        for x in range(num):
            btn = TargetButton(
                    duck,
                    size_hint=(size_hx, size_hy),
                    source=(self.ASSETPATH +
                            duck.normalimg + str(0)))

            self.shootscreen.add_widget(btn)

    def newimgpause(self):
        '''random img btn when the game is in pause'''
        btns = []
        for btn in self.shootscreen.children:
            if isinstance(btn, TargetButton):
                if 'bomb' in btn.duck.targettype:
                    pass
                else:
                    btns.append(btn)

        btn = random.choice(btns)

        btnpause = self.pausescreen.ids.birdgif
        btnpause.img = btn.duck.normalimg
        btnpause.imgindexmax = btn.duck.nbr_img
        btnpause.index = 0

    def updateimgpause(self, dt):
        '''update pause's GifButton'''
        btn = self.pausescreen.ids.birdgif

        btn.index += 1
        if btn.index >= btn.imgindexmax:
            btn.index = 0

        btn.source = (
                self.ASSETPATH +
                btn.img + str(btn.index))

    def reset_buttons(self):
        '''reset all the buttons to their original position and their original
        image'''
        self.hen_stopped = False
        for btn in self.shootscreen.children:
            if isinstance(btn, TargetButton):  # and
                # 'crasy' not in btn.duck.ducktype):
                if btn.duck.ducktype == 'hen' and btn.animation:
                    btn.hen_stop_anim()
                try:
                    if ('Bird' in btn.duck.targettype or
                            'bomb' in btn.duck.targettype):
                        self.reset_btn(btn)
                except AttributeError:
                    pass

    def move_buttons(self, dt):
        '''move every buttons (target) in the screen according to the dificulty
        and the rapidity of the target'''
        if self.screen_m.current != 'game':
            pass
        else:
            for btn in self.shootscreen.children:
                if (not self.end_anim and
                        isinstance(btn, TargetButton) and
                        btn.duck.ducktype != 'hen'):
                    if ('Bird' in btn.duck.targettype or
                            'bomb' in btn.duck.targettype):
                        if btn.killed and not btn.falling:
                            btn.falling = True
                            if 'bomb' not in btn.duck.targettype:
                                btn.dead_anim()

                    if btn.duck.ducktype == 'crasy':
                        self.move_btn_crasy(btn)
                    elif btn.duck.targettype == 'bomb':
                        self.move_btn_vertically(btn)
                    elif btn.duck.ducktype == 'medium':
                        self.move_diagonal(btn)
                    elif ('hen' in btn.duck.ducktype or
                            'egg' in btn.duck.ducktype):
                        pass

                    else:
                        btn.pos[0] += (btn.duck.rapidity *
                                       self.diffic_mult)

                    if ((btn.pos[0] > Window.size[0] + 490 or
                        btn.pos[1] < 0 - btn.texture.size[1] or
                            btn.pos[1] > (Window.size[1] +
                                          btn.texture.size[1])) and 'crasy'
                            not in btn.duck.ducktype):
                            self.reset_btn(btn)
                else:
                    if(isinstance(btn, TargetButton) and
                            self.end_anim):
                        btn.pos[0] += (btn.duck.rapidity * 6)
                        btn.pos[1] -= (btn.duck.rapidity * 6)

                        if ('hen' in btn.duck.ducktype and
                                btn.pos[1] < (0 - btn.texture.size[1])):
                            self.finish()
                        if ('hen' in btn.duck.ducktype and
                                btn.pos[0] > Window.size[0]/2 - btn.size[0]):
                            self.hen_stopped = True

    def move_btn_vertically(self, btn):
        '''move btn from top to bottom'''
        btn.pos[1] -= (btn.duck.rapidity *
                       self.diffic_mult)

    def move_diagonal(self, btn):
        '''btn bounce again the edge of the screen'''
        if self.end_anim:
            return
        btn.pos[1] += btn.velocity_y
        btn.pos[0] += (btn.duck.rapidity * self.diffic_mult)
        self.bounce_top_bottom(btn)

    def bounce_top_bottom(self, btn):
        '''btn bounce again the top and the bottom of the screen'''
        if (btn.top > Window.size[1] or btn.pos[1] < 0):
            btn.velocity_y *= -1

    def move_btn_crasy(self, btn):
        '''DRY principe so should be remove: use move_diagonal instead'''
        # let btn use btn.dead_anim()
        if btn.killed or self.end_anim:
            return
        # btn leave the screen
        if btn.duck.timehere < 0:
            btn.pos[0] += btn.velocity_x
            btn.pos[1] += btn.velocity_y

        else:
            # btn still not in the screen so it must come
            if btn.pos[0] < 0:
                btn.pos[0] += (btn.duck.rapidity *
                               self.diffic_mult)

            # move the btn
            btn.pos[0] += btn.velocity_x
            btn.pos[1] += btn.velocity_y
            if btn.touched:
                btn.killed = True
            # btn bounce over the border
            if not btn.touched:
                if btn.pos[0] < 0 or btn.pos[0] > (Window.size[0] -
                                                   btn.texture.size[0]/1.5):
                    btn.velocity_x *= -1

                self.bounce_top_bottom(btn)

    @property
    def diffic_mult(self):
        '''return the dificulty multiplier for move the buttons'''
        if self.dificulty == 'easy':
            return random.uniform(1.5, 2)
        elif self.dificulty == 'medium':
            return random.uniform(2.5, 3)
        elif self.dificulty == 'hard':
            return random.uniform(3.5, 4)
        else:
            return random.uniform(1, 2)  # easy

    def build(self):
        '''create a ScreenManager and add all the Screens'''
        self.load_volume_file()
        self.sound_game.play()
        filename = (os.getcwd() + '/shootgamebuild.kv')

        with open(filename, encoding='utf-8') as f:
            Builder.load_string(f.read())

        self.soundbtn.volume = 0.5
        self.screen_m = ScreenManager()
        self.screen_m.transition.direction = 'up'

        self.shootscreen = ShootScreen(name='game')
        self.pausescreen = PauseScreen(name='pause')
        self.creditsscreen = CreditsScreen(name='credits')
        self.optionsscreen = OptionsScreen(name='options')
        self.scoresscreen = ScoresScreen(name='scores')
        self.screen_m.add_widget(StartScreen(name='menu'))
        self.screen_m.add_widget(LevelScreen(name='level'))
        self.screen_m.add_widget(self.creditsscreen)
        self.screen_m.add_widget(self.optionsscreen)
        self.screen_m.add_widget(self.scoresscreen)
        self.screen_m.add_widget(self.pausescreen)
        self.screen_m.add_widget(WinScreen(name='win'))
        self.screen_m.add_widget(self.shootscreen)

        self.ducks_init()

        self.shootscreen.add_widget(self.scorelabel)
        self.add_targets(self.dkeasy, 5)
        self.add_targets(self.dkmedium, 3)
        self.add_targets(self.dkhard, 1)
        self.add_targets(self.dkbonus, 1)
        self.add_targets(self.dkcrasy, 1)
        self.add_targets(self.dkegg, 6, 0.16, 0.16)
        self.add_targets(self.dkbad, 3)
        self.add_targets(self.dkhen, 1)

        self.screen_m.current = 'menu'
        Clock.schedule_interval(self.endtime_mode, 1)
        Clock.schedule_interval(self.move_buttons, 0.01)
        Clock.schedule_interval(self._updt_game, 0.01)
        Clock.schedule_interval(self.gif, 0.2)
        Clock.schedule_interval(self.updateimgpause, 0.2)
        Clock.schedule_interval(self.updateimgscores, 0.2)
        Clock.schedule_interval(self._updt_eggs, 0.5)
        self.load_score()

        return self.screen_m

    def gif(self, dt):
        '''Clock for trigger update_img'''
        if self.screen_m.current != 'game':
            pass
        else:
            for btn in self.shootscreen.children:
                if isinstance(btn, TargetButton):
                    self.update_img(btn)

    def update_img(self, btn):
        '''update the gif on each btn:
            increase the index and change the path accordingly'''
        nbr = 0
        btn.index += 1
        if btn.touched:
            nbr = btn.nbr_img_hit
            if ('bomb' in btn.duck.targettype and
                    btn.index >= nbr):
                return
        else:
            nbr = btn.nbr_img

        if btn.index >= nbr:
            btn.index = 0

        if not btn.touched:
            btn.source = (self.ASSETPATH +
                          btn.duck.normalimg +
                          str(btn.index))
        else:
            btn.source = (self.ASSETPATH +
                          btn.duck.hurtimg +
                          str(btn.index))

    def on_start(self):
        '''Loop the keyboard input'''
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
        # self.screen_m.transition.direction = 'left'
        self.mode = 'arcade'

    def time_mode(self):
        '''initialize the timer'''
        # self.screen_m.transition = SlideTransition()
        # self.screen_m.transition.direction = 'left'
        self.shootscreen.ids.timerlabel.text = 'Time ' + str(self.timer)
        self.timer = 15  # default is 15
        self.shootscreen.ids.timerlabel.color = (0, 0, 0, 1)
        self.mode = 'time'

    def reset_btn(self, btn, pos_x=10000, crasy=False):
        '''reset the position,the source image and the status of the button'''
        btn.velocity_x = btn.duck.rapidity * self.diffic_mult
        btn.velocity_y = btn.duck.rapidity * self.diffic_mult
        btn.touched = False
        btn.killed = False
        btn.falling = False
        btn.duck.timehere = random.randrange(btn.duck.timeheredefault[0],
                                             btn.duck.timeheredefault[1])
        btn.duck.timebeforespawn = \
            (btn.duck.timehere +
             random.randrange(btn.duck.timespawn[0], btn.duck.timespawn[1]))
        btn.source = (self.ASSETPATH +
                      'BirdGreen-idle-1')

        if btn.duck.ducktype == 'crasy':
            btn.velocity_y = random.uniform(
                    (btn.duck.rapidity * self.diffic_mult),
                    (btn.duck.rapidity * -self.diffic_mult))
            # velocity_y can't be between -1 and 1 -> too slow
            btn.velocity_y += abs(btn.velocity_y)/btn.velocity_y

            btn.pos = (
                    0 - pos_x,
                    random.uniform(
                        btn.texture.size[1],
                        Window.size[1] - btn.texture.size[1]))

        elif btn.duck.targettype == 'bomb':
            btn.pos = (
                    random.uniform(
                        -300, Window.size[0] - 100),
                    random.uniform(
                        Window.size[1], Window.size[1] + 600))
        elif btn.duck.ducktype == 'hen':
            btn.pos = (
                    -500,
                    random.uniform(
                     0,
                     # 0+btn.texture.size[1],
                     Window.size[1]-btn.texture.size[1]))
        else:
            btn.pos = (
                    random.uniform(
                     -btn.texture.size[0], 0 - 600),
                    random.uniform(
                     0,
                     # 0+btn.texture.size[1],
                     Window.size[1]-btn.texture.size[1]))

    def _updt_game(self, dt):
        '''call methods that need to be updated with a clock'''
        if self.screen_m.current != 'game':
            return

        if self.timer > MAX_TIMER:
            self.timer = MAX_TIMER

        if self.timer <= 0:  # hide timer
            self.shootscreen.ids.timerlabel.color = (0, 0, 0, 0)

        self.upte_label_pts()
        self.fade_out_pts(dt)
        self.updt_coin()

    def updt_coin(self):
        for btn in self.shootscreen.children:
            if (isinstance(btn, TargetButton) and
                    'egg' in btn.duck.ducktype and
                    btn.touched and
                    btn.color[3] > 0):
                btn.color[3] -= 0.35

    def upte_label_pts(self):
        '''fade out the btn's points displayed and smoothly add scores pts'''

        if self.pointsdisplay < self.points:
            if self.pointsdisplay + 100 < self.points:
                self.pointsdisplay += random.randint(5, 9)
            else:
                self.pointsdisplay += random.randint(1, 5)
        else:  # self.pointsdisplay > self.points:
            self.pointsdisplay = self.points

    def fade_out_pts(self, dt):
        '''fade_out combo and points labels according to multshoot_time'''
        combo = shootgame.shootscreen.ids.combolabel
        if combo.color[3] > 0:
            combo.color[3] -= (dt/self.multshoot_time)
        if combo.color[3] < 0:
            combo.color[3] = 0

        for lbl in self.shootscreen.children:
            '''implement crasy duck clock'''
            if isinstance(lbl, ScoreLabel) and lbl.color[3] > 0:
                lbl.color[3] -= dt
                if lbl.color[3] < 0:
                    lbl.color[3] = 0

    def endtime_mode(self, dt):
        '''check if the timer is ended'''
        if self.screen_m.current != 'game':
            return

        self.multshoot_time -= 1
        if self.multshoot_time <= 0:
            self.lastshoot_type = None

            self.shootscreen.ids.combolabel.text = ''
            self.multshoot_type = 1

        for btn in self.shootscreen.children:
            '''implement crasy duck clock'''
            if (isinstance(btn, TargetButton) and
                    'crasy' in btn.duck.ducktype
                    and not self.end_anim):
                btn.duck.timebeforespawn -= 1

                if btn.duck.timebeforespawn < 0:
                    self.reset_btn(btn, btn.texture.size[0], True)

                btn.duck.timehere -= 1
                if btn.duck.timehere < 0:
                    pass

        if self.screen_m.current != 'game' or self.mode != 'time':
            pass
        else:

            if self.timer < 6:
                self.shootscreen.ids.timerlabel.color = (1, 0, 0, 1)
            else:
                self.shootscreen.ids.timerlabel.color = (0, 0, 0, 1)
            if self.timer > 0:
                self.timer -= 1
            else:
                for btn in self.shootscreen.children:
                    if isinstance(btn, TargetButton):
                        if btn.duck.ducktype == 'hen':
                            btn.hen_anim()
                        if btn.duck.ducktype == 'egg':
                            self.move_egg(btn)

    def move_egg(self, btn):
        if not btn.falling:
            operators = [operator.sub, operator.add]
            btn.dead_anim(random.choice(operators))
            btn.falling = True

    def _updt_eggs(self, dt):
        if (self.screen_m.current != 'game' or
                not self.end_anim):
            pass
        else:
            lista = []
            for btn in self.shootscreen.children:
                if (isinstance(btn, TargetButton)):
                    if not self.hen_stopped:
                        return
                    if btn.duck.ducktype == 'hen':
                        self.henpos = btn.pos
                    if (((btn.duck.ducktype == 'egg') or
                        (btn.duck.ducktype == 'bad')) and
                            (btn.pos[1] < (0 - btn.texture.size[1])) and
                            (btn.duck.ducktype not in lista) and
                            self.henpos):
                            try:
                                lista.append(btn.duck.ducktype)
                                btn.touched = False
                                btn.color[3] = 1
                                btn.pos = self.henpos
                                operators = [operator.sub, operator.add]
                                btn.coin_anim(random.choice(operators))
                            except AttributeError:
                                pass

    def new_score(self):
        if 'none' in self.dificulty:
            return False
        if self.points > int(self.bestscore[self.dificulty]):
            self.bestscore[self.dificulty] = self.points
            self.load_score_img()
            return True
        else:
            return False

    def finish(self):
        if self.new_score():
            self.newrecord = 'New Record !!!'
        else:
            self.newrecord = ''
        self.screen_m.current = 'win'

    def new_music(self, music):
        self.sound_game.stop()
        self.sound_game = music
        self.sound_game.volume = self.music_volume
        self.sound_game.play()

    def start(self):
        '''add the button to the screen and reset their position. reset the
        points'''
        self.new_music(self.sound_game_1)
        self.end_anim = False
        shootgame.shootscreen.ids.combolabel.text = ''
        self.lastshoot_type = None
        self.multshoot_type = 1

        self.lstscorebeforeaddtime = 0
        self.points = self.pointsdisplay = 0
        self.scorelabel.text = ''
        # self.screen_m.transition = SlideTransition()
        # self.screen_m.transition.direction = 'up'
        self.reset_buttons()

    def hook_keyboard(self, window, key, *largs):
        '''hook the back key'''
        if key == 27 or key == 97 or key == 1001:
            if isinstance(App.get_running_app().root_window.children[0],
                          Popup):
                    App.get_running_app().root_window.children[0].dismiss()
                    return True

            if self.screen_m.current == 'game':
                self.new_music(self.sound_game_menu)
                self.new_score()
                self.newimgpause()
                # self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'pause'
            elif self.screen_m.current == 'menu':
                self.leave()
            elif self.screen_m.current == 'options':
                self.save_volume_file()
                # self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'menu'
            else:
                # self.screen_m.transition = FadeTransition()
                self.screen_m.current = 'menu'
            return True

    def leave(self):
        '''shutdown the game'''
        App.get_running_app().stop()

    def on_pause(self):
        '''Enable pause on Android'''
        self.sound_game.volume = 0
        self.new_score()  # check this
        self.save_score()
        return True

    def on_stop(self):
        '''save score when the app stop'''
        self.sound_game.volume = 0
        self.new_score()  # check this
        self.save_score()

    def on_resume(self):
        '''Resume after on_pause on Android'''
        self.sound_game.volume = self.music_volume

    def save_volume_file(self):
        with open('volume.txt', 'w') as f:
            f.write(str(self.sound_game.volume))

    def load_volume_file(self):
        if os.path.isfile('volume.txt'):
            with open('volume.txt', 'r') as f:
                self.sound_game.volume = float(f.read())
                self.music_volume = self.sound_game.volume
        else:
            self.sound_game.volume = self.MASTER_MUSIC_VOLUME

    def save_score(self):
        '''save the score to a file'''
        if 'time' in shootgame.mode and self.dificulty != 'none':
            with open('scores.csv', 'w') as csvfile:
                fieldnames = ['dificulty', 'score']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for key, value in self.bestscore.items():
                    writer.writerow({'dificulty': key,
                                     'score': value})

    def load_score(self):
        '''load a score from a file'''
        if os.path.isfile('scores.csv'):
            try:
                with open('scores.csv') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        self.bestscore[row['dificulty']] = row['score']
            except ValueError:
                self.bestscore = 0
        self.load_score_img()

    def reset_score(self):
        if os.path.isfile('scores.csv'):
            os.remove('scores.csv')
        for score in self.bestscore:
            self.bestscore[score] = 0
        self.load_score_img()

    def load_score_img(self):
        for difficulty in self.bestscore:
            score = int(self.bestscore[difficulty])

            if score >= 2000 and score < 15000:
                img = 'BirdGreen-idle-'
                imgindexmax = 2
                txt = 'Novice'
            elif score >= 15000 and score < 50000:
                img = 'BirdYellow-idle-'
                imgindexmax = 8
                txt = 'Sophomore'
            elif score >= 100000 and score < 200000:
                img = 'BirdPurple-idle-'
                imgindexmax = 2
                txt = 'Intermediate'
            elif score >= 200000 and score < 400000:
                img = 'BirdRed-idle-'
                imgindexmax = 2
                txt = 'Advanced'
            elif score >= 400000:
                img = 'BirdHen-idle-'
                imgindexmax = 4
                txt = 'Expert'
            else:
                img = 'BirdGreen-idle-'
                imgindexmax = 2
                txt = 'Newbie'

            if difficulty == 'easy':
                self.scoresscreen.ids.bonus1.img = img
                self.scoresscreen.ids.textbonus1.text = txt
                self.scoresscreen.ids.bonus1.imgindexmax = imgindexmax

                self.scoresscreen.ids.bonus1.source = (self.ASSETPATH +
                                                       img + str(0))
            elif difficulty == 'medium':
                self.scoresscreen.ids.bonus2.img = img
                self.scoresscreen.ids.textbonus2.text = txt
                self.scoresscreen.ids.bonus2.imgindexmax = imgindexmax

                self.scoresscreen.ids.bonus2.source = (self.ASSETPATH +
                                                       img + str(0))
            elif difficulty == 'hard':
                self.scoresscreen.ids.bonus3.img = img
                self.scoresscreen.ids.textbonus3.text = txt
                self.scoresscreen.ids.bonus3.imgindexmax = imgindexmax

                self.scoresscreen.ids.bonus3.source = (self.ASSETPATH +
                                                       img + str(0))

    def updateimgscores(self, dt):
        '''update pause's GifButton'''
        btn = self.scoresscreen.ids.bonus1
        self.updateimgscoresindex(btn)
        btn = self.scoresscreen.ids.bonus2
        self.updateimgscoresindex(btn)
        btn = self.scoresscreen.ids.bonus3
        self.updateimgscoresindex(btn)

    def updateimgscoresindex(self, btn):
        btn.index += 1
        if btn.index >= btn.imgindexmax:
            btn.index = 0

        btn.source = (
                self.ASSETPATH +
                btn.img + str(btn.index))


if __name__ == '__main__':
    # import sys
    # print('SYS.GETFILESYSTEMENCODING()')
    # print(sys.getfilesystemencoding())
    shootgame = ShootGame()
    shootgame.run()
