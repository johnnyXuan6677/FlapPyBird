from itertools import cycle
import random
import sys
import time
import numpy

import pygame
from pygame.locals import *

import pykinect
from pykinect import nui
from pykinect.nui import JointId

from pygame.color import THECOLORS

up_down = [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
person_index = []
game_mode = 0
FPS = 30
SCREENWIDTH  = 1280
SCREENHEIGHT = 1024
PIPEGAPSIZE  = 300 # gap between upper and lower part of pipe
BASEY        = SCREENHEIGHT * 0.9
KINECTEVENT = pygame.USEREVENT
# image, sound and hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
)

# list of pipes
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
)


try:
    xrange
except NameError:
    xrange = range

# retrieve video from kinect
def video_frame_ready(frame):

    pass

    # if not video_display:
    #     return

    # with screen_lock:
    #     address = surface_to_array(screen)
    #     frame.image.copy_bits(address)
    #     del address
    #     if skeletons is not None and draw_skeleton:
    #         draw_skeletons(skeletons)
        
    #     pygame.display.update()

kinect = nui.Runtime()
kinect.skeleton_engine.enabled = True
def post_frame(frame):
    try:
        pygame.event.post(pygame.event.Event(KINECTEVENT, skeletons = frame.SkeletonData))
    except:
        # event queue full
        pass

kinect.skeleton_frame_ready += post_frame

# kinect.depth_frame_ready += depth_frame_ready    
kinect.video_frame_ready += video_frame_ready    

kinect.video_stream.open(nui.ImageStreamType.Video, 3, nui.ImageResolution.Resolution1280x1024 , nui.ImageType.Color)

skeleton_to_depth_image = nui.SkeletonEngine.skeleton_to_depth_image

def detect_person_index(skeletons, dispInfo) :

    # define variables
    person_index = []

    for index, data in enumerate(skeletons):
        WristRight = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristRight], dispInfo.current_w, dispInfo.current_h) 
        wristright_y  = int(WristRight[1])

        if wristright_y != 0 :
            person_index.append(index)

    return person_index

def game_start(skeletons, person_index, dispInfo) :

    # define variables
    global game_mode, up_down
    for index, data in enumerate(skeletons):
        WristRight = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristRight], dispInfo.current_w, dispInfo.current_h) 
        Center = skeleton_to_depth_image(data.SkeletonPositions[JointId.Spine], dispInfo.current_w, dispInfo.current_h) 
        wristright_y  = int(WristRight[1])
        center_y  = int(Center[1])
        WristLeft = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristLeft], dispInfo.current_w, dispInfo.current_h) 
        wristleft_y  = int(WristLeft[1])


        if index in person_index   :
            print((wristright_y < center_y-100),(wristleft_y < center_y-100))
            # print(index,int(WristRight[1]))
            # print(index,int(Center[1]))
            if (wristright_y < center_y-100) and (wristleft_y < center_y-100) :
                up_down[index][0] = 1
            elif (wristright_y > center_y) and (wristleft_y > center_y) :
                up_down[index][1] = 1
                if up_down[index][1]*up_down[index][0] :
                    game_mode = 1
                    up_down = [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
                    break

    return game_mode

def bird_jump(skeletons, up_down, dispInfo, chance,super_jump_time) :
    
    global person_index
    # jump = [0,0,0,0,0,0]
    jump = 0
    super_jump = 0

    for index, data in enumerate(skeletons): 
        WristRight = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristRight], dispInfo.current_w, dispInfo.current_h) 
        Center = skeleton_to_depth_image(data.SkeletonPositions[JointId.Spine], dispInfo.current_w, dispInfo.current_h) 
        wristright_y  = int(WristRight[1])
        center_y  = int(Center[1])
        WristLeft = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristLeft], dispInfo.current_w, dispInfo.current_h) 
        wristleft_y  = int(WristLeft[1])
        Footright = skeleton_to_depth_image(data.SkeletonPositions[JointId.FootRight], dispInfo.current_w, dispInfo.current_h) 
        Footright_y  = int(Footright[1])
        Footleft = skeleton_to_depth_image(data.SkeletonPositions[JointId.FootLeft], dispInfo.current_w, dispInfo.current_h) 
        Footleft_y  = int(Footleft[1])

        if index in person_index :
            if (wristright_y < center_y-100) and (wristleft_y < center_y-100) :
                up_down[index][0] = 1
                print("up=1")
                print("jump",jump)
            elif (wristright_y > center_y) and (wristleft_y > center_y) and (jump == 0) :
                up_down[index][1] = 1
                print("down=1")
                if up_down[index][1]*up_down[index][0]:
                    up_down = [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
                    print(up_down)
                    jump = 1
                    print("jump=1")
                    break

            if ((Footright_y < center_y+200) or (Footleft_y < center_y+200)) and (chance > 0) and(super_jump_time==0):
                super_jump = 1
                chance -= 1
    
    if super_jump == 1 :
        jump = 2

    return jump, up_down, chance


SKELETON_COLORS = [THECOLORS["red"], 
                   THECOLORS["blue"], 
                   THECOLORS["green"], 
                   THECOLORS["orange"], 
                   THECOLORS["purple"], 
                   THECOLORS["yellow"], 
                   THECOLORS["violet"]]

def draw_skeletons(skeletons,dispInfo):
    global person_index
    for index, data in enumerate(skeletons):
        # draw the Head
        if index in person_index :
            RightPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristRight], dispInfo.current_w, dispInfo.current_h) 
            LeftPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.WristLeft], dispInfo.current_w, dispInfo.current_h)
            pygame.draw.circle(SCREEN, SKELETON_COLORS[index], (int(RightPos[0]), int(RightPos[1])), 20, 0)
            pygame.draw.circle(SCREEN, SKELETON_COLORS[index], (int(LeftPos[0]), int(LeftPos[1])), 20, 0)
            SpinePos = skeleton_to_depth_image(data.SkeletonPositions[JointId.Spine], dispInfo.current_w, dispInfo.current_h)
            pygame.draw.line(SCREEN, SKELETON_COLORS[index], (0, int(SpinePos[1])),(1280, int(SpinePos[1])), 5)
            pygame.draw.line(SCREEN, SKELETON_COLORS[index], (0, int(SpinePos[1]-100)),(1280, int(SpinePos[1])-100), 5)
            pygame.draw.line(SCREEN, SKELETON_COLORS[index], (0, int(SpinePos[1]+200)),(1280, int(SpinePos[1])+200), 5)
            
            FootRightPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.FootRight], dispInfo.current_w, dispInfo.current_h) 
            FootLeftPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.FootLeft], dispInfo.current_w, dispInfo.current_h)
            pygame.draw.circle(SCREEN, SKELETON_COLORS[index], (int(FootRightPos[0]), int(FootRightPos[1])), 20, 0)
            pygame.draw.circle(SCREEN, SKELETON_COLORS[index], (int(FootLeftPos[0]), int(FootLeftPos[1])), 20, 0)

            # SCREEN.blit(IMAGES['background'], (0,0))
            pygame.display.update() 

def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    print("FPSCLOCK",FPSCLOCK)
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    # pygame.display.set_caption('Flappy Bird')
    

    # numbers sprites for score display
    IMAGES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha()
    )

    # game over sprite
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    # message sprite for welcome screen
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    # base (ground) sprite
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

    # sounds
    if 'win' in sys.platform:
        soundExt = '.wav'
    else:
        soundExt = '.ogg'

    SOUNDS['die']    = pygame.mixer.Sound('assets/audio/die' + soundExt)
    SOUNDS['hit']    = pygame.mixer.Sound('assets/audio/hit' + soundExt)
    SOUNDS['point']  = pygame.mixer.Sound('assets/audio/point' + soundExt)
    SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
    SOUNDS['wing']   = pygame.mixer.Sound('assets/audio/wing' + soundExt)

    

    while True:

        # select random background sprites
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

        # select random player sprites
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        IMAGES['pipe'] = (
            pygame.transform.flip(
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), False, True),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hismask for pipes
        HITMASKS['pipe'] = (
            getHitmask(IMAGES['pipe'][0]),
            getHitmask(IMAGES['pipe'][1]),
        )

        # hitmask for player
        HITMASKS['player'] = (
            getHitmask(IMAGES['player'][0]),
            getHitmask(IMAGES['player'][1]),
            getHitmask(IMAGES['player'][2]),
        )

        movementInfo = showWelcomeAnimation()
        crashInfo = mainGame(movementInfo)
        showGameOverScreen(crashInfo)


def showWelcomeAnimation():
    """Shows welcome screen animation of flappy bird"""
    global game_mode, up_down, person_index
    # index of player to blit on screen
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # iterator used to change playerIndex after every 5th iteration
    loopIter = 0

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    basex = 0
    # amount by which base can maximum shift to left
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # player shm for up-down motion on welcome screen
    playerShmVals = {'val': 0, 'dir': 1}

    while True:

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

        e = pygame.event.wait() 
        dispInfo = pygame.display.Info()
        # retireve skeletons dataS

        if e.type == KINECTEVENT : # and not game_mode:
            skeletons = e.skeletons
            # draw_skeletons(skeletons,dispInfo)

            if not game_mode :
                person_index = detect_person_index(skeletons, dispInfo)
                game_mode = game_start(skeletons, person_index, dispInfo)

            # elif e.type == pygame.QUIT:
            #     break

            

            if game_mode :
                SOUNDS['wing'].play()
                game_mode = 0
                return {
                    'playery': playery + playerShmVals['val'],
                    'basex': basex,
                    'playerIndexGen': playerIndexGen,
                }


            # adjust playery, playerIndex, basex
            if (loopIter + 1) % 5 == 0:
                playerIndex = next(playerIndexGen)
            loopIter = (loopIter + 1) % 30
            basex = -((-basex + 4) % baseShift)
            playerShm(playerShmVals)

            # draw sprites
            SCREEN.blit(IMAGES['background'], (0,0))
            SCREEN.blit(IMAGES['player'][playerIndex],
                        (playerx, playery + playerShmVals['val']))
            SCREEN.blit(IMAGES['message'], (messagex, messagey))
            SCREEN.blit(IMAGES['base'], (basex, BASEY))
            draw_skeletons(skeletons,dispInfo)

            pygame.display.update()
            FPSCLOCK.tick(FPS)


def mainGame(movementInfo):

    global game_mode, up_down, person_index
    chance = 5
    score = playerIndex = loopIter = 0
    playerIndexGen = movementInfo['playerIndexGen']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # get 2 new pipes to add to upperPipes lowerPipes list
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # list of upper pipes
    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]

    # list of lowerpipe
    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    pipeVelX = -20

    # player velocity, max velocity, downward accleration, accleration on flap
    playerVelY    =  -9   # player's velocity along Y, default same as playerFlapped
    playerMaxVelY =  10   # max vel along Y, max descend speed
    playerMinVelY =  -8   # min vel along Y, max ascend speed
    playerAccY    =   1   # players downward accleration
    playerRot     =  45   # player's rotation
    playerVelRot  =   3   # angular speed
    playerRotThr  =  20   # rotation threshold
    playerFlapAcc =  -9   # players speed on flapping
    playerFlapped = False # True when player flaps
    super_jump = 0
    super_jump_time = 0

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()


        e = pygame.event.wait() 
        dispInfo = pygame.display.Info()
        jump = 0
        # retireve skeletons dataS
        if e.type == KINECTEVENT : # and not game_mode:
            skeletons = e.skeletons
            # draw_skeletons(skeletons,dispInfo)
            jump, up_down, chance = bird_jump(skeletons, up_down, dispInfo, chance, super_jump_time)
        # elif e.type == pygame.QUIT:
        #     break
            print(super_jump_time)
            print(chance)

            if super_jump_time > 0:
                super_jump_time-=1

            if jump == 1 :
                if playery > -2 * IMAGES['player'][0].get_height():
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    SOUNDS['wing'].play()
            elif jump == 2 :
                playerVelY = playerFlapAcc
                playerFlapped = True
                super_jump = 1
                SOUNDS['wing'].play()
                SOUNDS['swoosh'].play()
                SOUNDS['swoosh'].play()
                SOUNDS['swoosh'].play()

                    

    #        time.sleep(0.05)
            # for event in pygame.event.get():
            #     if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            #         pygame.quit()
            #         sys.exit()
            #     if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
            #         if playery > -2 * IMAGES['player'][0].get_height():
            #             playerVelY = playerFlapAcc
            #             playerFlapped = True
            #             SOUNDS['wing'].play()

            # check for crash here
            crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex},
                                upperPipes, lowerPipes)
            if crashTest[0]:
                return {
                    'y': playery,
                    'groundCrash': crashTest[1],
                    'basex': basex,
                    'upperPipes': upperPipes,
                    'lowerPipes': lowerPipes,
                    'score': score,
                    'playerVelY': playerVelY,
                    'playerRot': playerRot
                }

            # check for score
            playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
            for pipe in upperPipes:
                pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
                if pipeMidPos <= playerMidPos < pipeMidPos + 20:
                    score += 1
                    SOUNDS['point'].play()

            # playerIndex basex change
            if (loopIter + 1) % 3 == 0:
                playerIndex = next(playerIndexGen)
            loopIter = (loopIter + 1) % 30
            basex = -((-basex + 100) % baseShift)

            # rotate the player
            if playerRot > -90:
                playerRot -= playerVelRot

            # player's movement
            if playerVelY < playerMaxVelY and not playerFlapped:
                playerVelY += playerAccY
            if playerFlapped:
                playerFlapped = False

                # more rotation to cover the threshold (calculated in visible rotation)
                playerRot = 45

            playerHeight = IMAGES['player'][playerIndex].get_height()
            playery += min(playerVelY, BASEY - playery - playerHeight)

            
            if super_jump :
                playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
                pipeMidPos0x = lowerPipes[0]['x'] + IMAGES['pipe'][0].get_width() / 2
                pipeMidPosy = lowerPipes[0]['y']-150
                if playerMidPos > pipeMidPos0x + 60:
                    pipeMidPosy = lowerPipes[1]['y']-150
                playery = pipeMidPosy
                super_jump = 0
                super_jump_time = 30




            # move pipes to left
            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                uPipe['x'] += pipeVelX
                lPipe['x'] += pipeVelX

            # add new pipe when first pipe is about to touch left of screen
            if 0 < upperPipes[0]['x'] < 25:
                newPipe = getRandomPipe()
                upperPipes.append(newPipe[0])
                lowerPipes.append(newPipe[1])

            # remove first pipe if its out of the screen
            if upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
                upperPipes.pop(0)
                lowerPipes.pop(0)

            # draw sprites
            SCREEN.blit(IMAGES['background'], (0,0))

            showScore(score)

            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
                SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

            SCREEN.blit(IMAGES['base'], (basex, BASEY))
            # print score so player overlaps the score
            # showScore(score)

            # Player rotation has a threshold
            visibleRot = playerRotThr
            if playerRot <= playerRotThr:
                visibleRot = playerRot
            
            playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
            SCREEN.blit(playerSurface, (playerx, playery))
            draw_skeletons(skeletons,dispInfo)

            pygame.display.update()
            FPSCLOCK.tick(FPS)


def showGameOverScreen(crashInfo):
    global game_mode, up_down, person_index
    """crashes the player down ans shows gameover image"""
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7

    basex = crashInfo['basex']

    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']

    # play hit and die sounds
    SOUNDS['hit'].play()
    if not crashInfo['groundCrash']:
        SOUNDS['die'].play()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
        e = pygame.event.wait() 
        dispInfo = pygame.display.Info()
        # retireve skeletons dataS

        
        if e.type == KINECTEVENT : # and not game_mode:
            skeletons = e.skeletons
            # draw_skeletons(skeletons,dispInfo)

            if not game_mode :
                person_index = detect_person_index(skeletons, dispInfo)
                game_mode = game_start(skeletons, person_index, dispInfo)

            # elif e.type == pygame.QUIT:
            #     break

            if game_mode :
                if playery + playerHeight >= BASEY - 1:
                    game_mode = 0
                    return
                    

            # player y shift
            if playery + playerHeight < BASEY - 1:
                playery += min(playerVelY, BASEY - playery - playerHeight)

            # player velocity change
            if playerVelY < 15:
                playerVelY += playerAccY

            # rotate only when it's a pipe crash
            if not crashInfo['groundCrash']:
                if playerRot > -90:
                    playerRot -= playerVelRot

            # draw sprites
            SCREEN.blit(IMAGES['background'], (0,0))

            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
                SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

            SCREEN.blit(IMAGES['base'], (basex, BASEY))
            showScore(score)

            


            playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
            SCREEN.blit(playerSurface, (playerx,playery))
            gameoverx = int((SCREENWIDTH - IMAGES['gameover'].get_width()) / 2)
            gameovery = int(SCREENHEIGHT * 0.12)
            SCREEN.blit(IMAGES['gameover'], (gameoverx, gameovery))
            draw_skeletons(skeletons,dispInfo)

            FPSCLOCK.tick(FPS)
            pygame.display.update()


def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
         playerShm['val'] += 1
    else:
        playerShm['val'] -= 1


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - pipeHeight },  # upper pipe
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE }, # lower pipe
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0 # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    Xoffset = (SCREENWIDTH - totalWidth) / 2

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
        Xoffset += IMAGES['numbers'][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]
    else:

        playerRect = pygame.Rect(player['x'], player['y'],
                      player['w'], player['h'])
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            # player and upper/lower pipe hitmasks
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1+x][y1+y] and hitmask2[x2+x][y2+y]:
                return True
    return False

def getHitmask(image):
    """returns a hitmask using an image's alpha."""
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x,y))[3]))
    return mask

if __name__ == '__main__':
    main()
