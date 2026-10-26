import logging
import asyncio

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from time import monotonic
from typing import Any, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import HeliosBase
from .constants import CONF_DEVICE_MODEL, CUSTOM_MODEL, MODEL_VALLOX_DIGIT_SE


_LOGGER = logging.getLogger("helios_vallox.coordinator")
RunFinishedCallback = Callable[[], None]
UpdateMethod = Callable[[], Awaitable[dict[str, Any]]]


class HeliosDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Data coordinator with timestamps for every completed full read."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        update_method: UpdateMethod,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Helios Vallox Data Coordinator",
            update_method=update_method,
            update_interval=timedelta(seconds=59),
        )

        self.last_run: datetime | None = None
        self.last_successful_full_run: datetime | None = None
        self.last_unsuccessful_run: datetime | None = None
        self.last_run_success: bool | None = None

        self._run_finished_listeners: set[RunFinishedCallback] = set()

    @callback
    def async_add_run_finished_listener(
        self,
        update_callback: RunFinishedCallback,
    ) -> Callable[[], None]:
        """Register a listener called after every completed coordinator run."""
        self._run_finished_listeners.add(update_callback)

        @callback
        def remove_listener() -> None:
            self._run_finished_listeners.discard(update_callback)

        return remove_listener

    @callback
    @override
    def _async_refresh_finished(self) -> None:
        """Store run timestamps and notify the connection entity."""
        super()._async_refresh_finished()

        now = dt_util.utcnow()

        self.last_run = now
        self.last_run_success = self.last_update_success

        if self.last_update_success:
            self.last_successful_full_run = now
        else:
            self.last_unsuccessful_run = now

        if self.hass.is_stopping:
            return

        for update_callback in tuple(self._run_finished_listeners):
            try:
                update_callback()
            except Exception:
                self.logger.exception(
                    "Unexpected error updating run-finished listener %s",
                    id(update_callback),
                )


class HeliosCoordinator:
    """Coordinate communication with a Helios/Vallox ventilation unit."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        connection: str,
        config_data: dict | None = None,
    ) -> None:
        self._hass = hass
        self._config_entry = config_entry
        self._connection = connection
        self._model = str(
            (config_data or {}).get(CONF_DEVICE_MODEL) or CUSTOM_MODEL
        )
        self._capabilities = {"co2": False, "rh": False}

        self._helios = HeliosBase(
            hass=hass,
            connection=connection,
            config_data=config_data,
        )
        self._coordinator = HeliosDataUpdateCoordinator(
            hass,
            config_entry,
            self._async_update_data,
        )

    @property
    def coordinator(self) -> HeliosDataUpdateCoordinator:
        """Return the Home Assistant data update coordinator."""
        return self._coordinator

    async def setup_coordinator(self) -> None:
        """Perform the initial full read."""
        await asyncio.sleep(5)
        await self._coordinator.async_config_entry_first_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Read all known registers from the ventilation unit."""
        started = monotonic()

        _LOGGER.debug(
            "Coordinator update started for '%s'.",
            self._config_entry.title,
        )

        try:
            data = await self._hass.async_add_executor_job(
                self._helios.readAllValues
            )
        except Exception as err:
            elapsed = monotonic() - started

            _LOGGER.debug(
                "Coordinator update raised an unexpected exception for "
                "'%s' after %.2f s.",
                self._config_entry.title,
                elapsed,
                exc_info=True,
            )

            raise UpdateFailed(
                f"Unexpected error reading ventilation data: {err}"
            ) from err

        read_elapsed = monotonic() - started

        if not data:
            _LOGGER.debug(
                "Coordinator update failed for '%s' after %.2f s: "
                "full read returned no data.",
                self._config_entry.title,
                read_elapsed,
            )

            raise UpdateFailed(
                "Ventilation unit returned no data during full read"
            )

        unavailable_values = sorted(
            key
            for key, value in data.items()
            if value is None
        )

        _LOGGER.debug(
            "Coordinator full read completed for '%s' in %.2f s: "
            "%d values received, %d unavailable: %s.",
            self._config_entry.title,
            read_elapsed,
            len(data),
            len(unavailable_values),
            ", ".join(unavailable_values) or "none",
        )

        self._capabilities = self._detect_capabilities(data, self._model)

        _LOGGER.debug(
            "Coordinator capabilities for '%s': CO2=%s, rH=%s.",
            self._config_entry.title,
            self._capabilities["co2"],
            self._capabilities["rh"],
        )

        _LOGGER.debug(
            "Coordinator update finished successfully for '%s' "
            "in %.2f s.",
            self._config_entry.title,
            monotonic() - started,
        )

        return data

    def has_capability(self, capability: str) -> bool:
        """Return whether the ventilation supports a capability."""
        return self._capabilities.get(capability, False)

    def supports_variable(self, variable: str, writable: bool = False) -> bool:
        """Return whether the configured device model supports a register."""
        vardef = self._helios._registers.get(variable)
        if vardef is None:
            return False
        return bool(vardef.get("write")) if writable else bool(vardef.get("read"))

    @staticmethod
    def _detect_capabilities(
        data: dict | None,
        model: str = CUSTOM_MODEL,
    ) -> dict[str, bool]:
        """Detect optional hardware features from the latest read data."""
        data = data or {}

        if model == MODEL_VALLOX_DIGIT_SE:
            # The Digit SE has no CO2 sensor presence register (0x2D).
            # Detect an installed CO2 sensor from a plausible reading instead:
            # without a sensor the combined reading is 0 (or unavailable).
            co2 = HeliosCoordinator._is_valid_co2_reading(
                data.get("co2_concentration")
            )
        else:
            co2 = any(
                data.get(f"co2_sensor{i}_present")
                for i in range(1, 6)
            )

        return {
            "co2": co2,
            "rh": any(
                HeliosCoordinator._is_valid_rh_raw(data.get(key))
                for key in (
                    "rh_sensor1_raw",
                    "rh_sensor2_raw",
                )
            ),
        }

    @staticmethod
    def _is_valid_co2_reading(value) -> bool:
        """Return whether a combined CO2 reading represents an installed sensor."""
        try:
            return 0 < int(value) <= 5000
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_valid_rh_raw(value) -> bool:
        """Return whether a raw humidity value represents a sensor."""
        try:
            return 0x33 <= int(value) <= 0xFF
        except (TypeError, ValueError):
            return False

    def write_value(
        self,
        variable,
        value,
        min_value=None,
        max_value=None,
    ):
        """Write a single register or handled pseudo-register."""
        try:
            if variable == "co2_setting_value":
                return self.write_co2_setting_value(
                    value,
                    min_value,
                    max_value,
                )

            result = self._helios.writeValue(
                variable,
                value,
                min_value,
                max_value,
            )

            if result:
                self._update_local_data({variable: value})

            return result

        except Exception as err:
            _LOGGER.error(
                "Error writing %s to %s: %s",
                value,
                variable,
                err,
                exc_info=True,
            )
            return False

    def reset_service_reminder(self):
        """Reset the service reminder."""
        try:
            result = self._helios.resetServiceReminder()

            if result:
                service_interval = None

                if self._coordinator.data:
                    service_interval = self._coordinator.data.get(
                        "service_interval"
                    )

                self._update_local_data(
                    {
                        "service_due_months": service_interval,
                        "service_requested": False,
                    }
                )

            return result

        except Exception as err:
            _LOGGER.error(
                "Error resetting service reminder: %s",
                err,
                exc_info=True,
            )
            return False

    def _update_local_data(self, values: dict) -> None:
        """Update cached values after a write without performing a bus read."""
        new_data = (
            self._coordinator.data.copy()
            if self._coordinator.data
            else {}
        )

        new_data.update(values)

        new_data = self._helios._addCalculationsToReadings(new_data)

        self._hass.loop.call_soon_threadsafe(
            self._coordinator.async_set_updated_data,
            new_data,
        )

    def write_co2_setting_value(
        self,
        value,
        min_value=None,
        max_value=None,
    ):
        """Write the combined 16-bit CO2 setpoint."""
        try:
            min_value = 500 if min_value is None else min_value
            max_value = 2000 if max_value is None else max_value

            value = int(round(float(value) / 50) * 50)
            value = max(
                int(min_value),
                min(int(max_value), value),
            )

            upper = value // 256
            lower = value % 256

            # Write the lower byte first. The mainboard appears to
            # latch/apply the value when the upper byte is written.
            lower_ok = self._helios.writeValue(
                "co2_setting_lower_byte",
                lower,
                0,
                255,
            )
            upper_ok = self._helios.writeValue(
                "co2_setting_upper_byte",
                upper,
                0,
                255,
            )

            if upper_ok and lower_ok:
                self._update_local_data(
                    {
                        "co2_setting_lower_byte": lower,
                        "co2_setting_upper_byte": upper,
                        "co2_setting_value": value,
                    }
                )
                return True

            return False

        except Exception as err:
            _LOGGER.error(
                "Error writing CO2 setting value %s: %s",
                value,
                err,
                exc_info=True,
            )
            return False

    def _uses_emulated_boost(self) -> bool:
        """Return True if the native boost switch is emulated locally.

        The Vallox Digit SE mainboard stores writes to the native boost
        trigger (register 0x71 bit 5) but never acts on them (verified on a
        real unit), so for this model the boost is emulated with a timed
        fan-speed write instead of the bus command.
        """
        return (
            self._model == MODEL_VALLOX_DIGIT_SE
            and getattr(self, "boost", None) is not None
        )

    async def _async_set_emulated_boost(self, active: bool) -> bool:
        """Start or stop the emulated boost for models without native support."""
        boost = getattr(self, "boost", None)
        if boost is None:
            return False
        if active:
            if not await boost.async_start():
                _LOGGER.error(
                    "Failed to start emulated boost (Stoßlüftung) for '%s'.",
                    self._config_entry.title,
                )
                return False
            return True
        await boost.async_stop()
        return True

    async def turn_on(self, variable):
        """Turn on a writable bit variable."""
        if variable == "activate_boost" and self._uses_emulated_boost():
            await self._async_set_emulated_boost(True)
            return
        await self._hass.async_add_executor_job(
            self.write_value,
            variable,
            1,
        )

    async def turn_off(self, variable):
        """Turn off a writable bit variable."""
        if variable == "activate_boost" and self._uses_emulated_boost():
            await self._async_set_emulated_boost(False)
            return
        await self._hass.async_add_executor_job(
            self.write_value,
            variable,
            0,
        )
