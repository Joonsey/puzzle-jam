import pygame
import math

def check_collision(rect: tuple[float, float, float, float], other_rect: tuple[float, float, float, float]) -> bool:
    x1, y1, w1, h1 = rect
    x2, y2, w2, h2 = other_rect

    overlap_x = (x1 < x2 + w2) and (x2 < x1 + w1)
    overlap_y = (y1 < y2 + h2) and (y2 < y1 + h1)
    return overlap_x and overlap_y


def lerp(a: float, b: float, f: float):
    return a * (1.0 - f) + (b * f)


def inverted(img: pygame.Surface):
   inv = pygame.Surface(img.get_rect().size, pygame.SRCALPHA)
   inv.fill((255, 255, 255, 255))
   inv.blit(img, (0, 0), None, pygame.BLEND_RGB_SUB)
   return inv


def outline(surf: pygame.Surface, dest: pygame.Surface, loc: tuple[int, int], depth: int = 1) -> None:
    temp_surf = surf.copy()
    inverted_surf = inverted(temp_surf)
    inverted_surf.set_colorkey((255, 255, 255))
    dest.blit(inverted_surf, (loc[0]-depth, loc[1]))
    dest.blit(inverted_surf, (loc[0]+depth, loc[1]))
    dest.blit(inverted_surf, (loc[0], loc[1]-depth))
    dest.blit(inverted_surf, (loc[0], loc[1]+depth))
    temp_surf.set_colorkey((0, 0, 0))
    dest.blit(temp_surf, (0, 0))


def render_stack(surf: pygame.Surface, images: list[pygame.Surface], pos: pygame.Vector2, rotation: int):
    count = len(images)
    for i, img in enumerate(images):
        rotated_img = pygame.transform.rotate(img, rotation)
        surf.blit(rotated_img, (pos.x - rotated_img.get_width() // 2 +
                  count, pos.y - rotated_img.get_height() // 2 - i + count))

def is_within_radius(center1: tuple[float, float], center2: tuple[float, float], radius: float):
    distance = math.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)
    return distance <= radius

def get_distance(start: tuple[float, float], target: tuple[float, float]) -> float:
    return math.sqrt((start[0] - target[0])**2 + (start[1] - target[1])**2)

def gaussian_value(midpoint: tuple[float, float], position: tuple[float, float], sigma: float):
    distance = math.sqrt((position[0] - midpoint[0])**2 + (position[1] - midpoint[1])**2)
    value = math.exp(-distance**2 / (2 * sigma**2))
    return value
