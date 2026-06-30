import pygame

def handle_input(event, controller) -> bool:
    """
    Central localized interface for structural keyboard controls.
    Returns True if an event was meaningfully consumed.
    """
    if not controller.playback:
        return False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            controller.playback.toggle_play()
            return True
        elif event.key == pygame.K_RIGHT:
            controller.playback.step_forward()
            return True
        elif event.key == pygame.K_LEFT:
            controller.playback.step_backward()
            return True
        elif event.key == pygame.K_UP:
            controller.playback.set_speed(controller.playback.speed + 0.5)
            return True
        elif event.key == pygame.K_DOWN:
            controller.playback.set_speed(controller.playback.speed - 0.5)
            return True
            
    return False