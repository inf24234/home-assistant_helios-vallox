# Helios Pro / Vallox Digit + SE ventilation control<br/><sup><sub>(for models with  built-in RS485 and Modbus-like Protocol)</sub></sup>


[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg)](https://www.home-assistant.io)
[![Custom integration](https://img.shields.io/badge/Custom%20Integration-%2341BDF5.svg)](https://www.home-assistant.io/getting-started/concepts-terminology)
[![HACS Listing](https://img.shields.io/badge/HACS%20Listing-default-green.svg)](https://github.com/hacs)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Tom-Bom-badil/home-assistant_helios-vallox/graphs/commit-activity)
[![HA Analytics](https://img.shields.io/badge/dynamic/json?url=https://analytics.home-assistant.io/custom_integrations.json&query=$.helios_vallox_ventilation.total&label=HA%20Analytics&suffix=%20installations%20%2A&color=green)](https://analytics.home-assistant.io/)

<sup><sub>* It is estimated that less than ¼ of all HA users have opted in to HA Analytics to share their usage data, so the actual number of installations is likely way higher.</sub></sup>

---

## Overview

👉 This is the Home-Assistant adaptation of my _SmartHomeNG Helios Plugin_, which<br/>
has been running 24/7 since 2014 on my previous home automation system. That plugin<br/>
used to be the first community-made software for these ventilation models. Over the<br/>
years, it became the basis for many other system adaptations.<br/>
<br/>
As I migrated to HA a while ago, I reworked the plugin to be a HA custom integration:

<a href="https://raw.githubusercontent.com/wiki/Tom-Bom-badil/home-assistant_helios-vallox/images/dashboard.png">
  <img width=70% alt="img1" src="https://raw.githubusercontent.com/wiki/Tom-Bom-badil/home-assistant_helios-vallox/images/dashboard.png" />
</a>

👉 Main features of the integration are:

- 🔥 New 🔥 Full `serialx` local and remote serial interface support
- 🔥 New 🔥 Looking for an ESP-based plug&play solution? Check [this guide](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki/esp-plug-and-play-solution)!
- ~70 predefined entities for common ventilation registers and derived values
- auto-detection of rH and CO2 sensors (if installed)
- support of multiple ventilation units
- write access to any writable register with plausibility and validity checks
- a callable register write service for your automations and helpers
- extensive derived calculations (airflow, power, efficiency, temperature balance)
- DIN-based calculation of the required 'design' airflow (individual to your house)
- extra fan entity for integration in Apple Home, Google Home, Alexa, HA Assist etc
- ready-to-use example dashboard, available for copy/paste in the Wiki
- mobile-friendly, multi-language software remote replacing your hardware remote

The software-based remote control is especially useful when your wall-mounted device<br/>became unreadable, or the remote itself is broken or no longer available.<br/>You can simply use your Smartphone to control the ventilation - including a new, much<br/>simplified 'software boost mode':

<a href="https://raw.githubusercontent.com/wiki/Tom-Bom-badil/home-assistant_helios-vallox/images/mobile-dashboard.png">
  <img width=70% alt="img1" src="https://raw.githubusercontent.com/wiki/Tom-Bom-badil/home-assistant_helios-vallox/images/mobile-dashboard.png" />
</a>

The integration has been tested with various RS485 LAN/Wi-Fi adapters.<br/>
For most of them, no soldering, no additional voltage or step-down boards are required.<br/>
Simply use the screw / plug-in terminals of the tested adapters (see [here](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki/Appendix-1-%E2%80%90-Tested-adaptors)).<br/>
Some adapters do not even require external power, they are just running on bus power.

## 📝 Compatible ventilation devices

If your ventilation system has this remote control, it is almost certainly compatible:<br/>

![image](https://github.com/user-attachments/assets/9e7d9699-751b-4856-8c68-797182ef8303)

👉 Over the years, users have reported the successful installation for:<br/>
_`Helios EC 200/300/500 Pro`, `Vallox Digit SE`, `Vallox 130 D`,<br/>
`Vallox 080/090/096/110/121/145/150 SE`, `ValloPlus 350/500/510/910 SE`._<br/>
_(the 130D requires changing a few register numbers due to different addresses; see [old wiki](https://github.com/Tom-Bom-badil/SmartHomeNG-Helios/wiki))._

👉 According to docs I came across, the following models should also work:<br/>
_`Vallox 150/270 SE`, `Vallox Digit SE2` (likely there are more models)<br/>
(Please report back if you got it working on one of these models, thanks in advance!)_

### Vallox Digit SE (dedicated device profile)

This fork adds an explicit **Vallox Digit SE** device model (selectable in the
config flow). The Digit SE protocol differs from the Helios default, so when
this model is selected the integration:

- only polls registers actually supported by the Digit SE (polling unsupported
  registers would otherwise stall every update cycle with read timeouts),
- only creates the entities the Digit SE supports,
- sends reads and writes from a panel bus address (`0x21`), like the verified
  Digit SE implementations [valloxesp](https://github.com/kotope/valloxesp)
  and [dirtyha/my-esp8266](https://github.com/dirtyha/my-esp8266),
- uses the Digit SE write sequence (panel → all mainboards, then mainboard 1 →
  all panels; the status register `0xA3` is written to mainboard 1 only),
- uses the Digit SE register map of [dirtyha/my-esp8266](https://github.com/dirtyha/my-esp8266)
  (the original Digit SE implementation): temperatures are read from `0x58`
  (outside), `0x5A` (extract), `0x5B` (supply) and `0x5C` (exhaust) - the
  Helios/SE-series registers `0x32..0x35` do **not** hold the temperatures on
  the Digit SE, humidity comes from the single register `0x4C`, and the
  supply air temperature setpoint `0xA4` (shown and stored by the panel even
  without a post-heater) is encoded as 8 discrete hex levels of
  10/13/15/18/20/23/25/27 °C (not on the NTC sensor scale),
- maps the Digit SE bit semantics correctly: `0xA3` bit 3 is the writable
  operating mode (the panel key "post-heating on/off and bypass of the heat
  exchanger in summer on/off": winter = heat exchanger active, summer =
  bypass), `0x08` bit 1 is the summer mode status
  (verified on a real Digit SE: bit 0 reads 1 even in winter mode with heat
  recovery active, so bit 0 is not the summer mode on this device),
- detects an installed CO2 sensor from the CO2 reading (the Digit SE has no
  CO2 sensor presence register `0x2D`).

Not available on the Digit SE (therefore hidden): max fanspeed, bypass/preheat/
defrost setpoints, defrost hysteresis, fan rpm calibration, analog input,
CO2 setting/alarm, CO2 sensor presence, basic humidity level, humidity control
mode, a second humidity sensor, effective airflow / electrical power (they
need the fan rpm registers), the fault number register `0x36` (Helios only;
the fault state itself is shown via `fault_detected`), pre-heating status
(the Digit SE has no front heating module) and the Helios post-heating target
register `0x57` (shown as `post_heating_target`; the Digit SE supply air
setpoint lives in `0xA4` instead). Also hidden on a Digit SE without
installed sensors/hardware: the CO2 and humidity indicator switches (the
panel keys for CO2/rH control have no function without the sensors) and the
post-heating status `post_heating_on` (`0xA3` bit 5, the panel LED "heating
coil operating", reads 1 statically when no post-heater is installed, so it
is meaningless - if you retrofit a post-heater (e.g. Vallox ENH 1001) or the
CO2/rH sensors, remove the `exclude_models` lines for `post_heating_on`,
`co2_indicator` and `rh_indicator` in `constants/entities.py`). The Digit SE
service/filter warning interval is 2..9 months (factory default 4), but it is
a **panel** (Reglereinheit H) setting: the mainboard answers polls of the
interval register `0xA6` with a fixed `0x7F` (127) that does not reflect the
panel setting. Out-of-range `0xA6` reads are therefore treated as invalid
(`number.ventilation_service_interval` shows "unavailable" instead of 127;
the number can still be set 2..9, and a valid read-back is shown normally).
Reset the service reminder at the panel (+/-) - the bus-side
`reset_service_reminder` button cannot work on the Digit SE because the true
interval is not readable from the bus. The
supply/extract
fan running sensors are shown as **derived** values (unit powered on +
fan speed >= 1), because the Digit SE does not report a motor running
status in register `0x08` (bits 3/5 stay 0 even while both fans are
running). Softboost fireplace mode is hidden (the exhaust fan cannot be
switched off via the bus; use the native `activate_boost` switch +
`boost_mode` select for the fireplace function instead).

## ⚙️ Compatible / tested ser2net adapters

A list of tested RS485-to-LAN/WiFi adapters can be found [here](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki/Appendix-1-%E2%80%90-Tested-adaptors) on the Wiki.

In addition, [this Wiki page](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki/esp-plug-and-play-solution) contains a detailed step-by-step guide on how to utilize an ESP as ser2WiFi adapter, including a ready-made ESPHome YAML configuration.

## ⚙️ Installation

Installation can be done either through HACS (recommended) or manually.<br/>
Please check [this Wiki page](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki/Installation-and-setup) for installation and configuration.

## 📝 Notes and feedback

👉 Lots of in-depth insights into how everything works, including descriptions of RS485<br/>
fundamentals and the protocol in use, installation instructions, RS485 adapter configuration<br/>
and tests, and a brief project history are available [on the Wiki](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/wiki).<br/>
<br/>
The Wiki also contains a 'Tinkerers corner' section with useful hardware and repair information.

**Contributions welcome!**

💬 Start a [discussion](https://github.com/Tom-Bom-badil/home-assistant_helios-vallox/discussions) if you run into issues.<br/>
✅ If it works for you, please let us know - it's great to hear success stories.<br/>
📬 Pull requests, improvements and feedback in general are always appreciated!

_Thank you for using this integration, and for your feedback! 😊_

---

<sub>* Active installations: Analytics numbers are based on HA Analytics opt-in users,<br/>
estimated to represent less than ¼ of all active HA installations. Click the badge for more info.</sub>
