import unittest
from objects import *  # Import the correct module with the Smart Home System
import json
import pydantic


class TestSmartHomeSystem(unittest.TestCase):

    def test_device_creation_valid(self):
        device = Device(name="Living Room Thermostat", device_type="thermostat", parent_id="room123")
        self.assertEqual(device.name, "Living Room Thermostat")
        self.assertEqual(device.device_type, "thermostat")
        self.assertIsInstance(device.id, str)
        self.assertFalse(device.enabled)
        self.assertEqual(device.settings, 0)

    def test_device_creation_invalid_type(self):
        with self.assertRaises(AssertionError):
            Device(name="Kitchen Fan", device_type="fan", parent_id="room123")

    def test_device_settings_invalid(self):
        device = Device(name="Bathroom Humidifier", device_type="humidifier", parent_id="room123")
        with self.assertRaises(ValueError):
            device.settings = "25.5"

    def test_room_creation(self):
        room = Room(name="Living Room", parent_id="floor123")
        self.assertEqual(room.name, "Living Room")
        self.assertIsInstance(room.id, str)

    def test_room_add_device(self):
        room = Room(name="Bedroom", parent_id="floor123")
        device_id = room.add_device("NewThermostat", "thermostat")
        self.assertIn(device_id, room.devices)
        self.assertEqual(len(room.devices), 1)

    def test_floor_creation(self):
        floor = Floor(name="First Floor", parent_id="house123")
        self.assertEqual(floor.name, "First Floor")
        self.assertIsInstance(floor.id, str)

    def test_house_creation(self):
        user = User(name="Test User")
        house_id = user.create_house("Test House")
        self.assertEqual(len(user.houses), 1)
        self.assertEqual(user.houses[house_id].name, "Test House")

    def test_user_create_house(self):
        user = User(name="Jake")
        house_id = user.create_house("Jake's House")
        self.assertEqual(len(user.houses), 1)
        self.assertIn(house_id, user.houses)

    def test_user_delete_house(self):
        user = User(name="Sam")
        house_id = user.create_house("Sam's Cabin")
        user.delete_house(house_id)
        self.assertEqual(len(user.houses), 0)

    def test_add_admin_permission(self):
        admin = User(name="AdminUser")
        house_id = admin.create_house("Admin's House")
        new_admin = User(name="New Admin")
        print(admin.houses[house_id].admins)
        print(admin.id)
        admin.houses[house_id].add_admin(admin.id, new_admin)
        self.assertIn(new_admin.id, admin.houses[house_id].admins)

    def test_add_admin_permission_error(self):
        admin = User(name="AdminUser")
        non_admin = User(name="NonAdmin")
        house_id = admin.create_house("Admin House")
        with self.assertRaises(PermissionError):
            admin.houses[house_id].add_admin(non_admin.id, non_admin)

    def test_whole_chain_and_read_user(self):
        admin = User(name="Admin")
        reader = User(name="Reader")
        testhouse = admin.create_house("Test House")
        testfloor = admin.houses[testhouse].add_floor("Test Floor")
        testroom = admin.houses[testhouse].floors[testfloor].add_room("Test Room")
        testdevice = admin.houses[testhouse].floors[testfloor].rooms[testroom].add_device("TestThermostat", "thermostat")

        # Modify device settings
        admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings = 25
        admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].enabled = True

        # Print the data for debugging
        print(json.dumps(admin.model_dump(), indent=4))

        # Ensure the settings are correct
        self.assertEqual(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings, 25)
        self.assertTrue(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].enabled)


if __name__ == "__main__":
    unittest.main()
