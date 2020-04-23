
class Vehicle:
    def __init__(self, client, vehicle):
        self.client = client
        self.vehicle = vehicle

    def is_mobile_access_enabled(self):
        return self.client.get(f'vehicles/{self.id}/mobile_enabled')

    def get_vehicle_data(self):
        return self.client.get(f'vehicles/{self.id}/vehicle_data')

    def wake_up(self):
        return self.client.post(f'vehicles/{self.id}/wake_up')

    def get_state(self):
        vehicles = self.client.get('vehicles')
        vehicles = [vehicle for vehicle in vehicles if vehicle['id'] == self.id]
        if len(vehicles) == 1:
            return vehicles.pop()['state']
        else:
            raise Exception('More than 1 vehicles detected.')

    def get_drive_state(self):
        return self.client.get(f'vehicles/{self.id}/data_request/drive_state')

    def get_charge_state(self):
        return self.client.get(f'vehicles/{self.id}/data_request/charge_state')

    def get_vehicle_state(self):
        return self.client.get(f'vehicles/{self.id}/data_request/vehicle_state')

    @property
    def id(self):
        return self.vehicle['id']

    @property
    def display_name(self):
        return self.vehicle['display_name']

    @property
    def vin(self):
        return self.vehicle['vin']

    @property
    def state(self):
        return self.vehicle['state']