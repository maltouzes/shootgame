# -*- coding: utf-8 -*-
__version__ = '0.0.35'
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
    '''cibles for shoot, is composed of the Duck class'''
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
        shootgame.shoot.play()
        ptsmulti = shootgame.dificultypts
        if self.touched is True and self.killed is not True:
            self.source = (shootgame.ASSETPATH +
                           self.duck.deadimg + str(0))

            ptswin = self.duck.hurtpts * ptsmulti
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
            ptswin = self.duck.normalpts * ptsmulti
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

            self.animation = Animation(pos=(
                win[0]/2, win[1]/2),
                t='linear',
                duration=3)

            for x in range(5):
                self.animation += Animation(pos=(
                    random.uniform(win[0]/2, win[0] - self.size[0]),
                    random.uniform(win[1]/1.3, win[1]/8)),
                    t='linear',
                    duration=1)

                self.animation += Animation(pos=(
                    random.uniform(0 + self.size[0], win[0]/2),
                    random.uniform(win[1]/1.3, win[1]/8)),
                    t='linear',
                    duration=1)

            self.animation.start(self)

    def hen_stop_anim(self):
        self.animation.stop(self)

    def dead_anim(self):
        '''anim when btn killed is True'''
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
                self.txt = re.sub(r'\*|http.*', '', self.txt)
        except FileNotFoundError:
            self.txt = (
                "\nCREDITS\n\n"
                "Please visit:\n\n"
                "https://github.com/maltouzes/shootgame/blob/master/CREDITS")


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
    ASSETPATH = 'atlas://atlas/birdsatlas/'

    background1 = ASSETPATH + ("2")
    background2 = ASSETPATH + ("1")
    background3 = ASSETPATH + ("4")

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
    multshoot_time = 3
    end_anim = False

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
        self.dkeasy = Duck('Bird', 'easy', 30, 50, 1,
                           'BirdGreen-idle-',
                           'BirdGreen-hit-',
                           'BirdGreen-hit-',
                           2, 2)

        self.dkmedium = Duck('Bird', 'medium', 40, 100, 1.3,
                             'BirdYellow-idle-',
                             'BirdYellow-hit-',
                             'BirdYellow-hit-',
                             8, 2)

        self.dkhard = Duck('Bird', 'hard', 10, 300, 2,  # pts, pts and rapidity
                           'BirdPurple-idle-',
                           'BirdPurple-hit-',
                           'BirdPurple-hit-',
                           2, 2)

        self.dkbonus = Duck('Bird', 'crasy', 800, 0, 3,
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

    def add_targets(self, duck, num):
        '''add the cibles take a duck parameter
        and add the coresponding duck multiplying the num parameter (number)'''

        for x in range(num):
            btn = TargetButton(
                    duck,
                    size_hint=(None, None),
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
        '''move every buttons (cibles) in the screen according to the dificulty
        and the rapidity of the cibles'''
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
                    elif 'hen' in btn.duck.ducktype:
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

    def move_btn_vertically(self, btn):
        '''move btn from top to bottom'''
        btn.pos[1] -= (btn.duck.rapidity *
                       self.diffic_mult)

    def move_diagonal(self, btn):
        '''btn bounce again the edge of the screen'''
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
        if btn.killed:
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
        self.pausescreen = PauseScreen(name='pause')
        self.creditsscreen = CreditsScreen(name='credits')
        self.screen_m.add_widget(StartScreen(name='menu'))
        self.screen_m.add_widget(LevelScreen(name='level'))
        self.screen_m.add_widget(self.creditsscreen)
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
        self.add_targets(self.dkbad, 3)
        self.add_targets(self.dkhen, 1)

        self.screen_m.current = 'menu'
        Clock.schedule_interval(self.endtime_mode, 1)
        Clock.schedule_interval(self.move_buttons, 0.01)
        Clock.schedule_interval(self._updt_game, 0.01)
        Clock.schedule_interval(self.gif, 0.2)
        Clock.schedule_interval(self.updateimgpause, 0.2)
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
        self.timer = 2
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

        self.upte_label_pts()
        self.fade_out_pts(dt)

    def upte_label_pts(self):
        '''fade out the btn's points displayed and smoothly add scores pts'''

        if self.pointsdisplay < self.points:
            if self.pointsdisplay + 100 < self.points:
                self.pointsdisplay += random.randint(5, 9) * self.dificultypts
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
            if isinstance(btn, TargetButton) and 'crasy' in btn.duck.ducktype:
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
                    if(isinstance(btn, TargetButton) and
                            btn.duck.ducktype == 'hen'):
                        btn.hen_anim()

                        '''
                if self.points > self.bestscore:
                    self.bestscore = self.points
                    self.newrecord = 'New Record !!!'
                else:
                    self.newrecord = ''
                self.screen_m.current = 'win'
                '''

    def start(self):
        '''add the button to the screen and reset their position. reset the
        points'''
        self.end_anim = False
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
                self.newimgpause()
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
