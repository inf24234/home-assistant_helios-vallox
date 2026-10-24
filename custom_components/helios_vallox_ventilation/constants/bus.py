import array

try:
    from .config import MODEL_VALLOX_DIGIT_SE
except ImportError:
    from constants.config import MODEL_VALLOX_DIGIT_SE

# domain
DOMAIN = "helios_vallox_ventilation"
# mapping for the four NTC5k temperature sensors
NTC5K_TEMPERATURES = array.array(
    "i",
    [
        -74,-70,-66,-62,-59,-56,-54,-52,-50,-48,-47,-46,-44,-43,-42,-41,-40,-39,-38,-37,-36,
        -35,-34,-33,-33,-32,-31,-30,-30,-29,-28,-28,-27,-27,-26,-25,-25,-24,-24,-23,-23,-22,
        -22,-21,-21,-20,-20,-19,-19,-19,-18,-18,-17,-17,-16,-16,-16,-15,-15,-14,-14,-14,-13,
        -13,-12,-12,-12,-11,-11,-11,-10,-10,-9,-9,-9,-8,-8,-8,-7,-7,-7,-6,-6,-6,-5,-5,-5,-4,
        -4,-4,-3,-3,-3,-2,-2,-2,-1,-1,-1,-1,0,0,0,1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,5,6,6,6,7,7,
        7,8,8,8,9,9,9,10,10,10,11,11,11,12,12,12,13,13,13,14,14,14,15,15,15,16,16,16,17,17,
        18,18,18,19,19,19,20,20,21,21,21,22,22,22,23,23,24,24,24,25,25,26,26,27,27,27,28,28,
        29,29,30,30,31,31,32,32,33,33,34,34,35,35,36,36,37,37,38,38,39,40,40,41,41,42,43,43,
        44,45,45,46,47,48,48,49,50,51,52,53,53,54,55,56,57,59,60,61,62,63,65,66,68,69,71,73,
        75,77,79,81,82,86,90,93,97,100,100,100,100,100,100,100,100,100
    ]
)
# mapping for valid senders / receivers
BUS_ADDRESSES = {
    "MB*": 0x10,  # all mainboards
    "MB1": 0x11,  # mainboard 1
    "FB*": 0x20,  # alle remote controls
    "FB1": 0x21,  # remote control 1
    "LON": 0x28,  # LON bus module (if any)
    "_HA": 0x2E,  # this HA Python script; we are simulating a remote
    "_SH": 0x2F   # SmartHomeNG Python script; also simulating a remote
}
# mapping bits to fan speeds
FANSPEEDS = {
    1:   1,
    3:   2,
    7:   3,
    15:  4,
    31:  5,
    63:  6,
    127: 7,
    255: 8
}

# Vallox Digit SE post-heating target (register 0xA4) hex encoding:
# 8 discrete levels, NOT on the NTC sensor scale.
# See dirtyha/my-esp8266 (hex2HtCel / htCel2Hex) and valloxesp (htCel2Hex).
HEATING_TARGET_HEX_TO_CELSIUS = {
    0x01: 10,
    0x03: 13,
    0x07: 15,
    0x0F: 18,
    0x1F: 20,
    0x3F: 23,
    0x7F: 25,
    0xFF: 27,
}

# mapping error messages / faults
COMPONENT_FAULTS = {
    0:  'none',
    5:  'supply_air_sensor_fault',
    6:  'co2_alarm',
    7:  'outdoor_air_sensor_fault',
    8:  'exhaust_air_sensor_fault',
    9:  'water_coil_frost_warning',
    10: 'extract_air_sensor_fault'
}
# mapping for registers and coils
REGISTERS_AND_COILS = {
    # Current fanspeed (EC300Pro: 1..8)
    "fanspeed":                {"varid": 0x29, 'type': 'fanspeed',    'bitposition': -1, 'read': True, 'write': True },
    # Fanspeed after switching on
    "initial_fanspeed":        {"varid": 0xA9, 'type': 'fanspeed',    'bitposition': -1, 'read': True, 'write': True },
    # Maximum settable fanspeed
    "max_fanspeed":            {"varid": 0xA5, 'type': 'fanspeed',    'bitposition': -1, 'read': True, 'write': True },
    # NTC5K sensors: outside air temperature
    "temperature_outdoor_air": {"varid": 0x32, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # NTC5K sensors: supply air temperature
    "temperature_supply_air":  {"varid": 0x35, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # NTC5K sensors: return air temperature
    "temperature_extract_air": {"varid": 0x34, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # NTC5K sensors: discharge air temperature
    "temperature_exhaust_air": {"varid": 0x33, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # Current post-heating target temperature on the NTC sensor scale
    "post_heating_target":     {"varid": 0x57, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # various coils in register 0xA3 that are displayed on the remote controls (0..3 read/write, 4..7 readonly)
    # FB LED1: on/off Caution: Remotes will not be switched back on automatically; initial_fanspeed set if done manually.
    "powerstate":              {"varid": 0xA3, 'type': 'bit',         'bitposition':  0, 'read': True, 'write': True },
    # FB LED2: CO2 warning
    "co2_indicator":           {"varid": 0xA3, 'type': 'bit',         'bitposition':  1, 'read': True, 'write': True },
    # FB LED3: Humidity warning
    "rh_indicator":            {"varid": 0xA3, 'type': 'bit',         'bitposition':  2, 'read': True, 'write': True },
    # FB LED4: 0 = summer mode with bypass, 1 = wintermode with heat regeneration (LED is on in winter mode)
    "winter_mode":             {"varid": 0xA3, 'type': 'bit',         'bitposition':  3, 'read': True, 'write': True },
    # FB icon 1: "Clean filter" warning
    "clean_filter":            {"varid": 0xA3, 'type': 'bit',         'bitposition':  4, 'read': True, 'write': False},
    # FB icon 2: Post-heating active
    "post_heating_on":         {"varid": 0xA3, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': False},
    # FB icon 3: Error / fault
    "fault_detected":          {"varid": 0xA3, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # FB icon 4: Service request
    "service_requested":       {"varid": 0xA3, 'type': 'bit',         'bitposition':  7, 'read': True, 'write': False},
    # Summer mode: Activate bypass from this temperature onwards if fresh air °C (outside) < extract air °C (inside)
    "bypass_setpoint":         {"varid": 0xAF, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': True },
    # Post-heating setpoint on the NTC sensor scale
    "post_heating_setpoint":   {"varid": 0xA4, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': True },
    # Pre-heating activation temperature on the NTC sensor scale
    "preheat_setpoint":        {"varid": 0xA7, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': True },
    # Pre / post heating is off (0) / on (1)
    "preheat_status":          {"varid": 0x70, 'type': 'bit',         'bitposition':  7, 'read': True, 'write': True },
    # Frost protection - switch off fresh air ventilator and heating below this temperature; -6 ... +15°C
    "defrost_setpoint":        {"varid": 0xA8, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': True },
    # Frost protection hysteresis - when to switch it on again (defrost_setpoint + (this_value/3)) --> 0x03 = 1°C
    "defrost_hysteresis":      {"varid": 0xB2, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # Boost mode: 0=fireplace  (ignition - no exhaust air in the first 15 minutes of boost); 1=normal boost mode
    "boost_mode":              {"varid": 0xAA, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': True },
    # Switch boost on for 45 minutes (set to 1; will be reset by mainboard automatically)
    "activate_boost":          {"varid": 0x71, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': True },
    # Current boost status (off/on)
    "boost_status":            {"varid": 0x71, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # Remaining minutes of boost if on
    "boost_remaining":         {"varid": 0x79, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # I/O port 0x08: read-only status bits and writable fan-off flags
    "bypass_damper_position":  {"varid": 0x08, 'type': 'bit',         'bitposition':  1, 'read': True, 'write': False},
    "fault_relay":             {"varid": 0x08, 'type': 'bit',         'bitposition':  2, 'read': True, 'write': False},
    # Fresh air vetilator off; set to 1 to switch off; requires to be set twice
    "input_fan_off":           {"varid": 0x08, 'type': 'bit',         'bitposition':  3, 'read': True, 'write': True },
    "preheating_on":           {"varid": 0x08, 'type': 'bit',         'bitposition':  4, 'read': True, 'write': False},
    # Exhaust air vetilator off; set to 1 to switch off; requires to be set twice
    "output_fan_off":          {"varid": 0x08, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': True },
    "external_boost_switch":   {"varid": 0x08, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # rpm of fresh air ventilator (65...100% - pneumatic calibration; default=100)
    "input_fan_percent":       {"varid": 0xB0, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # rpm of exhaust air ventilator (65...100% - pneumatic calibration; default=100)
    "output_fan_percent":      {"varid": 0xB1, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # Service reminder interval in months (used after reset f service reminder)
    "service_interval":        {"varid": 0xA6, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # Remaining months for current service reminder
    "service_due_months":      {"varid": 0xAB, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # Error / fault register. 0 = no fault. see COMPONENT_FAULTS above
    "fault_number":            {"varid": 0x36, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # Current mA/voltage input signal, raw scale 00H...FFH
    "analog_input":            {"varid": 0x2E, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # Humidity reading sensor 1. 33H = 0% RH FFH = 100% RH
    "rh_sensor1_raw":          {"varid": 0x2F, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # Humidity reading sensor 2. 33H = 0% RH FFH = 100% RH
    "rh_sensor2_raw":          {"varid": 0x30, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # Humidity control mode: Automatic humidity level search (0 = manual/off, 1 = automatic/on)
    'humidity_control_mode':   {'varid': 0xAA, 'type': 'bit',         'bitposition':  4, 'read': True, 'write': True },
    # Basic humidity level: AE: 33H = 0% RH, FFH = 100% RH, formula (x-51)/2.04
    'basic_humidity_level':    {'varid': 0xAE, 'type': 'rh_percent',  'bitposition': -1, 'read': True, 'write': True },
    # CO2 - installed sensors
    "co2_sensor1_present":     {"varid": 0x2D, 'type': 'bit',         'bitposition':  1, 'read': True, 'write': False},
    "co2_sensor2_present":     {"varid": 0x2D, 'type': 'bit',         'bitposition':  2, 'read': True, 'write': False},
    "co2_sensor3_present":     {"varid": 0x2D, 'type': 'bit',         'bitposition':  3, 'read': True, 'write': False},
    "co2_sensor4_present":     {"varid": 0x2D, 'type': 'bit',         'bitposition':  4, 'read': True, 'write': False},
    "co2_sensor5_present":     {"varid": 0x2D, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': False},
    # CO2 - measurements
    "co2_reading_upper_byte":  {"varid": 0x2B, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    "co2_reading_lower_byte":  {"varid": 0x2C, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    "co2_setting_upper_byte":  {"varid": 0xB3, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    "co2_setting_lower_byte":  {"varid": 0xB4, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # CO2 - alarm
    "co2_alarm":               {"varid": 0x6D, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
}

# Register set of the Vallox Digit SE (a.k.a. Digit SE / 130 E class).
#
# Based on the Digit SE protocol implementations of kotope/valloxesp
# (valloxesp/vallox_protocol.h, Vallox.cpp, Vallox.h) and dirtyha/my-esp8266,
# both verified with Vallox Digit SE / Digit SE 2 units.
#
# Differences to the Helios default table above:
# - Only registers actually supported by the Digit SE are included. Polling a
#   register that a unit does not implement makes every full read time out
#   (10 retries per register), so unsupported registers must not be read.
# - 0xA3 bit 3 is the writable heating mode (winter/summer switch on the Digit
#   SE; valloxesp maps it to HVAC mode HEAT/FAN).
# - 0x08 bit 1 is the summer mode status on the Digit SE (on Helios it is the
#   bypass damper position).
# - 0x08 bits 3 and 5 are read-only fan running statuses on the Digit SE
#   (on Helios they are writable fan-off flags).
# - 0xA4 is the (post-)heating target temperature, 10..27 °C.
# - Not supported by the Digit SE (therefore not polled here):
#   0x2D (CO2 sensor presence), 0x2E (analog input), 0x57 (post-heating target),
#   0x6D (CO2 alarm), 0x70 (preheat status), 0xA5 (max fanspeed), 0xA7 (preheat
#   setpoint), 0xA8 (defrost setpoint), 0xAE (basic humidity level),
#   0xAF (bypass setpoint), 0xB0/0xB1 (fan rpm calibration), 0xB2 (defrost
#   hysteresis), 0xB3/0xB4 (CO2 setting), 0xAA bit 4 (humidity control mode).
DIGIT_SE_REGISTERS_AND_COILS = {
    # Current fanspeed (Digit SE: 1..8)
    "fanspeed":                {"varid": 0x29, 'type': 'fanspeed',    'bitposition': -1, 'read': True, 'write': True },
    # Fanspeed after switching on
    "initial_fanspeed":        {"varid": 0xA9, 'type': 'fanspeed',    'bitposition': -1, 'read': True, 'write': True },
    # NTC5K sensors. Digit SE register map per dirtyha/my-esp8266 (the
    # registers 0x32..0x35 used by Helios / the SE series do NOT hold the
    # temperatures on the Digit SE - they answer with garbage there):
    # 0x58 = outside air, 0x5A = inside (extract) air,
    # 0x5B = incoming (supply) air, 0x5C = exhaust air
    "temperature_outdoor_air": {"varid": 0x58, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    "temperature_supply_air":  {"varid": 0x5B, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    "temperature_extract_air": {"varid": 0x5A, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    "temperature_exhaust_air": {"varid": 0x5C, 'type': 'temperature', 'bitposition': -1, 'read': True, 'write': False},
    # various coils in register 0xA3 (0..3 read/write, 4..7 readonly)
    # FB LED1: on/off
    "powerstate":              {"varid": 0xA3, 'type': 'bit',         'bitposition':  0, 'read': True, 'write': True },
    # FB LED2: CO2 warning
    "co2_indicator":           {"varid": 0xA3, 'type': 'bit',         'bitposition':  1, 'read': True, 'write': True },
    # FB LED3: Humidity warning
    "rh_indicator":            {"varid": 0xA3, 'type': 'bit',         'bitposition':  2, 'read': True, 'write': True },
    # FB LED4: heating mode on the Digit SE (1 = winter/heat recovery, 0 = summer);
    # valloxesp maps this bit to the HVAC mode HEAT/FAN
    "winter_mode":             {"varid": 0xA3, 'type': 'bit',         'bitposition':  3, 'read': True, 'write': True },
    # FB icon 1: "Clean filter" warning
    "clean_filter":            {"varid": 0xA3, 'type': 'bit',         'bitposition':  4, 'read': True, 'write': False},
    # FB icon 2: (Post-)heating active
    "post_heating_on":         {"varid": 0xA3, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': False},
    # FB icon 3: Error / fault
    "fault_detected":          {"varid": 0xA3, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # FB icon 4: Service request
    "service_requested":       {"varid": 0xA3, 'type': 'bit',         'bitposition':  7, 'read': True, 'write': False},
    # (Post-)heating target temperature. The Digit SE encodes this register
    # with 8 discrete hex levels (10..27 °C), NOT on the NTC sensor scale -
    # see HEATING_TARGET_HEX_TO_CELSIUS below and dirtyha/my-esp8266
    # (hex2HtCel / htCel2Hex).
    "post_heating_setpoint":   {"varid": 0xA4, 'type': 'heating_target', 'bitposition': -1, 'read': True, 'write': True },
    # Boost mode: 0=fireplace (ignition - no exhaust air in the first 15 minutes of boost); 1=normal boost mode
    "boost_mode":              {"varid": 0xAA, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': True },
    # Switch boost/fireplace on (set to 1; will be reset by mainboard automatically)
    "activate_boost":          {"varid": 0x71, 'type': 'bit',         'bitposition':  5, 'read': True, 'write': True },
    # Current boost/fireplace status (off/on)
    "boost_status":            {"varid": 0x71, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # Remaining minutes of boost/fireplace if on
    "boost_remaining":         {"varid": 0x79, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # I/O port 0x08 on the Digit SE: bit 1 is the summer mode status
    # (valloxesp VX_08_FLAG_SUMMER_MODE; on Helios it is the bypass damper
    # position). Verified against a real Digit SE: bit 0 reads 1 while the
    # unit is in winter mode with heat recovery active, so bit 0 is NOT the
    # summer mode on this device. The Digit SE does not report fan-running
    # or front-heating status in this register (bits 3/4/5 stay 0 even
    # while the fans are running) - the fan running states are derived
    # from powerstate + fanspeed instead (see api.py).
    "summer_mode":             {"varid": 0x08, 'type': 'bit',         'bitposition':  1, 'read': True, 'write': False},
    "fault_relay":             {"varid": 0x08, 'type': 'bit',         'bitposition':  2, 'read': True, 'write': False},
    # External fireplace/boost switch active
    "external_boost_switch":   {"varid": 0x08, 'type': 'bit',         'bitposition':  6, 'read': True, 'write': False},
    # Service reminder interval in months (used after reset of service reminder)
    "service_interval":        {"varid": 0xA6, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # Remaining months for current service reminder
    "service_due_months":      {"varid": 0xAB, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': True },
    # NOTE: no fault number register on the Digit SE - register 0x36 is a
    # Helios register and answers with garbage on the Digit SE. Fault state
    # is reported via register 0xA3 bit 6 ("fault_detected").
    # Humidity reading (Digit SE: single sensor at 0x4C per
    # dirtyha/my-esp8266). 33H = 0% RH, FFH = 100% RH; below 0x33 = no
    # sensor installed.
    "rh_sensor1_raw":          {"varid": 0x4C, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    # CO2 - measurements (upper/lower byte; combined = ppm)
    "co2_reading_upper_byte":  {"varid": 0x2B, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
    "co2_reading_lower_byte":  {"varid": 0x2C, 'type': 'dec',         'bitposition': -1, 'read': True, 'write': False},
}

# Register table per device model. Models without an entry use the Helios
# default table (REGISTERS_AND_COILS) above.
MODEL_REGISTERS = {
    MODEL_VALLOX_DIGIT_SE: DIGIT_SE_REGISTERS_AND_COILS,
}

# Bus addressing / write behaviour per device model.
#
# Default (models without a profile) is the proven Helios/SmartHomeNG behaviour:
# reads are sent from the "_HA" address to mainboard 1; writes are broadcast to
# all remote controls and all mainboards and finally sent directly to
# mainboard 1 with a repeated checksum byte.
#
# The Vallox Digit SE expects a panel address as sender (valloxesp uses 0x22,
# dirtyha/my-esp8266 uses panel 1 = 0x21). Writes go from the panel to all
# mainboards, then from mainboard 1 to all panels. The status register 0xA3
# is written to mainboard 1 only (valloxesp setStatusVariable()).
#
# Each write target is a tuple: (sender bus address key, receiver bus address
# key, repeat checksum byte on the telegram).
DEFAULT_MODEL_PROFILE = {
    "read_sender": "_HA",
    "read_receiver": "MB1",
    "write_targets": (
        ("_HA", "FB*", False),
        ("_HA", "MB*", False),
        ("_HA", "MB1", True),
    ),
}

MODEL_PROFILES = {
    MODEL_VALLOX_DIGIT_SE: {
        "read_sender": "FB1",
        "read_receiver": "MB1",
        "write_targets": (
            ("FB1", "MB*", False),
            ("MB1", "FB*", False),
        ),
        # The status register 0xA3 is only sent to mainboard 1 (plus the
        # notification to all panels), like valloxesp setStatusVariable().
        "status_write_targets": (
            ("FB1", "MB1", False),
            ("MB1", "FB*", False),
        ),
        "status_varid": 0xA3,
    },
}


def get_registers_for_model(model):
    """Return the register table for a device model (Helios default if unknown)."""
    return MODEL_REGISTERS.get(model, REGISTERS_AND_COILS)


def get_model_profile(model):
    """Return the bus profile for a device model (Helios default if unknown)."""
    return MODEL_PROFILES.get(model, DEFAULT_MODEL_PROFILE)
