import re

from django import forms
from django.utils.safestring import mark_safe


class IranianPlateWidget(forms.TextInput):

    def render(
        self,
        name,
        value,
        attrs=None,
        renderer=None,
    ):

        value = str(value or "")

        uid = attrs.get("id", name)

        left = ""
        letter = ""
        middle = ""
        city = ""

        match = re.match(
            r"(\d{2})([آ-ی])(\d{3})(\d{2})",
            value,
        )

        if match:

            left = match.group(1)
            letter = match.group(2)
            middle = match.group(3)
            city = match.group(4)

        html = f"""
        <div style="
            display:flex;
            align-items:center;
            gap:6px;
            flex-wrap:nowrap;
        ">

            <input
                type="text"
                id="{uid}_city"
                value="{city}"
                maxlength="2"
                class="vTextField"
                placeholder="67"
                style="
                    width:60px;
                    text-align:center;
                "
            >

            <input
                type="hidden"
                name="{name}"
                id="{uid}"
                value="{value}"
            >

            </span>

            <input
                type="text"
                id="{uid}_middle"
                value="{middle}"
                maxlength="3"
                class="vTextField"
                placeholder="345"
                style="
                    width:80px;
                    text-align:center;
                "
            >

            <span style="
                font-size:18px;
                font-weight:bold;
            ">
                
            </span>

            <input
                type="text"
                id="{uid}_letter"
                value="{letter}"
                maxlength="1"
                class="vTextField"
                placeholder="ب"
                style="
                    width:50px;
                    text-align:center;
                "
            >

            <span style="
                font-size:18px;
                font-weight:bold;
            ">
                
            </span>

            <input
                type="text"
                id="{uid}_left"
                value="{left}"
                maxlength="2"
                class="vTextField"
                placeholder="12"
                style="
                    width:60px;
                    text-align:center;
                "
            >

            <span style="
                font-size:18px;
                font-weight:bold;
            ">

        </div>

        <script>
        (function() {{

            const hidden =
                document.getElementById("{uid}");

            const left =
                document.getElementById("{uid}_left");

            const letter =
                document.getElementById("{uid}_letter");

            const middle =
                document.getElementById("{uid}_middle");

            const city =
                document.getElementById("{uid}_city");

            function updatePlate() {{

                hidden.value =
                    left.value.trim()
                    + letter.value.trim()
                    + middle.value.trim()
                    + city.value.trim();
            }}

            [left, letter, middle, city]
            .forEach(function(el) {{

                el.addEventListener(
                    "input",
                    updatePlate
                );

            }});

            updatePlate();

        }})();
        </script>
        """

        return mark_safe(html)