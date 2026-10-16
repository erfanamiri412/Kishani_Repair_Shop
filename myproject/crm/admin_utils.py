import re

from django.utils.html import format_html


def format_plate_admin(
    plate_number,
):

    plate = str(
        plate_number or ""
    ).strip()

    if not plate:

        return "-"


    match = re.match(
        r"^(\d{2})([آ-ی])(\d{3})(\d{2})$",
        plate,
    )


    if not match:

        return format_html(
            '<span dir="ltr" '
            'style="'
            'direction:ltr;'
            'unicode-bidi:isolate;'
            'white-space:nowrap;'
            '">'
            '{}'
            '</span>',
            plate,
        )


    first_two = match.group(1)
    letter = match.group(2)
    middle_three = match.group(3)
    iran_code = match.group(4)


    return format_html(
        '<span dir="ltr" '
        'style="'
        'direction:ltr;'
        'unicode-bidi:isolate;'
        'white-space:nowrap;'
        'display:inline-flex;'
        'align-items:center;'
        '">'

        '<span>{}</span>'

        '<span>&nbsp;/&nbsp;</span>'

        '<span>{}</span>'

        '<span>&nbsp;/&nbsp;</span>'

        '<span>{}</span>'

        '<span>&nbsp;/&nbsp;</span>'

        '<span dir="ltr">'
        'ایران&nbsp;{}'
        '</span>'

        '</span>',

        first_two,
        letter,
        middle_three,
        iran_code,
    )

import re


def format_plate_text(
    plate_number,
):

    import re

    plate = str(
        plate_number or ""
    ).strip()

    if not plate:
        return ""


    match = re.match(
        r"^(\d{2})([آ-ی])(\d{3})(\d{2})$",
        plate,
    )

    if not match:
        return plate


    first_two = match.group(1)
    letter = match.group(2)
    middle_three = match.group(3)
    iran_code = match.group(4)


    return (
        "\u2066"
        f"{first_two}"
        " / "
        f"{letter}"
        " / "
        f"{middle_three}"
        " / "
        "ایران "
        f"{iran_code}"
        "\u2069"
    )