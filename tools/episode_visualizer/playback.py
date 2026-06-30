class Playback:
    """Isolates all temporal playback control state"""
    def __init__(self, session):
        self.session = session
        self.current_frame = 0
        self.playing = False
        self.speed = 1.0
        self.loop = False
        self.total_frames = len(session.ticks) if session else 0

    def update(self, dt: float):
        if not self.playing or self.total_frames == 0:
            return
        
        # Calculate frame progression based on delta time and playback speed
        step = int(self.speed * (dt * 60))
        self.current_frame += max(1, step) if self.speed > 0 else step
        
        if self.current_frame >= self.total_frames:
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = self.total_frames - 1
                self.playing = False

    def toggle_play(self):
        self.playing = not self.playing

    def seek(self, frame: int):
        self.current_frame = max(0, min(frame, self.total_frames - 1))

    def step_forward(self):
        self.seek(self.current_frame + 1)

    def step_backward(self):
        self.seek(self.current_frame - 1)

    def set_speed(self, speed: float):
        self.speed = max(0.1, min(speed, 8.0))

    def get_current_tick(self):
        return self.session.get_tick(self.current_frame) if self.session else None