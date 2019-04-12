import cv2
import numpy as np
import time
import socket
import selectors
import types

inti_flag = False
position_x = 0
position_y = 0
direction = -1
dist_save = 0

host = '192.168.68.97'
port = 7777
 
def accept_wrapper(sock,sel):
    conn, addr = sock.accept()  # Should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask,sel,image):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)
            drawNewSpot(image,data.outb.decode())
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

def positionInitiate(event,x,y,flags,param):
    global position_x
    global position_y
    global inti_flag
    global direction

    if  event == cv2.EVENT_LBUTTONDOWN and (direction == -1 or inti_flag == False):    
        if inti_flag == False:
            position_x = x
            position_y = y
            print ("x: ",x)
            print ("y: ",y)
            inti_flag = True
        else:
            temp_x = x
            temp_y = y
            if abs(temp_x-position_x) > abs(temp_y - position_y):
                if temp_x < position_x:
                    direction = 270
                else:
                    direction = 90
            else:
                if temp_y > position_y:
                    direction = 180
                else:
                    direction = 0
            print ("dir: ",direction)

def addNewPosition(direct,dist):
    global inti_flag
    global direction
    global position_x
    global position_y
    global dist_save

    if inti_flag == True:
# change direction        
        if direct == "Right":
            dist_save = 0
            direction += 90
            if direction >= 360:
                direction -= 360
        elif direct == "Left":
            dist_save = 0
            direction -= 90
            if direction < 0:
                direction += 360
        elif direct == "No Turn" or direct == "":
            pass #no direction changes
        else:
            print(direct)

#change distance

        print(direction)
        dist = dist + dist_save # avoid error
        dist_cm = dist*100 # change meter to centimeter
        if dist_cm < 320:
            dist_save = dist_save + dist
        map_cm = dist_cm/320 # change the billy ruler
        pixel_num = int(map_cm*100/1.5) # change to pixel
        
        if direction == 0:
            position_y -= pixel_num
        elif direction == 90:
            position_x += pixel_num
        elif direction == 180:
            position_y += pixel_num
        elif direction == 270:
            position_x -= pixel_num
        else:
            pass

def drawNewSpot(image,data):
    global position_x
    global position_y

    cv2.circle(image,(position_x,position_y),1,(255,255,255),5)
    addNewPosition(data,1)
    cv2.circle(image,(position_x,position_y),1,(0,0,0),5)


def main():
    global position_x
    global position_y

    image = cv2.imread("../IMAGE/image_draw.JPG")
    cv2.namedWindow("Image")
    cv2.setMouseCallback('Image',positionInitiate)
    cv2.imshow("Image",image)
    cv2.waitKey(0)

    try:
        sel = selectors.DefaultSelector()

        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lsock.bind((host, port))
        lsock.listen()
        print('listening on', (host, port))
        lsock.setblocking(False)
        sel.register(lsock, selectors.EVENT_READ, data=None)
        while True:    
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj,sel)
                else:
                    service_connection(key, mask,sel,image)
            cv2.imshow("Image",image)
            if cv2.waitKey(500) & 0xFF == ord('q'):
                break

    finally:
        lsock.close()
        print("close socket")


if __name__ == "__main__" :
    main()
