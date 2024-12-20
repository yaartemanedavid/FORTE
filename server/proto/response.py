class ResponseMessage:
    xml_payload: str

    def __init__(self, xml_payload):
        self.xml_payload = xml_payload
