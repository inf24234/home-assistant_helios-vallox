import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .constants import (
    DOMAIN,
    MODEL_VALLOX_DIGIT_SE,
    SWITCH_ENTITIES,
    SOFTBOOST_SWITCH_ENTITIES,
    filter_entities_for_model,
)
from .device_info import build_device_info, build_entity_id, get_device_model


_LOGGER = logging.getLogger("helios_vallox.switch")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    model = get_device_model(entry)
    is_digit_se = model == MODEL_VALLOX_DIGIT_SE
    entities = [
        HeliosSwitch(coordinator, entry, switch_def)
        for switch_def in filter_entities_for_model(SWITCH_ENTITIES, model)
        # On the Digit SE the native boost is emulated locally (the mainboard
        # does not act on the bus trigger 0x71 bit 5) - dedicated entity below.
        if not (is_digit_se and switch_def["key"] == "activate_boost")
    ]
    if is_digit_se:
        entities.append(HeliosBoostSwitch(coordinator, entry))
    # Per-device Softboost switches.
    # These do not write directly to the ventilation unit.
    entities.extend(
        HeliosSoftBoostSwitch(coordinator, entry, switch_def)
        for switch_def in filter_entities_for_model(SOFTBOOST_SWITCH_ENTITIES, model)
    )
    async_add_entities(entities)


class HeliosSwitch(CoordinatorEntity, SwitchEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, switch_def):
        super().__init__(coordinator.coordinator)
        self._coordinator = coordinator
        self._variable = switch_def["key"]
        self._attr_translation_key = switch_def["key"]
        self._attr_unique_id = f"{entry.entry_id}_{switch_def['key']}"
        self.entity_id = build_entity_id("switch", entry, switch_def["key"])
        self._attr_icon = switch_def.get("icon")
        self._attr_entity_registry_enabled_default = switch_def.get("enabled_default", True)
        entity_category = switch_def.get("entity_category")
        if entity_category:
            self._attr_entity_category = EntityCategory(entity_category)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return build_device_info(self._entry)

    @property
    def is_on(self):
        if self.coordinator.data is None:
            return None
        return bool(self.coordinator.data.get(self._variable))

    async def async_turn_on(self, **kwargs):
        await self._coordinator.turn_on(self._variable)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._coordinator.turn_off(self._variable)
        self.async_write_ha_state()


class HeliosBoostSwitch(CoordinatorEntity, SwitchEntity):
    """Digit SE: emulated native boost switch ("Stoßlüftung aktivieren").

    The Digit SE mainboard does not act on the native bus boost trigger
    (register 0x71 bit 5), so this switch drives the emulated boost
    controller (fixed: max fan speed for 45 minutes; fireplace mode stops
    the exhaust fan for the first 15 minutes) via the coordinator.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, entry):
        super().__init__(coordinator.coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._variable = "activate_boost"

        self._attr_translation_key = "activate_boost"
        self._attr_unique_id = f"{entry.entry_id}_activate_boost"
        self.entity_id = build_entity_id("switch", entry, "activate_boost")
        self._attr_icon = "mdi:fan"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return build_device_info(self._entry)

    async def async_added_to_hass(self) -> None:
        """Register for emulated boost state updates."""
        await super().async_added_to_hass()
        boost = getattr(self._coordinator, "boost", None)
        if boost is not None:
            self.async_on_remove(
                boost.async_add_listener(self.schedule_update_ha_state)
            )

    @property
    def is_on(self):
        """Return the emulated boost state."""
        boost = getattr(self._coordinator, "boost", None)
        return bool(boost is not None and boost.is_active)

    async def async_turn_on(self, **kwargs):
        """Start the emulated boost (routed by the coordinator)."""
        await self._coordinator.turn_on(self._variable)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Stop the emulated boost and restore the previous fan speed."""
        await self._coordinator.turn_off(self._variable)
        self.async_write_ha_state()


class HeliosSoftBoostSwitch(CoordinatorEntity, SwitchEntity):
    """Local per-device Softboost switch without direct bus access."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, entry, switch_def):
        super().__init__(coordinator.coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._variable = switch_def["key"]

        self._attr_translation_key = self._variable
        self._attr_unique_id = f"{entry.entry_id}_{self._variable}"
        self.entity_id = build_entity_id("switch", entry, self._variable)
        self._attr_icon = switch_def.get("icon")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return build_device_info(self._entry)

    async def async_added_to_hass(self) -> None:
        """Register for Softboost state updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.softboost.async_add_listener(self.schedule_update_ha_state)
        )

    @property
    def is_on(self):
        """Return current local Softboost switch state."""
        softboost = self._coordinator.softboost
        if self._variable == "softboost_fireplace_mode":
            return softboost.state.fireplace_mode
        if self._variable == "softboost_active":
            return softboost.is_active
        return False

    async def async_turn_on(self, **kwargs):
        """Turn on local Softboost option or start Softboost."""
        softboost = self._coordinator.softboost
        if self._variable == "softboost_fireplace_mode":
            softboost.state.fireplace_mode = True
            await softboost.async_save()
            self.async_write_ha_state()
            return
        if self._variable == "softboost_active":
            await softboost.async_start()
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off local Softboost option or stop Softboost."""
        softboost = self._coordinator.softboost
        if self._variable == "softboost_fireplace_mode":
            softboost.state.fireplace_mode = False
            await softboost.async_save()
            self.async_write_ha_state()
            return
        if self._variable == "softboost_active":
            await softboost.async_stop()
            self.async_write_ha_state()