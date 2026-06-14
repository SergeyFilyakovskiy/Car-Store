from django.db import models


class BodyTypesEnum(models.TextChoices):
    MICRO = "micro", "Micro"
    HATCHBACK = "hatchback", "Hatchback"
    CROSSOVER = "crossover", "Crossover"
    SEDAN = "sedan", "Sedan"
    COUPE = "coupe", "Coupe"
    OFFROAD = "offroad", "Offroad"
    SPORT = "sport", "Sport"
    VAN = "van", "Van"


class FuelTypeEnum(models.TextChoices):
    PETROL = "petrol", "Petrol"
    DIESEL = "diesel", "Diesel"
    HYBRID = "hybrid", "Hybrid"
    ELECTRIC = "electric", "Electric"


class DriveTypeEnum(models.TextChoices):
    FWD = "FWD", "FWD"
    RWD = "RWD", "RWD"
    AWD = "AWD", "AWD"
    FOUR_WD = "4WD", "4WD"


class TransmissionTypeEnum(models.TextChoices):
    MT = "MT", "MT"
    AT = "AT", "AT"
    CVT = "CVT", "CVT"
    IMT = "iMT", "iMT"
    AMT = "AMT", "AMT"


class StatusEnum(models.TextChoices):
    PENDING = "PENDING", "Pending"
    MATCHED = "MATCHED", "Matched"
    COMPLETED = "COMPLETED", "Completed"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"
