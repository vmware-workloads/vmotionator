class VMotionatorException(Exception):
    def __init__(self, message: str):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
