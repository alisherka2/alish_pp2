"""
paint.py  –  Paint TSIS 2
Extends Practice 11 with:
  • Pencil (freehand, consecutive-point lines)
  • Straight line tool with live preview
  • Three brush sizes  [1] small  [2] medium  [3] large
  • Flood-fill tool
  • Text tool: click → type → Enter to commit / Escape to cancel
  • Ctrl+S  →  timestamped .png save
  • All shapes respect active brush size
"""

import sys
import datetime
import pygame

from tools import (
    # tool IDs
    TOOL_PENCIL, TOOL_LINE, TOOL_RECTANGLE, TOOL_SQUARE,
    TOOL_CIRCLE, TOOL_ERASER, TOOL_RTRIANGLE, TOOL_ETRIANGLE,
    TOOL_RHOMBUS, TOOL_FILL, TOOL_TEXT,
    # helpers
    BRUSH_SIZES, CANVAS_COLOR,
    draw_shape, flood_fill, TextState,
)

# ═══════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════

WINDOW_WIDTH  = 1100
WINDOW_HEIGHT = 720
TOOLBAR_H     = 100          # two-row toolbar
CANVAS_TOP    = TOOLBAR_H

PALETTE = [
    (0,   0,   0),
    (255, 255, 255),
    (255,   0,   0),
    (0,   200,   0),
    (0,     0, 255),
    (255, 255,   0),
    (255, 128,   0),
    (160,   0, 255),
    (0,   210, 255),
    (255,   0, 200),
    (139,  69,  19),
    (128, 128, 128),
]

SWATCH_SIZE   = 26
SWATCH_MARGIN = 4

TOOLBAR_BG    = (22, 22, 34)
TOOLBAR_BG2   = (30, 30, 46)
BORDER_COLOR  = (60, 60, 90)

TEXT_FONT_SIZE = 20   # size used for the text tool


# ═══════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════

def draw_button(surface, font, text, rect, active=False, accent=None):
    fill   = accent if (active and accent) else ((70, 140, 255) if active else (48, 48, 68))
    border = (220, 235, 255) if active else (80, 80, 110)
    pygame.draw.rect(surface, fill,   rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 2, border_radius=6)
    label = font.render(text, True, (240, 240, 240))
    lx = rect.x + (rect.width  - label.get_width())  // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    surface.blit(label, (lx, ly))


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("TSIS 2 – Paint Extended")

    font      = pygame.font.SysFont(None, 18)
    text_font = pygame.font.SysFont("consolas", TEXT_FONT_SIZE)
    clock     = pygame.time.Clock()

    # ── canvas ──
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - CANVAS_TOP))
    canvas.fill(CANVAS_COLOR)

    # ── state ──
    current_tool   = TOOL_PENCIL
    current_color  = PALETTE[0]
    brush_size_idx = 0           # index into BRUSH_SIZES
    drawing        = False
    start_pos      = None
    prev_pos       = None        # previous point for pencil segments
    preview_surf   = None
    text_state     = TextState()

    # ── tool list: (id, label, shortcut) ──
    tools = [
        (TOOL_PENCIL,    "Pencil",   "P"),
        (TOOL_LINE,      "Line",     "L"),
        (TOOL_RECTANGLE, "Rect",     "R"),
        (TOOL_SQUARE,    "Square",   "Q"),
        (TOOL_CIRCLE,    "Circle",   "C"),
        (TOOL_ERASER,    "Eraser",   "E"),
        (TOOL_RTRIANGLE, "R-Tri",    "T"),
        (TOOL_ETRIANGLE, "Eq-Tri",   "Y"),
        (TOOL_RHOMBUS,   "Rhombus",  "U"),
        (TOOL_FILL,      "Fill",     "F"),
        (TOOL_TEXT,      "Text",     "X"),
    ]

    # ── top row: tool buttons ──
    btn_w, btn_h = 74, 34
    row1_y = 8
    tool_rects = []
    for i in range(len(tools)):
        r = pygame.Rect(8 + i * (btn_w + 4), row1_y, btn_w, btn_h)
        tool_rects.append(r)

    # ── second row: brush-size buttons ──
    size_labels = ["Small [1]", "Med [2]", "Large [3]"]
    size_rects  = []
    for i in range(3):
        r = pygame.Rect(8 + i * (btn_w + 4), row1_y + btn_h + 6, btn_w, 28)
        size_rects.append(r)

    # ── Save button ──
    save_rect = pygame.Rect(8 + 3 * (btn_w + 4), row1_y + btn_h + 6, btn_w, 28)

    # ── Clear button ──
    clear_rect = pygame.Rect(8 + 4 * (btn_w + 4), row1_y + btn_h + 6, btn_w, 28)

    # ── colour swatches ──
    pal_x_start = 8 + len(tools) * (btn_w + 4) + 12
    palette_rects = []
    for i in range(len(PALETTE)):
        # two rows of 6
        col = i % 6
        row = i // 6
        r = pygame.Rect(
            pal_x_start + col * (SWATCH_SIZE + SWATCH_MARGIN),
            6 + row * (SWATCH_SIZE + SWATCH_MARGIN),
            SWATCH_SIZE, SWATCH_SIZE,
        )
        palette_rects.append(r)

    # ── keyboard shortcuts ──
    key_map = {t[2]: t[0] for t in tools}

    # ══════════════════════════════════════════
    #  MAIN LOOP
    # ══════════════════════════════════════════
    running = True
    while running:

        brush_size = BRUSH_SIZES[brush_size_idx]

        for event in pygame.event.get():

            # ── quit ──
            if event.type == pygame.QUIT:
                running = False
                break

            # ── keyboard ──
            elif event.type == pygame.KEYDOWN:

                # TEXT TOOL active: route all keys to the text buffer
                if text_state.active:
                    if event.key == pygame.K_RETURN:
                        text_state.commit(canvas, current_color, text_font)
                    elif event.key == pygame.K_ESCAPE:
                        text_state.cancel()
                    elif event.key == pygame.K_BACKSPACE:
                        text_state.backspace()
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable():
                            text_state.add_char(ch)
                    continue   # don't process tool shortcuts while typing

                # global shortcuts
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Ctrl+S  →  save
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    _save_canvas(canvas)

                # brush sizes 1/2/3
                elif event.key == pygame.K_1:
                    brush_size_idx = 0
                elif event.key == pygame.K_2:
                    brush_size_idx = 1
                elif event.key == pygame.K_3:
                    brush_size_idx = 2

                else:
                    char = pygame.key.name(event.key).upper()
                    if char in key_map:
                        current_tool = key_map[char]
                        if current_tool != TOOL_TEXT:
                            text_state.cancel()

            # ── mouse down ──
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                clicked_ui = False

                for i, r in enumerate(tool_rects):
                    if r.collidepoint(mx, my):
                        current_tool = tools[i][0]
                        if current_tool != TOOL_TEXT:
                            text_state.cancel()
                        clicked_ui = True
                        break

                for i, r in enumerate(size_rects):
                    if r.collidepoint(mx, my):
                        brush_size_idx = i
                        clicked_ui = True
                        break

                if save_rect.collidepoint(mx, my):
                    _save_canvas(canvas)
                    clicked_ui = True

                if clear_rect.collidepoint(mx, my):
                    canvas.fill(CANVAS_COLOR)
                    text_state.cancel()
                    clicked_ui = True

                for i, r in enumerate(palette_rects):
                    if r.collidepoint(mx, my):
                        current_color = PALETTE[i]
                        clicked_ui    = True
                        break

                if not clicked_ui and my >= CANVAS_TOP:
                    cx_ = mx
                    cy_ = my - CANVAS_TOP

                    if current_tool == TOOL_FILL:
                        flood_fill(canvas, cx_, cy_, current_color)

                    elif current_tool == TOOL_TEXT:
                        text_state.start(cx_, cy_)

                    else:
                        drawing   = True
                        start_pos = (cx_, cy_)
                        prev_pos  = (cx_, cy_)

            # ── mouse motion ──
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    mx, my = event.pos
                    cy_ = my - CANVAS_TOP

                    if current_tool == TOOL_PENCIL:
                        # draw a segment from the previous point to the current one
                        pygame.draw.line(canvas, current_color,
                                         prev_pos, (mx, cy_), brush_size)
                        prev_pos = (mx, cy_)

                    elif current_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, CANVAS_COLOR,
                                           (mx, cy_), brush_size * 4)
                        prev_pos = (mx, cy_)

                    else:
                        # ghost preview for shape / line tools
                        sx, sy = start_pos
                        preview_surf = canvas.copy()
                        draw_shape(preview_surf, current_tool, current_color,
                                   sx, sy, mx, cy_, brush_size)

            # ── mouse up – commit shape ──
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    mx, my = event.pos
                    cy_ = my - CANVAS_TOP
                    sx, sy = start_pos if start_pos else (mx, cy_)

                    # commit non-pencil/eraser shapes
                    if current_tool not in (TOOL_PENCIL, TOOL_ERASER):
                        draw_shape(canvas, current_tool, current_color,
                                   sx, sy, mx, cy_, brush_size)

                    drawing      = False
                    start_pos    = None
                    prev_pos     = None
                    preview_surf = None

        # ═══════════════════════════════════════
        #  RENDER
        # ═══════════════════════════════════════

        # toolbar background (two-tone)
        pygame.draw.rect(screen, TOOLBAR_BG,  (0, 0, WINDOW_WIDTH, TOOLBAR_H))
        pygame.draw.rect(screen, TOOLBAR_BG2, (0, row1_y + btn_h + 2,
                                                WINDOW_WIDTH, TOOLBAR_H - row1_y - btn_h - 2))

        # separator
        pygame.draw.line(screen, BORDER_COLOR,
                         (0, TOOLBAR_H), (WINDOW_WIDTH, TOOLBAR_H), 2)

        # canvas / preview
        blit_surf = preview_surf if preview_surf else canvas
        # If text tool active, draw text preview on top without committing
        if text_state.active:
            tmp = blit_surf.copy()
            text_state.draw_preview(tmp, current_color, text_font)
            screen.blit(tmp, (0, CANVAS_TOP))
        else:
            screen.blit(blit_surf, (0, CANVAS_TOP))

        # tool buttons  (row 1)
        for i, (tid, label, shortcut) in enumerate(tools):
            draw_button(screen, font,
                        f"{label}[{shortcut}]",
                        tool_rects[i],
                        active=(current_tool == tid))

        # size buttons  (row 2)
        for i, r in enumerate(size_rects):
            draw_button(screen, font, size_labels[i], r,
                        active=(brush_size_idx == i),
                        accent=(0, 160, 80))

        # save / clear buttons
        draw_button(screen, font, "Save[Ctrl+S]", save_rect)
        draw_button(screen, font, "Clear",        clear_rect)

        # colour swatches
        for i, r in enumerate(palette_rects):
            pygame.draw.rect(screen, PALETTE[i], r, border_radius=4)
            sel = (255, 255, 255) if current_color == PALETTE[i] else (50, 50, 70)
            pygame.draw.rect(screen, sel, r, 2, border_radius=4)

        # status bar
        mode_hint = " | typing – Enter=confirm  Esc=cancel" if text_state.active else ""
        status = font.render(
            f"Tool: {current_tool}   Size: {brush_size}px{mode_hint}   |   ESC=quit",
            True, (150, 150, 170)
        )
        screen.blit(status, (10, WINDOW_HEIGHT - 18))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# ═══════════════════════════════════════════════════
#  SAVE HELPER
# ═══════════════════════════════════════════════════

def _save_canvas(canvas):
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    pygame.image.save(canvas, filename)
    print(f"[Saved] {filename}")


# ═══════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    main()
