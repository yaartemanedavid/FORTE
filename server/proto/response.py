from typing import List

import bs4


class Response:
    id: int
    reason: str
    custom_payload: List[bs4.Tag] | None

    def __init__(self, resp_id: int, reason: str | None = None, custom_payload: List[bs4.Tag] | None = None):
        self.id = resp_id
        self.reason = reason
        self.custom_payload = custom_payload

    def to_xml(self) -> str:
        soup = bs4.BeautifulSoup('', 'xml')

        attrs = {'ID': self.id}
        if self.reason is not None:
            attrs['Reason'] = self.reason

        tag = soup.new_tag('Response', attrs=attrs)

        if self.custom_payload is not None:
            for custom_tag in self.custom_payload:
                tag.append(custom_tag)

        soup.append(tag)

        res = str(soup)
        return res[res.index('\n') + 1:]


class ResponseMessage:
    xml_payload: str

    def __init__(self, xml_payload):
        self.xml_payload = xml_payload

    @staticmethod
    def from_response(response: Response):
        return ResponseMessage(response.to_xml())
