import uuid
import immutables

class Device:
    def __init__(self, name, device_type):
        assert device_type in {"thermostat", "humidifier"}, f"Invalid device type: {device_type}"
        self.__name = name
        self.__id = str(uuid.uuid4())
        self.__type = device_type
        self.__settings = 0
        self.__enabled = False
        self.__output = "0%"
    
    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, new_name):
        self.__name = new_name
    
    @property
    def id(self):
        return self.__id
    
    @property
    def type(self):
        return self.__type
    
    @property
    def settings(self):
        return self.__settings
    
    @settings.setter
    def settings(self, new_setting : float):
        assert isinstance(new_setting, float) or isinstance(new_setting, int), "Settings must be float"
        self.__settings = new_setting

    @property
    def enabled(self):
        return self.__enabled
    
    @enabled.setter
    def enabled(self, enable : bool):
        self.__enabled = enable

    @property
    def output(self):
        return self.__output
   
class Room:
    def __init__(self, name):
        self._name = name
        self._id = str(uuid.uuid4())
        self._devices = {}

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name):
        self._name = new_name
    
    @property
    def id(self):
        return self._id
    
    @property
    def devices(self):
        return self._devices
    
    def add_device(self, deviceType, name):
        device = Device(deviceType, name)
        self._devices[device.id] = device
        return device.id

    def delete_device(self, deviceid):
        del self._devices[deviceid]

class Floor:
    def __init__(self, name):
        self._name = name
        self._id = str(uuid.uuid4())
        self._rooms = {}
        self._admins = set()
        self._read_users = set()

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name):
        self._name = new_name
    
    @property
    def id(self):
        return self._id
    
    @property
    def rooms(self):
        return self._rooms 
    
    def add_room(self, name):
        room = Room(name)
        self.rooms[room.id] = room
        return room.id

    def delete_room(self, roomid):
        del self.rooms[roomid]


class House:
    def __init__(self, name, admin_id = None):
        self._name = name
        self._id = str(uuid.uuid4())
        self._floors = {}
        self._admins = set()
        self._admins.add(admin_id)
        self._read_users = set()
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name):
        self._name = new_name
    
    @property
    def id(self):
        return self._id
    
    @property
    def floors(self):
        return self._floors 
    
    def add_floor(self, name):
        floor = Floor(name)
        self.floors[floor.id] = floor
        return floor.id

    def delete_floor(self, floorid):
        del self.floors[floorid]

    def add_admin(self, admin_id, new_admin):
        if admin_id in self._admins:
            self._admins.add(new_admin)
            new_admin.add_house(self)
        else:
            raise PermissionError("Only admins can add other admins.")

    def add_read_user(self, admin_id, user):
        if admin_id in self._admins:
            self._read_users.add(user)
            user.add_house(self)
        else:
            raise PermissionError("Only admins can add read users.")

class User:
    def __init__(self, name):
        self._name = name
        self._id = str(uuid.uuid4())
        self._houses = {}

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name : str):
        self._name = new_name

    @property
    def id(self):
        return self._id
    
    @property
    def houses(self):
        return self._houses if any(self._id in house._admins for house in self._houses.values()) else {house_id: immutables.Map(readonly = house) for house_id, house in self._houses.items()}
    
    def create_house(self, name : str):
        new_house = House(name, self.id)
        self._houses[new_house.id] = new_house
        return new_house.id

    def add_house(self, house : House):
        self._houses[house.id] = house

    def delete_house(self, houseid : str):
        del self._houses[houseid]
