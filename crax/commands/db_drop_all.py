"""
Command to drop all database tables
"""
from crax.database.command import MetadataCommands, OPTIONS


class DropAll(MetadataCommands):
    def drop_all(self) -> None:
        self.metadata.drop_all()


if __name__ == "__main__":  # pragma: no cover
    # This code excluded from reports 'cause it was tested directly
    drop_all = DropAll(OPTIONS).drop_all
    drop_all()
