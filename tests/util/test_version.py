from enum import unique
from typing import cast

from packaging.version import Version
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VersionClass(Base):
    __tablename__ = "version"

    id = Column(Integer, primary_key=True)
    version = cast(str, Column(String(255), unique=True))

    @property
    def version_to_class(cls) -> Version:
        return Version(cls.version)


def test_Version_Compare():

    low_version = Version("1.0.0")
    version_class: VersionClass = VersionClass(version="1.0.1")

    assert low_version < version_class.version_to_class
