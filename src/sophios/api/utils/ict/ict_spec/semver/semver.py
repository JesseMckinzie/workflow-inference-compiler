# pylint: disable=E0213
"""SemVer object."""
# TODO make this better in JSON schema
import re
from functools import singledispatchmethod
from typing import Any, Union

from pydantic import RootModel, field_validator


def _check_version_number(value: Union[str, int]) -> bool:
    if isinstance(value, int):
        value = str(value)
    if "-" in value:
        value = value.split("-")[0]
    if len(value) > 1 and value[0] == "0":
        return False
    return bool(re.match(r"^\d+$", value))


class Version(RootModel):
    """SemVer object."""

    root: str

    @field_validator("root")
    @classmethod
    def semantic_version(
        cls,
        value,
    ):  # ruff: noqa: ANN202, N805, ANN001
        """Pydantic Validator to check semver."""
        version = value.split(".")

        if not len(version) == 3:  # ruff: noqa: PLR2004
            raise ValueError(
                f"""Invalid version ({value}). 
            Version must follow semantic versioning (see semver.org)"""
            )
        if "-" in version[-1]:  # with hyphen
            idn = version[-1].split("-")[-1]
            id_reg = re.compile("[0-9A-Za-z-]+")
            assert bool(
                id_reg.match(idn),
            ), f"""Invalid version ({value}).
                Version must follow semantic versioning (see semver.org)"""

        if not all(map(_check_version_number, version)):
            raise ValueError(
                f"""Invalid version ({value}).
                Version must follow semantic versioning (see semver.org)"""
            )
        return value

    @property
    def major(self):
        """Return x from x.y.z ."""
        return self.root.split(".")[0]

    @property
    def minor(self):
        """Return y from x.y.z ."""
        return self.root.split(".")[1]

    @property
    def patch(self):
        """Return z from x.y.z ."""
        return self.root.split(".")[2]

    def __str__(self) -> str:
        """Return string representation of Version object."""
        return self.root

    @singledispatchmethod
    def __lt__(self, other: Any) -> bool:
        """Compare if Version is less than other object."""
        msg = "invalid type for comparison."
        raise TypeError(msg)

    @singledispatchmethod
    def __gt__(self, other: Any) -> bool:
        """Compare if Version is less than other object."""
        msg = "invalid type for comparison."
        raise TypeError(msg)

    @singledispatchmethod
    def __eq__(self, other: Any) -> bool:
        """Compare if two Version objects are equal."""
        msg = "invalid type for comparison."
        raise TypeError(msg)

    def __hash__(self) -> int:
        """Needed to use Version objects as dict keys."""
        return hash(self.root)

    def __repr__(self) -> str:
        """Return string representation of Version object."""
        return self.root


@Version.__eq__.register(Version)  # pylint: disable=no-member
def _(self, other):
    return (
        other.major == self.major
        and other.minor == self.minor
        and other.patch == self.patch
    )


@Version.__eq__.register(str)  # pylint: disable=no-member
def _(self, other):
    return self == Version(other)


@Version.__lt__.register(Version)  # pylint: disable=no-member
def _(self, other):
    if other.major > self.major:
        return True
    if other.major == self.major:
        if other.minor > self.minor:
            return True
        if other.minor == self.minor:
            if other.patch > self.patch:
                return True
            return False
        return False
    return False


@Version.__lt__.register(str)  # pylint: disable=no-member
def _(self, other):
    v = Version(other)
    return self < v


@Version.__gt__.register(Version)  # pylint: disable=no-member
def _(self, other):
    return other < self


@Version.__gt__.register(str)  # pylint: disable=no-member
def _(self, other):
    v = Version(other)
    return self > v
