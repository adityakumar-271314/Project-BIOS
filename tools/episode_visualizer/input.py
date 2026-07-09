import pygame

def handle_playback_input(event: pygame.event.Event, scene) -> bool:
    """Handles inputs specifically while an episode is actively playing back."""
    if event.type != pygame.KEYDOWN:
        return False

    # Escape returns to the browser scene context safely
    if event.key == pygame.K_ESCAPE:
        scene.controller.switch_to_scene("BROWSER")
        return True

    if not scene.playback:
        return False

    # --- Playback Engine Controls ---
    if event.key == pygame.K_SPACE:
        scene.playback.toggle_play()
        return True
    elif event.key == pygame.K_r:
        scene.playback.restart()
        return True
    elif event.key == pygame.K_l:
        scene.playback.toggle_loop()
        return True
    elif event.key == pygame.K_RIGHT:
        scene.playback.step_forward()
        return True
    elif event.key == pygame.K_LEFT:
        scene.playback.step_backward()
        return True
    elif event.key == pygame.K_UP:
        scene.playback.adjust_speed(0.25)
        return True
    elif event.key == pygame.K_DOWN:
        scene.playback.adjust_speed(-0.25)
        return True

    # --- Camera View Mode Adjustments ---
    elif event.key == pygame.K_1:
        scene.camera.set_mode("FOLLOW")
        return True
    elif event.key == pygame.K_2:
        scene.camera.set_mode("STATIC")
        scene.camera.reset_static = True
        return True
    elif event.key == pygame.K_3:
        scene.camera.set_mode("FIT")
        return True

    # --- UI Component & Telemetry Presentation Toggles ---
    elif event.key == pygame.K_h:
        scene.hud_overlay.visible = not scene.hud_overlay.visible
        return True
    elif event.key == pygame.K_t:
        scene.timeline_overlay.visible = not scene.timeline_overlay.visible
        return True
    elif event.key == pygame.K_d:
        scene.heading_overlay.visible = not scene.heading_overlay.visible
        return True
    elif event.key == pygame.K_g:
        scene.graphs_overlay.visible = not scene.graphs_overlay.visible
        return True
    elif event.key == pygame.K_c:
        scene.confidence_overlay.visible = not scene.confidence_overlay.visible
        return True
    elif event.key == pygame.K_p:
        scene.renderer.trail_visible = not scene.renderer.trail_visible
        return True
    elif event.key == pygame.K_v:
        scene.renderer.raw_visible = not scene.renderer.raw_visible
        return True

    return False