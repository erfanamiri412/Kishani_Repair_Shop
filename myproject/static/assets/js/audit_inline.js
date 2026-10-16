(function () {

    "use strict";


    function getRow(element) {

        return element.closest(
            "tr.form-row"
        );

    }


    function getUnitPrice(row) {

        return row.querySelector(
            'input[name$="-unit_price"]'
        );

    }


    function getQuantity(row) {

        return row.querySelector(
            'input[name$="-quantity"]'
        );

    }


    function getTotal(row) {

        return row.querySelector(
            ".field-total_price_display"
        );

    }


    function cleanNumber(value) {

        return Number(
            String(value || "0")
                .replace(/,/g, "")
                .replace(/٬/g, "")
                .replace(/[۰-۹]/g, function (char) {
                    return "۰۱۲۳۴۵۶۷۸۹".indexOf(char);
                })
                .replace(/[٠-٩]/g, function (char) {
                    return "٠١٢٣٤٥٦٧٨٩".indexOf(char);
                })
        ) || 0;

    }


    function calculateTotal(row) {

        if (!row) {
            return;
        }

        const quantity =
            getQuantity(row);

        const unitPrice =
            getUnitPrice(row);

        const total =
            getTotal(row);

        if (
            !quantity ||
            !unitPrice ||
            !total
        ) {
            return;
        }

        const qty =
            cleanNumber(
                quantity.value
            );

        const price =
            cleanNumber(
                unitPrice.value
            );

        total.textContent =
            (qty * price)
                .toLocaleString("en-US");

    }


    function loadPartPrice(
        row,
        partId
    ) {

        if (
            !row ||
            !partId
        ) {
            return;
        }

        const unitPrice =
            getUnitPrice(row);

        if (!unitPrice) {
            return;
        }

        fetch(
            "/admin/audit/auditlog/part-price/?part_id=" +
            encodeURIComponent(partId)
        )
        .then(function (response) {

            if (!response.ok) {
                throw new Error(
                    "HTTP " +
                    response.status
                );
            }

            return response.json();

        })
        .then(function (data) {

            if (!data.success) {
                throw new Error(
                    "قیمت قطعه پیدا نشد."
                );
            }

            const price =
                cleanNumber(
                    data.price
                );

            /*
             * قیمت واقعی فروش
             * بدون عدد فارسی
             */
            unitPrice.value =
                String(price);

            calculateTotal(row);

        })
        .catch(function (error) {

            console.error(
                "Part price error:",
                error
            );

            unitPrice.value = "";

            calculateTotal(row);

        });

    }


    /* =====================================================
       Django Admin Autocomplete
       ===================================================== */

    $(document).on(
        "select2:select",
        'select[name$="-part"]',
        function (event) {

            const select =
                this;

            const row =
                getRow(select);

            if (!row) {
                return;
            }

            let partId =
                select.value;

            if (
                event &&
                event.params &&
                event.params.data &&
                event.params.data.id
            ) {

                partId =
                    event.params.data.id;

            }

            loadPartPrice(
                row,
                partId
            );

        }
    );


    /* =====================================================
       Fallback
       ===================================================== */

    $(document).on(
        "change",
        'select[name$="-part"]',
        function () {

            const row =
                getRow(this);

            if (!row) {
                return;
            }

            const partId =
                this.value;

            if (!partId) {
                return;
            }

            loadPartPrice(
                row,
                partId
            );

        }
    );


    /* =====================================================
       Quantity
       ===================================================== */

    $(document).on(
        "input",
        'input[name$="-quantity"]',
        function () {

            calculateTotal(
                getRow(this)
            );

        }
    );


    /* =====================================================
       New Inline Row
       ===================================================== */

    $(document).on(
        "formset:added",
        function (event) {

            const row =
                event.target;

            if (!row) {
                return;
            }

            const unitPrice =
                getUnitPrice(row);

            const total =
                getTotal(row);

            if (unitPrice) {
                unitPrice.value = "";
            }

            if (total) {
                total.textContent = "0";
            }

        }
    );


})();
(function () {

    "use strict";

    function number(value) {

        return Number(
            String(value || "0")
                .replace(/,/g, "")
                .replace(/٬/g, "")
                .replace(/[۰-۹]/g, function (char) {
                    return "۰۱۲۳۴۵۶۷۸۹".indexOf(char);
                })
                .replace(/[٠-٩]/g, function (char) {
                    return "٠١٢٣٤٥٦٧٨٩".indexOf(char);
                })
        ) || 0;

    }


    function calculate(row) {

        if (!row) {
            return;
        }

        const quantity =
            row.querySelector(
                'input[name$="-quantity"]'
            );

        const unitPrice =
            row.querySelector(
                'input[name$="-unit_price"]'
            );

        const total =
            row.querySelector(
                ".field-total_price_display"
            );

        if (
            !quantity ||
            !unitPrice ||
            !total
        ) {
            return;
        }

        const result =
            number(quantity.value) *
            number(unitPrice.value);

        total.textContent =
            result.toLocaleString(
                "en-US"
            );

    }


    document.addEventListener(
        "input",
        function (event) {

            const target =
                event.target;

            if (
                !target.name
            ) {
                return;
            }

            if (
                !target.name.endsWith(
                    "-quantity"
                )
                &&
                !target.name.endsWith(
                    "-unit_price"
                )
            ) {
                return;
            }

            const row =
                target.closest(
                    "tr.form-row"
                );

            calculate(row);

        }
    );


    document.addEventListener(
        "formset:added",
        function (event) {

            calculate(
                event.target
            );

        }
    );


    window.addEventListener(
        "load",
        function () {

            document
                .querySelectorAll(
                    "tr.form-row"
                )
                .forEach(
                    function (row) {

                        calculate(row);

                    }
                );

        }
    );

})();


(function () {
    "use strict";

    function initializeRequestDetails() {
        const select = document.getElementById(
            "id_service_request"
        );

        if (!select || select.dataset.customerAutofillReady) {
            return;
        }

        select.dataset.customerAutofillReady = "true";

        const basePath = window.location.pathname.replace(
            /(?:add|[0-9]+\/change)\/?$/,
            ""
        );

        function updateReadonlyField(name, value) {
            const row = document.querySelector(
                ".field-" + name + " .readonly"
            );

            if (row) {
                row.textContent = value || "-";
            }
        }

        async function loadDetails() {
            const selectedId = select.value;

            if (!selectedId) {
                updateReadonlyField("customer_name", "-");
                updateReadonlyField("vehicle_display", "-");
                return;
            }

            const url = new URL(
                basePath + "service-request-details/",
                window.location.origin
            );

            url.searchParams.set(
                "service_request_id",
                selectedId
            );

            try {
                const response = await fetch(url, {
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                });

                if (!response.ok) {
                    throw new Error(
                        "HTTP " + response.status
                    );
                }

                const data = await response.json();

                if (select.value !== selectedId) {
                    return;
                }

                updateReadonlyField(
                    "customer_name",
                    data.success ? data.customer_name : "-"
                );

                updateReadonlyField(
                    "vehicle_display",
                    data.success ? data.vehicle_name : "-"
                );
            } catch (error) {
                console.error(error);
            }
        }

        if (window.django && window.django.jQuery) {
            window.django.jQuery(select).on(
                "change.auditCustomerAutofill select2:select.auditCustomerAutofill",
                loadDetails
            );
        } else {
            select.addEventListener(
                "change",
                loadDetails
            );
        }

        if (select.value) {
            loadDetails();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeRequestDetails
        );
    } else {
        initializeRequestDetails();
    }
})();
