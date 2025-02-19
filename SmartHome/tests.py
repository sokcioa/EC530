import unittest
from objects import *

class TestSmartHomeSystem(unittest.TestCase):
    
    def test_device_creation_valid(self):
        device = Device("Living Room Thermostat", "thermostat")
        self.assertEqual(device.name, "Living Room Thermostat")
        self.assertEqual(device.type, "thermostat")
        self.assertIsInstance(device.id, str)
        self.assertFalse(device.enabled)
        self.assertEqual(device.settings, 0)
    
    def test_device_creation_invalid_type(self):
        with self.assertRaises(AssertionError):
            device = Device("Kitchen Fan", "fan")

    def test_device_creation_invalid_name(self):
        with self.assertRaises(AssertionError):
            device = Device(["Kitchen Fan"], "fan")
    
    def test_device_name_setter(self):
        device = Device("Bedroom Thermostat", "thermostat")
        device.name = "Updated Thermostat"
        self.assertEqual(device.name, "Updated Thermostat")
    
    def test_device_settings_setter(self):
        device = Device("Bathroom Humidifier", "humidifier")
        device.settings = float(25.5)
        self.assertEqual(device.settings, 25.5)

    def test_device_settings_invalid(self):
        device = Device("Bathroom Humidifier", "humidifier")
        with self.assertRaises(AssertionError):
            device.settings = "25.5"
    
    def test_device_enabled_setter(self):
        device = Device("Living Room Humidifier", "humidifier")
        device.enabled = True
        self.assertTrue(device.enabled)

    def test_device_enabled_invalid(self):
        device = Device("Bathroom Humidifier", "humidifier")
        with self.assertRaises(AssertionError):
            device.enabled = "25.5"
    
    def test_room_creation(self):
        room = Room("Living Room")
        self.assertEqual(room.name, "Living Room")
        self.assertIsInstance(room.id, str)

    def test_room_invalid_name(self):
        with self.assertRaises(AssertionError):
            room = Room(10)
    
    def test_room_add_device(self):
        room = Room("Bedroom")
        room.add_device("NewThermostat", "thermostat")
        self.assertEqual(len(room.devices), 1)
    
    def test_room_delete_device(self):
        room = Room("Kitchen")
        room.add_device("NewHumidifier", "humidifier")
        device_id = list(room.devices.keys())[0]
        self.assertEqual(len(room.devices), 1)
        room.delete_device(device_id)
        self.assertEqual(len(room.devices), 0)
    
    def test_floor_creation(self):
        floor = Floor("First Floor")
        self.assertEqual(floor.name, "First Floor")
        self.assertIsInstance(floor.id, str)

    def test_floor_invalid_name(self):
        with self.assertRaises(AssertionError):
            floor = Floor([10])
           
    def test_floor_add_room(self):
        floor = Floor("Second Floor")
        floor.add_room("Master Bedroom")
        self.assertEqual(len(floor.rooms), 1)
    
    def test_floor_delete_room(self):
        floor = Floor("Ground Floor")
        floor.add_room("Guest Room")
        self.assertEqual(len(floor.rooms), 1)
        room_id = list(floor.rooms.keys())[0]
        floor.delete_room(room_id)
        self.assertEqual(len(floor.rooms), 0)
    
    def test_house_creation(self):
        house = House("My House", None)
        self.assertEqual(house.name, "My House")
        self.assertIsInstance(house.id, str)
        user = User("test")
        user.create_house("test_house")
        self.assertEqual(len(user.houses), 1)
        
    def test_house_invalid_name(self):
        user = User("test")
        with self.assertRaises(AssertionError):
            house = House(user)
    
    def test_house_add_floor(self):
        house = House("New House", None)
        house.add_floor("Top Floor")
        self.assertEqual(len(house.floors), 1)
    
    def test_house_delete_floor(self):
        house = House("Luxury House", None)
        house.add_floor("Middle Floor")
        floor_id = list(house.floors.keys())[0]
        house.delete_floor(floor_id)
        self.assertEqual(len(house.floors), 0)
    
    def test_user_creation(self):
        user = User("John Doe")
        self.assertEqual(user.name, "John Doe")
        self.assertIsInstance(user.id, str)
    
    def test_user_add_house(self):
        user = User("Jane Doe")
        house = House("Family Home", user.id)
        user.add_house(house)
        self.assertEqual(len(user.houses), 1)
    
    def test_user_create_house(self):
        user = User("Jake")
        user.create_house("Jake's House")
        self.assertEqual(len(user.houses), 1)
    
    def test_user_delete_house(self):
        user = User("Sam")
        house_id = user.create_house("Sam's Cabin")
        user.delete_house(house_id)
        self.assertEqual(len(user.houses), 0)
    
    def test_add_admin_permission(self):
        admin = User("AdminUser")
        house_id =  admin.create_house("Admin's House")
        newadmin = User("New Admin")
        admin.houses[house_id].add_admin(admin.id, newadmin)
        self.assertEqual(len( admin.houses[house_id]._admins), 2)
    
    def test_add_read_user_permission(self):
        admin = User("Admin")
        house = House("SmartHouse", admin.id)
        admin.add_house(house)
        house.add_admin(admin.id, admin)
        read_user = User("ReadUser")
        house.add_read_user(admin.id, read_user)
        self.assertEqual(len(house._read_users), 1)
    
    def test_add_admin_permission_error(self):
        admin = User("AdminUser")
        non_admin = User("NonAdmin")
        houseid = admin.create_house("Admin House")
        with self.assertRaises(PermissionError):
            admin.houses[houseid].add_admin(non_admin.id, non_admin)
    
    def test_add_read_user_permission_error(self):
        admin = User("AdminUser")
        non_admin = User("NonAdmin")
        house = House("House with Admins", admin.id)
        house.add_admin(admin.id, admin)
        with self.assertRaises(PermissionError):
            house.add_read_user(non_admin.id, non_admin)

    def test_whole_chain_and_read_user(self):
        admin = User("Admin")
        reader = User("Reader")
        testhouse = admin.create_house("Test House")
        testfloor = admin.houses[testhouse].add_floor("Test Floor")
        testroom = admin.houses[testhouse].floors[testfloor].add_room("Test Room")
        testdevice = admin.houses[testhouse].floors[testfloor].rooms[testroom].add_device("TestThermostat", "thermostat")
        admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings = 25
        admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].enabled = True
        print(admin.houses)
        print(admin.houses[testhouse].floors)
        print(admin.houses[testhouse].floors[testfloor].rooms)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice])
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].type)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].name)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].enabled)
        print(admin.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].output)
        admin.houses[testhouse].add_read_user(admin.id, reader)
        #try:
        #    reader.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings = 50
        #finally:
        #    print(reader.houses[testhouse].floors[testfloor].rooms[testroom].devices[testdevice].settings)



if __name__ == "__main__":
    unittest.main()
