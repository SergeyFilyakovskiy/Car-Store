from enum import StrEnum


class BodyTypesEnum(StrEnum):
    MICRO = "micro"
    HATCHBACK = "hatchback"
    CROSSOVER = "crossover"
    SEDAN = "sedan"
    COUPE = "coupe"
    OFFROAD = "offroad"
    SPORT = "sport"
    VAN = "van"


class FuelTypeEnum(StrEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"


class DriveTypeEnum(StrEnum):
    FWD = "FWD"
    RWD = "RWD"
    AWD = "AWD"
    _4WD = "4WD"


class TransmissionTypeEnum(StrEnum):
    MT = "MT"
    AT = "AT"
    CVT = "CVT"
    iMT = "iMT"
    AMT = "AMT"
