import math
import random

import pygame
import networkyshit
import game
import json
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-user", required=True, help="username (cant be the same as another player)", type=str)
parser.add_argument("-color", required=True, help="r,g,b (no spaces, just number then comma)", type=str)

def rgb_type(s):
    try:
        r, g, b = map(int, s.split(','))
        return (r, g, b)
    except:
        raise argparse.ArgumentTypeError("Color must be r,g,b")

args = parser.parse_args()
USERNAME = args.user # IMPORTANT TO NOT HAVE IT AS THE SAME AS SOMEONE ELSE
COLOR = rgb_type(args.color) # you can change this :D (with command line args now)
print(COLOR)
board = game.Game()
client = networkyshit.Client("167.172.148.33", 34197)


localplayer = game.MultiObject(random.uniform(0, 400), random.uniform(0, 400))
localplayerbody = [
    [15, -15],
    [0, -10],
    [-15, -15],
    [0, 15],
]
localplayergunshape = [
    [-10, -20],
    [-10, 10],
    [10, 10],
    [10, -20],
]
localplayergun = game.MultiObject(y=50)

localplayergunrenderer = game.PointShapeRenderer(localplayergunshape, (100,100,100))
localplayergun.renderer = localplayergunrenderer
renderer = game.CircleRenderer(30, COLOR)
collider = game.CircleCollider(60)
localplayer.collider = collider
localplayer.renderer = renderer
localplayer.children.append(localplayergun)
localplayer.tags.append("PLAYER_CHARACTER")
localplayer.attributes["PLAYER_USERNAME"] = USERNAME
localplayer.attributes["NAME"] = USERNAME
localplayergun.attributes["NAME"] = USERNAME+"gun"
localplayergun.attributes["RELOAD"] = 0
localplayergun.attributes["RELOADTIME"] = 60
localplayergun.tags.append("GUN")
localplayer.attributes["HEALTH"] = 100
objects = [localplayer]
client.send(json.dumps({
    "user": USERNAME,
    "eventType": 0,  # i should make a key for all the event types!
    "eventData": localplayer.to_dict()
}))

handle = [
    localplayer
]



def degrees_to_vector(degrees, length=1):
    angle_radians = math.radians(degrees)
    return (length * math.cos(angle_radians), length * math.sin(angle_radians))

# other variables
mouseaim = True
fire = False

# chat related
chatting = False
chatbox = game.TextObject("", (0,0,0), "", 20, 0, 0)
chatbox.lockedToCamera = True
objects.append(chatbox)
pendingChat = ""

# camera related
followPlayer = True

while board.running:
    game.clock.tick(60)
    # THIS IS THE HANDLING OF THE RECEIVED PACKETS BETWEEN COMPUTERS!!!!!!!
    dataRaw = client.poll()
    #if dataRaw != []: print(dataRaw)
    for eventRaw in dataRaw:
        event = json.loads(eventRaw)
        match event["eventType"]:
            case 0: # someone joined
                if event["user"] != USERNAME:
                    newPlayerChar = game.MultiObject.from_dict(event["eventData"])
                    objects.append(newPlayerChar)
                    userDisplay = game.TextObject(newPlayerChar.attributes["PLAYER_USERNAME"], (0,0,0), "",16, 0, 0)
                    userDisplay.tags.append("USERNAME_DISPLAY")
                    userDisplay.attributes["ATTACH"] = newPlayerChar.id
                    userDisplay.center = True
                    objects.append(userDisplay)
                    client.send(json.dumps({ # responding to join
                        "user": USERNAME,
                        "eventType": 1,
                        "eventData": localplayer.to_dict()
                    }))
            case 1:
                if event["user"] != USERNAME:
                    alreadyThere = False
                    for obj in objects:
                        if obj.id == event["eventData"]["id"]:
                            alreadyThere = True
                            break
                    if not alreadyThere:
                        newPlayerChar = game.MultiObject.from_dict(event["eventData"])
                        objects.append(newPlayerChar)
                        userDisplay = game.TextObject(newPlayerChar.attributes["PLAYER_USERNAME"], (0,0,0), "", 16, 0, 0)
                        userDisplay.tags.append("USERNAME_DISPLAY")
                        userDisplay.center = True
                        userDisplay.attributes["ATTACH"] = newPlayerChar.id
                        objects.append(userDisplay)
            case 2: # me when i add MOVEMEEEEENNNNNTTT
                if event["user"] != USERNAME:
                    for obj in objects:
                        if obj.id == event["eventData"][0]:
                            obj.x = event["eventData"][1]
                            obj.y = event["eventData"][2]
                            obj.rotation = event["eventData"][3]
                            obj.xVel = event["eventData"][4]
                            obj.yVel = event["eventData"][5]
            case 3:
                newChat = game.TextObject(event["user"] + " > " + event["eventData"], (0,0,0), "", 16, 0, 90)
                objects.append(newChat)
                for obj in objects:
                    if "CHAT" in obj.tags:
                        obj.y -= 18
                newChat.tags.append("CHAT")
                newChat.lockedToCamera = True
            case 4:
                for obj in objects + handle:
                    if obj.id == event["eventData"][0]:
                        print("damage")
                        obj.attributes["HEALTH"] -= event["eventData"][1]
                        print(obj.attributes)
                    if obj.attributes.get("HEALTH") is not None and obj.attributes.get("HEALTH") <= 0:
                        try:
                            handle.remove(obj)
                        except:
                            pass
                        try:
                            objects.remove(obj)
                        except:
                            pass
            case 5:
                if event["user"] != USERNAME:
                    newObject = game.MultiObject.from_dict(event["eventData"])
                    objects.append(newObject)
            case 6:
                for obj in objects + handle:
                    if obj.id == event["eventData"][0]:
                        print("deleting object")
                        try:
                            handle.remove(obj)
                        except:
                            pass
                        try:
                            objects.remove(obj)
                        except:
                            pass

    # END OF THE PACKET HANDLING
    keys = board.py.key.get_pressed()
    events = board.py.event.get()

    if not mouseaim:
        if abs(localplayer.xVel) > 0.001 or abs(localplayer.yVel) > 0.001:  # rotating the character
            targetRotation = -math.degrees(math.atan2(localplayer.xVel, localplayer.yVel))

            diff = (targetRotation - localplayer.rotation + 180) % 360 - 180
            dist = abs(diff)
            vel = math.sqrt(localplayer.xVel ** 2 + localplayer.yVel ** 2) * 2
            minRotSpeed = max(0, vel - 0.5)
            # scale speed based on distance
            t = min(dist / 360, 1.0)
            rot_speed = minRotSpeed + (vel - minRotSpeed) * t

            step = math.copysign(rot_speed, diff)

            # prevent overshoot
            if abs(step) > dist:
                localplayer.rotation = targetRotation
            else:
                localplayer.rotation += step
    if not chatting:
        if keys[pygame.K_w]:
            localplayer.yVel -= 0.2
        if keys[pygame.K_s]:
            localplayer.yVel += 0.2
        if keys[pygame.K_a]:
            localplayer.xVel -= 0.2
        if keys[pygame.K_d]:
            localplayer.xVel += 0.2
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:
                fire = True
                if chatting:
                    chatting = False
        if event.type == pygame.MOUSEBUTTONUP:
            if not pygame.mouse.get_pressed()[0]:
                fire = False

        if not chatting and event.type == pygame.KEYDOWN: # KEY DOWN WHILE NOT CHATTING
            if event.key == pygame.K_RETURN: # OPEN CHAT
                chatting = True

        # CHAT STUFF \/ \/ \/
        elif chatting and event.type == pygame.KEYDOWN: # CLOSE CHAT
            if event.key == pygame.K_RETURN:
                client.send(json.dumps({
                    "user": USERNAME,
                    "eventType": 3,
                    "eventData": pendingChat
                }))
                chatting = False
                pendingChat = ""

            elif event.key == pygame.K_BACKSPACE:
                pendingChat = pendingChat[:-1]

            else:
                pendingChat += event.unicode
        chatbox.text = pendingChat
        # CHAT STUFF /\ /\ /\

        if event.type == pygame.MOUSEMOTION: #aim use later
            mousePos = pygame.mouse.get_pos()
            aim = -math.degrees(math.atan2(mousePos[0] - board.screen.get_width()/2, mousePos[1] - board.screen.get_height()/2))
            localplayer.rotation = aim

    # okay gotta fire the weapons \/ \/ \/
    for child in localplayer.children:
        if "GUN" in child.tags:
            if child.attributes["RELOAD"] != 0:
                child.attributes["RELOAD"] -= 1
            elif fire:
                child.attributes["RELOAD"] = child.attributes["RELOADTIME"]
                newBullet = game.MultiObject(child.globalpos[0], child.globalpos[1])
                newBullet.renderer = game.CircleRenderer(10, COLOR)
                newBullet.collider = game.CircleCollider(40)
                angle = localplayer.rotation + child.rotation
                dirX,dirY = degrees_to_vector(angle + 90)
                print(dirX, dirY)
                newBullet.tags.append("BULLET")
                newBullet.rotation = angle
                newBullet.xVel = dirX * 5
                newBullet.yVel = dirY * 5
                handle.append(newBullet)
                client.send(json.dumps({
                    "user": USERNAME,
                    "eventType": 5,
                    "eventData": newBullet.to_dict()
                }))


    #print(math.atan2(localplayer.xVel, localplayer.yVel))
    if followPlayer:
        board.cameraPos[0] = localplayer.x - board.screen.get_width() / 2
        board.cameraPos[1] = localplayer.y - board.screen.get_height() / 2

    for obj in handle:
        obj.x += obj.xVel
        obj.y += obj.yVel
        client.send(json.dumps({
            "user": USERNAME,
            "eventType": 2,
            "eventData": [obj.id, obj.x, obj.y, obj.rotation, obj.xVel, obj.yVel]
        }))
        for obj2 in handle:

            if obj.id != obj2.id:
                collision = obj.collider.collide(obj2, obj.x, obj.y)
                if collision[0] != 0 or collision[1] != 0:
                    if "BULLET" in obj.tags:
                        client.send(json.dumps({
                            "user": USERNAME,
                            "eventType": 6,
                            "eventData": [obj.id]
                        }))
                        print(obj2.attributes)
                        if obj2.attributes["HEALTH"] != 0:
                            client.send(json.dumps({
                                "user": USERNAME,
                                "eventType": 4,
                                "eventData": [obj2.id, 50]
                            }))
                        break

                    if "BULLET" not in obj.tags and "BULLET" not in obj2.tags:
                        obj.xVel -= collision[0]
                        obj.yVel -= collision[1]
                        obj2.xVel += collision[0]
                        obj2.yVel += collision[1]
        for obj2 in objects:
            if obj.id != obj2.id:
                collision = obj.collider.collide(obj2, obj.x, obj.y)
                if collision[0] != 0 or collision[1] != 0:
                    if "BULLET" in obj.tags:
                        client.send(json.dumps({
                            "user": USERNAME,
                            "eventType": 6,
                            "eventData": [obj.id]
                        }))
                        print(obj2.attributes)
                        if obj2.attributes.get("HEALTH") is not None:
                            client.send(json.dumps({
                                "user": USERNAME,
                                "eventType": 4,
                                "eventData": [obj2.id, 50]
                            }))
                        break
                    if "BULLET" not in obj.tags and "BULLET" not in obj2.tags:
                        obj.xVel -= collision[0]
                        obj.yVel -= collision[1]

        client.send(json.dumps({
            "user": USERNAME,
            "eventType": 2,
            "eventData": [obj.id, obj.x, obj.y, obj.rotation, obj.xVel, obj.yVel]
        }))



    for obj in objects:
        if obj.id is not localplayer.id:
            obj.x += obj.xVel
            obj.y += obj.yVel
            if obj.collider is not None:
                collision = localplayer.collider.collide(obj, localplayer.x, localplayer.y)
                #print(collision, localplayer.attributes.get("NAME"))
                if "BULLET" not in obj.tags and "BULLET" not in obj2.tags:
                    obj.xVel -= collision[0]
                    obj.yVel -= collision[1]


        if "USERNAME_DISPLAY" in obj.tags:
            for obj2 in objects:
                if obj2.id == obj.attributes["ATTACH"]:

                    obj.x = obj2.x
                    obj.y = obj2.y

    if localplayer.yVel != 0 or localplayer.xVel != 0:
        client.send(json.dumps({
            "user": USERNAME,
            "eventType": 2,
            "eventData": [localplayer.id, localplayer.x, localplayer.y, localplayer.rotation, localplayer.xVel, localplayer.yVel]
        }))
    #print(localplayer.xVel, localplayer.yVel)
    localplayer.xVel /= max(1.05 ** abs(localplayer.xVel), 1.05)
    localplayer.yVel /= max(1.05 ** abs(localplayer.yVel), 1.05)
    board.render = objects + handle
    board.renderStep()