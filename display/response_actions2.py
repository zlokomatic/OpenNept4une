from enum import Enum


class DISPLAYINPUT(Enum):
    BUTTON = 0x65
    TEXT = 0x71
    ACK = 0x1a


# format is Page: Eventtype: EventId : Action
response_actions = {
    # Main Menu
    1: {
        DISPLAYINPUT.BUTTON: {
            1: ['Print', 'show'],
            2: ['PrepareMove', 'show'],
            3: ['Settings', 'show'],
            4: ['Level', 'show'],
        }
    },
    # Print page
    2: {
        DISPLAYINPUT.BUTTON: {
            0: ['Print', 'page_back'],
            1: ['Print', 'prev_page'],
            2: ['Print', 'next_page'],
            7: ['Print', 'print_file', 0],
            8: ['Print', 'print_file', 1],
            9: ['Print', 'print_file', 2],
            10: ['Print', 'print_file', 3],
            11: ['Print', 'print_file', 4]
        }
    },
    # Prepare ( Temp )
    6: {
        DISPLAYINPUT.BUTTON: {
            0: ['PrepareTemp', 'page_back'],
            1: ['PrepareTemp', 'extruder_off'],
            2: ['PrepareTemp', 'bed_off'],
            9: ['PrepareTemp', 'outerbed_off'],
            3: ['PrepareTemp', 'material', 'pla'],
            4: ['PrepareTemp', 'material', 'abs'],
            5: ['PrepareTemp', 'material', 'petg'],
            6: ['PrepareTemp', 'material', 'tpu'],
            7: ['PrepareMove', 'show'],
            8: ['PrepareExtruder', 'show'],
        },
        DISPLAYINPUT.TEXT: {
            0: ['PrepareTemp', 'set_extruder_target'],
            1: ['PrepareTemp', 'set_bed_target'],
            2: ['PrepareTemp', 'set_outerbed_target'],
        }
    },
    # Prepare ( Move )
    8: {
        DISPLAYINPUT.BUTTON: {
            0: ['PrepareMove', 'page_back'],
            1: ['PrepareMove', 'move_width', 10, 0.1],
            2: ['PrepareMove', 'move_width', 11, 1],
            3: ['PrepareMove', 'move_width', 12, 10],
            4: ['PrepareMove', 'move_home', 'x'],
            5: ['PrepareMove', 'move_home', 'y'],
            6: ['PrepareMove', 'move_axis', '+', 'z'],
            7: ['PrepareMove', 'move_axis', '-', 'y'],
            8: ['PrepareMove', 'move_axis', '+', 'x'],
            9: ['PrepareMove', 'move_axis', '-', 'x'],
            10: ['PrepareMove', 'move_axis', '+', 'y'],
            11: ['PrepareMove', 'move_axis', '-', 'z'],
            12: ['PrepareMove', 'move_home'],
            13: ['PrepareMove', 'move_home', 'z'],
            14: ['PrepareMove', 'move_toggle_fan'],
            15: ['PrepareTemp', 'show'],
            16: ['PrepareExtruder', 'show'],
        },
    },
    # Prepare ( Extruder )
    9: {
        DISPLAYINPUT.BUTTON: {
            0: ['PrepareExtruder', 'page_back'],
            1: ['PrepareExtruder', 'move', '-'],
            2: ['PrepareExtruder', 'move', '+'],
            3: ['PrepareMove', 'show'],
            4: ['PrepareTemp', 'show'],
        },
        DISPLAYINPUT.TEXT: {
            2: ['PrepareExtruder', 'set_width'],
            3: ['PrepareExtruder', 'set_speed'],
        }
    },
    # Settings ( Factory Settings )
    10: {
    },
    # Settings (Main)
    11: {
        DISPLAYINPUT.BUTTON: {
            0: ['Settings', 'page_back'],
            1: ['page', 12],  # Language
            2: ['page', 32],  # Temperature
            3: ['page', 84],  # Light
            4: ['settings_fan'],
            5: ['settings_motor'],
            6: ['settings_filament_sensor'],
            7: ['page', 10],  # Factory Reset
            8: ['page', 35],  # About
            9: ['page', 42],  # Advanced
        }
    },
    # Print Preview
    18: {
        DISPLAYINPUT.BUTTON: {
            0: ['Print', 'preview_confirm'],
            1: ['Print', 'preview_cancel']
        }
    },
    # Print page
    19: {
        DISPLAYINPUT.BUTTON: {
            0: ['Print', 'settings'],
            1: ['Print', 'pause'],
            2: ['Print', 'stop'],
            3: ['Print', 'led'],
            4: ['Print', 'emergency_shutdown']
        }
    },
    # Filament run out
    20: {
        DISPLAYINPUT.BUTTON : {
        }
    },
    # Filament run out continue
    22: {

    },
    # Stop print ?
    26: {

    },
    # Print settings ( Filament )
    27: {
        0: ['PrintSettingsFilament', 'page_back'], # picc=90 == selected
        1: ['PrintSettingsFilament', 'temperature_type', 'nozzle'], # picc=90 == selected
        2: ['PrintSettingsFilament', 'temperature_type', 'bed'], # picc=89
        3: ['PrintSettingsFilament', 'temperature', 1],
        4: ['PrintSettingsFilament', 'temperature', 5],
        5: ['PrintSettingsFilament', 'temperature', 10],
        6: ['PrintSettingsFilament', 'temperature_set', '+'],
        7: ['PrintSettingsFilament', 'temperature_set', '-'],
        8: ['PrintSettingsFilament', 'temperature_off'],
        10: ['PrintSettingsFilament', 'filament', 'load'],
        11: ['PrintSettingsFilament', 'filament', 'unload'],
        12: ['PrintSettingsSpeed', 'show'],
        13: ['PrintSettingsAdjust', 'show'],
    },
    # Print settings ( Filament ) ( Pro )
    28: {
        0: ['PrintSettingsFilament', 'page_back'], # picc=90 == selected
        1: ['PrintSettingsFilament', 'temperature_type', 'nozzle'], # picc=90 == selected
        2: ['PrintSettingsFilament', 'temperature_type', 'bed'], # picc=89
        3: ['PrintSettingsFilament', 'temperature', 1],
        4: ['PrintSettingsFilament', 'temperature', 5],
        5: ['PrintSettingsFilament', 'temperature', 10],
        6: ['PrintSettingsFilament', 'temperature_set', '+'],
        7: ['PrintSettingsFilament', 'temperature_set', '-'],
        8: ['PrintSettingsFilament', 'temperature_off'],
        9: ['PrintSettingsFilament', 'temperature_type', 'outer_bed'],
        10: ['PrintSettingsFilament', 'filament', 'load'],
        11: ['PrintSettingsFilament', 'filament', 'unload'],
        12: ['PrintSettingsSpeed', 'show'],
        13: ['PrintSettingsAdjust', 'show'],
    },
    37: {
        DISPLAYINPUT.BUTTON: {
            0: ['PrepareExtruder', 'confirm_temp'],
            1: ['PrepareExtruder', 'cancel_temp'],
        }
    },
    91: {
        DISPLAYINPUT.BUTTON: {
            0: ['page', 13],
            1: ['page', 1]
        }
    },
    # Print settings ( Adjust )
    127: {
        DISPLAYINPUT.BUTTON: {

        }
    },
    # Print settings ( Speed )
    135: {
        DISPLAYINPUT.BUTTON: {

        }
    }
}
