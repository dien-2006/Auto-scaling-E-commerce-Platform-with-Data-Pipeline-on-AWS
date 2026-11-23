from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(
        schema="marketplace",
        naming_convention={
            "pk": "%(table_name)s_pkey",
            "uq": "%(table_name)s_%(column_0_name)s_key",
        },
    )
