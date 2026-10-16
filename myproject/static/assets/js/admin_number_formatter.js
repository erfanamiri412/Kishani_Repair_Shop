(function () {
    "use strict";

    // ==========================================================
    // Number Helpers
    // ==========================================================

    function normalizeNumber(value) {
        if (value === null || value === undefined || value === "") {
            return "";
        }

        return String(value)
            .replace(/,/g, "")
            .replace(/٬/g, "")
            .replace(/[\s\u00A0]/g, "")
            .replace(/[۰-۹]/g, function (digit) {
                return "۰۱۲۳۴۵۶۷۸۹".indexOf(digit);
            })
            .replace(/[٠-٩]/g, function (digit) {
                return "٠١٢٣٤٥٦٧٨٩".indexOf(digit);
            });
    }

    function formatNumber(value) {
        const normalized = normalizeNumber(value);

        if (!normalized) {
            return "";
        }

        // Integer
        if (/^-?\d+$/.test(normalized)) {
            const sign = normalized.startsWith("-") ? "-" : "";
            const digits = normalized.replace(/^-/, "");

            return sign + digits.replace(
                /\B(?=(\d{3})+(?!\d))/g,
                ","
            );
        }

        // Decimal
        if (/^-?\d+\.\d+$/.test(normalized)) {
            const sign = normalized.startsWith("-") ? "-" : "";
            const unsigned = normalized.replace(/^-/, "");
            const parts = unsigned.split(".");

            return (
                sign +
                parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",") +
                "." +
                parts[1]
            );
        }

        return String(value);
    }

    // ==========================================================
    // Field Metadata
    // ==========================================================

    function getLabelText(element) {
        if (!element) {
            return "";
        }

        const labels = [];

        if (element.labels && element.labels.length) {
            Array.prototype.forEach.call(
                element.labels,
                function (label) {
                    if (label && label.textContent) {
                        labels.push(label.textContent.trim());
                    }
                }
            );
        }

        if (!labels.length && element.closest) {
            const row = element.closest(
                ".form-row, .fieldBox, .form-group"
            );

            const label = row
                ? row.querySelector("label[for='" + element.id + "']")
                    || row.querySelector("label")
                : null;

            if (label && label.textContent) {
                labels.push(label.textContent.trim());
            }
        }

        return labels.join(" ");
    }

    function getFieldText(element) {
        if (!element) {
            return "";
        }

        const className = typeof element.className === "string"
            ? element.className
            : "";

        return [
            element.name || "",
            element.id || "",
            className,
            element.getAttribute("data-field-name") || "",
            element.getAttribute("aria-label") || "",
            element.getAttribute("placeholder") || "",
            getLabelText(element)
        ].join(" ").toLowerCase();
    }

    function normalizeText(value) {
        return String(value || "")
            .toLowerCase()
            .replace(/[ي]/g, "ی")
            .replace(/[ك]/g, "ک")
            .replace(/[_\-./:]+/g, " ")
            .replace(/[^a-z0-9\u0600-\u06FF\s]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    function getFieldIdentifiers(element) {
        if (!element) {
            return [];
        }

        const rawIdentifiers = [
            element.name || "",
            element.id || "",
            element.getAttribute("data-field-name") || ""
        ];

        return rawIdentifiers
            .filter(Boolean)
            .map(function (identifier) {
                let normalized = normalizeText(identifier)
                    .replace(/\s+/g, "_");

                normalized = normalized.replace(/^id_/, "");
                normalized = normalized.replace(/^form_\d+_/, "");

                // حذف پیشوند ردیف‌های اینلاین Django
                // مانند parts-0-unit_price
                normalized = normalized.replace(
                    /^[a-z0-9_]+_\d+_/,
                    ""
                );

                return normalized;
            });
    }

    // ==========================================================
    // Fields That Must Never Be Formatted
    // ==========================================================

    function shouldIgnore(element) {
        if (!element) {
            return true;
        }

        const text = normalizeText(getFieldText(element));
        const tokens = text.split(" ");

        const ignoredIdentifiers = [
            // Phone and security
            "phone",
            "mobile",
            "telephone",
            "password",
            "otp",
            "national_code",
            "verification",
            "username",

            // Vehicle identity
            "plate",
            "plate_number",
            "plate_city",
            "plate_letter",
            "plate_middle",
            "plate_right",
            "vin",

            // Dates, years and quantities
            "year",
            "production_year",
            "vehicle_year",
            "quantity",
            "qty",
            "count",
            "mileage",
            "odometer"
        ];

        if (
            ignoredIdentifiers.some(function (word) {
                const normalizedWord = normalizeText(word);

                return normalizedWord.includes(" ")
                    ? text.includes(normalizedWord)
                    : tokens.includes(normalizedWord);
            })
        ) {
            return true;
        }

        const ignoredPersianPhrases = [
            "شماره تماس",
            "شماره موبایل",
            "کد ملی",
            "شماره ملی",
            "شماره شاسی",
            "سال ساخت",
            "تعداد",
            "کارکرد خودرو",
            "کیلومتر کارکرد",
            "شماره پلاک"
        ];

        return ignoredPersianPhrases.some(function (phrase) {
            return text.includes(normalizeText(phrase));
        });
    }

    // ==========================================================
    // Price Field Detection
    // ==========================================================

    // These names identify financial fields.
    // data-number-format alone does NOT mean a field is a price.

    const PRICE_FIELD_NAMES = new Set([
        "price",
        "unit_price",
        "purchase_price",
        "selling_price",
        "sell_price",
        "sale_price",
        "part_price",
        "service_price",
        "total_price",

        "amount",
        "paid_amount",
        "received_amount",
        "payment_amount",
        "invoice_amount",
        "total_amount",
        "remaining_amount",
        "balance_amount",
        "advance_amount",
        "credit_amount",
        "debit_amount",

        "cost",
        "unit_cost",
        "purchase_cost",
        "repair_cost",
        "labor_cost",
        "parts_cost",
        "total_cost",
        "services_cost",

        "discount_amount",
        "tax_amount",
        "salary_amount",
        "commission_amount",
        "calculated_amount",

        "amount_paid",
        "amount_due",
        "balance_due",
        "remaining_balance",

        "subtotal",
        "grand_total",
        "total",
        "invoice_total",
        "payment_total",
        "repair_total",
        "parts_total",
        "services_total",
        "total_due",

        "income",
        "daily_income",
        "revenue",
        "salary",
        "wage",
        "commission",
        "service_fee",
        "repair_fee",
        "labor_amount"
    ]);

    const PRICE_LABEL_PHRASES = [
        // Persian financial labels
        "قیمت",
        "مبلغ",
        "هزینه",
        "دستمزد",
        "اجرت",
        "بها",
        "جمع کل",
        "جمع قطعات",
        "جمع خدمات",
        "مبلغ پرداختی",
        "مبلغ دریافتی",
        "مبلغ فاکتور",
        "مبلغ کل",
        "مبلغ باقی مانده",
        "مانده بدهی",
        "مانده حساب",
        "حقوق",
        "درآمد",
        "کارمزد",
        "تخفیف مبلغی",
        "مالیات مبلغی",

        // English financial labels
        "price",
        "unit price",
        "purchase price",
        "selling price",
        "sale price",
        "amount",
        "paid amount",
        "received amount",
        "payment amount",
        "invoice amount",
        "total amount",
        "remaining amount",
        "balance due",
        "cost",
        "unit cost",
        "purchase cost",
        "repair cost",
        "labor cost",
        "parts cost",
        "total cost",
        "subtotal",
        "grand total",
        "invoice total",
        "payment total",
        "salary",
        "commission",
        "income",
        "revenue"
    ];

    function containsWholePhrase(haystack, phrase) {
        const normalizedHaystack = " " + normalizeText(haystack) + " ";
        const normalizedPhrase = " " + normalizeText(phrase) + " ";

        return normalizedHaystack.includes(normalizedPhrase);
    }

    function isSupportedPriceElement(element) {
        if (!element) {
            return false;
        }

        if (
            element.classList
            && element.classList.contains("readonly")
        ) {
            return true;
        }

        if (element.tagName === "TEXTAREA") {
            return true;
        }

        if (element.tagName === "INPUT") {
            const type = (element.type || "").toLowerCase();

            return ["text", "number", ""].includes(type);
        }

        return false;
    }

    function isPriceField(element) {
        if (!isSupportedPriceElement(element) || shouldIgnore(element)) {
            return false;
        }

        const identifiers = getFieldIdentifiers(element);

        // فیلدهای متنی نباید به‌عنوان مبلغ شناسایی شوند.
        const nonPriceFields = [
            "title",
            "description",
            "name",
            "notes",
            "note",
        ];

        if (
            identifiers.some(function (identifier) {
                return nonPriceFields.some(function (fieldName) {
                    return (
                        identifier === fieldName ||
                        identifier.endsWith("_" + fieldName)
                    );
                });
            })
        ) {
            return false;
        }

        if (element.dataset && element.dataset.priceField === "true") {
            return true;
        }

        if (
            identifiers.some(function (identifier) {
                return PRICE_FIELD_NAMES.has(identifier);
            })
        ) {
            return true;
        }

        const labelText = getLabelText(element);

        return PRICE_LABEL_PHRASES.some(function (phrase) {
            return containsWholePhrase(labelText, phrase);
        });
    }

    // Numeric formatting and currency labels are separate.
    // Integer/decimal fields may receive comma separators without "تومان".

    function isNumericFormatField(input) {
        if (!input || shouldIgnore(input)) {
            return false;
        }

        if (
            input.tagName !== "INPUT"
            && input.tagName !== "TEXTAREA"
        ) {
            return false;
        }

        const type = (input.type || "").toLowerCase();

        if (
            [
                "hidden",
                "checkbox",
                "radio",
                "date",
                "time",
                "file",
                "password"
            ].includes(type)
        ) {
            return false;
        }

        return Boolean(
            (
                input.dataset
                && input.dataset.numberFormat === "true"
            )
            || isPriceField(input)
        );
    }

    // ==========================================================
    // Toman Suffix — Price Fields Only
    // ==========================================================

    function addTomanSuffix(input) {
        if (!input || !isPriceField(input)) {
            return;
        }

        const next = input.nextElementSibling;

        if (
            next
            && next.classList.contains("admin-toman-suffix")
        ) {
            return;
        }

        const suffix = document.createElement("span");

        suffix.className = "admin-toman-suffix";
        suffix.textContent = "تومان";
        suffix.setAttribute("aria-label", "واحد پول تومان");

        suffix.style.display = "inline-block";
        suffix.style.marginRight = "8px";
        suffix.style.whiteSpace = "nowrap";
        suffix.style.fontWeight = "500";
        suffix.style.verticalAlign = "middle";

        // Append beside this input only.
        input.insertAdjacentElement("afterend", suffix);
    }

    // ==========================================================
    // Prepare and Format Numeric Inputs
    // ==========================================================

    function prepareInput(input) {
        if (!isNumericFormatField(input)) {
            return false;
        }

        if (input.type === "number") {
            input.type = "text";
        }

        input.setAttribute("inputmode", "decimal");
        input.setAttribute("autocomplete", "off");

        if (input.dataset) {
            input.dataset.numberFormat = "true";
        }

        return true;
    }

    function countNumericCharacters(value) {
        return normalizeNumber(value)
            .replace(/[^0-9]/g, "")
            .length;
    }

    function caretPositionAfterFormatting(
        formattedValue,
        numericCharactersBeforeCaret
    ) {
        if (numericCharactersBeforeCaret <= 0) {
            return 0;
        }

        let numericCount = 0;

        for (
            let index = 0;
            index < formattedValue.length;
            index += 1
        ) {
            if (/\d/.test(formattedValue[index])) {
                numericCount += 1;
            }

            if (numericCount >= numericCharactersBeforeCaret) {
                return index + 1;
            }
        }

        return formattedValue.length;
    }

    function formatInput(input) {
        if (!prepareInput(input)) {
            return;
        }

        // Adds the currency suffix only if this is a price field.
        addTomanSuffix(input);

        if (input.dataset.formatterInitialized === "true") {
            input.value = formatNumber(input.value);
            return;
        }

        input.dataset.formatterInitialized = "true";
        input.value = formatNumber(input.value);

        // Live formatting.
        input.addEventListener("input", function () {
            const oldValue = this.value;
            const oldCaret = this.selectionStart;

            const beforeCaret = oldCaret === null
                ? oldValue
                : oldValue.slice(0, oldCaret);

            const numericCharactersBeforeCaret =
                countNumericCharacters(beforeCaret);

            const formattedValue = formatNumber(oldValue);

            this.value = formattedValue;

            const newCaret = caretPositionAfterFormatting(
                formattedValue,
                numericCharactersBeforeCaret
            );

            try {
                this.setSelectionRange(newCaret, newCaret);
            } catch (error) {
                // Some input types do not support selection ranges.
            }
        });

        // Format on change.
        input.addEventListener("change", function () {
            this.value = formatNumber(this.value);
        });

        // Format pasted values.
        input.addEventListener("paste", function () {
            const inputElement = this;

            window.setTimeout(function () {
                inputElement.value = formatNumber(inputElement.value);
            }, 0);
        });
    }

    // ==========================================================
    // Readonly Price Values
    // ==========================================================

    function formatReadonly(element) {
        if (!element || !isPriceField(element)) {
            return;
        }

        const rawText = (element.textContent || "").trim();

        if (!rawText || /تومان\s*$/.test(rawText)) {
            return;
        }

        const normalized = normalizeNumber(rawText);

        if (!/^-?\d+(?:\.\d+)?$/.test(normalized)) {
            return;
        }

        element.textContent = formatNumber(normalized) + " تومان";
    }

    // ==========================================================
    // Admin Buttons
    // ==========================================================

    function hideExtraButtons() {
        document.querySelectorAll(
            'input[name="_continue"]'
        ).forEach(function (element) {
            element.style.display = "none";
        });

        document.querySelectorAll(
            'input[name="_addanother"]'
        ).forEach(function (element) {
            element.style.display = "none";
        });

        document.querySelectorAll(
            'input[name="_saveasnew"]'
        ).forEach(function (element) {
            element.style.display = "none";
        });

        document.querySelectorAll(
            ".deletelink"
        ).forEach(function (element) {
            element.style.display = "none";
        });
    }

    // ==========================================================
    // Initialize Numeric Inputs
    // ==========================================================

    function initializeNumericInputs(root) {
        if (!root) {
            return;
        }

        if (
            root.matches
            && root.matches("input, textarea")
        ) {
            if (isNumericFormatField(root)) {
                formatInput(root);
            }
        }

        if (!root.querySelectorAll) {
            return;
        }

        root.querySelectorAll(
            "input, textarea"
        ).forEach(function (element) {
            if (isNumericFormatField(element)) {
                formatInput(element);
            }
        });
    }

    // ==========================================================
    // Normalize Numeric Values Before Submit
    // ==========================================================

    function normalizeNumericInputs(form) {
        if (!form) {
            return;
        }

        form.querySelectorAll(
            "input, textarea"
        ).forEach(function (input) {
            if (!isNumericFormatField(input)) {
                return;
            }

            input.value = normalizeNumber(input.value);
        });
    }

    // ==========================================================
    // Initialize
    // ==========================================================

    function initialize() {
        initializeNumericInputs(document);

        document.querySelectorAll(
            ".readonly"
        ).forEach(function (element) {
            formatReadonly(element);
        });

        hideExtraButtons();

        document.querySelectorAll("form").forEach(function (form) {
            if (
                form.dataset.priceNormalizerInitialized === "true"
            ) {
                return;
            }

            form.dataset.priceNormalizerInitialized = "true";

            form.addEventListener("submit", function () {
                normalizeNumericInputs(form);
            });
        });

        if (
            !document.body
            || typeof MutationObserver === "undefined"
        ) {
            return;
        }

        // Support dynamically added inline rows.
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        return;
                    }

                    initializeNumericInputs(node);

                    if (
                        node.matches
                        && node.matches(".readonly")
                    ) {
                        formatReadonly(node);
                    }

                    if (node.querySelectorAll) {
                        node.querySelectorAll(
                            ".readonly"
                        ).forEach(function (element) {
                            formatReadonly(element);
                        });
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // ==========================================================
    // DOM Ready
    // ==========================================================

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialize
        );
    } else {
        initialize();
    }
})();