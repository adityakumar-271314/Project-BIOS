import pygame

def handle_input(event, controller) -> bool:
    if event.type != pygame.KEYDOWN:
        return False

    if event.key == pygame.K_ESCAPE:
        controller.app_state = "BROWSER"
        controller.refresh_browser_list()
        return True

    # Global interactive command reference helper sheet
    if event.key == pygame.K_F1:
        controller.show_guide = not controller.show_guide
        return True

    if not controller.playback:
        return False

    if event.key == pygame.K_SPACE:
        controller.playback.toggle_play()
        return True
    elif event.key == pygame.K_r:
        controller.playback.restart()
        return True
    elif event.key == pygame.K_l:
        controller.playback.toggle_loop()
        return True
    elif event.key == pygame.K_RIGHT:
        controller.playback.step_forward()
        return True
    elif event.key == pygame.K_LEFT:
        controller.playback.step_backward()
        return True
    elif event.key == pygame.K_UP:
        controller.playback.adjust_speed(0.25)
        return True
    elif event.key == pygame.K_DOWN:
        controller.playback.adjust_speed(-0.25)
        return True
    elif event.key == pygame.K_1:
        controller.camera.set_mode("FOLLOW")
        return True
    elif event.key == pygame.K_2:
        controller.camera.set_mode("STATIC")
        controller.camera.reset_static = True
        return True
    elif event.key == pygame.K_3:
        controller.camera.set_mode("FIT")
        return True

    # Target Structural Presentation Toggles
    elif event.key == pygame.K_h:
        controller.heading_overlay.visible = not controller.heading_overlay.visible
        return True
    elif event.key == pygame.K_t:
        controller.renderer.trail_visible = not controller.renderer.trail_visible
        return True
    elif event.key == pygame.K_g:
        controller.graphs_overlay.visible = not controller.graphs_overlay.visible
        return True
    elif event.key == pygame.K_c:
        controller.confidence_overlay.visible = not controller.confidence_overlay.visible
        return True

    return False