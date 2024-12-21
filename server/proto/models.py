from bs4 import Tag


class ProtoEntity:
    def __init__(self, data: Tag):
        self.raw_data = data
        pass


class FB(ProtoEntity):
    name: str
    type: str

    def __init__(self, data: Tag):
        super().__init__(data)
        self.name = data.attrs['Name']
        self.type = data.attrs['Type']


class Connection(ProtoEntity):
    source: str
    destination: str

    def __init__(self, data: Tag):
        super().__init__(data)
        self.source = data.attrs['Source']
        self.destination = data.attrs['Destination']


model_index: dict[str, type[ProtoEntity]] = {
    'FB': FB,
    'Connection': Connection,
}
