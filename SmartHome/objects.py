import uuid
from pydantic import BaseModel, Field
from typing import Dict, List, Set, Optional

houses_db: Dict[str, "House"] = {}
floors_db: Dict[str, "Floor"] = {}
rooms_db: Dict[str, "Room"] = {}
devices_db: Dict[str, "Device"] = {}

class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str  # ID of the room it belongs to
    name: str
    device_type: str
    settings: float = 0
    enabled: bool = False
    output: str = "0%"

    def __init__(self, **data):
        super().__init__(**data)
        assert self.device_type in {"thermostat", "humidifier"}, f"Invalid device type: {self.device_type}"


class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str  # ID of the floor it belongs to
    name: str
    devices: List[str] = Field(default_factory=list)

    def add_device(self, name: str, device_type: str) -> str:
        device = Device(name=name, device_type=device_type, parent_id=self.id)
        self.devices[device.id] = device
        return device.id

    def get_device(self, device_id: str) -> Optional[Device]:
        return self.devices.get(device_id)

    def update_device(self, device_id: str, **kwargs):
        if device_id in self.devices:
            for key, value in kwargs.items():
                setattr(self.devices[device_id], key, value)

    def delete_device(self, device_id: str):
        self.devices.pop(device_id, None)


class Floor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str  # ID of the house it belongs to
    name: str
    rooms: List[str] = Field(default_factory=list)
    admins: List[str] = Field(default_factory=list)
    read_users: List[str] = Field(default_factory=list)

    def add_room(self, name: str) -> str:
        room = Room(name=name, parent_id=self.id)
        self.rooms[room.id] = room
        return room.id

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def update_room(self, room_id: str, **kwargs):
        if room_id in self.rooms:
            for key, value in kwargs.items():
                setattr(self.rooms[room_id], key, value)

    def delete_room(self, room_id: str):
        self.rooms.pop(room_id, None)


class House(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str  # ID of the user who owns it
    name: str
    floors: List[str] = Field(default_factory=list)
    admins: List[str] = Field(default_factory=list)
    read_users: List[str] = Field(default_factory=list)    
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.id not in self.admins:
            self.admins.append(self.parent_id)

    def add_floor(self, name: str) -> str:
        floor = Floor(name=name, parent_id=self.id)
        self.floors[floor.id] = floor
        return floor.id

    def get_floor(self, floor_id: str) -> Optional[Floor]:
        return self.floors.get(floor_id)

    def update_floor(self, floor_id: str, **kwargs):
        if floor_id in self.floors:
            for key, value in kwargs.items():
                setattr(self.floors[floor_id], key, value)

    def delete_floor(self, floor_id: str):
        self.floors.pop(floor_id, None)

    def add_admin(self, admin_id: str, new_admin: "User"):
        if admin_id in self.admins:
            self.admins.append(new_admin.id)
            new_admin.add_house(self)
        else:
            raise PermissionError("Only admins can add other admins.")

    def add_read_user(self, admin_id: str, user: "User"):
        if admin_id in self.admins:
            self.read_users.append(user.id)
            user.add_house(self.id)
        else:
            raise PermissionError("Only admins can add read users.")


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    houses: List[str] = Field(default_factory=list)

    def create_house(self, name: str) -> str:
        new_house = House(name=name, parent_id=self.id)
        houses_db[new_house.id] = new_house
        self.houses.append(new_house.id)
        return new_house.id
    
    def add_house(self, house):
        self.houses[house]

    def get_house(self, house_id: str) -> Optional[House]:
        return self.houses.get(house_id)

    def update_house(self, house_id: str, **kwargs):
        if house_id in self.houses:
            for key, value in kwargs.items():
                setattr(self.houses[house_id], key, value)

    def delete_house(self, house_id: str):
        self.houses.pop(house_id, None)
