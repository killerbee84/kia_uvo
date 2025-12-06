"""Switch for Hyundai / Kia Connect."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HyundaiKiaConnectDataUpdateCoordinator
from .entity import HyundaiKiaConnectEntity

_LOGGER = logging.getLogger(__name__)

SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="ev_battery_precondition_enabled",
        name="Battery Preconditioning",
        icon="mdi:battery-clock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Hyundai / Kia Connect switches."""
    coordinator: HyundaiKiaConnectDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities: list[HyundaiKiaConnectSwitch] = []

    for vehicle_id, vehicle in coordinator.vehicle_manager.vehicles.items():
        for description in SWITCH_DESCRIPTIONS:
            if getattr(vehicle, description.key, None) is not None:
                entities.append(
                    HyundaiKiaConnectSwitch(coordinator, vehicle_id, description)
                )

    async_add_entities(entities)


class HyundaiKiaConnectSwitch(HyundaiKiaConnectEntity, SwitchEntity):
    """Hyundai / Kia Connect Switch."""

    def __init__(
        self,
        coordinator: HyundaiKiaConnectDataUpdateCoordinator,
        vehicle_id: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, vehicle_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{vehicle_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return getattr(self.vehicle, self.entity_description.key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self.entity_description.key == "ev_battery_precondition_enabled":
            await self.hass.async_add_executor_job(
                self.coordinator.vehicle_manager.api.start_battery_preconditioning,
                self.coordinator.vehicle_manager.token,
                self.vehicle,
            )
            # Optimistically update the state
            setattr(self.vehicle, self.entity_description.key, True)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self.entity_description.key == "ev_battery_precondition_enabled":
            await self.hass.async_add_executor_job(
                self.coordinator.vehicle_manager.api.stop_battery_preconditioning,
                self.coordinator.vehicle_manager.token,
                self.vehicle,
            )
            # Optimistically update the state
            setattr(self.vehicle, self.entity_description.key, False)
            self.async_write_ha_state()
