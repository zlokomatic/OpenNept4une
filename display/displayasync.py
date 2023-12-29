from __future__ import annotations
import asyncio
import datetime
import logging
from deepmerge import always_merger

import serial_asyncio
from moonraker_api import MoonrakerListener, MoonrakerClient
from moonraker_api.const import WEBSOCKET_STATE_CONNECTED

from response_actions2 import response_actions, DISPLAYINPUT
import views

logging.basicConfig(
    level=logging.WARNING, format="%(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("Neptune 4 Display").setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

VIEWS = [
    'Prepare',
    'Main',
    'Print',
    'PrepareMove',
    'PrepareTemp',
    'PrepareExtruder',
]

TEMPERATURE_SENSORS = [
    'extruder',
    'heater_bed',
    'heater_bed_outer',
]


class NavigationController:
    def __init__(self, event_loop, display, moonraker):
        self.loop = event_loop
        self.display = display
        self.moonraker = moonraker
        self.views = {}
        self.history = []

        for view_name in VIEWS:
            view = getattr(views, view_name)
            self.views[view_name] = view(event_loop, self, moonraker)

    async def startup(self):
        await self.views['Prepare'].show()

        while True:
            printer_ready = await self._is_printer_ready()
            websocket_ready = self.moonraker.is_connected
            if printer_ready and websocket_ready and self.moonraker.printer_status:
                break
            await asyncio.sleep(1)

        await self._render_navigation()

    async def page(self, page_number, with_history=True):
        if not self.history or self.history[-1] != page_number:
            if with_history:
                self.history.append(page_number)

        await self.display.send_data(f"page {page_number}")
        _LOGGER.debug("Navigating to page %s", page_number)

    async def page_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back_page = self.history[-1]
            await self.page(back_page, False)
        else:
            print("Already at the main page.")

    async def send_data(self, data):
        await self.display.send_data(data)

    async def send_cmd(self, data):
        await self.display.send_cmd(data)

    async def send_cmds(self, data):
        await self.display.send_cmds(data)

    async def send_gcode(self, gcode):
        await self.moonraker.call_method('printer.gcode.script', script=gcode)

    async def update_printer_status(self):
        update_commands = []
        status = self.moonraker.printer_status

        toolhead = status['toolhead']

        update_commands.append(f'nozzletemp.txt="{int(status["extruder"]["temperature"])}°C"')
        update_commands.append(f'nozzletemp_t.txt="{int(status["extruder"]["target"])}°C"')
        update_commands.append(f'bedtemp.txt="{int(status["heater_bed"]["temperature"])}°C"')
        update_commands.append(f'bedtemp_t.txt="{int(status["heater_bed"]["target"])}°C"')

        show_outer_bed = False
        if 'temperature' in status['heater_bed_outer']:
            show_outer_bed = True
            update_commands.append(f'out_bedtemp.txt="{int(status["heater_bed_outer"]["temperature"])}°C"')
            update_commands.append(f'out_bedtemp_t.txt="{int(status["heater_bed_outer"]["target"])}°C"')

        update_commands.append(f'vis q5,{int(show_outer_bed)}')
        update_commands.append(f'vis out_bedtemp,{int(show_outer_bed)}')

        update_commands.append(f'x_pos.txt="{int(toolhead["position"][0])}"')
        update_commands.append(f'y_pos.txt="{int(toolhead["position"][1])}"')
        update_commands.append(f'z_pos.txt="{int(toolhead["position"][2])}"')

        print_stats = status['print_stats']
        gcode_move = status['gcode_move']
        if print_stats['state'] == 'printing':
            update_commands.append(f'p0.pic=68')
            update_commands.append(f'vis cp0,0')
            update_commands.append(f't0.txt="{print_stats["filename"]}')
            update_commands.append(f'printpause.cp0.close()')
            update_commands.append(f'x_pos.txt="X[{int(gcode_move["position"][0])}]')
            update_commands.append(f'y_pos.txt="Y[{int(gcode_move["position"][1])}]"')
            update_commands.append(
                f'nozzletemp.txt="{int(status["extruder"]["temperature"])}/{int(status["extruder"]["target"])}"')
            update_commands.append(f'fanspeed.txt="{int(status["fan"]["speed"])}%"')
            update_commands.append(f'flow_speed.txt="100%"')
            update_commands.append(f'zvalue.txt="{int(gcode_move["position"][2])}"')
            update_commands.append(f'printspeed.txt="100%"')
            update_commands.append(f'printtime.txt="{str(datetime.timedelta(seconds=print_stats["print_duration"]))}"')
            update_commands.append(f't7.txt="{str(datetime.timedelta(seconds=print_stats["total_duration"]))}"')
            update_commands.append(f'printvalue.txt="0"')
            update_commands.append(f'pressure_val.txt="{int(gcode_move["speed"])}mm/s"')

        await self.send_cmds(update_commands)

    async def _render_navigation(self):
        status = self.moonraker.printer_status

        if status['print_stats']['state'] != 'printing':
            await self.views['Main'].show()
        else:
            await self.views['Print'].print_status()

        while True:
            await self.update_printer_status()
            command = self.display.get_command()

            if not command:
                await asyncio.sleep(0.5)
                continue

            await self._handle_command(command)
            await asyncio.sleep(0.5)

    def _split_command(self, command):
        # Types:
        # 65 Button pushed
        # 71 Text input
        # 21 ACK

        try:
            data = {
                "type": DISPLAYINPUT(command[0]),
                "page": int(command[1]),
                "action": int(command[2]),
                "value": int(command[3])
            }

            if data['type'] == DISPLAYINPUT.ACK:
                return

            _LOGGER.debug('Split command data to %s', repr(data))
            return data
        except ValueError as e:
            print(repr(e))
            _LOGGER.error('Command not implemented %s', command)

    async def _handle_command(self, command) -> None:
        # _LOGGER.debug('Handling command %s', command)
        command_data = self._split_command(command)

        if not command_data or command_data['type'] == DISPLAYINPUT.ACK:
            return

        try:
            signature = response_actions[command_data['page']][command_data['type']][command_data['action']]
            view = signature[0]
            method = signature[1]

            if command_data['type'] == DISPLAYINPUT.TEXT:
                arguments = [command_data['value']]
            else:
                arguments = signature[2:]

            func = getattr(self.views[view], method)

            _LOGGER.debug(f"Execute command {signature}")
            await func(*arguments)

        except (KeyError, TypeError) as e:
            print(repr(e))
            _LOGGER.error("No action for response: %s", repr(command_data))

    async def _is_printer_ready(self) -> bool:
        return await self.moonraker.get_klipper_status() == 'ready'


class MoonrakerController(MoonrakerListener, MoonrakerClient):
    printer_status = {}

    def __init__(self, event_loop):
        super().__init__(listener=self, host='127.0.0.1', loop=event_loop)
        self.loop = event_loop

    async def query_printer(self, **kwargs):
        response = await self.call_method('printer.objects.query', **kwargs)

        return response['status']

    async def query_printer_status(self):
        objects = {'toolhead': None, 'print_stats': None}

        for sensor in TEMPERATURE_SENSORS:
            objects[sensor] = None

        status = await self.query_printer(objects=objects)

        self.printer_status = status

        return status

    async def query_temperatures(self):
        objects = {}

        for sensor in TEMPERATURE_SENSORS:
            objects[sensor] = None

        response = await self.query_printer(objects=objects)

        return response

    async def subscribe_printer(self, **kwargs):
        response = await self.call_method('printer.objects.subscribe', **kwargs)
        return response['status']

    async def state_changed(self, state: str) -> None:
        if state == WEBSOCKET_STATE_CONNECTED:
            objects = {'toolhead': None, 'print_stats': None, 'fan': None, 'gcode_move': None}

            for sensor in TEMPERATURE_SENSORS:
                objects[sensor] = None

            self.printer_status = await self.subscribe_printer(objects=objects)

    async def on_notification(self, method: str, data) -> None:
        """Notifies of state updates."""

        # _LOGGER.debug("Received notification %s -> %s", method, data)

        # Subscription notifications
        if method == "notify_status_update":
            message = data[0]
            self.printer_status = always_merger.merge(self.printer_status, message)


class DisplayController(asyncio.Protocol):
    def __init__(self):
        self.command_queue = []
        self.buffer = b''
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        transport.serial.rts = False  # You can manipulate Serial object via transport

    def get_command(self) -> str | None:
        if not self.command_queue:
            return None

        return self.command_queue.pop()

    def data_received(self, data) -> None:
        # self.buffer += data

        #while len(self.buffer) >= 6:
        #    command = self.buffer[0:6]
        #    self.buffer = self.buffer[6:]
        #    print('data received split commands', command, repr(self.buffer))

        self.command_queue.append(data)

    def connection_lost(self, exc) -> None:
        print('port closed')
        self.transport.loop.stop()

    async def send_data(self, data):
        await self.send(data)

    async def send_cmd(self, data):
        await self.send(data)

    async def send_cmds(self, commands):
        if not isinstance(commands, list):
            commands = [commands]

        command_queue = bytearray()
        padding = [0xFF, 0xFF, 0xFF]

        for command in commands:
            command_queue.extend(str.encode(command))
            command_queue.extend(bytes(padding))

        self.transport.serial.write(bytes(command_queue))

    async def send(self, data) -> None:
        padding = [0xFF, 0xFF, 0xFF]
        self.transport.serial.write(bytes(str.encode(data)))
        self.transport.serial.write(bytes(bytearray(padding)))
        await asyncio.sleep(0.05)


async def main(event_loop):
    transport, protocol = await serial_asyncio.create_serial_connection(event_loop,
                                                                        DisplayController,
                                                                        '/dev/ttyS1',
                                                                        baudrate=115200,
                                                                        timeout=0,
                                                                        writeTimeout=0)

    listener = MoonrakerController(event_loop)
    await listener.connect()

    navigation = NavigationController(loop, protocol, listener)
    await navigation.startup()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))
    loop.run_forever()
