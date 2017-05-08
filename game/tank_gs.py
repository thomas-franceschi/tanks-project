#! /usr/bin/python3
# Thomas Franceschi
# Ben Becker

import pygame
from game.terrain import Terrain
from game.tank import MidTank
from game.mid_bullet import MidBullet
from game.background import Background
from pygame.locals import *
import time
from twisted.internet import reactor
import net.client, net.server

FIRSTPORT = 50000
TANKPORT = 50001
BULLETPORT = 50002
TERRAINPORT = 50003

PIXEL_SIZE = 5
EXPLOSION_SIZE = 8*PIXEL_SIZE

class GameSpace():
    def __init__(self, isServer=True):
        self.isServer = isServer
        self.connections = [False] * 4

    def remove_blocks(self, x, y):
        self.remove_from_gmap(x - EXPLOSION_SIZE,
                                 x + EXPLOSION_SIZE,
                                 self.height - y - EXPLOSION_SIZE,
                                 self.height - y + EXPLOSION_SIZE)

        # self.gs.terrain.create_surface()
        self.terrain.remove_blocks(x - EXPLOSION_SIZE,
                                      x + EXPLOSION_SIZE,
                                      y - EXPLOSION_SIZE,
                                      y + EXPLOSION_SIZE)

    def get_height(self, x):
        x = x % self.width
        col =  [1 if i else 0 for i in self.gmap[x,:] ]
        # print(col)
        # h = 1
        for i in range(0, self.height):
            # print(i)
            if not col[i]:
                return i
        return 1

        # col = [1 for i in self.gmap[x,:] if i]
        # return sum(col)

    def remove_from_gmap(self,x1,x2,y1,y2):
        self.gmap[x1:x2,y1:y2] = 0

    def main(self):
        # init gamespace
        pygame.init()
        self.size = self.width, self.height = 1750, 600
        self.black = 0, 0, 0
        self.screen = pygame.display.set_mode(self.size)
        self.game_over = False

        # init gameobjects
        self.clock = pygame.time.Clock()
        self.count = 0
        self.gameobjects = []

        if self.isServer:
            self.terrain = Terrain.random(self)
            # self.terrain.update()
            # pygame.display.flip()
            self.player1 = MidTank(self, ([50, 300]))
            self.player2 = MidTank(self, ([1700, 300]))
            self.gameobjects.append(self.terrain)
            self.gameobjects.append(self.player1)
            self.gameobjects.append(self.player2)
            self.server_start()
        else:
            print('uhh')
            self.client_start()


        pygame.key.set_repeat(1, 30)

        # start game loop
        while 1:
            start = time.time()
            self.clock.tick(60)
            self.count += 1

            if self.game_over:
                return 1
            # read user input
            for event in pygame.event.get():
                if event.type == QUIT:
                    return 0
                if event.type == KEYDOWN:
                    keys = pygame.key.get_pressed()
                    if keys[K_w]:
                        #print("jump!")
                        self.player1.vel[1] += 50
                    if keys[K_a]:
                        self.gameobjects[1].pos[0] -= 4
                        #self.bg.shift_left()
                    if keys[K_d]:
                        self.gameobjects[1].pos[0] += 4
                        #self.bg.shift_right()
                if event.type == MOUSEBUTTONDOWN:
                    mouse = pygame.mouse.get_pressed()
                    if mouse[0]:
                        pos = self.player1.get_pos()
                        obj = MidBullet.from_local(self, pos, 10)
                        self.gameobjects.append(obj)
                        self.bulletConnection.transport.write((pos, obj.vel))

            self.tankConnection.transport.write((self.player1.get_pos(), self.player1.vel))

            #blank out screen
            self.screen.fill(self.black)

            # call tick on each object
            for gameobject in self.gameobjects:
                gameobject.tick()

            # update screen
            for gameobject in self.gameobjects:
                gameobject.update()

            pygame.display.flip()

            end = time.time()
            print(end-start)

    def server_start(self):
        reactor.listenTCP(FIRSTPORT, server.FirstFactory(self))
        reactor.listenTCP(TANKPORT, server.TankFactory(self))
        reactor.listenTCP(BULLETPORT, server.BulletFactory(self))
        reactor.listenTCP(TERRAINPORT, server.TerrainFactory(self))

        reactor.run()

        while not all(self.connections):
            time.sleep(1)

    def client_start(self):
        self.firstConnection = reactor.connectTCP('localhost',FIRSTPORT, client.FirstFactory(self))
        self.tankConnection = reactor.connectTCP('localhost',TANKPORT, client.TankFactory(self))
        self.bulletConnection = reactor.connectTCP('localhost', BULLETPORT, client.BulletFactory(self))
        self.terrainConnection = reactor.connectTCP('localhost', TERRAINPORT, client.TerrainFactory(self))

        reactor.run()