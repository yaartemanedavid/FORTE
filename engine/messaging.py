class Request:
    id: str
    action: str

    def __init__(self, req_id: str, action: str):
        self.id = req_id
        self.action = action
