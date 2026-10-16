from datetime import date, timedelta


JALALI_MONTH_NAMES = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]


def jalali_to_gregorian(year, month, day):

    year -= 979

    if month <= 6:
        days = (
            365 * year
            + year // 33 * 8
            + ((year % 33) + 3) // 4
            + (month - 1) * 31
            + day - 1
        )
    else:
        days = (
            365 * year
            + year // 33 * 8
            + ((year % 33) + 3) // 4
            + (month - 1) * 30
            + 6
            + day - 1
        )

    days += 79

    gy = 1600 + 400 * (days // 146097)
    days %= 146097

    leap = True

    if days >= 36525:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524

        if days >= 365:
            days += 1
        else:
            leap = False

    gy += 4 * (days // 1461)
    days %= 1461

    if days >= 366:
        leap = False
        days -= 1
        gy += days // 365
        days %= 365

    month_days = [
        31,
        29 if leap else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    gm = 1

    while gm <= 12 and days >= month_days[gm - 1]:
        days -= month_days[gm - 1]
        gm += 1

    gd = days + 1

    return date(
        gy,
        gm,
        gd,
    )


def gregorian_to_jalali(year, month, day):

    gy = year - 1600
    gm = month - 1
    gd = day - 1

    g_days_in_month = [
        31,
        28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    days = (
        365 * gy
        + (gy + 3) // 4
        - (gy + 99) // 100
        + (gy + 399) // 400
    )

    for index in range(gm):
        days += g_days_in_month[index]

    if gm > 1 and (
        year % 4 == 0
        and (
            year % 100 != 0
            or year % 400 == 0
        )
    ):
        days += 1

    days += gd
    days -= 79

    jy = 979 + 33 * (days // 12053)
    days %= 12053

    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30

    return (
        jy,
        jm,
        jd,
    )


def today_jalali():

    try:
        import jdatetime

        today = jdatetime.date.today()

        return (
            today.year,
            today.month,
            today.day,
        )

    except ImportError:

        return gregorian_to_jalali(
            *date.today().timetuple()[:3]
        )


def get_month_period(year, month):

    start_date = jalali_to_gregorian(
        year,
        month,
        1,
    )

    if month == 12:
        next_start = jalali_to_gregorian(
            year + 1,
            1,
            1,
        )
    else:
        next_start = jalali_to_gregorian(
            year,
            month + 1,
            1,
        )

    end_date = next_start - timedelta(
        days=1
    )

    return (
        start_date,
        end_date,
    )


def get_year_period(year):

    return (
        jalali_to_gregorian(year, 1, 1),
        jalali_to_gregorian(year + 1, 1, 1)
        - timedelta(days=1),
    )


def previous_jalali_month(year, month):

    if month == 1:
        return (
            year - 1,
            12,
        )

    return (
        year,
        month - 1,
    )


def jalali_month_label(year, month):

    month_name = JALALI_MONTH_NAMES[
        month - 1
    ]

    return (
        f"{month_name} {year}"
    )


def jalali_date_label(value):

    year, month, day = gregorian_to_jalali(
        value.year,
        value.month,
        value.day,
    )

    return (
        f"{year:04d}/{month:02d}/{day:02d}"
    )
