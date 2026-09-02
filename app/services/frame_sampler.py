import time

class FrameSampler:
    """
    Determines if a frame should be kept based on target FPS.
    """
    def __init__(self, target_fps: int):
        self.target_fps = target_fps
        self.last_sampled_time = 0.0
        
    def set_target_fps(self, target_fps: int):
        if target_fps > 0:
            self.target_fps = target_fps

    def should_sample(self, current_time: float = None) -> bool:
        if current_time is None:
            current_time = time.time()
            
        interval = 1.0 / self.target_fps
        
        if (current_time - self.last_sampled_time) >= interval:
            self.last_sampled_time = current_time
            return True
            
        return False
        
    def reset(self):
        self.last_sampled_time = 0.0
