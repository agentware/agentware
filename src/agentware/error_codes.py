class ErrorCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message


AGENT_NOT_FOUND = ErrorCode(20001, "AGENT_NOT_FOUND")
INVALID_AGENT_ID = ErrorCode(20002, "INVALID_AGENT_ID")
