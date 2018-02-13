from typing import Dict, List
import logging
import os
import time
import gettext
import pygame

from bobcat_validator import LOCALEDIR, MSG, SOUNDSDIR
from bobcat_validator.schema_validator import validate_config_schema
from bobcat_validator.validate_request import VALIDATE_RESULT_MSG
from bobcat_mtb.mtb_validate_result import MtbValidateResult, ValidateResult

from . import Display
from .display_device import DisplayDevice

RESOLUTION = WIDTH, HEIGHT = 480, 272
MARGIN = 14

COLOR_BLACK = 0, 0, 0
COLOR_WHITE = 255, 255, 255
COLOR_YELLOW = 241, 200, 0
COLOR_GRAY = 83, 86, 90

DEFAULT_FONT = "Roboto"
DEFAULT_LOGO = os.path.dirname(__file__) + '/ul.png'

SOUND_FAILED = "failed"
SOUND_GRACED = "graced"
SOUND_SUCCESS = "success"

class DisplayText:
    def __init__(self, text: str, fontSize: int=40, offset: int=0, color=COLOR_WHITE, translation: gettext.NullTranslations=None) -> None:
        """Creates text surface"""     
        if translation is None:
            translation = self.translation

        self.text = text        
        self.color = color
        self.offset = offset
        self.fontSize = fontSize
        self.font = pygame.font.SysFont(DEFAULT_FONT, self.fontSize, True)
        self.surface = self.font.render(self.text, True, self.color)        

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
    """Generic display driver"""

    def __init__(self, device: DisplayDevice, config: Dict) -> None:
        self.device = device
        self.config = config        
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
            self.header_surface = pygame.Surface((480, 62))
            self.status_surface = pygame.Surface((480, 210))                        
            self.set_background()            
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
                self.screen.blit(self.header_surface, (0, 0))         
                self.screen.blit(self.status_surface,(0, 62))     
                pygame.display.update()
                pygame.event.pump()

    def set_background(self) -> None:
        """Setup background"""

        # fill background
        self.screen.fill(COLOR_GRAY)
        self.status_surface.fill(COLOR_GRAY)
        self.header_surface.fill(COLOR_YELLOW)        

        # add logo
        logo_filename = DEFAULT_LOGO
        logo_surface = pygame.image.load(logo_filename).convert_alpha()
        logo_surface = pygame.transform.smoothscale(logo_surface, (34, 34))
        self.header_surface.blit(logo_surface, (MARGIN, MARGIN))        

    def text_status(self, displayTexts: List[DisplayText], translation: gettext.NullTranslations=None) -> None:
        """Set display status text"""        
        totalTextHeight = 0
        for displayText in displayTexts:            
            totalTextHeight += displayText.font.get_height() + displayText.offset        
        posY = self.status_surface.get_height()/2 - (totalTextHeight/ 2)
        posX = 50
        for displayText in displayTexts:
            offsetY = posY + displayText.offset
            self.status_surface.blit(displayText.surface, (posX, offsetY))
            logging.info("posY: " + str(posY) + " | offsetY: " + str(offsetY) + " | new posY:" + str(offsetY + displayText.font.get_height()) )
            posY = offsetY + displayText.font.get_height()            

    def idle(self, last_result: MtbValidateResult)-> None:
        """Show idle display"""
        self.status_ready = self.device.ready
        if self.screen and (last_result is None or self.last_result == last_result):
            self.status_surface.fill(COLOR_GRAY)
            if self.status_ready:                   
                self.text_status([DisplayText("Hej!", 40, 0, COLOR_YELLOW), DisplayText("Blippa här.", 40, -10)])
            else:                                
                self.text_status([DisplayText("Hoppsan", 40, 0, COLOR_YELLOW), DisplayText("Något är fel,", 26, -10), DisplayText("prata med föraren.", 26, -10)])
            self.show()

    def feedback(self, result: MtbValidateResult) -> None:
        """Emit feedback via display"""
        self.last_result = result
        res = result.best_result
        reason = result.best_reason
        graced = self.device.dispatcher.is_graced_result(res)
        titles = []
        if self.screen:            
            langs = [self.device.dispatcher.language]
            if result.best_ticket_id:
                pid = result.best_participant_id
                ticket = result.ticket_bundle.get_ticket(pid, result.best_ticket_id)
                md = ticket.get_metadata()
                if 'pln' in md:
                    langs.insert(0, md['pln'])

            if res == ValidateResult.success or graced:                                
                titles = titles + DisplayText("Trevlig resa!"))                   
            else:                                
                titles = titles + DisplayText("Ajdå!", 40, 0, COLOR_YELLOW)
                titles = titles + DisplayText("Du har inte", 26, -10)
                titles = titles + DisplayText("en giltig biljett.", 26, -10)
            # if reason:
            
            # elif res != ValidateResult.success:
            
            self.status_surface.fill(COLOR_GRAY)
            self.text_status(titles, gettext.translation(self.domain, localedir=LOCALEDIR, languages=langs))
            self.show()
        if self.sound is not None:
            if res == ValidateResult.success:
                self.sound.play_status(SOUND_SUCCESS)
            elif graced:
                self.sound.play_status(SOUND_SUCCESS)
            else:
                self.sound.play_status(SOUND_FAILED)