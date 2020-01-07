import json
import logging
import os
import subprocess

from simple_pi_servo_wrapper import Servo
from stateless_slack_RTM_bot import SlackBot
from sys import exit


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

SLACK_CONFIG_FILEPATH = 'config/slack/bot_config.json'

SERVO_CONFIG_FILEPATH = 'config/motor/HS-425BB.specs.json'
SERVO_CONFIG_FALLBACK_FILEPATH = 'config/motor/HS-425BB.specs.immutable.json'

class GateBot:
    def __init__(self):
        self.client = SlackBot(SLACK_CONFIG_FILEPATH)

    def kill_bot(self):
        exit()

    def ip(self):
        result = subprocess.run(['ip', 'addr'], stdout=subprocess.PIPE, text=True)
        return result.stdout

    def _modify_config(self, filepath, key, value):
        with open(filepath, 'r') as f:
            config = json.loads(f.read())

        config[key] = value

        with open(filepath, 'w') as f:
            f.write(json.dumps(config, indent=2))
        return 'Success'

    def modify_slack_config(self, key, value):
        return self._modify_config(SLACK_CONFIG_FILEPATH, key, value)

    def get_servo_config(self):
        with open(SERVO_CONFIG_FILEPATH, 'r') as f:
            string = f.read()
        return string

    def set_servo_home_position(self, degrees):
        degrees = int(degrees)
        return self._modify_config(SERVO_CONFIG_FILEPATH, 'home_position_degrees', degrees)

    def move_servo(self, degrees):
        degrees = int(degrees)
        self.servo.move_to_position(degrees)


    def set_avatar(self, emoji):
        return self.modify_slack_config('response_avatar', emoji)

    def set_botname(self, name):
        return self._modify_slack_config('response_username', name)

    def start(self):
        self.client.register_function('ip',
                                      self.ip,
                                      'Returns the result of "ip addr" so you can SSH',
                                      admin_only=True)

        self.client.register_function('restart',
                                      self.kill_bot,
                                      'Restarts this bot in order to reload config',
                                      admin_only=True)

        self.client.register_function('set_avatar',
                                      self.set_avatar,
                                      'Sets the avatar the bot responds with. Example '
                                      'usage: "set_avatar :heart:"',
                                      admin_only=True)

        self.client.register_function('set_botname',
                                      self.set_botname,
                                      'Sets the name this bot responds under. Currently '
                                      'only accepts 1 word. Example usage: '
                                      '"set_botname Beakman"',
                                      admin_only=True)

        # Try to instantiate servo
        servo_failed = True
        try:
            self.servo = Servo(SERVO_CONFIG_FILEPATH, 12)
            servo_failed = False
        except Exception:
            pass
        if servo_failed:
            try:
                self.servo = Servo(SERVO_CONFIG_FALLBACK_FILEPATH, 12)
                servo_failed = False
            except:
                pass

        self.client.register_function('get_servo_config',
                                      self.get_servo_config,
                                      'Returns the current settings for the motor.',
                                      admin_only=True)

        self.client.register_function('set_servo_home_position',
                                      self.set_servo_home_position,
                                      'Sets the position the motor should start in when '
                                      'the device is powered. Example usage: '
                                      '"set_servo_home_position -5"',
                                      admin_only=True)

        if not servo_failed:
            self.client.register_function('move_servo',
                                          self.move_servo,
                                          'Moves servo to hold position. Example usage: '
                                          '"move_servo -20"',
                                          admin_only=True)

        self.client.start()




if __name__ == '__main__':
    gate_bot = GateBot()
    gate_bot.start()
