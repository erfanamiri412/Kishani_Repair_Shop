document.addEventListener("DOMContentLoaded", function () {

    const plate = document.querySelector(
        ".custom-iran-plate"
    );

    if (!plate) {
        return;
    }


    const fields = [
        plate.querySelector(
            'input[name="plate_city"]'
        ),

        plate.querySelector(
            'input[name="plate_letter"]'
        ),

        plate.querySelector(
            'input[name="plate_middle"]'
        ),

        plate.querySelector(
            'input[name="plate_right"]'
        )
    ].filter(Boolean);


    fields.forEach(function (field, index) {

        field.addEventListener(
            "input",
            function () {

                // حذف فاصله
                this.value =
                    this.value.replace(/\s/g, "");


                // بخش‌های عددی
                if (
                    this.name === "plate_city" ||
                    this.name === "plate_middle" ||
                    this.name === "plate_right"
                ) {

                    this.value =
                        this.value.replace(
                            /[^\d۰-۹]/g,
                            ""
                        );

                }


                // بخش حرف
                if (
                    this.name === "plate_letter"
                ) {

                    this.value =
                        this.value.replace(
                            /[^آ-ی]/g,
                            ""
                        );

                }


                // رفتن به فیلد بعدی
                if (
                    this.value.length >=
                    this.maxLength &&
                    fields[index + 1]
                ) {

                    fields[index + 1].focus();

                    fields[index + 1].select();

                }

            }
        );


        // Backspace روی فیلد خالی
        field.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Backspace" &&
                    this.value === "" &&
                    fields[index - 1]
                ) {

                    event.preventDefault();

                    fields[index - 1].focus();

                }

            }
        );

    });

});