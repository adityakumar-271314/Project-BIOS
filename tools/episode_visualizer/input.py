import pygame

def handle_input(event, controller) -> bool:
    if event.type != pygame.KEYDOWN:
        return False

    # Back out routing safely returning into Episode Browser views
    if event.key == pygame.K_ESCAPE:
        controller.app_state = "BROWSER"
        controller.refresh_browser_list()
        return True

    if not controller.playback:
        return False

    # Structural core operational hotkey triggers
    if event.key == pygame.K_SPACE:
        controller.playback.toggle_play()
        return True
    elif event.key == pygame.K_RIGHT:
        controller.playback.step_forward()
        return True
    elif event.key == pygame.K_LEFT:
        controller.playback.step_backward()
        return True
    elif event.key == pygame.K_1:
        controller.camera.set_mode("FOLLOW")
        return True
    elif event.key == pygame.K_2:
        controller.camera.set_mode("STATIC")
        return True
    elif event.key == pygame.K_3:
        controller.camera.set_mode("FIT")
        return True
            
    return False