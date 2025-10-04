import cv2 as cv
import mediapipe as mp
import time
from djitellopy import tello


# Установка соединения с дроном, подключение к его камере, вывод процент оставшегося заряда
me = tello.Tello()
me.connect()
me.streamon()
print(me.get_battery())

# Подключение к камере для управления жестами
cap = cv.VideoCapture(0)

# Создание объектов для трекинга рук
mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.7, max_num_hands=1)
mpDraw = mp.solutions.drawing_utils

# Переменные для отслеживания времени для расчета фпс
pTime = 0
cTime = 0

# Направление или команда текущего полета
direction = 'none'
# Текущая скорость
speed = 0
# Максимально возможная скорость (ограничивается)
max_speed = 50
# Угол текущего поворота
rotate_angle = 0
# Маскимально возможный угол поворота за раз (ограничивается)
max_rotate_angle = 45
# Вспомогательная проверка
speed_flag = True
take_off_flag = False


# Функция для сообщения дрону нужной команды
def move():
    global me, direction, speed, rotate_angle, max_rotate_angle
    if direction == 'take off':
        me.takeoff()
        time.sleep(0.1)
    elif direction == 'land':
        me.land()
        time.sleep(0.1)
    elif direction == 'stop':
        me.send_rc_control(0, 0, 0, 0)
        time.sleep(0.1)
    elif direction == 'forward':
        me.send_rc_control(0, int(speed), 0, 0)
        time.sleep(0.1)
    elif direction == 'backward':
        me.send_rc_control(0, -1 * int(speed), 0, 0)
        time.sleep(0.1)
    elif direction == 'up':
        me.send_rc_control(0, 0, int(speed), 0)
        time.sleep(0.1)
    elif direction == 'down':
        me.send_rc_control(0, 0, -1 * int(speed), 0)
        time.sleep(0.1)
    elif direction == 'left':
        me.send_rc_control(-1 * int(speed), 0, 0, 0)
        time.sleep(0.1)
    elif direction == 'right':
        me.send_rc_control(int(speed), 0, 0, 0)
        time.sleep(0.1)
    elif direction == 'rotate clockwise':
        me.rotate_clockwise(max_rotate_angle)
        rotate_angle += max_rotate_angle
        while rotate_angle >= 360:
            rotate_angle -= 360
        time.sleep(0.1)
    elif direction == 'rotate counter-clockwise':
        me.rotate_counter_clockwise(max_rotate_angle)
        rotate_angle -= max_rotate_angle
        while rotate_angle < 0:
            rotate_angle += 360
        time.sleep(0.1)
    else:
        me.send_rc_control(0, 0, 0, 0)
        time.sleep(0.1)


while True:
    # Получение изображения с камеры, трекинг рук
    success, image = cap.read()
    image = cv.flip(image, 1)
    imageRGB = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    results = hands.process(imageRGB)
    h, w, c = image.shape
    if results.multi_hand_landmarks:
        coords = []
        for handlm in results.multi_hand_landmarks:
            for id, lm in enumerate(handlm.landmark):
                coords.append([int(lm.x * w), int(lm.y * h)])
            mpDraw.draw_landmarks(image, handlm, mpHands.HAND_CONNECTIONS)
        # Жест прекращения вращения
        if (direction in ['rotate clockwise', 'rotate counter-clockwise'] and
            ((coords[8][0] > coords[6][0] and coords[6][0] < coords[5][0] and coords[12][0] > coords[10][0] and coords[10][0] < coords[9][0] and
            coords[16][0] > coords[14][0] and coords[14][0] < coords[13][0] and coords[20][0] > coords[18][0] and coords[18][0] < coords[17][0] and
            coords[4][1] > coords[3][1]) or
            (coords[8][0] < coords[6][0] and coords[6][0] > coords[5][0] and coords[12][0] < coords[10][0] and coords[10][0] > coords[9][0] and
            coords[16][0] < coords[14][0] and coords[14][0] > coords[13][0] and coords[20][0] < coords[18][0] and coords[18][0] > coords[17][0] and
            coords[4][1] > coords[3][1])) and
            abs(coords[5][0] - coords[17][0]) / (abs(coords[5][1] - coords[17][1]) + 1) < 0.2):
            direction = 'none'
            speed = 0
            speed_flag = True
        # Жест взлета
        elif (not take_off_flag and coords[8][1] < coords[7][1] < coords[6][1] < coords[5][1] and
            coords[15][1] > coords[8][1] and coords[19][1] > coords[8][1] and
            coords[12][1] < coords[11][1] < coords[10][1] < coords[9][1] and
            coords[15][1] > coords[12][1] and coords[19][1] > coords[12][1] and
            abs(coords[8][0] - coords[5][0]) / (abs(coords[8][1] - coords[5][1]) + 1) < 0.2 and
            abs(coords[5][1] - coords[8][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[8][1] - coords[6][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[12][0] - coords[9][0]) / (abs(coords[12][1] - coords[9][1]) + 1) < 0.2 and
            abs(coords[9][1] - coords[12][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[12][1] - coords[10][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[16][1] - coords[14][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[20][1] - coords[18][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            ((coords[4][0] > coords[3][0] and coords[5][0] < coords[17][0]) or (coords[4][0] < coords[3][0] and coords[5][0] > coords[17][0]))):
            direction = 'take off'
            speed = 0
            speed_flag = True
            take_off_flag = True
            move()
        # Жест посадки
        elif (take_off_flag and coords[8][1] > coords[7][1] > coords[6][1] > coords[5][1] and
            coords[15][1] < coords[8][1] and coords[19][1] < coords[8][1] and
            coords[12][1] > coords[11][1] > coords[10][1] > coords[9][1] and
            coords[15][1] < coords[12][1] and coords[19][1] < coords[12][1] and
            abs(coords[8][0] - coords[5][0]) / (abs(coords[8][1] - coords[5][1]) + 1) < 0.2 and
            abs(coords[5][1] - coords[8][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[8][1] - coords[6][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[12][0] - coords[9][0]) / (abs(coords[12][1] - coords[9][1]) + 1) < 0.2 and
            abs(coords[9][1] - coords[12][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[12][1] - coords[10][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[16][1] - coords[14][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[20][1] - coords[18][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            ((coords[4][0] > coords[3][0] and coords[5][0] < coords[17][0]) or (coords[4][0] < coords[3][0] and coords[5][0] > coords[17][0]))):
            direction = 'land'
            speed = 0
            speed_flag = True
            take_off_flag = False
            move()
        # Жест движения вперед
        elif (take_off_flag and coords[4][1] < coords[8][1] < coords[12][1] < coords[16][1] and
            abs(coords[4][0] - coords[2][0]) / (abs(coords[4][1] - coords[2][1]) + 1) < 0.2 and
            abs(coords[5][0] - coords[17][0]) / (abs(coords[5][1] - coords[17][1]) + 1) < 0.2 and
            (coords[2][1] - coords[4][1]) / (coords[13][1] - coords[5][1]) > 0.75 and coords[4][1] < coords[3][1] and
            (((coords[4][0]) > coords[6][0] and coords[6][0] < coords[8][0] and coords[10][0] < coords[12][0] and coords[14][0] < coords[16][0] and coords[18][0] < coords[20][0]) or
            (coords[4][0]) < coords[6][0] and coords[6][0] > coords[8][0] and coords[10][0] > coords[12][0] and coords[14][0] > coords[16][0] and coords[18][0] > coords[20][0])):
            direction = 'forward'
            speed = 0
            speed_flag = True
        # Жест двжения назад
        elif (take_off_flag and coords[4][1] > coords[8][1] > coords[12][1] > coords[16][1] and
            abs(coords[4][0] - coords[2][0]) / (abs(coords[4][1] - coords[2][1]) + 1) < 0.2 and
            abs(coords[5][0] - coords[17][0]) / (abs(coords[5][1] - coords[17][1]) + 1) < 0.2 and
            (coords[4][1] - coords[2][1]) / (coords[5][1] - coords[13][1]) > 0.75 and coords[4][1] > coords[3][1] and
            (((coords[4][0]) > coords[6][0] and coords[6][0] < coords[8][0] and coords[10][0] < coords[12][0] and coords[14][0] < coords[16][0] and coords[18][0] < coords[20][0]) or
            (coords[4][0]) < coords[6][0] and coords[6][0] > coords[8][0] and coords[10][0] > coords[12][0] and coords[14][0] > coords[16][0] and coords[18][0] > coords[20][0])):
            direction = 'backward'
            speed = 0
            speed_flag = True
        # Жест движения влево
        elif (take_off_flag and coords[4][0] < coords[6][0] < coords[10][0] < coords[14][0] and coords[4][0] < coords[3][0] and
            abs(coords[4][1] - coords[2][1]) / (abs(coords[4][0] - coords[2][0]) + 1) < 0.2 and
            abs(coords[5][1] - coords[17][1]) / (abs(coords[5][0] - coords[17][0]) + 1) < 0.2 and
            coords[7][1] > coords[5][1] and coords[11][1] > coords[9][1] and coords[15][1] > coords[13][1] and coords[19][1] > coords[17][1] and
            coords[4][1] > coords[6][1] and coords[10][1] < coords[12][1] and coords[14][1] < coords[16][1] and coords[18][1] < coords[20][1]):
            direction = 'left'
            speed = 0
            speed_flag = True
        # Жест движения вправо
        elif (take_off_flag and coords[4][0] > coords[8][0] > coords[12][0] > coords[16][0] and coords[4][0] > coords[3][0] and
            abs(coords[4][1] - coords[2][1]) / (abs(coords[4][0] - coords[2][0]) + 1) < 0.2 and
            abs(coords[5][1] - coords[17][1]) / (abs(coords[5][0] - coords[17][0]) + 1) < 0.2 and
            coords[7][1] > coords[5][1] and coords[11][1] > coords[9][1] and coords[15][1] > coords[13][1] and coords[19][1] > coords[17][1] and
            coords[4][1] > coords[6][1] and coords[10][1] < coords[12][1] and coords[14][1] < coords[16][1] and coords[18][1] < coords[20][1]):
            direction = 'right'
            speed = 0
            speed_flag = True
        # Жест остановки движения
        elif (take_off_flag and abs(coords[0][0] - coords[12][0]) / (abs(coords[0][1] - coords[12][1]) + 1) < 0.2 and
            (coords[5][1] - min(coords[8][1], coords[12][1], coords[16][1], coords[20][1])) / (abs(coords[0][1] - coords[5][1]) + 1) > 0.75 and
            coords[5][1] > coords[6][1] > coords[7][1] > coords[8][1] and coords[9][1] > coords[10][1] > coords[11][1] > coords[12][1] and
            coords[13][1] > coords[14][1] > coords[15][1] > coords[16][1] and coords[17][1] > coords[18][1] > coords[19][1] > coords[20][1]):
            direction = 'stop'
            speed = 0
            speed_flag = True
            move()
        # Жест движения вверх
        elif (take_off_flag and coords[8][1] < coords[7][1] < coords[6][1] < coords[5][1] and
            coords[11][1] > coords[8][1] and coords[15][1] > coords[8][1] and coords[19][1] > coords[8][1] and
            abs(coords[8][0] - coords[5][0]) / (abs(coords[8][1] - coords[5][1]) + 1) < 0.2 and
            abs(coords[5][1] - coords[8][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[8][1] - coords[6][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[12][1] - coords[10][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[16][1] - coords[14][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[20][1] - coords[18][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            ((coords[4][0] > coords[3][0] and coords[5][0] < coords[17][0]) or (coords[4][0] < coords[3][0] and coords[5][0] > coords[17][0]))):
            direction = 'up'
            speed = 0
            speed_flag = True
        # Жест движения вниз
        elif (take_off_flag and coords[8][1] > coords[7][1] > coords[6][1] > coords[5][1] and
            coords[11][1] < coords[8][1] and coords[15][1] < coords[8][1] and coords[19][1] < coords[8][1] and
            abs(coords[8][0] - coords[5][0]) / (abs(coords[8][1] - coords[5][1]) + 1) < 0.2 and
            abs(coords[5][1] - coords[8][1]) / (abs(coords[17][1] - coords[0][1]) + 1) > 0.9 and
            abs(coords[8][1] - coords[6][1]) / (abs(coords[18][1] - coords[17][1]) + 1) > 0.9 and
            abs(coords[12][1] - coords[10][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[16][1] - coords[14][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            abs(coords[20][1] - coords[18][1]) / (abs(coords[8][1] - coords[6][1]) + 1) < 0.9 and
            ((coords[4][0] > coords[3][0] and coords[5][0] < coords[17][0]) or (coords[4][0] < coords[3][0] and coords[5][0] > coords[17][0]))):
            direction = 'down'
            speed = 0
            speed_flag = True
        # Жест вращения по часовой стрелке для правой руки
        elif (take_off_flag and coords[8][0] < coords[7][0] < coords[6][0] < coords[5][0] and coords[4][0] > coords[6][0] and
            coords[11][0] > coords[8][0] and coords[15][0] > coords[8][0] and coords[19][0] > coords[8][0] and
            abs(coords[8][1] - coords[5][1]) / (abs(coords[8][0] - coords[5][0]) + 1) < 0.2 and
            abs(coords[5][0] - coords[8][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[12][0] < coords[11][0] < coords[10][0] < coords[9][0] and coords[4][1] < coords[10][1] and
            coords[11][0] > coords[12][0] and coords[15][0] > coords[12][0] and coords[19][0] > coords[12][0] and
            abs(coords[12][1] - coords[9][1]) / (abs(coords[12][0] - coords[9][0]) + 1) < 0.2 and
            abs(coords[9][0] - coords[12][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[4][0] > coords[7][0] and coords[12][0] < coords[7][0] and direction not in ['rotate clockwise', 'rotate counter-clockwise'] and
            abs(coords[8][0] - coords[5][0]) / (((coords[5][0] - coords[17][0]) ** 2 + (coords[5][1] - coords[17][1]) ** 2) ** 0.5 + 1) > 0.75):
            direction = 'rotate clockwise'
            speed = 0
            speed_flag = True
            move()
        # Жест вращения против часовой стрелки для правой руки
        elif (take_off_flag and coords[8][0] < coords[7][0] < coords[6][0] < coords[5][0] and coords[4][0] > coords[6][0] and
            coords[11][0] > coords[8][0] and coords[15][0] > coords[8][0] and coords[19][0] > coords[8][0] and
            abs(coords[8][1] - coords[5][1]) / (abs(coords[8][0] - coords[5][0]) + 1) < 0.2 and
            abs(coords[5][0] - coords[8][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[11][0] > coords[7][0] and coords[12][0] > coords[7][0] and coords[4][1] < coords[10][1] and
            abs(coords[8][0] - coords[5][0]) / (((coords[5][0] - coords[17][0]) ** 2 + (coords[5][1] - coords[17][1]) ** 2) ** 0.5 + 1) > 0.75 and
            coords[4][0] > coords[7][0] and direction not in ['rotate clockwise', 'rotate counter-clockwise']):
            direction = 'rotate counter-clockwise'
            speed = 0
            speed_flag = True
            move()
        # Жест вращения против часовой стрелки для левой руки
        elif (take_off_flag and coords[8][0] > coords[7][0] > coords[6][0] > coords[5][0] and coords[4][0] < coords[6][0] and
            coords[11][0] < coords[8][0] and coords[15][0] < coords[8][0] and coords[19][0] < coords[8][0] and
            abs(coords[8][1] - coords[5][1]) / (abs(coords[8][0] - coords[5][0]) + 1) < 0.2 and
            abs(coords[5][0] - coords[8][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[12][0] > coords[11][0] > coords[10][0] > coords[9][0] and coords[4][1] < coords[10][1] and
            coords[11][0] < coords[12][0] and coords[15][0] < coords[12][0] and coords[19][0] < coords[12][0] and
            abs(coords[12][1] - coords[9][1]) / (abs(coords[12][0] - coords[9][0]) + 1) < 0.2 and
            abs(coords[9][0] - coords[12][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[4][0] < coords[7][0] and coords[12][0] > coords[7][0] and direction not in ['rotate clockwise', 'rotate counter-clockwise'] and
            abs(coords[8][0] - coords[5][0]) / (((coords[5][0] - coords[17][0]) ** 2 + (coords[5][1] - coords[17][1]) ** 2) ** 0.5 + 1) > 0.75):
            direction = 'rotate counter-clockwise'
            speed = 0
            speed_flag = True
            move()
        # Жест вращения по часовой стрелке для левой руки
        elif (take_off_flag and coords[8][0] > coords[7][0] > coords[6][0] > coords[5][0] and coords[4][0] < coords[6][0] and
            coords[11][0] < coords[8][0] and coords[15][0] < coords[8][0] and coords[19][0] < coords[8][0] and
            abs(coords[8][1] - coords[5][1]) / (abs(coords[8][0] - coords[5][0]) + 1) < 0.2 and
            abs(coords[5][0] - coords[8][0]) / (abs(coords[5][0] - coords[0][0]) + 1) > 0.9 and
            coords[11][0] < coords[7][0] and coords[12][0] < coords[7][0] and coords[4][1] < coords[10][1] and
            abs(coords[8][0] - coords[5][0]) / (((coords[5][0] - coords[17][0]) ** 2 + (coords[5][1] - coords[17][1]) ** 2) ** 0.5 + 1) > 0.75 and
            coords[4][0] < coords[7][0] and direction not in ['rotate clockwise', 'rotate counter-clockwise']):
            direction = 'rotate clockwise'
            speed = 0
            speed_flag = True
            move()
        # Жест скорости для правой руки
        elif (take_off_flag and coords[4][0] < coords[3][0] < coords[2][0] < coords[5][0] and coords[4][0] < coords[9][0] and
            0.9 < (((coords[8][0] - coords[7][0]) ** 2 + (coords[8][1] - coords[7][1]) ** 2) ** 0.5 + ((coords[7][0] - coords[6][0]) ** 2 + (coords[7][1] - coords[6][1]) ** 2) ** 0.5 + ((coords[6][0] - coords[5][0]) ** 2 + (coords[6][1] - coords[5][1]) ** 2) ** 0.5) / (((coords[8][0] - coords[5][0]) ** 2 + (coords[8][1] - coords[5][1]) ** 2) ** 0.5 + 1) < 1.1 and
            0.9 < (((coords[4][0] - coords[3][0]) ** 2 + (coords[4][1] - coords[3][1]) ** 2) ** 0.5 + ((coords[3][0] - coords[2][0]) ** 2 + (coords[3][1] - coords[2][1]) ** 2) ** 0.5) / (((coords[4][0] - coords[2][0]) ** 2 + (coords[4][1] - coords[2][1]) ** 2) ** 0.5 + 1) < 1.1 and
            0.6 < ((coords[4][0] - coords[3][0]) ** 2 + (coords[4][1] - coords[3][1]) ** 2) ** 0.5 / (((coords[3][0] - coords[2][0]) ** 2 + (coords[3][1] - coords[2][1]) ** 2) ** 0.5 + 1) < 1.2 and
            coords[6][1] < coords[10][1] and coords[6][1] < coords[14][1] and coords[6][1] < coords[18][1] and
            (coords[8][0] < coords[3][0] or (coords[8][0] >= coords[3][0] and coords[8][1] < coords[7][1] < coords[6][1] < coords[5][1])) and
            direction not in ['land', 'take off', 'stop', 'none', 'rotate clockwise', 'rotate counter-clockwise']):
            cv.circle(image, (coords[4][0], coords[4][1]),15, (255, 0, 255), cv.FILLED)
            cv.circle(image, (coords[8][0], coords[8][1]), 15, (255, 0, 255), cv.FILLED)
            cv.line(image, (coords[4][0], coords[4][1]), (coords[8][0], coords[8][1]), (255, 0, 255), 3)
            s24 = ((coords[2][0] - coords[4][0]) ** 2 + (coords[2][1] - coords[4][1]) ** 2) ** 0.5
            s28 = ((coords[2][0] - coords[8][0]) ** 2 + (coords[2][1] - coords[8][1]) ** 2) ** 0.5
            s48 = ((coords[4][0] - coords[8][0]) ** 2 + (coords[4][1] - coords[8][1]) ** 2) ** 0.5
            cos = (s24 ** 2 + s28 ** 2 - s48 ** 2) / (2 * s24 * s28 + 1)
            if 1 > cos > 0:
                speed_now = (1 - cos) * max_speed * 1.1
                if speed_flag is True and speed_now // 10 * 10 == 0:
                    speed_flag = False
                if (speed_now // 10 * 10 > speed or speed_now // 10 * 10 < speed) and speed_flag is False:
                    speed = speed_now // 10 * 10
            move()
        # Жест скорости для левой руки
        elif (take_off_flag and coords[4][0] > coords[3][0] > coords[2][0] > coords[5][0] and coords[4][0] > coords[9][0] and
            0.9 < (((coords[8][0] - coords[7][0]) ** 2 + (coords[8][1] - coords[7][1]) ** 2) ** 0.5 + ((coords[7][0] - coords[6][0]) ** 2 + (coords[7][1] - coords[6][1]) ** 2) ** 0.5 + ((coords[6][0] - coords[5][0]) ** 2 + (coords[6][1] - coords[5][1]) ** 2) ** 0.5) / (((coords[8][0] - coords[5][0]) ** 2 + (coords[8][1] - coords[5][1]) ** 2) ** 0.5 + 1) < 1.1 and
            0.9 < (((coords[4][0] - coords[3][0]) ** 2 + (coords[4][1] - coords[3][1]) ** 2) ** 0.5 + ((coords[3][0] - coords[2][0]) ** 2 + (coords[3][1] - coords[2][1]) ** 2) ** 0.5) / (((coords[4][0] - coords[2][0]) ** 2 + (coords[4][1] - coords[2][1]) ** 2) ** 0.5 + 1) < 1.1 and
            0.6 < ((coords[4][0] - coords[3][0]) ** 2 + (coords[4][1] - coords[3][1]) ** 2) ** 0.5 / (((coords[3][0] - coords[2][0]) ** 2 + (coords[3][1] - coords[2][1]) ** 2) ** 0.5 + 1) < 1.2 and
            coords[6][1] < coords[10][1] and coords[6][1] < coords[14][1] and coords[6][1] < coords[18][1] and
            (coords[8][0] > coords[3][0] or (coords[8][0] <= coords[3][0] and coords[8][1] < coords[7][1] < coords[6][1] < coords[5][1])) and
            direction not in ['land', 'take off', 'stop', 'none']):
            cv.circle(image, (coords[4][0], coords[4][1]),15, (255, 0, 255), cv.FILLED)
            cv.circle(image, (coords[8][0], coords[8][1]), 15, (255, 0, 255), cv.FILLED)
            cv.line(image, (coords[4][0], coords[4][1]), (coords[8][0], coords[8][1]), (255, 0, 255), 3)
            s24 = ((coords[2][0] - coords[4][0]) ** 2 + (coords[2][1] - coords[4][1]) ** 2) ** 0.5
            s28 = ((coords[2][0] - coords[8][0]) ** 2 + (coords[2][1] - coords[8][1]) ** 2) ** 0.5
            s48 = ((coords[4][0] - coords[8][0]) ** 2 + (coords[4][1] - coords[8][1]) ** 2) ** 0.5
            cos = (s24 ** 2 + s28 ** 2 - s48 ** 2) / (2 * s24 * s28 + 1)
            if 1 > cos > 0:
                speed_now = (1 - cos) * max_speed * 1.1
                if speed_flag is True and speed_now // 10 * 10 == 0:
                    speed_flag = False
                if (speed_now // 10 * 10 > speed or speed_now // 10 * 10 < speed) and speed_flag is False:
                    speed = speed_now // 10 * 10
            move()
    else:
        direction = 'none'
        speed = 0
        speed_flag = True

    # Вычисление фпс
    cTime = time.time()
    fps = 1/(cTime - pTime)
    pTime = cTime

    # Вывод на экран камеры и вспомогательной информации
    cv.putText(image, f'fps: {str(int(fps))}', (10, 30), cv.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 255), 3)
    cv.putText(image, f'direction: {direction}', (10, 60), cv.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 255), 3)
    cv.putText(image, f'speed: {str(int(speed))}', (10, 90), cv.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 255), 3)
    cv.putText(image, f'rotate angle: {str(rotate_angle)}', (10, 120), cv.FONT_HERSHEY_TRIPLEX, 1, (255, 0, 255), 3)
    cv.imshow('Image', image)
    cv.waitKey(1)

    # Кадрирование изображения с камеры дрона, его вывод
    frame = me.get_frame_read().frame
    p = 0.5
    w = int(frame.shape[1] * p)
    h = int(frame.shape[0] * p)
    frame = cv.resize(frame, (w, h))
    cv.imshow('Drone cam', frame)
    cv.waitKey(1)
