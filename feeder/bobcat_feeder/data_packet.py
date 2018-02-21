from typing import Any, Dict, List, Optional, Union

class DataPacket:
    """Holds data with metadata
       Data is assumed to be stored as byte array, bytes or str.
       UTF-8 assumed
    """
    def __init__(self, data: Any, metadata: Dict) -> None:
        self.data = data
        self.metadata = metadata

    def __eq__(self, other: Any) -> bool:
        """Equality test"""
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other: Any) -> bool:
        """Non-equality test"""
        return not self.__eq__(other)

    def as_bytes(self) -> bytes:
        """Return data as bytes"""
        if isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, str):
            return self.data.encode()
        else:
            return bytes(self.data)

    def as_str(self) -> str:
        """Return data as str (UTF-8)"""
        if isinstance(self.data, str):
            return self.data
        elif isinstance(self.data, bytes):
            return self.data.decode()
        else:
            return bytes(self.data).decode()

    @property
    def format(self) -> str:
        return self.metadata['format']

    @property
    def outputs(self) -> List[str]:
        return self.metadata.get('outputs', [])

    @classmethod
    def create_data_packet(cls, data: Any, format: str, output: Optional[Union[str, List[str]]] = None) -> 'DataPacket':
        meta = {'format': format}  # type: Dict[str, Union[str, List[str]]]
        if output:
            if isinstance(output, str):
                output = [output]
            meta['outputs'] = output
        return cls(data, meta)