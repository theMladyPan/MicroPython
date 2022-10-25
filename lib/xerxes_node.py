from xerxes import MsgId, c2b, read_msg, send_msg, PROTOCOL_VERSION_MAJOR, PROTOCOL_VERSION_MIN


class Node:    
    def __init__(self, com: UART, address: int, device_id: int, *, timeout: int=5) -> None:
        self._com = com
        self._addr = address    
        self._dev_id = device_id
        self._timeout = timeout
        self._fetch_handler = lambda:None
    
    def sync(self) -> bool:
        """Handle incoming message if any is present
        """
        if self._com.any():
            msg = read_msg(com=self._com, timeout=self._timeout)
        
            if msg.message_id_bytes == MsgId.ping_req:
                self._handle_ping(return_addr=msg.source)
                return True
            
            elif msg.message_id_bytes == MsgId.fetch:
                self._handle_fetch(return_addr=msg.source, msgid=MsgId.fetch_generic)
                return True
        
        else:
            return False
    
    
    def bind_fetch_handler(self, handler: callable) -> None:
        self._fetch_handler = handler
    
    
    def _send(self, destination: bytes, msgid: MsgId, payload: bytes) -> None:
        send_msg(
            com=self._com, 
            sender=self._addr.to_bytes(1, "little"),
            destination=destination,
            payload=msgid+payload
        )
    
    
    def _handle_ping(self, return_addr: int) -> None:
        """Handle ping request
        """
        self._send(
            destination=return_addr,
            msgid=MsgId.ping_reply,
            payload=c2b(self._dev_id)+c2b(PROTOCOL_VERSION_MAJOR)+c2b(PROTOCOL_VERSION_MIN)
        )
        
    def _handle_fetch(self, return_addr: int, msgid: bytes) -> None:
        self._send(
            destination=return_addr,
            msgid=msgid,
            payload=self._fetch_handler()
        )