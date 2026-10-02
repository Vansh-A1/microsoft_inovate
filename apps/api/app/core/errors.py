class DomainError(Exception):
    def __init__(self, status, code, message, *, details=None, retryable=False):
        self.status, self.code, self.message = status, code, message
        self.details, self.retryable = details or {}, retryable
        super().__init__(code)


def unavailable():
    return DomainError(404, 'RESOURCE_UNAVAILABLE', 'This resource is unavailable in your authorized scope.')
