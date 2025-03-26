import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";

export class PatientEid extends Component {
    static template = "synergia_pharmacy.PatientEid";
    static props = {
        ...standardFieldProps,
        placeholder: { type: String, optional: true },
    };

    setup() {
        super.setup();

        // Initialize the input field and manage its updates
        this.inputValue = this.props.record.data[this.props.name] || ''; // Keep track of the current value
        useInputField({
            getValue: () => this.inputValue, // Get value from state
            setValue: (value) => this.updateFormattedValue(value), // Update the formatted value
        });
    }

    /**
     * Handles the input event, formatting the value while preserving the cursor position.
     * @param {Event} event
     */
    onInput(event) {
//        const inputElement = this.refs.input;  // Access the input element correctly using refs
        const inputElement = event.target;  // Access the input element correctly using refs
        let rawValue = inputElement.value.replace(/\D/g, ""); // Remove non-numeric characters

        // Save cursor position before formatting
        const previousLength = inputElement.value.length;
        const cursorPosition = inputElement.selectionStart;

        // Format the raw value into the desired format
        const formattedValue = this.formatEID(rawValue);

        // Manually update the input element value to ensure the correct format
        inputElement.value = formattedValue;

        // Recalculate the cursor position
        let newCursorPosition = cursorPosition + (formattedValue.length - previousLength);
        newCursorPosition = Math.min(newCursorPosition, formattedValue.length);

        // Ensure the cursor stays in the correct position
        setTimeout(() => {
            inputElement.setSelectionRange(newCursorPosition, newCursorPosition);
        }, 0);

        // Update internal state (no immediate props.record.update)
        this.inputValue = formattedValue;
    }

    /**
     * Formats the input into a specific EID format: 000-0000-00000-000-0
     * @param {string} value - The raw numeric string.
     * @returns {string} - The formatted string.
     */
    formatEID(value) {
        let formatted = "";

        if (value.length > 0) formatted += value.substring(0, 3);
        if (value.length > 3) formatted += "-" + value.substring(3, 7);
        if (value.length > 7) formatted += "-" + value.substring(7, 12);
        if (value.length > 12) formatted += "-" + value.substring(12, 15);
        if (value.length > 15) formatted += "-" + value.substring(15, 16);

        return formatted;
    }

    /**
     * Saves the formatted EID value to the model (backend).
     */
    save() {
//        const inputElement = this.refs.input;  // Correct reference to the input element
        const inputElement = event.target;  // Correct reference to the input element
        if (inputElement) {
            const formattedValue = this.formatEID(inputElement.value.replace(/\D/g, ""));
            this.props.record.update({ [this.props.name]: formattedValue });
        }
    }

    /**
     * Handles the blur event to trigger saving the value to the database
     * and update the field in the backend.
     */
    onBlur(event) {
        this.save();
    }
}

// Register the custom widget for EID
export const patientEidField = {
    component: PatientEid,
    displayName: _t("Patient EID"),
    supportedTypes: ["char"],
    extractProps: ({ attrs }) => ({
        placeholder: attrs.placeholder || "000-0000-00000-000-0",
    }),
};

registry.category("fields").add("patient_eid_autofill", patientEidField);
