
(function () {
    "use strict";

    let activeInput = null;
    let picker = null;

    // =====================================================
    // Helpers
    // =====================================================

    function pad(value) {
        return String(value).padStart(2, "0");
    }

    function normalizeDigits(value) {
        return String(value || "")
            .replace(/[۰-۹]/g, function (char) {
                return "۰۱۲۳۴۵۶۷۸۹".indexOf(char);
            })
            .replace(/[٠-٩]/g, function (char) {
                return "٠١٢٣٤٥٦٧٨٩".indexOf(char);
            })
            .replace(/[^\d]/g, "");
    }

    function isTimeInput(input) {
        if (!input) {
            return false;
        }

        if (
            input.dataset.timePicker === "true"
            || input.classList.contains("admin-time-input")
        ) {
            return true;
        }

        const id = input.id || "";
        const name = input.name || "";

        /*
         * Django SplitDateTimeWidget
         * معمولاً بخش دوم زمان است.
         */
        if (
            id.endsWith("_1")
            || name.endsWith("_1")
        ) {
            return true;
        }

        /*
         * HTML time input
         */
        if (input.type === "time") {
            return true;
        }

        /*
         * بررسی فرم-row برای AdminSplitJalaliDateTime
         */
        const row = input.closest(".form-row");

        if (!row) {
            return false;
        }

        const label = row.querySelector("label");

        if (!label) {
            return false;
        }

        const labelText = (
            label.textContent || ""
        ).trim();

        return (
            labelText.includes("زمان")
            || labelText.includes("Time")
        );
    }

    function getPickerInputs() {
        return {
            hour: picker.querySelector(
                ".admin-time-picker-input-hour"
            ),

            minute: picker.querySelector(
                ".admin-time-picker-input-minute"
            ),

            value: picker.querySelector(
                ".admin-time-picker-value"
            ),

            error: picker.querySelector(
                ".admin-time-error"
            ),
        };
    }

    // =====================================================
    // Picker
    // =====================================================

    function createPicker() {
        if (picker && document.body.contains(picker)) {
            return picker;
        }

        picker = document.createElement("div");

        picker.className =
            "admin-time-picker";

        picker.style.display = "none";

        picker.innerHTML = `
            <div class="admin-time-picker-header">

                <span class="admin-time-picker-title">
                    انتخاب زمان
                </span>

                <span class="admin-time-picker-value">
                    00:00
                </span>

            </div>

            <div class="admin-time-picker-fields">

                <div class="admin-time-picker-field">

                    <label>
                        ساعت
                    </label>

                    <input
                        type="text"
                        class="
                            admin-time-picker-input
                            admin-time-picker-input-hour
                        "
                        inputmode="numeric"
                        maxlength="2"
                        autocomplete="off"
                        placeholder="00"
                    >

                </div>

                <div class="admin-time-picker-field">

                    <label>
                        دقیقه
                    </label>

                    <input
                        type="text"
                        class="
                            admin-time-picker-input
                            admin-time-picker-input-minute
                        "
                        inputmode="numeric"
                        maxlength="2"
                        autocomplete="off"
                        placeholder="00"
                    >

                </div>

            </div>

            <div class="admin-time-picker-hint">
                ساعت: 00 تا 23 — دقیقه: 00 تا 59
            </div>

            <div
                class="admin-time-error"
                style="display:none;"
            ></div>

            <div class="admin-time-picker-footer">

                <button
                    type="button"
                    class="admin-time-now"
                >
                    الان
                </button>

                <button
                    type="button"
                    class="admin-time-confirm"
                >
                    ثبت
                </button>

            </div>
        `;

        document.body.appendChild(
            picker
        );

        return picker;
    }

    // =====================================================
    // Error
    // =====================================================

    function showError(message) {
        const inputs =
            getPickerInputs();

        inputs.error.textContent =
            message;

        inputs.error.style.display =
            "block";
    }

    function clearError() {
        const inputs =
            getPickerInputs();

        inputs.error.textContent =
            "";

        inputs.error.style.display =
            "none";
    }

    // =====================================================
    // Preview
    // =====================================================

    function updatePreview() {
        const inputs =
            getPickerInputs();

        const hourValue =
            normalizeDigits(
                inputs.hour.value
            );

        const minuteValue =
            normalizeDigits(
                inputs.minute.value
            );

        const hour =
            hourValue
                ? Math.min(
                    parseInt(
                        hourValue,
                        10
                    ),
                    23
                )
                : 0;

        const minute =
            minuteValue
                ? Math.min(
                    parseInt(
                        minuteValue,
                        10
                    ),
                    59
                )
                : 0;

        inputs.value.textContent =
            `${pad(hour)}:${pad(minute)}`;
    }

    // =====================================================
    // Existing Value
    // =====================================================

    function getExistingTime() {
        if (!activeInput) {
            return null;
        }

        let value = (
            activeInput.value || ""
        ).trim();

        /*
         * پشتیبانی از مقدارهایی مثل:
         * 21:35
         * 21:35:00
         */
        const match = value.match(
            /^(\d{1,2}):(\d{1,2})(?::\d{1,2})?$/
        );

        if (!match) {
            return null;
        }

        return {
            hour: parseInt(
                match[1],
                10
            ),

            minute: parseInt(
                match[2],
                10
            ),
        };
    }

    function loadExistingTime() {
        const inputs =
            getPickerInputs();

        const current =
            getExistingTime();

        if (!current) {

            inputs.hour.value =
                "";

            inputs.minute.value =
                "";

            inputs.value.textContent =
                "00:00";

            return;
        }

        inputs.hour.value =
            pad(current.hour);

        inputs.minute.value =
            pad(current.minute);

        updatePreview();
    }

    // =====================================================
    // Current Time
    // =====================================================

    function setCurrentTime() {
        const now =
            new Date();

        const inputs =
            getPickerInputs();

        inputs.hour.value =
            pad(
                now.getHours()
            );

        inputs.minute.value =
            pad(
                now.getMinutes()
            );

        clearError();

        updatePreview();

        /*
         * فقط مقدار را داخل پنجره
         * می‌گذاریم.
         *
         * ثبت واقعی با دکمه «ثبت»
         * انجام می‌شود.
         */
    }

    // =====================================================
    // Position
    // =====================================================

    function positionPicker() {
        if (
            !activeInput
            || !picker
        ) {
            return;
        }

        const rect =
            activeInput.getBoundingClientRect();

        picker.style.display =
            "block";

        const pickerWidth =
            picker.offsetWidth;

        const viewportWidth =
            document.documentElement.clientWidth;

        let left =
            rect.left
            + window.scrollX;

        let top =
            rect.bottom
            + window.scrollY
            + 6;

        /*
         * جلوگیری از خروج از سمت راست
         */
        if (
            left + pickerWidth
            > viewportWidth
            + window.scrollX
        ) {
            left =
                viewportWidth
                + window.scrollX
                - pickerWidth
                - 10;
        }

        /*
         * جلوگیری از خروج از سمت چپ
         */
        if (left < 10) {
            left = 10;
        }

        picker.style.left =
            `${left}px`;

        picker.style.top =
            `${top}px`;
    }

    // =====================================================
    // Open
    // =====================================================

    function openPicker(input) {
        if (!isTimeInput(input)) {
            return;
        }

        activeInput =
            input;

        createPicker();

        clearError();

        loadExistingTime();

        positionPicker();

        const inputs =
            getPickerInputs();

        setTimeout(
            function () {
                inputs.hour.focus();
                inputs.hour.select();
            },
            0
        );
    }

    // =====================================================
    // Close
    // =====================================================

    function closePicker() {
        if (!picker) {
            return;
        }

        picker.style.display =
            "none";

        activeInput =
            null;
    }

    // =====================================================
    // Confirm
    // =====================================================

    function confirmTime() {
        if (!activeInput) {
            return;
        }

        const inputs =
            getPickerInputs();

        const hourText =
            normalizeDigits(
                inputs.hour.value
            );

        const minuteText =
            normalizeDigits(
                inputs.minute.value
            );

        if (!hourText) {

            showError(
                "لطفاً ساعت را وارد کنید."
            );

            inputs.hour.focus();

            return;
        }

        if (!minuteText) {

            showError(
                "لطفاً دقیقه را وارد کنید."
            );

            inputs.minute.focus();

            return;
        }

        const hour =
            parseInt(
                hourText,
                10
            );

        const minute =
            parseInt(
                minuteText,
                10
            );

        if (
            Number.isNaN(hour)
            || hour < 0
            || hour > 23
        ) {

            showError(
                "ساعت باید بین 00 تا 23 باشد."
            );

            inputs.hour.focus();

            return;
        }

        if (
            Number.isNaN(minute)
            || minute < 0
            || minute > 59
        ) {

            showError(
                "دقیقه باید بین 00 تا 59 باشد."
            );

            inputs.minute.focus();

            return;
        }

        const formattedTime =
            `${pad(hour)}:${pad(minute)}`;

        activeInput.value =
            formattedTime;

        /*
         * اطلاع به Django
         */
        activeInput.dispatchEvent(
            new Event(
                "input",
                {
                    bubbles: true,
                }
            )
        );

        activeInput.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true,
                }
            )
        );

        /*
         * برای بعضی Widgetها
         * blur هم مهم است.
         */
        activeInput.dispatchEvent(
            new Event(
                "blur",
                {
                    bubbles: true,
                }
            )
        );

        closePicker();
    }

    // =====================================================
    // Input Handling
    // =====================================================

    function restrictPickerInput(
        input
    ) {

        const value =
            normalizeDigits(
                input.value
            );

        input.value =
            value.slice(
                0,
                2
            );

        clearError();

        updatePreview();
    }

    // =====================================================
    // Initialize Existing Inputs
    // =====================================================

    function initializeInputs() {

        const inputs =
            document.querySelectorAll(
                "input"
            );

        inputs.forEach(
            function (input) {

                if (
                    isTimeInput(input)
                ) {

                    input.classList.add(
                        "admin-time-input"
                    );

                    input.dataset.timePicker =
                        "true";
                }
            }
        );
    }

    // =====================================================
    // Document Events
    // =====================================================

    document.addEventListener(
        "click",
        function (event) {

            const target =
                event.target;

            /*
             * دکمه الان
             */
            if (
                target.closest(
                    ".admin-time-now"
                )
            ) {

                event.preventDefault();

                setCurrentTime();

                return;
            }

            /*
             * دکمه ثبت
             */
            if (
                target.closest(
                    ".admin-time-confirm"
                )
            ) {

                event.preventDefault();

                confirmTime();

                return;
            }

            /*
             * کلیک روی input زمان
             *
             * اینجا دیگر وابسته به
             * initialization نیستیم.
             */
            const input =
                target.closest(
                    "input"
                );

            if (
                input
                && isTimeInput(input)
            ) {

                event.preventDefault();

                openPicker(
                    input
                );

                return;
            }

            /*
             * کلیک بیرون
             */
            if (
                picker
                && !picker.contains(
                    target
                )
            ) {

                closePicker();
            }
        }
    );

    // =====================================================
    // Focus
    // =====================================================

    document.addEventListener(
        "focusin",
        function (event) {

            const input =
                event.target;

            if (
                input
                && isTimeInput(input)
            ) {

                /*
                 * با focus باز شود.
                 */
                openPicker(
                    input
                );
            }
        }
    );

    // =====================================================
    // Keyboard
    // =====================================================

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                !picker
                || picker.style.display
                    === "none"
            ) {
                return;
            }

            if (
                event.key === "Escape"
            ) {

                event.preventDefault();

                closePicker();

                return;
            }

            if (
                event.key === "Enter"
            ) {

                const target =
                    event.target;

                if (
                    target.classList.contains(
                        "admin-time-picker-input"
                    )
                ) {

                    event.preventDefault();

                    confirmTime();
                }
            }

            if (
                event.key === "Tab"
            ) {

                const target =
                    event.target;

                if (
                    target.classList.contains(
                        "admin-time-picker-input-hour"
                    )
                ) {

                    event.preventDefault();

                    const inputs =
                        getPickerInputs();

                    inputs.minute.focus();
                    inputs.minute.select();
                }
            }
        }
    );

    // =====================================================
    // Picker Input
    // =====================================================

    document.addEventListener(
        "input",
        function (event) {

            const input =
                event.target;

            if (
                !input.classList.contains(
                    "admin-time-picker-input"
                )
            ) {
                return;
            }

            restrictPickerInput(
                input
            );
        }
    );

    // =====================================================
    // Resize / Scroll
    // =====================================================

    window.addEventListener(
        "resize",
        function () {

            if (
                activeInput
            ) {

                positionPicker();
            }
        }
    );

    window.addEventListener(
        "scroll",
        function () {

            if (
                activeInput
            ) {

                positionPicker();
            }
        },
        true
    );

    // =====================================================
    // Initialization
    // =====================================================

    function initialize() {

        createPicker();

        initializeInputs();
    }

    /*
     * اگر DOM هنوز آماده نیست
     */
    if (
        document.readyState
        === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize
        );

    } else {

        /*
         * اگر Django Admin فایل JS را
         * بعد از DOMContentLoaded لود کرده باشد.
         */
        initialize();
    }

})();