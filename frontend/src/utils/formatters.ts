/**
 * Formats a number as currency.
 * @param value The number to format.
 * @param showSign Whether to show a '+' sign for positive numbers.
 * @param currencySymbol The currency symbol (default: '$').
 * @param locale The locale for formatting (default: 'en-US').
 * @returns Formatted currency string or 'N/A'.
 */
export const formatCurrency = (
    value: number | string | null | undefined,
    showSign: boolean = false,
    currencySymbol: string = '$',
    locale: string = 'en-US'
): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    const options: Intl.NumberFormatOptions = {
        style: 'currency',
        currency: 'USD', // TODO: Make currency configurable
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    };
    const formatted = new Intl.NumberFormat(locale, options).format(num);
    
    if (showSign && num > 0) {
        return `+${formatted}`;
    }
    // Negative sign is handled by Intl.NumberFormat
    return formatted;
};

/**
 * Formats a number as a percentage.
 * @param value The number (as a decimal, e.g., 0.05 for 5%) to format.
 * @param locale The locale for formatting (default: 'en-US').
 * @returns Formatted percentage string or 'N/A'.
 */
export const formatPercentage = (
    value: number | string | null | undefined,
    locale: string = 'en-US'
): string => {
     const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    const options: Intl.NumberFormatOptions = {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    };
    return new Intl.NumberFormat(locale, options).format(num);
};

/**
 * Formats a large number with abbreviations (K, M, B, T).
 * @param value The number to format.
 * @param precision Number of decimal places for the abbreviated value.
 * @returns Formatted string or 'N/A'.
 */
export const formatLargeNumber = (
    value: number | string | null | undefined,
    precision: number = 2
): string => {
     const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }

    if (Math.abs(num) < 1000) {
        return num.toString();
    }

    const tiers = [
        { value: 1e12, symbol: "T" },
        { value: 1e9,  symbol: "B" },
        { value: 1e6,  symbol: "M" },
        { value: 1e3,  symbol: "K" },
    ];

    for (const tier of tiers) {
        if (Math.abs(num) >= tier.value) {
            const scaledValue = num / tier.value;
            return `${scaledValue.toFixed(precision)}${tier.symbol}`;
        }
    }

    return num.toFixed(precision); // Fallback for numbers between 1000 and -1000? Should not happen based on check above.
};


/**
 * Formats a number with fixed decimal places.
 * @param value The number to format.
 * @param precision Number of decimal places.
 * @returns Formatted string or 'N/A'.
 */
export const formatNumber = (
    value: number | string | null | undefined,
    precision: number = 2
): string => {
     const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    return num.toFixed(precision);
};

/**
 * Formats a Date object or timestamp string into a readable date string.
 * @param dateInput Date object, ISO string, or timestamp number.
 * @param options Intl.DateTimeFormat options.
 * @param locale Locale string.
 * @returns Formatted date string or 'Invalid Date'.
 */
export const formatDate = (
    dateInput: Date | string | number | null | undefined,
    options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'short', day: 'numeric' },
    locale: string = 'en-US'
): string => {
    if (!dateInput) return 'N/A';

    try {
        const date = new Date(dateInput);
        if (isNaN(date.getTime())) {
            return 'Invalid Date';
        }
        return new Intl.DateTimeFormat(locale, options).format(date);
    } catch (error) {
        console.error("Error formatting date:", error);
        return 'Invalid Date';
    }
};