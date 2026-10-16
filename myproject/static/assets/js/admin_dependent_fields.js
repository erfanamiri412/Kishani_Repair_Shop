(function () {

    "use strict";


    // =====================================================
    // Helpers
    // =====================================================

    function getCustomerId() {

        const customer =
            document.querySelector(
                "#id_customer"
            );

        if (!customer) {
            return "";
        }

        return customer.value || "";
    }


    function getVehicleField() {

        return document.querySelector(
            "#id_vehicle"
        );

    }


    function getServiceRequestField() {

        return document.querySelector(
            "#id_service_request"
        );

    }


    function clearField(field) {

        if (
            !field ||
            !window.django ||
            !django.jQuery
        ) {
            return;
        }

        const $field =
            django.jQuery(
                field
            );

        $field.val(null);

        $field.trigger(
            "change"
        );

    }


    // =====================================================
    // Autocomplete Request Filter
    // =====================================================

    function installAutocompleteFilter() {

        if (
            !window.django ||
            !django.jQuery
        ) {
            return;
        }

        const $ =
            django.jQuery;


        if (
            window.__kishaniAutocompleteFilterInstalled
        ) {
            return;
        }


        window.__kishaniAutocompleteFilterInstalled =
            true;


        $.ajaxPrefilter(
            function (
                options,
                originalOptions
            ) {

                if (
                    !options ||
                    !options.url ||
                    options.url.indexOf(
                        "/admin/autocomplete/"
                    ) === -1
                ) {
                    return;
                }


                let data =
                    options.data;


                // =================================================
                // String Data
                // =================================================

                if (
                    typeof data === "string"
                ) {

                    const params =
                        new URLSearchParams(
                            data
                        );


                    const fieldName =
                        params.get(
                            "field_name"
                        );


                    // ---------------------------------------------
                    // Vehicle
                    // ---------------------------------------------

                    if (
                        fieldName ===
                        "vehicle"
                    ) {

                        params.set(
                            "customer_id",
                            getCustomerId()
                        );

                    }


                    // ---------------------------------------------
                    // Service Request
                    // ---------------------------------------------

                    if (
                        fieldName ===
                        "service_request"
                    ) {

                        params.set(
                            "customer_id",
                            getCustomerId()
                        );


                        const vehicle =
                            getVehicleField();


                        params.set(
                            "vehicle_id",
                            vehicle
                                ? (
                                    vehicle.value
                                    || ""
                                )
                                : ""
                        );

                    }


                    options.data =
                        params.toString();

                    return;
                }


                // =================================================
                // Object Data
                // =================================================

                if (!data) {

                    data = {};

                }


                const fieldName =
                    data.field_name;


                // ---------------------------------------------
                // Vehicle
                // ---------------------------------------------

                if (
                    fieldName ===
                    "vehicle"
                ) {

                    data.customer_id =
                        getCustomerId();

                }


                // ---------------------------------------------
                // Service Request
                // ---------------------------------------------

                if (
                    fieldName ===
                    "service_request"
                ) {

                    data.customer_id =
                        getCustomerId();


                    const vehicle =
                        getVehicleField();


                    data.vehicle_id =
                        vehicle
                            ? (
                                vehicle.value
                                || ""
                            )
                            : "";

                }


                options.data =
                    data;

            }
        );

    }


    // =====================================================
    // Customer Changed
    // =====================================================

    function customerChanged() {

        const vehicle =
            getVehicleField();

        const serviceRequest =
            getServiceRequestField();


        clearField(
            vehicle
        );

        clearField(
            serviceRequest
        );

    }


    // =====================================================
    // Vehicle Changed
    // =====================================================

    function vehicleChanged() {

        const serviceRequest =
            getServiceRequestField();


        clearField(
            serviceRequest
        );

    }


    // =====================================================
    // Vehicle Autocomplete Display
    // =====================================================

    function renderVehicleAutocomplete(
        data
    ) {

        if (
            !data ||
            data.loading
        ) {

            return data
                ? data.text
                : "";

        }


        const rawText =
            String(
                data.text || ""
            )
            .replace(
                /[\u2066\u2067\u2068\u2069]/g,
                ""
            )
            .trim();


        // =================================================
        // Extract Plate
        // =================================================

        const plateMatch = rawText.match(
            /\(\s*(\d{2})\s*[-/]?\s*([آ-ی])\s*[-/]?\s*(\d{3})\s*[-/]?\s*(\d{2})\s*(?:ایران)?\s*\)$/
        );

        const formattedMatch =
            rawText.match(
                /^(.*?)\s*\|\s*(\d{2})\s*\/\s*([آ-ی])\s*\/\s*(\d{3})\s*\/\s*ایران\s*(\d{2})$/
            );


        let vehicleName = "";
        let firstTwo = "";
        let letter = "";
        let middleThree = "";
        let iranCode = "";


        // =================================================
        // Raw __str__ Format
        // =================================================

        if (plateMatch) {

            vehicleName =
                rawText
                    .slice(
                        0,
                        plateMatch.index
                    )
                    .trim();


            firstTwo =
                plateMatch[1];

            letter =
                plateMatch[2];

            middleThree =
                plateMatch[3];

            iranCode =
                plateMatch[4];

        }


        // =================================================
        // Formatted Format
        // =================================================

        else if (formattedMatch) {

            vehicleName =
                formattedMatch[1]
                    .trim();

            firstTwo =
                formattedMatch[2];

            letter =
                formattedMatch[3];

            middleThree =
                formattedMatch[4];

            iranCode =
                formattedMatch[5];

        }


        else {

            return data.text;

        }


        // =================================================
        // Main Wrapper
        // =================================================

        const wrapper =
            document.createElement(
                "span"
            );

        wrapper.style.display =
            "inline-flex";

        wrapper.style.alignItems =
            "center";

        wrapper.style.gap =
            "6px";

        wrapper.style.whiteSpace =
            "nowrap";

        wrapper.style.direction =
            "rtl";


        // =================================================
        // Vehicle Name
        // =================================================

        const vehicle =
            document.createElement(
                "span"
            );

        vehicle.textContent =
            vehicleName;

        vehicle.dir =
            "rtl";


        // =================================================
        // Separator
        // =================================================

        const separator =
            document.createElement(
                "span"
            );

        separator.textContent =
            "|";


        // =================================================
        // Plate Container
        // =================================================

        const plate =
            document.createElement(
                "span"
            );

        plate.style.display =
            "inline-flex";

        plate.style.alignItems =
            "center";

        plate.style.direction =
            "ltr";

        plate.style.unicodeBidi =
            "isolate";

        plate.style.whiteSpace =
            "nowrap";


        // =================================================
        // Plate Part Helper
        // =================================================

        function createPart(
            text,
            direction = "ltr"
        ) {

            const part =
                document.createElement(
                    "span"
                );

            part.textContent =
                text;

            part.style.direction =
                direction;

            part.style.unicodeBidi =
                "isolate";

            part.style.display =
                "inline-block";

            return part;

        }


        // =================================================
        // First Two Digits
        // =================================================

        plate.appendChild(
            createPart(
                firstTwo
            )
        );


        // =================================================
        // Slash
        // =================================================

        plate.appendChild(
            createPart(
                "/"
            )
        );


        // =================================================
        // Letter
        // =================================================

        plate.appendChild(
            createPart(
                letter
            )
        );


        // =================================================
        // Slash
        // =================================================

        plate.appendChild(
            createPart(
                "/"
            )
        );


        // =================================================
        // Middle Three Digits
        // =================================================

        plate.appendChild(
            createPart(
                middleThree
            )
        );


        // =================================================
        // Slash
        // =================================================

        plate.appendChild(
            createPart(
                "/"
            )
        );


        // =================================================
        // Iran Label
        // =================================================

        plate.appendChild(
            createPart(
                "ایران",
                "rtl"
            )
        );


        // =================================================
        // Final Two Digits
        // =================================================

        plate.appendChild(
            createPart(
                iranCode
            )
        );


        // =================================================
        // Append
        // =================================================

        wrapper.appendChild(
            vehicle
        );

        wrapper.appendChild(
            separator
        );

        wrapper.appendChild(
            plate
        );


        return wrapper;

    }


    // =====================================================
    // Apply Vehicle Autocomplete Display
    // =====================================================

    function updateVehicleAutocompleteDisplay() {

        if (
            !window.django ||
            !django.jQuery
        ) {
            return false;
        }


        const vehicle =
            getVehicleField();


        if (!vehicle) {
            return false;
        }


        const $vehicle =
            django.jQuery(
                vehicle
            );


        const select2 =
            $vehicle.data(
                "select2"
            );


        if (!select2) {
            return false;
        }


        const options =
            select2.options.options;


        options.templateResult =
            renderVehicleAutocomplete;


        options.templateSelection =
            renderVehicleAutocomplete;


        return true;

    }


    // =====================================================
    // Ensure Vehicle Autocomplete Display
    // =====================================================

    function ensureVehicleAutocompleteDisplay() {

        if (
            updateVehicleAutocompleteDisplay()
        ) {
            return;
        }


        /*
         * Select2 ممکن است کمی بعد از DOM آماده شود.
         * چند بار با فاصله کوتاه بررسی می‌کنیم.
         */

        const delays = [
            50,
            150,
            300,
            600,
            1000,
        ];


        delays.forEach(
            function (delay) {

                window.setTimeout(
                    function () {

                        updateVehicleAutocompleteDisplay();

                    },
                    delay
                );

            }
        );

    }


    // =====================================================
    // Bind Events
    // =====================================================

    function bindEvents() {

        if (
            !window.django ||
            !django.jQuery
        ) {
            return;
        }


        const $ =
            django.jQuery;


        const customer =
            document.querySelector(
                "#id_customer"
            );

        const vehicle =
            document.querySelector(
                "#id_vehicle"
            );


        // =================================================
        // Customer
        // =================================================

        if (
            customer &&
            !customer.dataset
                .repairDependencyInitialized
        ) {

            customer.dataset
                .repairDependencyInitialized =
                "true";


            $(customer).on(
                "change",
                customerChanged
            );


            $(customer).on(
                "select2:select",
                customerChanged
            );

        }


        // =================================================
        // Vehicle
        // =================================================

        if (
            vehicle &&
            !vehicle.dataset
                .repairDependencyInitialized
        ) {

            vehicle.dataset
                .repairDependencyInitialized =
                "true";


            $(vehicle).on(
                "change",
                vehicleChanged
            );


            $(vehicle).on(
                "select2:select",
                vehicleChanged
            );


            /*
             * قبل از باز شدن لیست خودرو،
             * قالب نمایش را مجدداً اعمال می‌کنیم.
             */

            $(vehicle).on(
                "select2:opening",
                function () {

                    updateVehicleAutocompleteDisplay();

                }
            );


            $(vehicle).on(
                "select2:open",
                function () {

                    updateVehicleAutocompleteDisplay();

                }
            );

        }


        // =================================================
        // Make Sure Display Is Applied
        // =================================================

        ensureVehicleAutocompleteDisplay();

    }


    // =====================================================
    // Initialize
    // =====================================================

    function initialize() {

        installAutocompleteFilter();

        bindEvents();

        ensureVehicleAutocompleteDisplay();

    }


    // =====================================================
    // Boot
    // =====================================================

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize
        );

    } else {

        initialize();

    }


    // =====================================================
    // Django Admin Dynamic DOM
    // =====================================================

    if (
        window.MutationObserver
    ) {

        const observer =
            new MutationObserver(
                function () {

                    bindEvents();

                }
            );


        if (
            document.body
        ) {

            observer.observe(
                document.body,
                {
                    childList: true,
                    subtree: true,
                }
            );

        }

    }


})();