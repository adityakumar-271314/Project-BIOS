from tools.episode_visualizer.replay_session import ReplaySession

class Playback:
    def __init__(self, session: ReplaySession):
        self.session = session
        self.current_frame = 0
        self.playing = False
        self.speed = 1.0
        self.loop = False
        self.total_frames = len(session.ticks) if session else 0
        self.time_accumulator = 0.0
        self.seconds_per_tick = 0.1  # 10Hz sequence data sampling constraint

    def update(self, dt: float):
        if not self.playing or self.total_frames == 0:
            return
        
        self.time_accumulator += dt * self.speed
        
        while self.time_accumulator >= self.seconds_per_tick:
            self.time_accumulator -= self.seconds_per_tick
            
            if self.current_frame >= self.total_frames - 1:
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = self.total_frames - 1
                    self.playing = False
                    self.time_accumulator = 0.0
                    break
            else:
                self.current_frame += 1

    def toggle_play(self):
        self.playing = not self.playing

    def toggle_loop(self):
        self.loop = not self.loop

    def restart(self):
        self.current_frame = 0
        self.time_accumulator = 0.0
        self.playing = True

    def seek(self, frame: int):
        self.current_frame = max(0, min(frame, self.total_frames - 1))
        self.time_accumulator = 0.0

    def step_forward(self):
        if self.current_frame < self.total_frames - 1:
            self.seek(self.current_frame + 1)
        elif self.loop:
            self.seek(0)

    def step_backward(self):
        if self.current_frame > 0:
            self.seek(self.current_frame - 1)
        elif self.loop:
            self.seek(self.total_frames - 1)

    def adjust_speed(self, amount: float):
        # Step modifiers: 0.5x, 1.0x, 2.0x, etc.
        self.speed = max(0.25, min(self.speed + amount, 4.0))

    def get_current_tick(self):
        return self.session.get_tick(self.current_frame) if self.session else None