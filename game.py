import math
import random
import string

import pygame

clock = pygame.time.Clock()



class Object:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.xVel = 0
        self.yVel = 0
        self.rotation = 0
        self.tags = []
        self.attributes = {}
        self.id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        self.type = self.__class__.__name__
        self.lockedToCamera = False


class Serializable:
    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d):
        obj = cls.__new__(cls)   # bypass __init__
        obj.__dict__.update(d)
        return obj

class CircleCollider(Serializable):
    def __init__(self, radius):
        self.radius = radius
        self.type = "CircleCollider"

    def collide(self, other, x, y):
        distance = math.sqrt((other.x - x) ** 2 + (other.y - y) ** 2)
        if distance <= self.radius:
            collisionV = [
                (other.x - x) / distance,
                (other.y - y) / distance
            ]
            #print(collisionV)
            return collisionV
        return [0,0]

class PointShapeCollider(Serializable):
    def collide(self, other, x, y):
        return [0, 0]

class CircleRenderer(Serializable):
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color
        self.type = "CircleRenderer"
        self.lockedToCamera = False

    def render(self, screen, cameraPos, x, y, angle):
        if self.lockedToCamera:
            pygame.draw.circle(screen, self.color, (x,y), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (x - cameraPos[0], y - cameraPos[1]), self.radius)

class PointShapeRenderer(Serializable):
    def __init__(self, points, color=(0,0,0)):
        self.points = points
        self.color = color
        self.type = "PointShapeRenderer"
        self.lockedToCamera = False

    def render(self, screen, cameraPos,  x, y, angle):
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        if self.lockedToCamera:
            transformed = [
                ((x) + px * ca - py * sa,
                 (y) + px * sa + py * ca)
                for px, py in self.points
            ]
            pygame.draw.polygon(screen, self.color, transformed, 0)
        else:
            transformed = [
                ((x - cameraPos[0]) + px * ca - py * sa,
                 (y - cameraPos[1]) + px * sa + py * ca)
                for px, py in self.points
            ]
            pygame.draw.polygon(screen, self.color, transformed, 0)

class MultiObject(Object): # RECURSION!!!!!!!!
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.parent = None
        self.globalpos = [0, 0]
        self.collider = None
        self.type = "MultiObject"
        self.children = [] # this will be a container that holds other multi objects
        self.renderer = None # this will be the container for the object that handles rendering (png or point object?)


    def render(self, screen, cameraPos, px=0, py=0, prot=0):
        #print(self.attributes.get("NAME"), self.renderer.type)
        rot = prot + self.rotation

        cos_r = math.cos(math.radians(prot))
        sin_r = math.sin(math.radians(prot))

        rx = self.x * cos_r - self.y * sin_r
        ry = self.x * sin_r + self.y * cos_r

        x = px + rx
        y = py + ry
        self.globalpos[0] = x
        self.globalpos[1] = y

        if self.renderer is not None:
            self.renderer.render(screen, cameraPos, x, y, rot)

        # render children
        for child in self.children:
            child.render(screen, cameraPos, x, y, rot)

    def to_dict(self):
        return {
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "renderer": self.renderer.to_dict() if self.renderer else None,
            "collider": self.collider.to_dict() if self.collider else None,
            "children": [child.to_dict() for child in self.children],
            "tags": self.tags,
            "attributes": self.attributes,
            "id": self.id

        }

    @classmethod
    def from_dict(cls, d, parent=None):
        obj = cls(d["x"], d["y"])
        obj.rotation = d["rotation"]
        obj.parent = parent
        obj.attributes = d["attributes"]
        obj.id = d["id"]
        obj.tags = d["tags"]

        if d["renderer"]:
            rdata = d["renderer"]
            rcls = CLASSLIST[rdata["type"]]
            obj.renderer = rcls.from_dict(rdata)
            obj.renderer.owner = obj

        if d["collider"]:
            cdata = d["collider"]
            ccls = CLASSLIST[cdata["type"]]
            obj.collider = ccls.from_dict(cdata)
            obj.collider.owner = obj

        for child_d in d["children"]:
            child = cls.from_dict(child_d, obj)
            obj.children.append(child)

        return obj



class TextObject(Object, Serializable):
    def __init__(self, text, color, font, size, x, y):
        super().__init__(x, y)
        self.text = text
        self.color = color
        self.font = pygame.font.SysFont(font, size)
        self.canCollide = False
        self.renderedText = self.font.render(self.text, False, self.color)
        self.renderedTextCurrent = text
        self.size = self.renderedText.get_size()
        self.center = False
        self.collider = None



    def render(self, screen, cameraPos):
        if self.text != self.renderedTextCurrent:
            self.renderedText = self.font.render(self.text, False, self.color)
            self.renderedTextCurrent = self.text
            self.size = self.renderedText.get_size()
        targetX = self.x
        targetY = self.y
        if not self.lockedToCamera:
            targetX -= cameraPos[0]
            targetY -= cameraPos[1]
        if self.center:
            screen.blit(self.renderedText, (targetX - (self.size[0] / 2), targetY - (self.size[1] / 2)))
        else:
            screen.blit(self.renderedText, (targetX, targetY))


class CircleObject(Serializable):
    def __init__(self, x, y, radius, color):
        super().__init__(x, y)
        self.radius = radius
        self.color = color
        self.canCollide = True


    def render(self, screen, cameraPos):
        if self.lockedToCamera:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        else:
            pygame.draw.circle(screen, self.color, (self.x - cameraPos[0], self.y - cameraPos[1]), self.radius)

class Game: # game window
    def __init__(self):
        self.cameraPos = [0, 0]
        pygame.font.init()
        pygame.init()
        self.py = pygame
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("BRO WHAT")
        self.render = {}
        pygame.display.flip()

        self.running = True

    def renderStep(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        self.screen.fill((200, 200, 200))
        for obj in self.render:
            obj.render(self.screen, self.cameraPos)
        pygame.display.flip()


CLASSLIST = {
    "PointShapeRenderer": PointShapeRenderer,
    "CircleRenderer": CircleRenderer,
    "CircleCollider": CircleCollider,
    "PointShapeCollider": PointShapeCollider,
    "MultiObject": MultiObject,
    "TextObject": TextObject,
    "CircleObject": CircleObject,
}