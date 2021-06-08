class DB:
    def __init__(self, connection, cursor) -> None:
        self.connection = connection
        self.cursor = cursor