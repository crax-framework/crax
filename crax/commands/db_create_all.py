"""
Yet another way to create database from models, defined in project's applications.
Also database can be created using "migrate" command
"""

from crax.database.command import MetadataCommands, OPTIONS


class CreateAll(MetadataCommands):
    def create_all(self) -> None:
        self.metadata.create_all()


if __name__ == "__main__":  # pragma: no cover
    # This code excluded from reports 'cause it was tested directly
    create_all = CreateAll(OPTIONS).create_all
    create_all()
