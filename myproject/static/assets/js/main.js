/**
* Template Name: Logis
* Template URL: https://bootstrapmade.com/logis-bootstrap-logistics-website-template/
* Updated: Aug 07 2024 with Bootstrap v5.3.3
* Author: BootstrapMade.com
* License: https://bootstrapmade.com/license/
*/

(function () {
  "use strict";

  /**
   * Apply .scrolled class to the body as the page is scrolled down
   */
  function toggleScrolled() {
    const selectBody = document.querySelector('body');
    const selectHeader = document.querySelector('#header');
    if (!selectHeader.classList.contains('scroll-up-sticky') && !selectHeader.classList.contains('sticky-top') && !selectHeader.classList.contains('fixed-top')) return;
    window.scrollY > 100 ? selectBody.classList.add('scrolled') : selectBody.classList.remove('scrolled');
  }

  document.addEventListener('scroll', toggleScrolled);
  window.addEventListener('load', toggleScrolled);

  /**
   * Mobile nav toggle
   */
  const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');

  function mobileNavToogle() {
    document.querySelector('body').classList.toggle('mobile-nav-active');
  }
  mobileNavToggleBtn.addEventListener('click', mobileNavToogle);

  /**
   * Hide mobile nav on same-page/hash links
   */
  document.querySelectorAll('#navmenu a').forEach(navmenu => {
    navmenu.addEventListener('click', () => {
      if (document.querySelector('.mobile-nav-active')) {
        mobileNavToogle();
      }
    });

  });

  /**
   * Toggle mobile nav dropdowns
   */
  document.querySelectorAll('.navmenu .toggle-dropdown').forEach(navmenu => {
    navmenu.addEventListener('click', function (e) {
      e.preventDefault();
      this.parentNode.classList.toggle('active');
      this.parentNode.nextElementSibling.classList.toggle('dropdown-active');
      e.stopImmediatePropagation();
    });
  });

  /**
   * Preloader
   */
  const preloader = document.querySelector('#preloader');
  if (preloader) {
    window.addEventListener('load', () => {
      preloader.remove();
    });
  }

  /**
   * Scroll top button
   */
  let scrollTop = document.querySelector('.scroll-top');

  function toggleScrollTop() {
    if (scrollTop) {
      window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
    }
  }
  scrollTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  window.addEventListener('load', toggleScrollTop);
  document.addEventListener('scroll', toggleScrollTop);

  /**
   * Animation on scroll function and init
   */
  function aosInit() {
    AOS.init({
      duration: 600,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    });
  }
  window.addEventListener('load', aosInit);

  /**
   * Initiate Pure Counter
   */
  new PureCounter();

  /**
   * Initiate glightbox
   */
  const glightbox = GLightbox({
    selector: '.glightbox'
  });

  /**
   * Init swiper sliders
   */
  function initSwiper() {
    document.querySelectorAll(".init-swiper").forEach(function (swiperElement) {
      let config = JSON.parse(
        swiperElement.querySelector(".swiper-config").innerHTML.trim()
      );

      if (swiperElement.classList.contains("swiper-tab")) {
        initSwiperWithCustomPagination(swiperElement, config);
      } else {
        new Swiper(swiperElement, config);
      }
    });
  }

  window.addEventListener("load", initSwiper);

  /**
   * Frequently Asked Questions Toggle
   */
  document.querySelectorAll('.faq-item h3, .faq-item .faq-toggle').forEach((faqItem) => {
    faqItem.addEventListener('click', () => {
      faqItem.parentNode.classList.toggle('faq-active');
    });
  });

})();


// تبدیل اعداد انگلیسی به فارسی در کل سایت
function convertToPersianNumbers(element) {
  const persianMap = {
    '0': '۰',
    '1': '۱',
    '2': '۲',
    '3': '۳',
    '4': '۴',
    '5': '۵',
    '6': '۶',
    '7': '۷',
    '8': '۸',
    '9': '۹'
  };

  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  let node;

  while ((node = walker.nextNode())) {
    node.nodeValue = node.nodeValue.replace(/\d/g, d => persianMap[d]);
  }
}

window.addEventListener('load', () => {
  convertToPersianNumbers(document.body);
});


document.addEventListener("DOMContentLoaded", function () {

  const closeBtn = document.querySelector(".mobile-nav-close");

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      document.body.classList.remove("mobile-nav-active");
    });
  }

});


/* =========================================
   Iranian License Plate Input
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    const plateWrapper =
        document.querySelector(".plate-input-wrapper");

    if (!plateWrapper) {
        return;
    }


    const fields = [
        plateWrapper.querySelector(".plate-city"),
        plateWrapper.querySelector(".plate-middle"),
        plateWrapper.querySelector(".plate-letter"),
        plateWrapper.querySelector(".plate-right")
    ];


    fields.forEach(function (field, index) {

        if (!field) {
            return;
        }


        field.addEventListener("input", function () {

            /*
             * فقط مقدار مورد نیاز را نگه می‌داریم
             */

            this.value = this.value
                .replace(/[^\u06F0-\u06F9\d\u0660-\u0669a-zA-Zآ-ی]/g, "");


            /*
             * اگر به حداکثر طول رسید
             * برو فیلد بعدی
             */

            if (
                this.value.length >=
                this.maxLength &&
                fields[index + 1]
            ) {

                fields[index + 1].focus();

            }

        });


        /*
         * Backspace روی فیلد خالی
         * برگردد به فیلد قبلی
         */

        field.addEventListener("keydown", function (event) {

            if (
                event.key === "Backspace" &&
                this.value === "" &&
                fields[index - 1]
            ) {

                fields[index - 1].focus();

            }

        });

    });

});


/* =========================================================
   Service Request - Persian Digits
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector(
        "#service-request-form"
    );

    if (!form) {
        return;
    }


    const inputs = form.querySelectorAll(
        'input[type="tel"], input[inputmode="numeric"]'
    );


    const toPersianDigits = (value) => {

        return String(value)
            .replace(/[0-9]/g, function (digit) {

                return "۰۱۲۳۴۵۶۷۸۹"[
                    Number(digit)
                ];

            })
            .replace(/[٠-٩]/g, function (digit) {

                return "۰۱۲۳۴۵۶۷۸۹"[
                    "٠١٢٣٤٥٦٧٨٩".indexOf(digit)
                ];

            });

    };


    inputs.forEach(function (input) {

        input.addEventListener(
            "input",
            function () {

                const start =
                    this.selectionStart;

                const end =
                    this.selectionEnd;


                this.value =
                    toPersianDigits(
                        this.value
                    );


                /*
                 * حفظ موقعیت Cursor
                 */
                try {

                    this.setSelectionRange(
                        start,
                        end
                    );

                } catch (error) {

                    // بعضی inputها selection را پشتیبانی نمی‌کنند.

                }

            }
        );

    });

});

/* =========================================================
   Service Request Form
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form = document.getElementById(
            "service-request-form"
        );

        if (!form) {
            return;
        }


        form.addEventListener(
            "submit",
            function () {

                const submitButton =
                    document.getElementById(
                        "service-request-submit"
                    );

                if (submitButton) {

                    submitButton.disabled = true;

                    submitButton
                        .querySelector("span")
                        .textContent =
                        "در حال ثبت درخواست...";

                }

            }
        );

    }
);

/* =========================================================
   Site Messages
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const messages =
            document.querySelectorAll(
                ".site-message"
            );


        messages.forEach(function (message) {

            const closeButton =
                message.querySelector(
                    ".site-message__close"
                );


            const hideMessage =
                function () {

                    if (
                        message.classList.contains(
                            "is-hiding"
                        )
                    ) {
                        return;
                    }


                    message.classList.add(
                        "is-hiding"
                    );


                    setTimeout(
                        function () {

                            message.remove();

                        },
                        300
                    );

                };


            /* بستن دستی */

            if (closeButton) {

                closeButton.addEventListener(
                    "click",
                    hideMessage
                );

            }


            /* بستن خودکار بعد از 5 ثانیه */

            setTimeout(
                hideMessage,
                5000
            );

        });

    }
);

/* =========================================================
   Iranian License Plate Display Formatter
   Format:
   12-ب-345-67ایران
========================================================= */

(function () {

    "use strict";


    // =========================================================
    // Digit Normalization
    // =========================================================

    function normalizePlateDigits(value) {

        return String(value || "")

            // Persian digits → English
            .replace(/[۰-۹]/g, function (digit) {

                return "۰۱۲۳۴۵۶۷۸۹".indexOf(digit);

            })

            // Arabic digits → English
            .replace(/[٠-٩]/g, function (digit) {

                return "٠١٢٣٤٥٦٧٨٩".indexOf(digit);

            });
    }


    // =========================================================
    // Plate Formatter
    // =========================================================

    function formatIranianPlate(value) {

        if (!value) {
            return "";
        }


        let text =
            normalizePlateDigits(value)
                .trim();


        /*
         * Remove common separators only for detection.
         *
         * Examples:
         *
         * 12ب34567
         * 12-ب-345-67
         * 12 / ب / 345 / 67
         *
         */

        const compact =
            text
                .replace(
                    /\s+/g,
                    ""
                )
                .replace(
                    /[-/|]/g,
                    ""
                );


        /*
         * Iranian plate structure:
         *
         * 2 digits
         * 1 Persian letter
         * 3 digits
         * 2 digits
         */

        const match =
            compact.match(
                /^(\d{2})([آ-ی])(\d{3})(\d{2})$/
            );


        if (!match) {
            return text;
        }


        return (
            match[1] +
            "-" +
            match[2] +
            "-" +
            match[3] +
            "-" +
            match[4] +
            "ایران"
        );
    }


    // =========================================================
    // Replace Plate Inside Larger Text
    // =========================================================

    function formatPlateInsideText(value) {

        if (!value) {
            return value;
        }


        const normalized =
            normalizePlateDigits(value);


        /*
         * This regex finds a raw plate anywhere
         * inside a larger string.
         *
         * Example:
         *
         * "پژو 206 - 12ب34567"
         *
         * becomes:
         *
         * "پژو 206 - 12-ب-345-67ایران"
         */

        return normalized.replace(
            /(\d{2})\s*([آ-ی])\s*(\d{3})\s*(\d{2})(?!\d)/g,
            function (
                full,
                city,
                letter,
                middle,
                right
            ) {

                return (
                    city +
                    "-" +
                    letter +
                    "-" +
                    middle +
                    "-" +
                    right +
                    "ایران"
                );
            }
        );
    }


    // =========================================================
    // ForeignKey / Select Options
    // =========================================================

    function formatPlateOptions(root) {

        if (!root) {
            return;
        }


        /*
         * All select options:
         *
         * Django ForeignKey choices are rendered
         * as <option> elements.
         */

        const options =
            root.querySelectorAll
                ? root.querySelectorAll(
                    "select option"
                )
                : [];


        options.forEach(
            function (option) {

                const original =
                    option.textContent;


                if (!original) {
                    return;
                }


                const formatted =
                    formatPlateInsideText(
                        original
                    );


                if (
                    formatted !== original
                ) {

                    option.textContent =
                        formatted;

                    option.dir =
                        "ltr";
                }
            }
        );
    }


    // =========================================================
    // Standalone Plate Elements
    // =========================================================

    function formatPlateElements(root) {

        if (!root) {
            return;
        }


        const elements =
            root.querySelectorAll
                ? root.querySelectorAll(
                    [
                        ".formatted-plate",
                        ".plate-display",
                        ".plate-number-display",
                        "[data-plate]",
                        "[data-plate-number]"
                    ].join(",")
                )
                : [];


        elements.forEach(
            function (element) {

                const value =
                    element.textContent ||
                    element.getAttribute(
                        "data-plate-number"
                    ) ||
                    "";


                const formatted =
                    formatIranianPlate(
                        value
                    );


                if (formatted) {

                    element.textContent =
                        formatted;

                    element.dir =
                        "ltr";
                }
            }
        );
    }


    // =========================================================
    // Main Initializer
    // =========================================================

    function initializePlateFormatter(
        root
    ) {

        if (!root) {
            return;
        }


        formatPlateOptions(
            root
        );


        formatPlateElements(
            root
        );
    }


    // =========================================================
    // DOM Ready
    // =========================================================

    function initialize() {

        initializePlateFormatter(
            document
        );


        /*
         * Django Admin dynamically creates
         * inline rows and form elements.
         *
         * MutationObserver makes the formatter
         * work there as well.
         */

        if (!document.body) {
            return;
        }


        const observer =
            new MutationObserver(
                function (mutations) {

                    mutations.forEach(
                        function (mutation) {

                            mutation.addedNodes.forEach(
                                function (node) {

                                    if (
                                        node.nodeType !==
                                        Node.ELEMENT_NODE
                                    ) {
                                        return;
                                    }


                                    initializePlateFormatter(
                                        node
                                    );
                                }
                            );
                        }
                    );
                }
            );


        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );
    }


    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            { once: true }
        );

    } else {

        initialize();
    }


    /*
     * Expose formatter globally.
     *
     * Useful for other admin/public scripts.
     */

    window.formatIranianPlate =
        formatIranianPlate;

    window.formatPlateInsideText =
        formatPlateInsideText;

})();

/* =========================================================
   Reduce Browser Autofill / Saved Input Suggestions
========================================================= */

(function () {
    "use strict";

    const fieldSelector = [
        'input:not([type="hidden"])',
        'textarea',
        'select'
    ].join(",");

    const protectedTypes = new Set([
        "text",
        "email",
        "tel",
        "search",
        "url",
        "password"
    ]);

    function protectField(field) {
        if (field.dataset.autofillGuard === "1") {
            return;
        }

        if (field.disabled) {
            return;
        }

        const tagName = field.tagName.toLowerCase();
        const type = (
            tagName === "textarea"
                ? "text"
                : field.type || ""
        ).toLowerCase();

        if ([
            "hidden",
            "submit",
            "button",
            "reset",
            "checkbox",
            "radio",
            "file"
        ].includes(type)) {
            return;
        }

        field.dataset.autofillGuard = "1";

        field.setAttribute("autocomplete", "off");
        field.setAttribute("autocorrect", "off");
        field.setAttribute("autocapitalize", "off");

        if (protectedTypes.has(type)) {
            field.setAttribute("autocomplete", "new-password");

            // فقط readonlyهایی را برمی‌داریم که خودمان اعمال کرده‌ایم.
            if (!field.readOnly) {
                field.readOnly = true;
                field.dataset.autofillReadonly = "1";
            }
        }
    }

    function applyProtection(root) {
        if (!root || root.nodeType !== Node.ELEMENT_NODE) {
            return;
        }

        if (root.matches("form")) {
            root.setAttribute("autocomplete", "off");
        }

        if (root.matches(fieldSelector)) {
            protectField(root);
        }

        root.querySelectorAll("form").forEach(function (form) {
            form.setAttribute("autocomplete", "off");
        });

        root.querySelectorAll(fieldSelector).forEach(
            protectField
        );
    }

    function initialize() {
        document.querySelectorAll("form").forEach(function (form) {
            form.setAttribute("autocomplete", "off");
        });

        applyProtection(document.documentElement);

        // آزاد کردن فیلد هنگام تعامل کاربر
        document.addEventListener("focusin", function (event) {
            const field = event.target;

            if (
                !field ||
                !field.matches ||
                !field.matches(fieldSelector)
            ) {
                return;
            }

            if (field.dataset.autofillReadonly === "1") {
                field.readOnly = false;
                delete field.dataset.autofillReadonly;
            }

            const type = (
                field.tagName.toLowerCase() === "textarea"
                    ? "text"
                    : field.type || ""
            ).toLowerCase();

            field.setAttribute(
                "autocomplete",
                protectedTypes.has(type)
                    ? "new-password"
                    : "off"
            );

            const form = field.closest("form");

            if (form) {
                form.setAttribute("autocomplete", "off");
            }
        }, true);

        // پشتیبانی از فیلدها و ردیف‌های داینامیک
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        applyProtection(node);
                    }
                });
            });
        });

        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            { once: true }
        );
    } else {
        initialize();
    }
})();