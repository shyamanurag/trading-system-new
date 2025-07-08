import { useEffect, useState } from 'react';

/**
 * Custom hook for debouncing values
 * Useful for optimizing search performance by delaying API calls
 * until user has stopped typing for a specified delay
 * 
 * @param {any} value - The value to debounce
 * @param {number} delay - The delay in milliseconds (default: 300ms)
 * @returns {any} - The debounced value
 */
export const useDebounce = (value, delay = 300) => {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        // Set up a timer to update the debounced value after the delay
        const timer = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        // Clean up the timer if value changes before delay completes
        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);

    return [debouncedValue, setDebouncedValue];
};

/**
 * Custom hook for debouncing with loading state
 * Provides additional loading indicator while debouncing
 * 
 * @param {any} value - The value to debounce
 * @param {number} delay - The delay in milliseconds (default: 300ms)
 * @returns {[any, boolean]} - The debounced value and loading state
 */
export const useDebounceWithLoading = (value, delay = 300) => {
    const [debouncedValue, setDebouncedValue] = useState(value);
    const [isDebouncing, setIsDebouncing] = useState(false);

    useEffect(() => {
        setIsDebouncing(true);

        const timer = setTimeout(() => {
            setDebouncedValue(value);
            setIsDebouncing(false);
        }, delay);

        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);

    return [debouncedValue, isDebouncing];
};

/**
 * Custom hook for debouncing with callback
 * Executes a callback function after debouncing
 * 
 * @param {function} callback - The callback to execute
 * @param {number} delay - The delay in milliseconds (default: 300ms)
 * @returns {function} - The debounced callback function
 */
export const useDebounceCallback = (callback, delay = 300) => {
    const [debounceTimer, setDebounceTimer] = useState(null);

    const debouncedCallback = (...args) => {
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }

        const newTimer = setTimeout(() => {
            callback(...args);
        }, delay);

        setDebounceTimer(newTimer);
    };

    useEffect(() => {
        // Clean up timer on unmount
        return () => {
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }
        };
    }, [debounceTimer]);

    return debouncedCallback;
};

export default useDebounce; 