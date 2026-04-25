"""
╔══════════════════════════════════════════════════════════════╗
║              GORGON'S REALM - Prototipo 2D                  ║
║                                                              ║
║  Personaje : Gorgona mitológica (cola de serpiente)          ║
║  Patrón    : Decorador estructural para efectos de Orbe      ║
║  Orbes     : Speed, Jump, Shield (20-60 seg random)          ║
╚══════════════════════════════════════════════════════════════╝

Estructura de archivos esperada:
  gorgon_game.py          ← este archivo
  assets/
    sprites/
      Idle.png            ← 7 frames, 128x128 c/u
      Idle_2.png          ← 5 frames, 128x128 c/u  (animación de salto)
      Walk.png            ← 13 frames, 128x128 c/u
      Run.png             ← 7 frames, 128x128 c/u

Controles:
  ← / →        Caminar
  Shift + ←/→  Correr
  Espacio       Saltar
  ESC           Salir
"""

import pygame
import sys
import random
import math
import os
import abc
from typing import Optional

# ─────────────────────────────────────────────
#  CONSTANTES GLOBALES
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1100, 620
FPS = 60
GRAVITY = 0.55
TITLE = "Gorgona - Patrón Decorador"

# Ruta base de sprites (relativa al script)
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(BASE_DIR, "assets", "sprites")

# Paleta de colores
C_BG_TOP    = (15,  10,  30)
C_BG_BOT    = (35,  20,  55)
C_PLATFORM  = (60,  40,  80)
C_PLAT_TOP  = (100, 65, 110)
C_PLAT_SIDE = (40,  25,  55)
C_UI_BG     = (10,  6,  20, 180)
C_WHITE     = (255, 255, 255)
C_GOLD      = (255, 210,  60)
C_RED       = (220,  60,  60)
C_GREEN     = (80,  200, 100)
C_BLUE      = (80,  140, 240)
C_SHIELD    = (100, 200, 255, 90)

# Colores de orbes
ORB_COLORS = {
    "speed_boost":  (255, 140,  30),
    "speed_slow":   ( 80,  80, 200),
    "jump_super":   (180, 255,  80),
    "jump_none":    (180,  40,  40),
    "shield":       (100, 200, 255),
}

ORB_NAMES = {
    "speed_boost": "¡VELOCIDAD!",
    "speed_slow":  "LENTITUD...",
    "jump_super":  "¡SÚPER SALTO!",
    "jump_none":   "SIN SALTO",
    "shield":      "¡ESCUDO!",
}


class CharacterStats(abc.ABC):
    """Interfaz base que todo decorador y componente concreto debe cumplir."""

    @abc.abstractmethod
    def get_speed(self) -> float: ...

    @abc.abstractmethod
    def get_jump_force(self) -> float: ...

    @abc.abstractmethod
    def can_jump(self) -> bool: ...

    @abc.abstractmethod
    def has_shield(self) -> bool: ...


class BaseStats(CharacterStats):
    """Componente concreto: estadísticas base de la Gorgona sin modificaciones."""

    BASE_SPEED      = 3.5
    BASE_JUMP_FORCE = -13.0

    def get_speed(self)      -> float: return self.BASE_SPEED
    def get_jump_force(self) -> float: return self.BASE_JUMP_FORCE
    def can_jump(self)       -> bool:  return True
    def has_shield(self)     -> bool:  return False


class OrbDecorator(CharacterStats):
    """
    Decorador abstracto.
    Mantiene referencia al componente envuelto (wrappee) y delega
    todos los métodos por defecto, permitiendo que cada orbe
    sobreescriba sólo lo que le corresponde.
    """

    def __init__(self, wrappee: CharacterStats, duration: float):
        self._wrappee  = wrappee
        self.duration  = duration          # segundos totales del efecto
        self.remaining = duration          # tiempo restante

    # Delegación por defecto ──────────────────
    def get_speed(self)      -> float: return self._wrappee.get_speed()
    def get_jump_force(self) -> float: return self._wrappee.get_jump_force()
    def can_jump(self)       -> bool:  return self._wrappee.can_jump()
    def has_shield(self)     -> bool:  return self._wrappee.has_shield()

    def tick(self, dt: float) -> bool:
        """Actualiza el temporizador. Retorna True si el efecto expiró."""
        self.remaining -= dt
        return self.remaining <= 0

    @property
    def progress(self) -> float:
        """Fracción de tiempo restante [0..1]."""
        return max(0.0, self.remaining / self.duration)

    @abc.abstractmethod
    def orb_type(self) -> str: ...

    @abc.abstractmethod
    def label(self) -> str: ...

    @abc.abstractmethod
    def color(self) -> tuple: ...


# ── Decoradores concretos ─────────────────────

class SpeedBoostOrb(OrbDecorator):
    """Aumenta la velocidad de movimiento × 1.8."""
    MULTIPLIER = 1.8

    def get_speed(self) -> float:
        return self._wrappee.get_speed() * self.MULTIPLIER

    def orb_type(self) -> str: return "speed_boost"
    def label(self)    -> str: return ORB_NAMES["speed_boost"]
    def color(self)    -> tuple: return ORB_COLORS["speed_boost"]


class SpeedSlowOrb(OrbDecorator):
    """Reduce la velocidad de movimiento × 0.45."""
    MULTIPLIER = 0.45

    def get_speed(self) -> float:
        return self._wrappee.get_speed() * self.MULTIPLIER

    def orb_type(self) -> str: return "speed_slow"
    def label(self)    -> str: return ORB_NAMES["speed_slow"]
    def color(self)    -> tuple: return ORB_COLORS["speed_slow"]


class SuperJumpOrb(OrbDecorator):
    """Potencia el salto × 1.65 (fuerza negativa → más negativa)."""
    MULTIPLIER = 1.65

    def get_jump_force(self) -> float:
        return self._wrappee.get_jump_force() * self.MULTIPLIER

    def orb_type(self) -> str: return "jump_super"
    def label(self)    -> str: return ORB_NAMES["jump_super"]
    def color(self)    -> tuple: return ORB_COLORS["jump_super"]


class NoJumpOrb(OrbDecorator):
    """Deshabilita por completo la capacidad de salto."""

    def can_jump(self) -> bool: return False

    def orb_type(self) -> str: return "jump_none"
    def label(self)    -> str: return ORB_NAMES["jump_none"]
    def color(self)    -> tuple: return ORB_COLORS["jump_none"]


class ShieldOrb(OrbDecorator):
    """Agrega un escudo visual (y lógico) al personaje."""

    def has_shield(self) -> bool: return True

    def orb_type(self) -> str: return "shield"
    def label(self)    -> str: return ORB_NAMES["shield"]
    def color(self)    -> tuple: return ORB_COLORS["shield"]


# Mapa de fábrica para crear orbes aleatoriamente
ORB_FACTORY = [SpeedBoostOrb, SpeedSlowOrb, SuperJumpOrb, NoJumpOrb, ShieldOrb]

#  ANIMACIÓN DE SPRITES

class SpriteAnimation:
    """Carga y reproduce un spritesheet horizontal con frames de igual ancho."""

    def __init__(self, path: str, frame_count: int,
                 frame_w: int = 128, frame_h: int = 128,
                 fps: float = 10.0):
        self.fps         = fps
        self.frame_count = frame_count
        self._timer      = 0.0
        self.current     = 0
        self.frames: list[pygame.Surface] = []

        sheet = pygame.image.load(path).convert_alpha()
        for i in range(frame_count):
            rect   = pygame.Rect(i * frame_w, 0, frame_w, frame_h)
            frame  = sheet.subsurface(rect).copy()
            self.frames.append(frame)

    def update(self, dt: float):
        self._timer += dt
        if self._timer >= 1.0 / self.fps:
            self._timer  = 0.0
            self.current = (self.current + 1) % self.frame_count

    def reset(self):
        self.current = 0
        self._timer  = 0.0

    def get_frame(self) -> pygame.Surface:
        return self.frames[self.current]


#  GORGONA — PERSONAJE PRINCIPAL

class Gorgon:
    FRAME_W     = 128
    FRAME_H     = 128
    SCALE       = 1.5          # tamaño en pantalla ×1.5
    COLL_W      = 48           # hitbox más estrecha que el sprite
    COLL_H      = 90

    def __init__(self, x: float, y: float):
        self.x      = float(x)
        self.y      = float(y)
        self.vel_x  = 0.0
        self.vel_y  = 0.0
        self.facing = 1          # 1 = derecha, -1 = izquierda
        self.on_ground = False
        self.is_running = False

        # Estado del decorador (pila de efectos activos)
        self._base_stats: CharacterStats = BaseStats()
        self._active_orbs: list[OrbDecorator] = []

        # Cache de stats efectivas
        self._effective: CharacterStats = self._base_stats

        # Cargar animaciones
        self.anims = {
            "idle":  SpriteAnimation(os.path.join(SPRITE_DIR, "Idle.png"),   7,  fps=9),
            "idle2": SpriteAnimation(os.path.join(SPRITE_DIR, "Idle_2.png"), 5,  fps=9),
            "walk":  SpriteAnimation(os.path.join(SPRITE_DIR, "Walk.png"),   13, fps=13),
            "run":   SpriteAnimation(os.path.join(SPRITE_DIR, "Run.png"),    7,  fps=14),
        }
        self._current_anim = "idle"

        # Orbe flotante visual (el que está "en el mundo")
        self.world_orbs: list["WorldOrb"] = []

        # Notificación de efecto activo
        self.effect_label: str = ""
        self.effect_color: tuple = C_WHITE
        self.effect_timer: float = 0.0

        # Escudo visual
        self._shield_pulse = 0.0

    # ── Propiedades físicas derivadas ─────────
    @property
    def speed(self)      -> float: return self._effective.get_speed()
    @property
    def jump_force(self) -> float: return self._effective.get_jump_force()
    @property
    def can_jump(self)   -> bool:  return self._effective.can_jump()
    @property
    def has_shield(self) -> bool:  return self._effective.has_shield()

    # ── Colisión (rect en píxeles de pantalla) ─
    @property
    def rect(self) -> pygame.Rect:
        sw = int(self.FRAME_W * self.SCALE)
        sh = int(self.FRAME_H * self.SCALE)
        cx = int(self.x) + sw // 2 - self.COLL_W // 2
        cy = int(self.y) + sh - self.COLL_H
        return pygame.Rect(cx, cy, self.COLL_W, self.COLL_H)

    # ── Aplicar orbe ──────────────────────────
    def apply_orb(self, orb_class):
        duration = random.uniform(20, 60)
        new_orb  = orb_class(self._base_stats, duration)
        self._active_orbs.append(new_orb)
        self._rebuild_stack()

        self.effect_label = new_orb.label()
        self.effect_color = new_orb.color()
        self.effect_timer = 3.0          # mostrar notificación 3 seg

    def _rebuild_stack(self):
        """Reconstruye la cadena de decoradores sobre BaseStats."""
        stats: CharacterStats = self._base_stats
        for orb in self._active_orbs:
            orb._wrappee = stats
            stats = orb
        self._effective = stats

    # ── Update ────────────────────────────────
    def update(self, dt: float, platforms: list[pygame.Rect]):
        keys = pygame.key.get_pressed()

        # Velocidad horizontal
        move = keys[pygame.K_d] - keys[pygame.K_a]
        self.is_running = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and move != 0
        run_mult = 1.9 if self.is_running else 1.0

        self.vel_x = move * self.speed * run_mult
        if move != 0:
            self.facing = move

        # Salto
        if keys[pygame.K_SPACE] and self.on_ground and self.can_jump:
            self.vel_y = self.jump_force

        # Gravedad
        self.vel_y += GRAVITY
        self.vel_y  = min(self.vel_y, 20)

        # Mover en X
        self.x += self.vel_x
        # Límites laterales
        sw = int(self.FRAME_W * self.SCALE)
        self.x = max(0, min(self.x, SCREEN_W - sw))

        # Mover en Y y colisionar con plataformas
        self.y += self.vel_y
        self.on_ground = False
        r = self.rect

        for plat in platforms:
            if r.colliderect(plat):
                # Venía desde arriba
                if self.vel_y > 0 and r.bottom - self.vel_y <= plat.top + 4:
                    # Ajustar posición Y
                    diff     = r.bottom - plat.top
                    self.y  -= diff
                    self.vel_y  = 0
                    self.on_ground = True

        # Suelo absoluto (por si cae fuera)
        floor = SCREEN_H - 80
        sw_h  = int(self.FRAME_H * self.SCALE)
        if self.y + sw_h > floor:
            self.y     = floor - sw_h
            self.vel_y = 0
            self.on_ground = True

        # Actualizar animación
        if not self.on_ground:
            anim = "idle2"
        elif abs(self.vel_x) > 0.1:
            anim = "run" if self.is_running else "walk"
        else:
            anim = "idle"

        if anim != self._current_anim:
            self.anims[anim].reset()
            self._current_anim = anim
        self.anims[self._current_anim].update(dt)

        # Actualizar orbes activos
        expired = []
        for orb in self._active_orbs:
            if orb.tick(dt):
                expired.append(orb)
        for orb in expired:
            self._active_orbs.remove(orb)
        if expired:
            self._rebuild_stack()

        # Temporizador de notificación
        if self.effect_timer > 0:
            self.effect_timer -= dt

        # Escudo pulso
        self._shield_pulse = (self._shield_pulse + dt * 3) % (2 * math.pi)

        # Colisionar con orbes del mundo
        to_collect = []
        for worb in self.world_orbs:
            worb.update(dt)
            if self.rect.colliderect(worb.rect):
                to_collect.append(worb)
        for worb in to_collect:
            self.world_orbs.remove(worb)
            self.apply_orb(worb.orb_class)

    # ── Dibujar ───────────────────────────────
    def draw(self, surface: pygame.Surface):
        frame = self.anims[self._current_anim].get_frame()
        sw    = int(self.FRAME_W * self.SCALE)
        sh    = int(self.FRAME_H * self.SCALE)
        scaled = pygame.transform.scale(frame, (sw, sh))

        if self.facing == -1:
            scaled = pygame.transform.flip(scaled, True, False)

        # Escudo visual
        if self.has_shield:
            cx = int(self.x) + sw // 2
            cy = int(self.y) + sh // 2
            r  = int(40 + 4 * math.sin(self._shield_pulse))
            shield_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (100, 200, 255, 55), (r, r), r)
            pygame.draw.circle(shield_surf, (150, 220, 255, 120), (r, r), r, 3)
            surface.blit(shield_surf, (cx - r, cy - r))

        surface.blit(scaled, (int(self.x), int(self.y)))

        # Orbes del mundo
        for worb in self.world_orbs:
            worb.draw(surface)


#  ORBE EN EL MUNDO (objeto recolectable)

class WorldOrb:
    RADIUS = 16

    def __init__(self, x: float, y: float, orb_class):
        self.x         = x
        self.y         = y
        self.orb_class = orb_class
        self._bob      = random.uniform(0, math.pi * 2)   # fase inicial
        self._bob_t    = 0.0
        self._rot      = 0.0

        # Color según tipo
        temp         = orb_class(BaseStats(), 1)
        self.color   = temp.color()
        self.label   = temp.label()

        # Partículas de brillo
        self._sparks = [
            {"angle": random.uniform(0, 2*math.pi),
             "dist":  random.uniform(14, 22),
             "speed": random.uniform(0.5, 1.5)}
            for _ in range(5)
        ]

    @property
    def rect(self) -> pygame.Rect:
        r = self.RADIUS
        return pygame.Rect(self.x - r, self.y - r + self._bob_offset, r*2, r*2)

    @property
    def _bob_offset(self) -> float:
        return math.sin(self._bob_t) * 6

    def update(self, dt: float):
        self._bob_t += dt * 2.5
        self._rot   = (self._rot + dt * 90) % 360
        for sp in self._sparks:
            sp["angle"] = (sp["angle"] + dt * sp["speed"]) % (2*math.pi)

    def draw(self, surface: pygame.Surface):
        yoff = self._bob_offset
        cx, cy = int(self.x), int(self.y + yoff)
        r  = self.RADIUS

        # Halo exterior
        halo = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*self.color, 40), (r*2, r*2), r*2)
        surface.blit(halo, (cx - r*2, cy - r*2))

        # Cuerpo principal
        pygame.draw.circle(surface, self.color, (cx, cy), r)
        # Brillo interior
        bright = tuple(min(255, c + 80) for c in self.color)
        pygame.draw.circle(surface, bright, (cx - r//4, cy - r//4), r//3)

        # Borde
        pygame.draw.circle(surface, C_WHITE, (cx, cy), r, 2)

        # Chispas orbitales
        for sp in self._sparks:
            sx = cx + int(math.cos(sp["angle"]) * sp["dist"])
            sy = cy + int(math.sin(sp["angle"]) * sp["dist"])
            pygame.draw.circle(surface, C_WHITE, (sx, sy), 2)


#  HUD — INTERFAZ DE USUARIO

class HUD:
    def __init__(self, font_big, font_med, font_sm):
        self.font_big = font_big
        self.font_med = font_med
        self.font_sm  = font_sm

    def draw(self, surface: pygame.Surface, gorgon: Gorgon):
        # ── Panel de efectos activos ──────────
        panel_x, panel_y = 16, 16
        panel_w           = 260

        # Fondo semitransparente
        orb_count = len(gorgon._active_orbs)
        if orb_count > 0:
            ph = 18 + orb_count * 38
            panel = pygame.Surface((panel_w, ph), pygame.SRCALPHA)
            panel.fill((10, 6, 20, 170))
            pygame.draw.rect(panel, (120, 80, 160, 180), (0, 0, panel_w, ph), 2, border_radius=8)
            surface.blit(panel, (panel_x, panel_y))

            title = self.font_sm.render("EFECTOS ACTIVOS", True, (180, 140, 220))
            surface.blit(title, (panel_x + 8, panel_y + 4))

            for i, orb in enumerate(gorgon._active_orbs):
                oy = panel_y + 22 + i * 38
                # Barra de tiempo
                bar_w  = panel_w - 16
                filled = int(bar_w * orb.progress)
                bg_bar = pygame.Rect(panel_x + 8, oy + 18, bar_w, 8)
                fg_bar = pygame.Rect(panel_x + 8, oy + 18, filled, 8)
                pygame.draw.rect(surface, (40, 30, 55), bg_bar, border_radius=4)
                pygame.draw.rect(surface, orb.color(), fg_bar, border_radius=4)

                # Etiqueta + tiempo
                lbl  = self.font_sm.render(orb.label(), True, orb.color())
                secs = self.font_sm.render(f"{orb.remaining:.0f}s", True, C_WHITE)
                surface.blit(lbl,  (panel_x + 8,         oy))
                surface.blit(secs, (panel_x + panel_w - 36, oy))

        # ── Notificación central de orbe recogido ──
        if gorgon.effect_timer > 0:
            alpha_f  = min(1.0, gorgon.effect_timer / 0.5)   # fade out
            txt_surf = self.font_big.render(gorgon.effect_label, True, gorgon.effect_color)
            tw        = txt_surf.get_width()
            tx        = (SCREEN_W - tw) // 2
            ty        = SCREEN_H // 2 - 80
            # Sombra
            shadow = self.font_big.render(gorgon.effect_label, True, (0,0,0))
            surface.blit(shadow, (tx + 3, ty + 3))
            surface.blit(txt_surf, (tx, ty))

        # ── Stats en esquina inferior derecha ──
        stats_lines = [
            f"Velocidad : {gorgon.speed:.2f}",
            f"Salto     : {'✓' if gorgon.can_jump else '✗'}",
            f"Escudo    : {'✓' if gorgon.has_shield else '✗'}",
        ]
        for i, line in enumerate(stats_lines):
            txt = self.font_sm.render(line, True, (200, 180, 220))
            surface.blit(txt, (SCREEN_W - 210, SCREEN_H - 90 + i * 22))

        # ── Controles (pequeño) ───────────────
        controls = "← = a, → = b Mover  |  SHIFT Correr  |  SPACE Saltar  |  ESC Salir"
        ctxt = self.font_sm.render(controls, True, (120, 100, 140))
        surface.blit(ctxt, (SCREEN_W // 2 - ctxt.get_width() // 2, SCREEN_H - 26))


#  ESCENARIO

def build_platforms() -> list[pygame.Rect]:
    """Devuelve lista de rectángulos de colisión para las plataformas."""
    return [
        # Suelo principal
        pygame.Rect(0,       SCREEN_H - 80, SCREEN_W, 80),
        # Plataformas elevadas
        pygame.Rect(150,     SCREEN_H - 220, 200, 22),
        pygame.Rect(480,     SCREEN_H - 310, 200, 22),
        pygame.Rect(800,     SCREEN_H - 220, 200, 22),
        pygame.Rect(340,     SCREEN_H - 430, 180, 22),
        pygame.Rect(620,     SCREEN_H - 430, 180, 22),
    ]


def draw_background(surface: pygame.Surface):
    """Fondo degradado oscuro + detalles de ambiente."""
    for y in range(SCREEN_H):
        t   = y / SCREEN_H
        r   = int(C_BG_TOP[0] + (C_BG_BOT[0] - C_BG_TOP[0]) * t)
        g   = int(C_BG_TOP[1] + (C_BG_BOT[1] - C_BG_TOP[1]) * t)
        b   = int(C_BG_TOP[2] + (C_BG_BOT[2] - C_BG_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_W, y))

    # Estrellas/runas decorativas estáticas
    rng = random.Random(42)
    for _ in range(60):
        sx = rng.randint(0, SCREEN_W)
        sy = rng.randint(0, SCREEN_H - 120)
        sr = rng.randint(1, 2)
        alpha = rng.randint(80, 180)
        pygame.draw.circle(surface, (alpha, alpha - 20, alpha + 40), (sx, sy), sr)


def draw_platforms(surface: pygame.Surface, platforms: list[pygame.Rect]):
    """Dibuja plataformas con un estilo piedra/tierra."""
    for i, plat in enumerate(platforms):
        # Cuerpo
        pygame.draw.rect(surface, C_PLATFORM, plat, border_radius=6)
        # Borde superior iluminado
        top = pygame.Rect(plat.x, plat.y, plat.w, 6)
        pygame.draw.rect(surface, C_PLAT_TOP, top, border_radius=6)
        # Borde inferior sombreado
        pygame.draw.rect(surface, C_PLAT_SIDE,
                         pygame.Rect(plat.x, plat.bottom - 4, plat.w, 4),
                         border_radius=6)
        # Detalle: línea de roca
        if plat.w > 60:
            for lx in range(plat.x + 20, plat.right - 20, 35):
                pygame.draw.line(surface, C_PLAT_SIDE,
                                 (lx, plat.y + 8), (lx + 12, plat.y + 8), 1)


#  ORB SPAWNER — genera orbes periódicamente

class OrbSpawner:
    MIN_INTERVAL = 8.0
    MAX_INTERVAL = 18.0

    def __init__(self, platforms: list[pygame.Rect]):
        self._platforms   = platforms[1:]   # excluir suelo
        self._timer       = 0.0
        self._next_spawn  = random.uniform(self.MIN_INTERVAL, self.MAX_INTERVAL)

    def update(self, dt: float, world_orbs: list) -> Optional[WorldOrb]:
        self._timer += dt
        if self._timer >= self._next_spawn:
            self._timer      = 0.0
            self._next_spawn = random.uniform(self.MIN_INTERVAL, self.MAX_INTERVAL)
            return self._spawn(world_orbs)
        return None

    def _spawn(self, world_orbs: list) -> WorldOrb:
        plat = random.choice(self._platforms)
        x    = random.randint(plat.x + 20, plat.right - 20)
        y    = plat.y - WorldOrb.RADIUS - 4
        cls  = random.choice(ORB_FACTORY)
        orb  = WorldOrb(float(x), float(y), cls)
        world_orbs.append(orb)
        return orb


#  BUCLE PRINCIPAL

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()

    # Fuentes
    font_big = pygame.font.SysFont("Arial", 36, bold=True)
    font_med = pygame.font.SysFont("Arial", 22)
    font_sm  = pygame.font.SysFont("Arial", 16)

    # Escenario
    platforms = build_platforms()

    # Fondo pre-renderizado
    bg_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_background(bg_surf)

    # Gorgona
    gorgon = Gorgon(x=100, y=SCREEN_H - 80 - int(128 * Gorgon.SCALE))

    # Orbes del mundo son manejados por la gorgona (lista compartida)
    spawner = OrbSpawner(platforms)
    gorgon.world_orbs = []

    # HUD
    hud = HUD(font_big, font_med, font_sm)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # segundos por frame

        # ── Eventos ──────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ── Actualizar ───────────────────────
        gorgon.update(dt, platforms)
        spawner.update(dt, gorgon.world_orbs)

        # ── Dibujar ──────────────────────────
        screen.blit(bg_surf, (0, 0))
        draw_platforms(screen, platforms)

        # Dibujar orbes del mundo (antes de la gorgona para que quede encima)
        for worb in gorgon.world_orbs:
            worb.draw(screen)

        gorgon.draw(screen)
        hud.draw(screen, gorgon)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
