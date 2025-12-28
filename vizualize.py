import pygame
import math
from simulation import (
    SimulationEngine,
    BOB_RADIUS,
    BOX_WIDTH,
    BOX_HEIGHT,
    GRAVITY,
    FORCE_MAGNITUDE,
    load_templates,
    save_template,
    delete_template,
)

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1280, 720
TOOLBAR_HEIGHT = 60
CANVAS_TOP = TOOLBAR_HEIGHT
DEBUG_PANEL_WIDTH = 300

BG_COLOR = (18, 18, 24)
TOOLBAR_BG = (28, 28, 36)
BOB_COLOR = (255, 107, 107)
BOB_HOVER = (255, 140, 140)
BOB_SELECTED = (255, 200, 100)
BOX_COLOR = (147, 112, 219)
BOX_HOVER = (180, 150, 240)
ROD_COLOR = (100, 181, 246)
FORCE_COLOR = (255, 193, 7)
BTN_COLOR = (45, 45, 60)
BTN_HOVER = (65, 65, 85)
BTN_ACTIVE = (80, 200, 120)
TEXT_COLOR = (220, 220, 230)
GRID_COLOR = (30, 30, 40)
DEBUG_BG = (22, 22, 30, 220)
DEBUG_BORDER = (50, 50, 70)
DEBUG_LABEL = (130, 130, 150)
DEBUG_VALUE = (200, 200, 220)
DEBUG_HIGHLIGHT = (66, 133, 244)

SELECTED_COLOR = (66, 133, 244)
SELECTED_GLOW = (66, 133, 244, 80)
SELECTED_BORDER = (100, 160, 255)

INPUT_BG = (35, 35, 48)
INPUT_BG_ACTIVE = (45, 50, 65)
INPUT_BORDER = (60, 60, 80)
INPUT_BORDER_ACTIVE = (66, 133, 244)
INPUT_TEXT = (220, 220, 230)

font_large = pygame.font.SysFont("SF Pro Display", 18, bold=True)
font_small = pygame.font.SysFont("SF Pro Display", 14)
font_mono = pygame.font.SysFont("SF Mono", 13)
font_debug_title = pygame.font.SysFont("SF Pro Display", 18, bold=True)
font_debug = pygame.font.SysFont("SF Mono", 14)
font_debug_label = pygame.font.SysFont("SF Pro Display", 13)
font_input = pygame.font.SysFont("SF Mono", 13)


class Button:
    def __init__(self, x, y, w, h, text, callback, name=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.active = False
        self.name = name or text

    def draw(self, surface):
        if self.active:
            color = BTN_ACTIVE
        elif self.hovered:
            color = BTN_HOVER
        else:
            color = BTN_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (60, 60, 80), self.rect, 1, border_radius=6)
        text_surf = font_small.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False

    def get_debug_info(self):
        return {
            "type": "Button",
            "name": self.name,
            "text": self.text,
            "x": self.rect.x,
            "y": self.rect.y,
            "width": self.rect.width,
            "height": self.rect.height,
            "hovered": self.hovered,
            "active": self.active,
        }


class InputField:
    def __init__(
        self, x, y, width, height, key, value, on_change=None, editable=True
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.key = key
        self.value = str(value)
        self.original_value = value
        self.on_change = on_change
        self.active = False
        self.editable = editable
        self.cursor_pos = len(self.value)
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if not self.editable:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            if self.active and not was_active:
                self.cursor_pos = len(self.value)
            return self.active

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self._apply_value()
                self.active = False
                return True
            elif event.key == pygame.K_ESCAPE:
                self.value = str(self.original_value)
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.value = (
                        self.value[: self.cursor_pos - 1]
                        + self.value[self.cursor_pos :]
                    )
                    self.cursor_pos -= 1
                return True
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.value):
                    self.value = (
                        self.value[: self.cursor_pos]
                        + self.value[self.cursor_pos + 1 :]
                    )
                return True
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.value), self.cursor_pos + 1)
                return True
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
                return True
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.value)
                return True
            elif event.unicode and event.unicode.isprintable():
                self.value = (
                    self.value[: self.cursor_pos]
                    + event.unicode
                    + self.value[self.cursor_pos :]
                )
                self.cursor_pos += 1
                return True

        return False

    def _apply_value(self):
        if self.on_change and self.value != str(self.original_value):
            try:
                if isinstance(self.original_value, bool):
                    new_val = self.value.lower() in ("true", "1", "yes")
                elif isinstance(self.original_value, int):
                    new_val = int(float(self.value))
                elif isinstance(self.original_value, float):
                    new_val = float(self.value)
                else:
                    new_val = self.value
                self.on_change(self.key, new_val)
                self.original_value = new_val
            except ValueError:
                self.value = str(self.original_value)

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface, offset_x=0, offset_y=0):
        rect = pygame.Rect(
            self.rect.x + offset_x,
            self.rect.y + offset_y,
            self.rect.width,
            self.rect.height,
        )

        if self.active:
            bg_color = INPUT_BG_ACTIVE
            border_color = INPUT_BORDER_ACTIVE
        else:
            bg_color = INPUT_BG
            border_color = INPUT_BORDER

        pygame.draw.rect(surface, bg_color, rect, border_radius=4)
        pygame.draw.rect(surface, border_color, rect, 1, border_radius=4)

        if not self.editable:
            pygame.draw.rect(surface, (50, 50, 60), rect, border_radius=4)

        if isinstance(self.original_value, bool):
            val_color = (
                (80, 200, 120)
                if self.value.lower() in ("true", "1", "yes")
                else (255, 107, 107)
            )
        elif isinstance(self.original_value, (int, float)):
            val_color = (255, 200, 100)
        else:
            val_color = INPUT_TEXT

        text_surface = font_input.render(self.value, True, val_color)
        text_rect = text_surface.get_rect(midleft=(rect.x + 10, rect.centery))

        clip_rect = pygame.Rect(
            rect.x + 6, rect.y, rect.width - 12, rect.height
        )
        surface.set_clip(clip_rect)
        surface.blit(text_surface, text_rect)
        surface.set_clip(None)

        if self.active and self.cursor_visible:
            cursor_x = (
                rect.x + 10 + font_input.size(self.value[: self.cursor_pos])[0]
            )
            pygame.draw.line(
                surface,
                INPUT_TEXT,
                (cursor_x, rect.y + 5),
                (cursor_x, rect.y + rect.height - 5),
                2,
            )


class DebugPanel:
    READ_ONLY_KEYS = {
        "type",
        "name",
        "id",
        "hovered",
        "active",
        "is_running",
        "bob_count",
        "box_count",
        "rod_count",
        "moi",
        "torque",
        "force.x",
        "force.y",
        "current_length",
        "stretch",
        "fps",
        "dt",
        "bob1",
        "bob2",
    }

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.selected_object = None
        self.visible = True
        self.scroll_y = 0
        self.input_fields = []
        self.active_field = None

    def set_selected(self, obj):
        self.selected_object = obj
        self.scroll_y = 0
        self._rebuild_fields()

    def _rebuild_fields(self):
        self.input_fields = []
        self.active_field = None

        if self.selected_object is None:
            return

        if hasattr(self.selected_object, "get_debug_info"):
            debug_info = self.selected_object.get_debug_info()
        else:
            debug_info = self.selected_object

        y_offset = 135
        label_width = 95
        field_x = label_width + 20
        field_width = self.rect.width - field_x - 25
        field_height = 26

        for key, value in debug_info.items():
            if key in ["type", "name"]:
                continue

            editable = key not in self.READ_ONLY_KEYS and hasattr(
                self.selected_object, "set_property"
            )

            field = InputField(
                field_x,
                y_offset,
                field_width,
                field_height,
                key,
                value,
                on_change=self._on_value_change,
                editable=editable,
            )
            self.input_fields.append((key, field))
            y_offset += 32

    def _on_value_change(self, key, new_value):
        if self.selected_object and hasattr(
            self.selected_object, "set_property"
        ):
            self.selected_object.set_property(key, new_value)
            self._rebuild_fields()

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                for _, field in self.input_fields:
                    if field.active:
                        field._apply_value()
                        field.active = False
                return False

        if hasattr(event, "pos"):
            rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - self.rect.y)
            modified_event = pygame.event.Event(
                event.type, {**event.__dict__, "pos": rel_pos}
            )
        else:
            modified_event = event

        for _, field in self.input_fields:
            if field.handle_event(modified_event):
                self.active_field = field if field.active else None
                return True

        return False

    def has_active_input(self):
        return any(field.active for _, field in self.input_fields)

    def update(self, dt):
        for _, field in self.input_fields:
            field.update(dt)

        if self.selected_object is None:
            return

        if hasattr(self.selected_object, "get_debug_info"):
            debug_info = self.selected_object.get_debug_info()
        else:
            debug_info = self.selected_object

        for key, field in self.input_fields:
            if field.active:
                continue
            if key in debug_info:
                new_value = str(debug_info[key])
                if field.value != new_value:
                    field.value = new_value
                    field.original_value = debug_info[key]

    def draw(self, surface):
        if not self.visible:
            return

        panel_surface = pygame.Surface(
            (self.rect.width, self.rect.height), pygame.SRCALPHA
        )
        panel_surface.fill(DEBUG_BG)

        pygame.draw.rect(
            panel_surface,
            DEBUG_BORDER,
            (0, 0, self.rect.width, self.rect.height),
            1,
            border_radius=8,
        )

        header_rect = pygame.Rect(0, 0, self.rect.width, 50)
        pygame.draw.rect(
            panel_surface,
            (28, 28, 38, 240),
            header_rect,
            border_top_left_radius=8,
            border_top_right_radius=8,
        )
        pygame.draw.line(
            panel_surface, DEBUG_BORDER, (0, 50), (self.rect.width, 50), 1
        )

        pygame.draw.circle(panel_surface, SELECTED_COLOR, (22, 25), 6)
        title = font_debug_title.render(
            "DEBUG INSPECTOR", True, DEBUG_HIGHLIGHT
        )
        panel_surface.blit(title, (38, 15))

        if self.selected_object is None:
            hint = font_debug.render("Click a Bob or Rod", True, DEBUG_LABEL)
            panel_surface.blit(hint, (15, 75))
            hint2 = font_debug.render(
                "to inspect its values", True, DEBUG_LABEL
            )
            panel_surface.blit(hint2, (15, 100))

            pygame.draw.rect(
                panel_surface,
                (35, 35, 50),
                (15, 135, self.rect.width - 30, 70),
                border_radius=6,
            )
            icon_text = font_debug.render(
                "Select an object", True, (80, 80, 100)
            )
            panel_surface.blit(icon_text, (25, 162))
        else:
            if hasattr(self.selected_object, "get_debug_info"):
                debug_info = self.selected_object.get_debug_info()
            else:
                debug_info = self.selected_object

            y_offset = 62

            obj_type = debug_info.get("type", "Object")
            obj_name = debug_info.get("name", "Unknown")

            type_badge_width = font_debug_title.size(obj_type)[0] + 20
            pygame.draw.rect(
                panel_surface,
                SELECTED_COLOR,
                (15, y_offset - 2, type_badge_width, 28),
                border_radius=5,
            )
            type_surface = font_debug_title.render(
                obj_type, True, (255, 255, 255)
            )
            panel_surface.blit(type_surface, (25, y_offset + 2))
            y_offset += 34

            name_surface = font_debug.render(obj_name, True, DEBUG_VALUE)
            panel_surface.blit(name_surface, (15, y_offset))
            y_offset += 30

            pygame.draw.line(
                panel_surface,
                DEBUG_BORDER,
                (15, y_offset),
                (self.rect.width - 15, y_offset),
                1,
            )
            y_offset += 14

            section_title = font_debug_label.render(
                "PROPERTIES", True, (80, 80, 100)
            )
            panel_surface.blit(section_title, (15, y_offset))
            y_offset += 26

            for key, field in self.input_fields:
                if field.rect.y > self.rect.height - 50:
                    break

                label_surface = font_debug_label.render(
                    f"{key}:", True, DEBUG_LABEL
                )
                panel_surface.blit(label_surface, (15, field.rect.y + 5))

                field.draw(panel_surface)

                if field.editable:
                    indicator_x = self.rect.width - 15
                    indicator_y = field.rect.y + field.rect.height // 2
                    pygame.draw.circle(
                        panel_surface,
                        SELECTED_COLOR,
                        (indicator_x - 6, indicator_y),
                        4,
                    )

            help_y = self.rect.height - 35
            pygame.draw.line(
                panel_surface,
                DEBUG_BORDER,
                (15, help_y - 10),
                (self.rect.width - 15, help_y - 10),
                1,
            )
            help_text = font_debug_label.render(
                "Enter to apply | Esc to cancel", True, (70, 70, 90)
            )
            panel_surface.blit(help_text, (15, help_y))

        surface.blit(panel_surface, self.rect.topleft)


class SaveDialog:
    def __init__(self, x, y, width, height, on_save, on_cancel):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.visible = False
        self.text = ""
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0

    def show(self):
        self.visible = True
        self.text = ""
        self.cursor_pos = 0

    def hide(self):
        self.visible = False
        self.text = ""

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.hide()
                return True

            save_btn = pygame.Rect(
                self.rect.x + self.rect.width - 90,
                self.rect.y + self.rect.height - 50,
                70,
                35
            )
            cancel_btn = pygame.Rect(
                self.rect.x + self.rect.width - 170,
                self.rect.y + self.rect.height - 50,
                70,
                35
            )

            if save_btn.collidepoint(event.pos) and self.text.strip():
                self.on_save(self.text.strip())
                self.hide()
                return True
            elif cancel_btn.collidepoint(event.pos):
                self.hide()
                return True
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.text.strip():
                    self.on_save(self.text.strip())
                    self.hide()
                return True
            elif event.key == pygame.K_ESCAPE:
                self.hide()
                return True
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                return True
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
                return True
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
                return True
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
                return True
            elif event.unicode and event.unicode.isprintable():
                self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += 1
                return True

        return False

    def update(self, dt):
        if not self.visible:
            return
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface):
        if not self.visible:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill((28, 28, 38, 250))
        pygame.draw.rect(panel, DEBUG_BORDER, (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)

        title = font_debug_title.render("Save Template", True, DEBUG_HIGHLIGHT)
        panel.blit(title, (20, 20))

        label = font_debug_label.render("Template Name:", True, DEBUG_LABEL)
        panel.blit(label, (20, 60))

        input_rect = pygame.Rect(20, 85, self.rect.width - 40, 35)
        pygame.draw.rect(panel, INPUT_BG, input_rect, border_radius=6)
        pygame.draw.rect(panel, INPUT_BORDER_ACTIVE, input_rect, 2, border_radius=6)

        text_surface = font_input.render(self.text, True, INPUT_TEXT)
        panel.blit(text_surface, (input_rect.x + 10, input_rect.y + 9))

        if self.cursor_visible:
            cursor_x = input_rect.x + 10 + font_input.size(self.text[:self.cursor_pos])[0]
            pygame.draw.line(panel, INPUT_TEXT, (cursor_x, input_rect.y + 8), (cursor_x, input_rect.y + 27), 2)

        save_btn = pygame.Rect(self.rect.width - 90, self.rect.height - 50, 70, 35)
        cancel_btn = pygame.Rect(self.rect.width - 170, self.rect.height - 50, 70, 35)

        save_color = BTN_ACTIVE if self.text.strip() else BTN_COLOR
        pygame.draw.rect(panel, save_color, save_btn, border_radius=6)
        save_text = font_small.render("Save", True, TEXT_COLOR)
        panel.blit(save_text, (save_btn.x + 20, save_btn.y + 9))

        pygame.draw.rect(panel, BTN_COLOR, cancel_btn, border_radius=6)
        cancel_text = font_small.render("Cancel", True, TEXT_COLOR)
        panel.blit(cancel_text, (cancel_btn.x + 12, cancel_btn.y + 9))

        surface.blit(panel, self.rect.topleft)


class TemplatePanel:
    def __init__(self, x, y, width, height, on_select, on_close):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_select = on_select
        self.on_close = on_close
        self.visible = False
        self.templates = {}
        self.scroll_y = 0
        self.hovered_template = None
        self.delete_hovered = None

    def show(self):
        self.visible = True
        self.templates = load_templates()
        self.scroll_y = 0

    def hide(self):
        self.visible = False

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.hide()
                return True

            rel_x = event.pos[0] - self.rect.x
            rel_y = event.pos[1] - self.rect.y + self.scroll_y

            y_offset = 50
            for name in self.templates.keys():
                item_rect = pygame.Rect(15, y_offset, self.rect.width - 30, 45)
                delete_rect = pygame.Rect(self.rect.width - 50, y_offset + 10, 25, 25)

                if delete_rect.collidepoint(rel_x, rel_y):
                    delete_template(name)
                    self.templates = load_templates()
                    return True
                elif item_rect.collidepoint(rel_x, rel_y):
                    self.on_select(name, self.templates[name])
                    self.hide()
                    return True
                y_offset += 55

            return True

        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                rel_x = event.pos[0] - self.rect.x
                rel_y = event.pos[1] - self.rect.y + self.scroll_y

                self.hovered_template = None
                self.delete_hovered = None
                y_offset = 50
                for name in self.templates.keys():
                    item_rect = pygame.Rect(15, y_offset, self.rect.width - 30, 45)
                    delete_rect = pygame.Rect(self.rect.width - 50, y_offset + 10, 25, 25)

                    if delete_rect.collidepoint(rel_x, rel_y):
                        self.delete_hovered = name
                    elif item_rect.collidepoint(rel_x, rel_y):
                        self.hovered_template = name
                    y_offset += 55

        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            max_scroll = max(0, len(self.templates) * 55 + 60 - self.rect.height)
            self.scroll_y = max(0, min(max_scroll, self.scroll_y - event.y * 20))
            return True

        return False

    def draw(self, surface):
        if not self.visible:
            return

        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill((28, 28, 38, 245))
        pygame.draw.rect(panel, DEBUG_BORDER, (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)

        header_rect = pygame.Rect(0, 0, self.rect.width, 45)
        pygame.draw.rect(panel, (35, 35, 50, 250), header_rect, border_top_left_radius=12, border_top_right_radius=12)

        icon_surface = font_large.render("SAVEs", True, DEBUG_HIGHLIGHT)
        panel.blit(icon_surface, (15, 12))
        title = font_debug_title.render("Templates", True, DEBUG_HIGHLIGHT)
        panel.blit(title, (45, 14))

        pygame.draw.line(panel, DEBUG_BORDER, (0, 45), (self.rect.width, 45), 1)

        content_surface = pygame.Surface((self.rect.width - 4, self.rect.height - 50), pygame.SRCALPHA)

        if not self.templates:
            empty_text = font_debug.render("No templates saved", True, DEBUG_LABEL)
            content_surface.blit(empty_text, (20, 30))
            hint_text = font_debug_label.render("Click Save to create one", True, (70, 70, 90))
            content_surface.blit(hint_text, (20, 55))
        else:
            y_offset = 10 - self.scroll_y
            for name, data in self.templates.items():
                if y_offset + 45 > 0 and y_offset < self.rect.height - 50:
                    item_rect = pygame.Rect(15, y_offset, self.rect.width - 34, 45)

                    if name == self.hovered_template:
                        pygame.draw.rect(content_surface, (50, 55, 70), item_rect, border_radius=8)
                    else:
                        pygame.draw.rect(content_surface, (38, 38, 52), item_rect, border_radius=8)

                    pygame.draw.rect(content_surface, (55, 55, 75), item_rect, 1, border_radius=8)

                    name_text = font_debug.render(name[:20], True, DEBUG_VALUE)
                    content_surface.blit(name_text, (item_rect.x + 12, item_rect.y + 6))

                    bobs = len(data.get("bobs", []))
                    boxes = len(data.get("boxes", []))
                    rods = len(data.get("rods", []))
                    info = f"{bobs} bobs, {boxes} boxes, {rods} rods"
                    info_text = font_debug_label.render(info, True, DEBUG_LABEL)
                    content_surface.blit(info_text, (item_rect.x + 12, item_rect.y + 26))

                    delete_rect = pygame.Rect(item_rect.right - 35, item_rect.y + 10, 25, 25)
                    delete_color = (255, 80, 80) if name == self.delete_hovered else (120, 80, 80)
                    pygame.draw.rect(content_surface, delete_color, delete_rect, border_radius=4)
                    x_text = font_small.render("×", True, (255, 255, 255))
                    content_surface.blit(x_text, (delete_rect.x + 7, delete_rect.y + 3))

                y_offset += 55

        panel.blit(content_surface, (2, 48))
        surface.blit(panel, self.rect.topleft)


class SimulationUI:
    def __init__(self, engine):
        self.engine = engine
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Physics Simulation")
        self.clock = pygame.time.Clock()

        self.mode = "bob"
        self.connecting_body = None
        self.connecting_anchor = None
        self.current_fps = 60
        self.current_dt = 0
        self.force_start = None
        self.force_target = None

        self.debug_panel = DebugPanel(
            WIDTH - DEBUG_PANEL_WIDTH - 15,
            TOOLBAR_HEIGHT + 15,
            DEBUG_PANEL_WIDTH,
            HEIGHT - TOOLBAR_HEIGHT - 30,
        )

        self.save_dialog = SaveDialog(
            WIDTH // 2 - 175,
            HEIGHT // 2 - 85,
            350,
            170,
            self.on_save_template,
            lambda: None
        )

        self.template_panel = TemplatePanel(
            WIDTH // 2 - 175,
            HEIGHT // 2 - 150,
            350,
            300,
            self.on_load_template,
            lambda: None
        )

        self.buttons = []
        self.setup_ui()

    def setup_ui(self):
        btn_y = 12
        btn_h = 36

        self.bob_btn = Button(
            20, btn_y, 70, btn_h, "Bob", self.set_bob_mode, "BobButton"
        )
        self.box_btn = Button(
            95, btn_y, 70, btn_h, "Box", self.set_box_mode, "BoxButton"
        )
        self.rod_btn = Button(
            170, btn_y, 70, btn_h, "Rod", self.set_rod_mode, "RodButton"
        )
        self.pin_btn = Button(
            245, btn_y, 70, btn_h, "Pin", self.set_pin_mode, "PinButton"
        )
        self.force_btn = Button(
            320, btn_y, 70, btn_h, "Force", self.set_force_mode, "ForceButton"
        )
        self.save_btn = Button(
            400, btn_y, 70, btn_h, "Save", self.show_save_dialog, "SaveButton"
        )
        self.templates_btn = Button(
            475, btn_y, 36, btn_h, "Saves", self.toggle_templates, "TemplatesButton"
        )
        self.start_btn = Button(
            WIDTH - 290,
            btn_y,
            80,
            btn_h,
            "Start",
            self.toggle_simulation,
            "StartButton",
        )
        self.clear_btn = Button(
            WIDTH - 200,
            btn_y,
            80,
            btn_h,
            "Clear",
            self.clear_all,
            "ClearButton",
        )
        self.debug_btn = Button(
            WIDTH - 110,
            btn_y,
            90,
            btn_h,
            "Debug",
            self.toggle_debug,
            "DebugButton",
        )

        self.buttons = [
            self.bob_btn,
            self.box_btn,
            self.rod_btn,
            self.pin_btn,
            self.force_btn,
            self.save_btn,
            self.templates_btn,
            self.start_btn,
            self.clear_btn,
            self.debug_btn,
        ]
        self.bob_btn.active = True
        self.debug_btn.active = True

    def _clear_mode_buttons(self):
        self.bob_btn.active = False
        self.box_btn.active = False
        self.rod_btn.active = False
        self.pin_btn.active = False
        self.force_btn.active = False

    def set_bob_mode(self):
        self.mode = "bob"
        self._clear_mode_buttons()
        self.bob_btn.active = True

    def set_box_mode(self):
        self.mode = "box"
        self._clear_mode_buttons()
        self.box_btn.active = True

    def set_rod_mode(self):
        self.mode = "rod"
        self._clear_mode_buttons()
        self.rod_btn.active = True

    def set_pin_mode(self):
        self.mode = "pin"
        self._clear_mode_buttons()
        self.pin_btn.active = True

    def set_force_mode(self):
        self.mode = "force"
        self._clear_mode_buttons()
        self.force_btn.active = True

    def toggle_simulation(self):
        self.engine.toggle()
        self.start_btn.text = "Stop" if self.engine.running else "Start"
        self.start_btn.active = self.engine.running

    def toggle_debug(self):
        self.debug_panel.visible = not self.debug_panel.visible
        self.debug_btn.active = self.debug_panel.visible

    def show_save_dialog(self):
        if len(self.engine.bobs) == 0 and len(self.engine.boxes) <= 1:
            return
        self.save_dialog.show()

    def toggle_templates(self):
        self.template_panel.toggle()
        self.templates_btn.active = self.template_panel.visible

    def on_save_template(self, name):
        data = self.engine.serialize()
        save_template(name, data)

    def on_load_template(self, name, data):
        self.engine.load_template(data)

    def clear_all(self):
        self.engine.clear()
        self.start_btn.text = "Start"
        self.start_btn.active = False
        self.connecting_body = None
        self.connecting_anchor = None
        self.force_start = None
        self.force_target = None
        self.debug_panel.set_selected(None)

    def get_button_at(self, x, y):
        for btn in self.buttons:
            if btn.rect.collidepoint(x, y):
                return btn
        return None

    def handle_event(self, event):
        if self.save_dialog.visible:
            if self.save_dialog.handle_event(event):
                return
            return

        if self.template_panel.visible:
            if self.template_panel.handle_event(event):
                return

        if self.debug_panel.visible and self.debug_panel.handle_event(event):
            return

        if self.debug_panel.has_active_input():
            if event.type == pygame.KEYDOWN:
                return

        for btn in self.buttons:
            if btn.handle_event(event):
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos

            if self.debug_panel.visible and self.debug_panel.rect.collidepoint(
                x, y
            ):
                return

            if y < CANVAS_TOP:
                return

            clicked_bob = self.engine.get_bob_at(x, y)
            clicked_box = (
                self.engine.get_box_at(x, y) if not clicked_bob else None
            )
            clicked_body = clicked_bob or clicked_box
            clicked_rod = (
                self.engine.get_rod_at(x, y) if not clicked_body else None
            )

            if self.mode == "force":
                if clicked_body:
                    self.force_start = (x, y)
                    self.force_target = clicked_body
                    self.debug_panel.set_selected(clicked_body)
                return

            if clicked_body:
                self.debug_panel.set_selected(clicked_body)
            elif clicked_rod:
                self.debug_panel.set_selected(clicked_rod)
            else:
                self.debug_panel.set_selected(
                    self.engine.get_debug_info(
                        self.current_fps, self.current_dt
                    )
                )

            if self.engine.running:
                if clicked_body:
                    self.engine.set_dragging(clicked_body)
            else:
                if self.mode == "bob":
                    if clicked_bob:
                        self.engine.set_dragging(clicked_bob)
                    elif not clicked_rod and not clicked_box:
                        new_bob = self.engine.create_bob(x, y, pinned=False)
                        self.engine.set_dragging(new_bob)
                        self.debug_panel.set_selected(new_bob)
                elif self.mode == "box":
                    if clicked_box:
                        self.engine.set_dragging(clicked_box)
                    elif not clicked_rod and not clicked_bob:
                        new_box = self.engine.create_box(x, y, pinned=False)
                        self.engine.set_dragging(new_box)
                        self.debug_panel.set_selected(new_box)
                elif self.mode == "pin":
                    if clicked_body:
                        self.engine.toggle_pin(clicked_body)
                    elif not clicked_rod:
                        new_bob = self.engine.create_bob(x, y, pinned=True)
                        self.debug_panel.set_selected(new_bob)
                elif self.mode == "rod":
                    if clicked_body:
                        from simulation import Box
                        anchor = None
                        if isinstance(clicked_body, Box):
                            anchor = clicked_body.get_nearest_anchor(x, y)

                        if self.connecting_body is None:
                            self.connecting_body = clicked_body
                            self.connecting_anchor = anchor
                        elif self.connecting_body != clicked_body:
                            new_rod = self.engine.create_rod(
                                self.connecting_body, clicked_body,
                                self.connecting_anchor, anchor
                            )
                            if new_rod:
                                self.debug_panel.set_selected(new_rod)
                            self.connecting_body = None
                            self.connecting_anchor = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            x, y = event.pos
            if y >= CANVAS_TOP:
                clicked_bob = self.engine.get_bob_at(x, y)
                clicked_box = (
                    self.engine.get_box_at(x, y) if not clicked_bob else None
                )
                clicked_body = clicked_bob or clicked_box
                clicked_rod = (
                    self.engine.get_rod_at(x, y) if not clicked_body else None
                )

                if clicked_body:
                    self.debug_panel.set_selected(clicked_body)
                elif clicked_rod:
                    self.debug_panel.set_selected(clicked_rod)
                else:
                    self.debug_panel.set_selected(
                        self.engine.get_debug_info(
                            self.current_fps, self.current_dt
                        )
                    )

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.mode == "force" and self.force_start and self.force_target:
                x, y = event.pos
                dx = x - self.force_start[0]
                dy = y - self.force_start[1]
                length = (dx * dx + dy * dy) ** 0.5
                if length > 10:
                    scale = FORCE_MAGNITUDE * (length / 100)
                    force_x = (dx / length) * scale
                    force_y = (dy / length) * scale
                    from simulation import Vector

                    self.force_target.body.apply_point_force(
                        Vector(force_x, force_y),
                        Vector(self.force_start[0], self.force_start[1]),
                    )
            self.force_start = None
            self.force_target = None
            self.engine.release()

        elif event.type == pygame.MOUSEMOTION:
            if self.engine.dragging_bob:
                x, y = event.pos
                y = max(CANVAS_TOP + BOB_RADIUS, y)
                self.engine.move(self.engine.dragging_bob, x, y)
            elif self.engine.dragging_box:
                x, y = event.pos
                y = max(CANVAS_TOP + self.engine.dragging_box.height // 2, y)
                self.engine.move(self.engine.dragging_box, x, y)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.connecting_body = None
                self.connecting_anchor = None
                self.force_start = None
                self.force_target = None
            elif event.key == pygame.K_SPACE:
                self.toggle_simulation()
            elif event.key == pygame.K_d:
                self.toggle_debug()
            elif (
                event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE
            ):
                x, y = pygame.mouse.get_pos()
                bob_to_delete = self.engine.get_bob_at(x, y)
                box_to_delete = (
                    self.engine.get_box_at(x, y) if not bob_to_delete else None
                )
                if bob_to_delete and not self.engine.running:
                    if self.debug_panel.selected_object == bob_to_delete:
                        self.debug_panel.set_selected(None)
                    if self.connecting_body == bob_to_delete:
                        self.connecting_body = None
                    self.engine.delete_bob(bob_to_delete)
                elif box_to_delete and not self.engine.running:
                    if self.debug_panel.selected_object == box_to_delete:
                        self.debug_panel.set_selected(None)
                    if self.connecting_body == box_to_delete:
                        self.connecting_body = None
                    self.engine.delete_box(box_to_delete)

    def draw_grid(self, surface):
        spacing = 40
        for x in range(0, WIDTH, spacing):
            pygame.draw.line(
                surface, GRID_COLOR, (x, CANVAS_TOP), (x, HEIGHT), 1
            )
        for y in range(CANVAS_TOP, HEIGHT, spacing):
            pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y), 1)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        self.draw_grid(surface)

        pygame.draw.rect(surface, TOOLBAR_BG, (0, 0, WIDTH, TOOLBAR_HEIGHT))
        pygame.draw.line(
            surface,
            (40, 40, 55),
            (0, TOOLBAR_HEIGHT - 1),
            (WIDTH, TOOLBAR_HEIGHT - 1),
            1,
        )

        for btn in self.buttons:
            btn.draw(surface)

        mode_text = font_small.render(
            f"Mode: {self.mode.upper()}", True, (120, 120, 140)
        )
        surface.blit(mode_text, (530, 22))

        if self.engine.running:
            status = font_small.render("RUNNING", True, (80, 200, 120))
        else:
            status = font_small.render("PAUSED", True, (255, 107, 107))
        surface.blit(status, (640, 22))

        for rod in self.engine.rods:
            p1 = rod.get_endpoint1()
            p2 = rod.get_endpoint2()
            x1, y1 = int(p1[0]), int(p1[1])
            x2, y2 = int(p2[0]), int(p2[1])

            is_selected = self.debug_panel.selected_object == rod
            color = SELECTED_COLOR if is_selected else ROD_COLOR
            width = 5 if is_selected else 3

            if is_selected:
                pygame.draw.line(
                    surface, SELECTED_BORDER, (x1, y1), (x2, y2), width + 4
                )
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), width)

        if self.connecting_body:
            mx, my = pygame.mouse.get_pos()
            from simulation import Box
            if isinstance(self.connecting_body, Box) and self.connecting_anchor:
                anchor_pos = self.connecting_body.get_world_anchor(self.connecting_anchor)
                x1, y1 = int(anchor_pos.x), int(anchor_pos.y)
            else:
                x1 = int(self.connecting_body.body.position.x)
                y1 = int(self.connecting_body.body.position.y)
            pygame.draw.line(surface, (80, 80, 100), (x1, y1), (mx, my), 2)

        mx, my = pygame.mouse.get_pos()
        hovered_bob = self.engine.get_bob_at(mx, my)
        hovered_box = (
            self.engine.get_box_at(mx, my) if not hovered_bob else None
        )

        for box in self.engine.boxes:
            cx = box.body.position.x
            cy = box.body.position.y
            angle = box.body.orientation
            hw = box.width / 2
            hh = box.height / 2

            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
            rotated = []
            for lx, ly in corners:
                rx = cx + lx * cos_a - ly * sin_a
                ry = cy + lx * sin_a + ly * cos_a
                rotated.append((rx, ry))

            is_selected = self.debug_panel.selected_object == box

            if box == self.engine.dragging_box or box == self.connecting_body:
                color = BOB_SELECTED
            elif is_selected:
                color = SELECTED_COLOR
            elif box == hovered_box:
                color = BOX_HOVER
            else:
                color = BOX_COLOR

            if is_selected:
                pygame.draw.polygon(surface, SELECTED_BORDER, rotated, 4)

            pygame.draw.polygon(surface, color, rotated)
            pygame.draw.polygon(surface, (255, 255, 255), rotated, 2)

            if box.pinned:
                pygame.draw.circle(
                    surface, (255, 255, 255), (int(cx), int(cy)), 6
                )
                pygame.draw.circle(surface, (0, 0, 0), (int(cx), int(cy)), 4)

            if self.mode == "rod" and box != self.engine.ground:
                anchors = box.get_all_world_anchors()
                for name, (ax, ay) in anchors.items():
                    ax_i, ay_i = int(ax), int(ay)
                    dist_sq = (mx - ax) ** 2 + (my - ay) ** 2
                    if dist_sq < 400:
                        pygame.draw.circle(surface, (255, 200, 100), (ax_i, ay_i), 8)
                        pygame.draw.circle(surface, (255, 255, 255), (ax_i, ay_i), 8, 2)
                    else:
                        pygame.draw.circle(surface, (100, 180, 255), (ax_i, ay_i), 5)
                        pygame.draw.circle(surface, (255, 255, 255), (ax_i, ay_i), 5, 1)

        for bob in self.engine.bobs:
            x = int(bob.body.position.x)
            y = int(bob.body.position.y)

            is_selected = self.debug_panel.selected_object == bob

            if bob == self.engine.dragging_bob or bob == self.connecting_body:
                color = BOB_SELECTED
            elif is_selected:
                color = SELECTED_COLOR
            elif bob == hovered_bob:
                color = BOB_HOVER
            else:
                color = BOB_COLOR

            if is_selected:
                pygame.draw.circle(
                    surface, SELECTED_BORDER, (x, y), bob.radius + 8, 2
                )
                pygame.draw.circle(
                    surface, SELECTED_COLOR, (x, y), bob.radius + 4, 2
                )

            pygame.draw.circle(surface, color, (x, y), bob.radius)

            if bob.pinned:
                pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)

        if self.mode == "force" and self.force_start and self.force_target:
            sx, sy = self.force_start
            ex, ey = pygame.mouse.get_pos()
            dx = ex - sx
            dy = ey - sy
            length = (dx * dx + dy * dy) ** 0.5
            if length > 5:
                pygame.draw.line(surface, FORCE_COLOR, (sx, sy), (ex, ey), 3)
                angle = math.atan2(dy, dx)
                arrow_len = 12
                arrow_angle = 0.5
                ax1 = ex - arrow_len * math.cos(angle - arrow_angle)
                ay1 = ey - arrow_len * math.sin(angle - arrow_angle)
                ax2 = ex - arrow_len * math.cos(angle + arrow_angle)
                ay2 = ey - arrow_len * math.sin(angle + arrow_angle)
                pygame.draw.polygon(
                    surface, FORCE_COLOR, [(ex, ey), (ax1, ay1), (ax2, ay2)]
                )
                pygame.draw.circle(surface, FORCE_COLOR, (int(sx), int(sy)), 6)

        self.debug_panel.draw(surface)

        self.template_panel.draw(surface)
        self.save_dialog.draw(surface)

        help_text = font_small.render(
            "SPACE: Start/Stop | D: Debug | DEL: Delete | ESC: Cancel | Right-Click: Inspect",
            True,
            (80, 80, 100),
        )
        surface.blit(help_text, (20, HEIGHT - 30))

    def update(self, dt):
        self.current_dt = dt
        self.current_fps = self.clock.get_fps()
        self.engine.update(dt)
        self.debug_panel.update(dt)
        self.save_dialog.update(dt)

    def tick(self):
        return self.clock.tick(60) / 1000.0
