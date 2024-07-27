from typing import Tuple
import datetime
import time
import os
import pytz

import rgbmatrix
from rgbmatrix import core
from rgbmatrix import graphics

from colors import Colors

# Facts about my display.
_TIME_ZONE = "America/Los_Angeles" # My Local Time Zone
_LED_COLS = 64
_LED_ROWS = 64
_LED_CHAIN = 3
# NOTE: This file must be specified relative to the source code location due to how the bindings are written.
# TODO: Maybe update the original code to fix this someday???
_FONT_PATH = "fonts/7x13.bdf"
_TIME_FONT_PATH = "fonts/9x15B.bdf"
_DATE_FONT_PATH = "fonts/7x13.bdf"

class Display:
    """Setups and drives the LED Matrix display."""
    def __init__(self, cols, rows, chain, date_font_path, time_font_path, time_zone):
        options = rgbmatrix.RGBMatrixOptions()
        options.rows = cols
        options.cols = rows
        options.chain_length = chain
        self.matrix = rgbmatrix.RGBMatrix(options = options)
        self.date_font = graphics.Font()
        self.time_font = graphics.Font()
        try: 
            self.date_font.LoadFont(date_font_path)
            self.time_font.LoadFont(time_font_path)
        except FileNotFoundError as e:
            e.strerror("The font files can't be opened.")
        
        self.time_zone = pytz.timezone(time_zone)

    
    @staticmethod
    def _get_date() -> Tuple[str, str]:
        """Gets the day of the week and current date and returns as a tuple of strings."""
        date = datetime.date.today().strftime("%A %B %d, %Y")
        return date

    def _get_time_alternating(self) -> str:
        """Gets the current time alternating between UTC and local time."""
        seconds = datetime.datetime.now().strftime("%S")
        tens = seconds[0]
        if int(tens) % 2 == 0:
            time = datetime.datetime.now(pytz.timezone("UTC"))
            time_color = graphics.Color(*Colors.BLUE.value)
        else:
            time = datetime.datetime.now(self.time_zone)
            time_color = graphics.Color(*Colors.RED.value)
        return time_color, time.strftime("%H:%M:%S:%Z")
            
    def _draw_date(self, offscreen_canvas: core.FrameCanvas) -> None:
        """Draws the date"""
        date = self._get_date()
        date_color = graphics.Color(*Colors.GREEN.value)
        graphics.DrawText(offscreen_canvas, self.date_font, 1, self.date_font.baseline * 2 + 2, date_color, date)

    def _draw_time(self, offscreen_canvas: core.FrameCanvas ) -> None:
        """Draws the time."""
        time_color, current_time = self._get_time_alternating()
        graphics.DrawText(offscreen_canvas, self.time_font, 1, self.time_font.baseline, time_color, current_time)


    def run(self):
        """Driver loop for display."""
        offscreen_canvas = self.matrix.CreateFrameCanvas()

        date_color = graphics.Color(255,255,0)
        time_color = date_color
        pos = offscreen_canvas.width

        while True:
            offscreen_canvas.Clear()

            self._draw_time(offscreen_canvas)
            self._draw_date(offscreen_canvas)


            #length = graphics.DrawText(offscreen_canvas, self.font, pos, 0 + self.font.baseline * 2, date_color, current_time + date)
            #pos -=1
            #if (pos + length < 0):
            #    pos = offscreen_canvas.width
            time.sleep(0.05)


            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)









def main():
    """Uh, main..."""
    display = Display(_LED_COLS, _LED_ROWS, _LED_CHAIN, _DATE_FONT_PATH, _TIME_FONT_PATH, _TIME_ZONE)
    display.run()


if __name__ == "__main__":
    main()