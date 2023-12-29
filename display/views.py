import asyncio
import glob


class View:
    def __init__(self, loop, navigation, moonraker):
        self.loop = loop
        self.navigation = navigation
        self.moonraker = moonraker

    async def show(self):
        pass

    async def page_back(self):
        await self.navigation.page_back()


class Prepare(View):
    async def show(self):
        await self.navigation.page(109, False)


class Main(View):

    async def show(self):
        await self.navigation.page(1)


class Print(View):
    files = []
    page = 0
    files_per_page = 5
    file_to_print = None
    gcode_root = '/home/mks/printer_data/gcodes'

    async def show(self):
        await self._refresh_files()
        await self._refresh_page()
        await self._show_file_list()

    async def prev_page(self):
        if self.page >= 1:
            self.page -= 1
            await self._refresh_page()
            await self._show_file_list()

    async def next_page(self):
        if (self.page * self.files_per_page) <= len(self.files):
            self.page += 1
            await self._refresh_page()
            await self._show_file_list()

    async def print_file(self, slot):
        offset = self.page * self.files_per_page + slot
        file_data = self.files[offset]

        await self.navigation.page(18, False)

        filename = file_data['filename']
        self.file_to_print = filename
        print_preview_cmds = [f't0.txt="{filename}"']

        if 'thumbnail' in file_data:
            print(file_data['thumbnail'])

        await self.navigation.send_cmds(print_preview_cmds)

    async def print_status(self):
        await self.navigation.page(19, False)

    async def preview_confirm(self):
        if not self.file_to_print:
            return

        filename = self.file_to_print['filename']
        await self.moonraker.call_method('printer.print.start', filename=filename)

    async def preview_cancel(self):
        self.file_to_print = None
        await self.show()

    async def _refresh_page(self):
        await self.navigation.page(2)

    async def _refresh_files(self):
        roots = await self.moonraker.call_method('server.files.roots')
        self.gcode_root = next(filter(lambda root_data: root_data['name'] == 'gcodes', roots))['path']

        print_files = await self.moonraker.call_method('server.files.list', root='gcodes')
        for file_data in print_files:
            filename = file_data['path']
            metadata = await self.moonraker.call_method('server.files.metadata', filename=filename)

            thumbnail = None

            if 'thumbnails' in metadata:
                thumbnail = metadata['thumbnails'][0]

            self.files.append({'filename': file_data['path'], 'thumbnail': thumbnail})

    async def _show_file_list(self):
        file_list_commands = []
        offset = self.page * self.files_per_page
        cnt = 10
        for idx in range(offset, offset + self.files_per_page):
            if idx >= len(self.files):
                break

            file_data = self.files[idx]

            file_list_commands.append(f't{cnt}.txt="{file_data["filename"]}"')
            # File: 193
            # Empty: 194
            # Directory: 195
            file_list_commands.append(f'p{cnt}.pic=193')
            cnt += 1
        await self.navigation.send_cmds(file_list_commands)


class PrepareMove(View):
    move_distance = 1

    async def show(self):
        await self.navigation.page(8)
        await self.navigation.send_cmd(f"p0.pic={11}")  # Initialize to 1

    async def move_width(self, button_id, width):
        self.move_distance = width
        await self.navigation.send_cmd(f"p0.pic={button_id}")

    async def move_home(self, axis=''):
        await self.navigation.send_gcode(f"G28 {axis}")

    async def move_axis(self, operator, axis):
        distance = self.move_distance
        await self.navigation.send_gcode('G91')  # Set to relative positioning
        await self.navigation.send_gcode(f'G1 {axis} {operator}{distance}')  # Move axis
        await self.navigation.send_gcode('G90')  # Set back to absolute positioning

    async def move_toggle_fan(self):
        status = self.moonraker.printer_status

        fan = status['fan']

        if fan['speed'] == 0:
            await self.navigation.send_gcode('M106 S255')
        else:
            await self.navigation.send_gcode('M106 S0')


class PrepareTemp(View):

    async def show(self):
        await self.navigation.page(6)
        status = self.moonraker.printer_status
        commands = [f'nozzle.txt="{int(status["extruder"]["target"])}"',
                    f'bed.txt="{int(status["heater_bed"]["target"])}"']

        if 'target' in status['heater_bed_outer']:
            commands.append(f'out_bed.txt="{int(status["heater_bed_outer"]["target"])}"')

        await self.navigation.send_cmds(commands)

    async def extruder_off(self):
        await self.navigation.send_gcode('SET_HEATER_TEMPERATURE heater=extruder target=0')
        await self.navigation.send_cmd('nozzle.txt="0"')

    async def bed_off(self):
        await self.navigation.send_gcode('SET_HEATER_TEMPERATURE heater=heater_bed target=0')
        await self.navigation.send_cmd('bed.txt="0"')

    async def outerbed_off(self):
        await self.navigation.send_gcode('SET_HEATER_TEMPERATURE heater=heater_bed_outer target=0')
        await self.navigation.send_cmd('out_bed.txt="0"')

    async def set_extruder_target(self, target):
        await self.navigation.send_gcode(f'SET_HEATER_TEMPERATURE heater=extruder target={target}')
        await self.navigation.send_cmd(f'nozzle.txt="{int(target)}"')

    async def set_bed_target(self, target):
        await self.navigation.send_gcode(f'SET_HEATER_TEMPERATURE heater=heater_bed target={target}')
        await self.navigation.send_cmd(f'bed.txt="{int(target)}"')

    async def set_outer_bed_target(self, target):
        await self.navigation.send_gcode(f'SET_HEATER_TEMPERATURE heater=heater_bed_outer target={target}')
        await self.navigation.send_cmd(f'out_bed.txt="{int(target)}"')

    async def material(self, material_type):
        extruder = 0
        bed = 0
        if material_type == 'pla':
            extruder = 205
            bed = 60
        elif material_type == 'abs':
            extruder = 240
            bed = 80
        elif material_type == 'petg':
            extruder = 220
            bed = 70
        elif material_type == 'tpu':
            extruder = 230
            bed = 50

        await self.set_extruder_target(extruder)
        await self.set_bed_target(bed)


class PrepareExtruder(View):
    width = 50
    speed = 150
    extruder_target = 170

    async def show(self):
        await self.navigation.page(9)

        status = self.moonraker.printer_status

    async def move(self, direction):
        status = self.moonraker.printer_status

        if status['extruder']['temperature'] < self.extruder_target:
            await self.navigation.page(37, False)
            return

        await self.navigation.send_gcode('M83')
        await self.navigation.send_gcode(f'G1 E{direction}{self.width} F{self.speed}')

    async def confirm_temp(self):
        await self.navigation.send_gcode(f'SET_HEATER_TEMPERATURE heater=extruder target={self.extruder_target}')

    async def cancel_temp(self):
        await self.navigation.page(9, False)

    async def set_width(self, width):
        # TODO: Check Boundaries
        self.width = width
        await self.navigation.send_cmd(f'filamentlength.txt="{self.width}"')

    async def set_speed(self, speed):
        # TODO: Check Boundaries

        self.speed = speed
        await self.navigation.send_cmd(f'filamentspeed.txt="{self.speed}"')

class Settings(View):
    pass

class Level(View):
    pass