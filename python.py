import pygame
import math

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Robot autonome + LiDAR + Évitement intelligent + Détection des bords")
clock = pygame.time.Clock()

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
YELLOW = (255, 255, 0)

# Robot paramètres
robot_pos = [400, 300]
robot_angle = 0  # degrés
speed = 2.0
turn_speed = 3.0  # degrés par frame
avoidance_threshold = 60
robot_size = 10  # taille du triangle

# Variables d'évitement intelligent
avoid_turning = False
avoid_direction = None  # 'left' ou 'right'
avoid_frames = 0

# Obstacles
obstacles = [
    pygame.Rect(300, 200, 100, 50),
    pygame.Rect(500, 400, 120, 60),
    pygame.Rect(600, 100, 50, 200)
]

# LiDAR
angle_step = 5
ray_length = 150

font = pygame.font.SysFont(None, 24)

def get_robot_points(pos, angle, size):
    rad = math.radians(angle)
    front = (pos[0] + size * math.cos(rad), pos[1] + size * math.sin(rad))
    left = (pos[0] + size * math.cos(rad + 2.5), pos[1] + size * math.sin(rad + 2.5))
    right = (pos[0] + size * math.cos(rad - 2.5), pos[1] + size * math.sin(rad - 2.5))
    return [front, left, right]

def check_collision(poly_points, rect):
    poly_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
    pygame.draw.polygon(poly_surf, (255, 255, 255), poly_points)
    poly_mask = pygame.mask.from_surface(poly_surf)

    rect_surf = pygame.Surface((rect.width, rect.height))
    rect_surf.fill((255, 255, 255))
    rect_mask = pygame.mask.from_surface(rect_surf)

    offset = (int(rect.left), int(rect.top))
    overlap = poly_mask.overlap(rect_mask, offset)
    return overlap is not None

def cast_ray(pos, angle):
    x, y = pos
    rad = math.radians(angle)
    for dist in range(ray_length):
        rx = x + dist * math.cos(rad)
        ry = y + dist * math.sin(rad)
        point = (rx, ry)
        for obs in obstacles:
            if obs.collidepoint(point):
                return point, dist
    end_x = x + ray_length * math.cos(rad)
    end_y = y + ray_length * math.sin(rad)
    return (end_x, end_y), ray_length

def draw_text(text, pos, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, pos)

import sys

running = True
while running:
    screen.fill(BLACK)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                speed = min(speed + 0.1, 10)
            elif event.key == pygame.K_s:
                speed = max(speed - 0.1, 0)
            elif event.key == pygame.K_a:
                turn_speed = max(turn_speed - 0.1, 0.1)
            elif event.key == pygame.K_d:
                turn_speed = min(turn_speed + 0.1, 10)
            elif event.key == pygame.K_q:
                avoidance_threshold = max(avoidance_threshold - 1, 10)
            elif event.key == pygame.K_e:
                avoidance_threshold = min(avoidance_threshold + 1, 150)

    # LiDAR 360°
    distances = []
    angles = list(range(0, 360, angle_step))

    for a in angles:
        global_angle = (robot_angle + a) % 360
        hit_point, dist = cast_ray(robot_pos, global_angle)
        distances.append((a, dist, hit_point))
        if dist < avoidance_threshold / 2:
            color = RED
        elif dist < avoidance_threshold:
            color = YELLOW
        else:
            color = GREEN
        pygame.draw.line(screen, color, robot_pos, hit_point, 1)

    # Analyse des distances
    front_angles = [d for d in distances if d[0] >= 330 or d[0] <= 30]
    left_angles = [d for d in distances if 60 <= d[0] <= 120]
    right_angles = [d for d in distances if 240 <= d[0] <= 300]

    min_front_dist = min(front_angles, key=lambda x: x[1])[1]
    min_left_dist = min(left_angles, key=lambda x: x[1])[1]
    min_right_dist = min(right_angles, key=lambda x: x[1])[1]

    # --- Logique d'évitement améliorée ---
    if avoid_turning:
        # Continue à tourner pendant un certain temps
        if avoid_direction == 'left':
            robot_angle += turn_speed
        else:
            robot_angle -= turn_speed

        rad = math.radians(robot_angle)
        robot_pos[0] += speed * math.cos(rad)
        robot_pos[1] += speed * math.sin(rad)
        avoid_frames -= 1
        if avoid_frames <= 0:
            avoid_turning = False

    elif min_front_dist < avoidance_threshold:
        # Commence une manœuvre d'évitement
        avoid_turning = True
        if min_left_dist > min_right_dist:
            avoid_direction = 'left'
        else:
            avoid_direction = 'right'
        avoid_frames = 30  # durée de la manœuvre

    else:
        # Mouvement normal
        rad = math.radians(robot_angle)
        new_pos = [robot_pos[0] + speed * math.cos(rad),
                   robot_pos[1] + speed * math.sin(rad)]
        new_points = get_robot_points(new_pos, robot_angle, robot_size)
        collision = any(check_collision(new_points, obs) for obs in obstacles)

        if not collision:
            robot_pos = new_pos
        else:
            # recule légèrement en cas de collision
            robot_pos[0] -= speed * math.cos(rad)
            robot_pos[1] -= speed * math.sin(rad)
            robot_angle += 20  # tourne un peu

    # --- Gestion du franchissement des bords ---
    # Si le robot sort d'un bord, il réapparaît de l'autre côté (tore)
    if robot_pos[0] < 0:
        robot_pos[0] = 800
    elif robot_pos[0] > 800:
        robot_pos[0] = 0

    if robot_pos[1] < 0:
        robot_pos[1] = 600
    elif robot_pos[1] > 600:
        robot_pos[1] = 0

    # Dessin des obstacles
    for obs in obstacles:
        pygame.draw.rect(screen, BLUE, obs)

    # Dessin du robot
    points = get_robot_points(robot_pos, robot_angle, robot_size)
    pygame.draw.polygon(screen, WHITE, points)

    # Affichage texte
    draw_text(f"Position: ({int(robot_pos[0])}, {int(robot_pos[1])})", (10, 10))
    draw_text(f"Angle: {int(robot_angle) % 360}°", (10, 30))
    draw_text(f"Vitesse: {speed:.1f} px/frame (W/S)", (10, 50))
    draw_text(f"Rotation: {turn_speed:.1f}°/frame (A/D)", (10, 70))
    draw_text(f"Seuil évitement: {avoidance_threshold}px (Q/E)", (10, 90))
    draw_text("Commandes: W/S=+/- vitesse, A/D=+/- rotation, Q/E=+/- seuil évitement", (10, 570))

    pygame.display.update()
    clock.tick(60)

pygame.quit()