import pygame
import sys

# ──────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────
WINDOW_WIDTH  = 900
WINDOW_HEIGHT = 650
TOOLBAR_H     = 60          # height of the top toolbar
CANVAS_TOP    = TOOLBAR_H   # canvas starts below toolbar

# Colour palette offered to the user
PALETTE = [
    (0,   0,   0),    # black
    (255, 255, 255),  # white
    (255,   0,   0),  # red
    (0,   255,   0),  # green
    (0,     0, 255),  # blue
    (255, 255,   0),  # yellow
    (255, 128,   0),  # orange
    (128,   0, 255),  # purple
    (0,   255, 255),  # cyan
    (255,   0, 255),  # magenta
]

SWATCH_SIZE   = 30
SWATCH_MARGIN = 6

# Tools
TOOL_PENCIL    = "pencil"
TOOL_RECTANGLE = "rectangle"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"

BG_COLOR     = (30, 30, 30)    # toolbar background
CANVAS_COLOR = (255, 255, 255) # white canvas

# ──────────────────────────────────────────────
#  HELPER – draw a labelled button
# ──────────────────────────────────────────────
def draw_button(surface, font, text, rect, active=False):
    color  = (100, 180, 255) if active else (70, 70, 90)
    border = (200, 220, 255) if active else (120, 120, 140)
    pygame.draw.rect(surface, color,  rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 2, border_radius=6)
    label = font.render(text, True, (240, 240, 240))
    lx = rect.x + (rect.width  - label.get_width())  // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    surface.blit(label, (lx, ly))


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Practice 10 – Paint")
    clock  = pygame.font.SysFont(None, 20)   # re-used for timing
    font   = pygame.font.SysFont(None, 20)

    # ── persistent canvas surface ──
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT - CANVAS_TOP))
    canvas.fill(CANVAS_COLOR)

    # ── state ──
    current_tool  = TOOL_PENCIL
    current_color = PALETTE[0]          # start with black
    brush_size    = 5
    eraser_size   = 20

    drawing       = False               # mouse button held
    start_pos     = None                # for rect / circle drag
    preview_surf  = None                # ghost shape while dragging

    # ── build tool-button rects ──
    tools = [TOOL_PENCIL, TOOL_RECTANGLE, TOOL_CIRCLE, TOOL_ERASER]
    tool_labels = ["Pencil", "Rectangle", "Circle", "Eraser"]
    btn_w, btn_h = 90, 36
    btn_y = (TOOLBAR_H - btn_h) // 2
    tool_rects = []
    for i, _ in enumerate(tools):
        r = pygame.Rect(10 + i * (btn_w + 6), btn_y, btn_w, btn_h)
        tool_rects.append(r)

    # ── palette swatch rects ──
    palette_rects = []
    px_start = 10 + len(tools) * (btn_w + 6) + 20
    for i, _ in enumerate(PALETTE):
        r = pygame.Rect(
            px_start + i * (SWATCH_SIZE + SWATCH_MARGIN),
            (TOOLBAR_H - SWATCH_SIZE) // 2,
            SWATCH_SIZE, SWATCH_SIZE
        )
        palette_rects.append(r)

    # ── main loop ──
    running = True
    while running:
        # ── event handling ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            # ── key shortcuts ──
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    current_tool = TOOL_PENCIL
                elif event.key == pygame.K_r:
                    current_tool = TOOL_RECTANGLE
                elif event.key == pygame.K_c:
                    current_tool = TOOL_CIRCLE
                elif event.key == pygame.K_e:
                    current_tool = TOOL_ERASER
                elif event.key == pygame.K_ESCAPE:
                    running = False

            # ── mouse button down ──
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # check toolbar buttons
                clicked_ui = False
                for i, r in enumerate(tool_rects):
                    if r.collidepoint(mx, my):
                        current_tool = tools[i]
                        clicked_ui = True
                        break
                for i, r in enumerate(palette_rects):
                    if r.collidepoint(mx, my):
                        current_color = PALETTE[i]
                        clicked_ui = True
                        break

                # start drawing on canvas
                if not clicked_ui and my >= CANVAS_TOP:
                    drawing   = True
                    start_pos = (mx, my - CANVAS_TOP)

            # ── mouse motion ──
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    mx, my = event.pos
                    cy = my - CANVAS_TOP
                    if current_tool == TOOL_PENCIL:
                        pygame.draw.circle(canvas, current_color,
                                           (mx, cy), brush_size)
                    elif current_tool == TOOL_ERASER:
                        pygame.draw.circle(canvas, CANVAS_COLOR,
                                           (mx, cy), eraser_size)
                    elif current_tool in (TOOL_RECTANGLE, TOOL_CIRCLE):
                        # build a preview surface (doesn't modify canvas yet)
                        preview_surf = canvas.copy()
                        sx, sy = start_pos
                        if current_tool == TOOL_RECTANGLE:
                            rect = pygame.Rect(
                                min(sx, mx), min(sy, cy),
                                abs(mx - sx), abs(cy - sy)
                            )
                            pygame.draw.rect(preview_surf, current_color,
                                             rect, 2)
                        else:  # circle
                            cx_ = (sx + mx) // 2
                            cy_ = (sy + cy) // 2
                            radius = max(
                                abs(mx - sx), abs(cy - sy)) // 2
                            pygame.draw.circle(preview_surf, current_color,
                                               (cx_, cy_), radius, 2)

            # ── mouse button up ──
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    mx, my = event.pos
                    cy = my - CANVAS_TOP
                    sx, sy = start_pos if start_pos else (mx, cy)

                    if current_tool == TOOL_RECTANGLE:
                        rect = pygame.Rect(
                            min(sx, mx), min(sy, cy),
                            abs(mx - sx), abs(cy - sy)
                        )
                        pygame.draw.rect(canvas, current_color, rect, 2)

                    elif current_tool == TOOL_CIRCLE:
                        cx_ = (sx + mx) // 2
                        cy_ = (sy + cy) // 2
                        radius = max(abs(mx - sx), abs(cy - sy)) // 2
                        pygame.draw.circle(canvas, current_color,
                                           (cx_, cy_), radius, 2)

                    drawing      = False
                    start_pos    = None
                    preview_surf = None

        # ──────────────────────────────────────
        #  DRAWING
        # ──────────────────────────────────────
        screen.fill(BG_COLOR)

        # canvas (or preview)
        if preview_surf:
            screen.blit(preview_surf, (0, CANVAS_TOP))
        else:
            screen.blit(canvas, (0, CANVAS_TOP))

        # toolbar separator line
        pygame.draw.line(screen, (80, 80, 100),
                         (0, TOOLBAR_H), (WINDOW_WIDTH, TOOLBAR_H), 2)

        # tool buttons
        for i, r in enumerate(tool_rects):
            active = (current_tool == tools[i])
            draw_button(screen, font, tool_labels[i], r, active)

        # palette swatches
        for i, r in enumerate(palette_rects):
            pygame.draw.rect(screen, PALETTE[i], r, border_radius=4)
            border = (255, 255, 255) if current_color == PALETTE[i] else (80, 80, 80)
            pygame.draw.rect(screen, border, r, 2, border_radius=4)

        # status label (bottom-left)
        status = font.render(
            f"Tool: {current_tool}   [P]encil [R]ect [C]ircle [E]raser  ESC=quit",
            True, (180, 180, 180)
        )
        screen.blit(status, (10, WINDOW_HEIGHT - 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
