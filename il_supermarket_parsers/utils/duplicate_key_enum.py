class DuplicateValueEnum:
    """simulate enum with duplicate values"""

    _members = {}

    def __init_subclass__(cls):
        """init memebers"""
        cls._members = {}
        for key, value in cls.__dict__.items():
            if not key.startswith("_"):
                if key in cls._members:
                    raise ValueError(f"Duplicate key found: {key}")
                cls._members[key] = value

    @classmethod
    def keys(cls):
        """Return all unique keys (names)"""
        return list(cls._members.keys())

    @classmethod
    def values(cls):
        """Return all values (including duplicates)"""
        return list(cls._members.values())

    @classmethod
    def get(cls, key):
        """Get the value by key"""
        return cls._members.get(key)

    def __getitem__(self, key):
        """get the class"""
        return self.get(key)
