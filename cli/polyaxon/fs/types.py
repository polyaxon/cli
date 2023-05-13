from typing import Union

from fsspec import AbstractFileSystem
from fsspec.asyn import AsyncFileSystem

FSSystem = Union[AbstractFileSystem, AsyncFileSystem]
