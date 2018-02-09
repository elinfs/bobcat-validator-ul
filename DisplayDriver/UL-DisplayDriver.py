

"""UL display driver"""

from typing import Dict, List
import logging
import os
import time
import gettext
import pygame
import tzlocal

from bobcat_validator import LOCALEDIR, MSG, SOUNDSDIR
from bobcat_validator.schema_validator import validate_config_schema
from bobcat_validator.validate_request import VALIDATE_RESULT_MSG
from bobcat_mtb.mtb_validate_result import MtbValidateResult, ValidateResult

from . import Display
from .display_device import DisplayDevice

RESOLUTION = WIDTH, HEIGHT = 480, 272
MARGIN = 14

COLOUR_GRAY = 83, 86, 90
COLOUR_BLACK = 0, 0, 0
COLOUR_WHITE = 255, 255, 255
COLOUR_YELLOW = 241, 200, 0
COLOUR_RED = 231, 67, 42

DEFAULT_FONT = "Roboto Bold"
DEFAULT_LOGO = os.path.dirname(__file__) + '/ul.png'

SOUND_FAILED = "failed"
SOUND_GRACED = "graced"
SOUND_SUCCESS = "success"


class SoundGeneric(object):
    """Generic sound driver (used by DisplayGeneric)"""

    def __init__(self, config: Dict) -> None:
        self.sounds = {}  # type: pygame.mixer.Sound
        pygame.mixer.init()
        for sound_id, sound_config in config.items():
            if sound_config['file'].startswith('/'):
                file = sound_config['file']
            else:
                file = SOUNDSDIR + "/" + sound_config['file']
            self.sounds[sound_id] = pygame.mixer.Sound(file)

    def play_tag(self, tag: str) -> None:
        """Play sound by tag"""
        sound = self.sounds.get(tag)
        if sound is not None:
            sound.play()

    def play_status(self, status: str) -> None:
        """Play sound by status"""
        self.play_tag(status)


class DisplayGeneric(Display):
    """UL display driver"""

    def __init__(self, device: DisplayDevice, config: Dict) -> None:
        self.device = device
        self.config = config
        self.tz = tzlocal.get_localzone()
        validate_config_schema(config, "display_generic")
        self.domain = device.dispatcher.domain
        self.translation = device.dispatcher.translation
        environment = config.get('environment')
        if environment is not None:
            for key, value in environment.items():
                logging.info("setenv %s=%s", key, value)
                os.environ[key] = value
        logging.debug("Initializing graphics & sound")
        pygame.init()
        if config.get('screen', True):
            fullscreen = config.get('fullscreen', False)
            flags = 0
            if fullscreen:
                flags = flags | pygame.FULLSCREEN
                pygame.mouse.set_visible(0)
            self.screen = pygame.display.set_mode(RESOLUTION, flags)
            self.status_surface = pygame.Surface((480, 62))
            self.timestamp_surface = pygame.Surface((200, 20))
            if not hasattr(self, 'title'):
                self.title = "Bobcat Validator"
            self.set_background()
            self.idle_text = ""
            self.spacing = config.get('spacing', 4)
        else:
            self.screen = None
        if 'sound' in config:
            self.sound = SoundGeneric(config['sound'])
            self.sound.play_tag('startup')
        else:
            self.sound = None
        self.last_result = None  # type: MtbValidateResult

    def show(self) -> None:
        """Update display"""
        if self.screen:
            if self.status_ready != self.device.ready:
                self.idle(None)
            else:
                self.screen.blit(self.status_surface, (0, 0))
                self.update_timestamp()
                pygame.display.update()
                pygame.event.pump()

    def update_timestamp(self) -> None:
        """Update time on display"""
        timestamp = self.device.dispatcher.realtime.time.astimezone(self.tz).strftime("%Y-%m-%d %H:%M")
        config_time = self.config.get("time", {})
        font = pygame.font.SysFont(config_time.get("font", DEFAULT_FONT), config_time.get("size", 20))
        size = font.size(timestamp)
        ren = font.render(timestamp, True, COLOUR_BLACK)
        self.timestamp_surface.fill(COLOUR_WHITE)
        self.timestamp_surface.blit(ren, (0, 0))
        self.screen.blit(self.timestamp_surface, (WIDTH - MARGIN - size[0], 60))

    def set_background(self) -> None:
        """Setup background"""

        # fill background
        self.screen.fill(COLOUR_GRAY)

        # add logo
        logo_filename = DEFAULT_LOGO
        logo_surface = pygame.image.load(logo_filename).convert_alpha()
        logo_surface = pygame.transform.smoothscale(logo_surface, (34, 34))
        self.screen.blit(logo_surface, (MARGIN, MARGIN))

        # add title
        config_title = self.config.get("title", {})
        font = pygame.font.SysFont(config_title.get("font", DEFAULT_FONT), config_title.get("size", 18))
        size = font.size(self.title)
        ren = font.render(self.title, True, COLOUR_BLACK)
        self.screen.blit(ren, (WIDTH - MARGIN - size[0], 30))

    def text_status(self, lines: List[str], translation: gettext.NullTranslations=None) -> None:
        """Set display status text"""
        if translation is None:
            translation = self.translation
        config_status = self.config.get("status", {})
        font = pygame.font.SysFont(config_status.get("font", DEFAULT_FONT), config_status.get("size", 20))
        font_height = font.get_height() + font.get_ascent() + font.get_descent()
        max_lines = self.status_surface.get_height() / (font_height + self.spacing)
        no_lines = len(lines)
        if no_lines > max_lines:
            no_lines = max_lines
        y_step = self.status_surface.get_height() / no_lines
        y_base = 0
        for text in lines:
            translated = translation.gettext(text)
            size = font.size(translated)
            ren = font.render(translated, True, COLOUR_BLACK)
            pos_x = int((self.status_surface.get_width() - size[0]) / 2)
            pos_y = int(y_base + (y_step - size[1]) / 2)
            self.status_surface.blit(ren, (pos_x, pos_y))
            y_base += y_step

    def idle(self, last_result: MtbValidateResult)-> None:
        """Show idle display"""
        self.status_ready = self.device.ready
        if self.screen and (last_result is None or self.last_result == last_result):
            if self.status_ready:
                self.status_surface.fill(COLOUR_YELLOW)
                self.text_status([self.idle_text, MSG("SHOW_TICKET")])
            else:
                self.status_surface.fill(COLOUR_RED)
                self.text_status([self.idle_text, MSG("NOT_READY")])
            self.show()

    def feedback(self, result: MtbValidateResult) -> None:
        """Emit feedback via display"""
        self.last_result = result
        res = result.best_result
        reason = result.best_reason
        graced = self.device.dispatcher.is_graced_result(res)
        if self.screen:
            product_name = []
            langs = [self.device.dispatcher.language]
            if result.best_ticket_id:
                pid = result.best_participant_id
                ticket = result.ticket_bundle.get_ticket(pid, result.best_ticket_id)
                md = ticket.get_metadata()
                if 'pln' in md:
                    langs.insert(0, md['pln'])
                if 'pds' in md and self.device.dispatcher.products:
                    for prd_id in md['pds']:
                        pn = self.device.dispatcher.products.get_name(pid, prd_id, langs)
                        if pn:
                            product_name.append(pn)
                    if not product_name:
                        product_name.append(MSG("UNKNOWN_PRODUCT"))
            if res == ValidateResult.success:                
                msg = [MSG("SUCCESS")]

            elif graced:                
                msg = [MSG("GRACED")]
            else:                
                msg = [MSG("FAILED")]
            if reason:
                msg.append(reason)
            elif res != ValidateResult.success:
                msg.append(VALIDATE_RESULT_MSG[result.best_result])
            msg += product_name
            self.text_status(msg, gettext.translation(self.domain, localedir=LOCALEDIR, languages=langs))
            self.show()
        if self.sound is not None:
            if res == ValidateResult.success:
                self.sound.play_status(SOUND_SUCCESS)
            elif graced:
                self.sound.play_status(SOUND_GRACED)
            else:
                self.sound.play_status(SOUND_FAILED)