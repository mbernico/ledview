from typing import Tuple
import datetime
import time
import os
import pytz
import asyncio

import rgbmatrix
from rgbmatrix import core
from rgbmatrix import graphics
# https://python-weather.readthedocs.io/en/latest/
import python_weather
# https://pypi.org/project/pynytimes/
from pynytimes import NYTAPI

from colors import Colors
import secrets

# Facts about my display.
_TIME_ZONE = "America/Los_Angeles" # My Local Time Zone
_LOCATION = "Benicia, CA"
_WEATHER_SLEEP = 3600 # Update weather hourly.
_NEWS_SLEEP = 3600 # Update news every hour.
_LED_COLS = 64
_LED_ROWS = 64
_LED_CHAIN = 3
# NOTE: This file must be specified relative to the source code location due to how the bindings are written.
# TODO: Maybe update the original code to fix this someday???
_TIME_FONT_PATH = "fonts/9x15B.bdf"
_DATE_FONT_PATH = "fonts/7x13.bdf"
_WEATHER_FONT_PATH = "fonts/5x7.bdf"


class Display:
    """Setups and drives the LED Matrix display."""
    def __init__(self, cols, rows, chain):
        options = rgbmatrix.RGBMatrixOptions()
        options.rows = cols
        options.cols = rows
        options.chain_length = chain
        self.matrix = rgbmatrix.RGBMatrix(options = options)
        self.date_font = graphics.Font()
        self.time_font = graphics.Font()
        self.weather_font = graphics.Font()
        try: 
            self.date_font.LoadFont(_DATE_FONT_PATH)
            self.time_font.LoadFont(_TIME_FONT_PATH)
            self.weather_font.LoadFont(_WEATHER_FONT_PATH)
        except FileNotFoundError as e:
            e.strerror("The font files can't be opened.")
        
        self.time_zone = pytz.timezone(_TIME_ZONE)

        self.offscreen_canvas = self.matrix.CreateFrameCanvas()
        self.weather = None
        self.weather_update_time = None
        self.nyt = NYTAPI(secrets.NYT_API_KEY, parse_dates=True)
        self.nyt_update_time = None
        self.top_stories = None

    
    async def _maybe_update_weather(self) -> python_weather.forecast.Forecast:
        """Update the weather from our API if it's old enough."""
        if (
            (self.weather_update_time == None) or 
            ((self.weather_update_time - datetime.datetime.now()).total_seconds() > _WEATHER_SLEEP)):
            async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
                self.weather = await client.get(_LOCATION)
                self.weather_update_time = datetime.datetime.now()


    
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
            
    def _draw_date(self) -> None:
        """Draws the date"""
        date = self._get_date()
        date_color = graphics.Color(*Colors.GREEN.value)
        graphics.DrawText(self.offscreen_canvas, self.date_font, 10, self.date_font.baseline * 2 + 10, date_color, date)

    def _draw_time(self) -> None:
        """Draws the time."""
        time_color, current_time = self._get_time_alternating()
        graphics.DrawText(self.offscreen_canvas, self.time_font, 1, self.time_font.baseline, time_color, current_time)

    def _draw_weather(self) -> None:
        """Draws the weather"""
        #weather = asyncio.run(self._get_weather())
        weather_color = graphics.Color(*Colors.PURPLE.value)
        weather_string = f"{self.weather.temperature}" + u'\N{DEGREE SIGN}' + " " + self.weather.wind_direction.value + " " + str(self.weather.wind_speed)
        kind_string = f"{str(self.weather.kind)}"
        graphics.DrawText(self.offscreen_canvas, self.weather_font, 120, 1 + self.weather_font.baseline, weather_color, weather_string)
        graphics.DrawText(self.offscreen_canvas, self.weather_font, 120, 3 + self.weather_font.baseline *2, weather_color, kind_string)
    
    def _get_top_stories(self) -> None:
        titles = []
        if (
            (self.nyt_update_time == None) or 
            ((self.nyt_update_time - datetime.datetime.now()).total_seconds() > _NEWS_SLEEP)):
            self.nyt_update_time = datetime.datetime.now()
            top_stories = self.nyt.top_stories()

            for story in top_stories:
                titles.append(story['title'])
        
            self.top_stories = " ".join(titles)




    def run(self):
        """Driver loop for display."""
        scroll_position = self.offscreen_canvas.width

        while True:
            self.offscreen_canvas.Clear()
            asyncio.run(self._maybe_update_weather())

            self._draw_time()
            self._draw_date()
            self._draw_weather()
            self._get_top_stories()

            news_scroll_len = graphics.DrawText(
                self.offscreen_canvas,
                self.date_font,
                scroll_position,
                self.date_font.baseline * 5 + 5,
                graphics.Color(*Colors.PURPLE.value),
                self.top_stories)
            
            scroll_position -= 1
            if (scroll_position + news_scroll_len < 0):
                scroll_position = self.offscreen_canvas.width


            
            time.sleep(0.05)

            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

def main():
    """Uh, main..."""
    display = Display(_LED_COLS, _LED_ROWS, _LED_CHAIN)
    display.run()

if __name__ == "__main__":
    main()