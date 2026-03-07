from __future__ import annotations

import time

class CountDownTimer:
    def __init__(self, countdownsecs: float) -> None:
        self.end_time: float = time.time() + countdownsecs

    def get_countdown_reached_and_timer_string(self) -> tuple[bool, str]:
        # Calculate the time left
        time_left: int = int(max(0, self.end_time - time.time()))
        minutes: int = time_left // 60
        seconds: int = time_left % 60
        return time_left == 0, f"{minutes:02}:{seconds:02}"
