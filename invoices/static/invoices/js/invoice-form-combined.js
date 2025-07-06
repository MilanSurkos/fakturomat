/**
 * Invoice Form JavaScript
 * Handles dynamic form fields, calculations, and validation
 */

// Main invoice form object
window.invoiceForm = (function() {
    'use strict';

    // DOM elements
    let form;
    let formsetContainer;
    let addButton;
    let totalFormsInput;
    let emptyForm;
    let formsetPrefix;
    let calculationError;

    // Constants
    const CURRENCY = '€';
    const TAX_RATE = 0.20; // 20% VAT
    const DECIMAL_PLACES = 2;

    /**
     * Initialize the invoice form
     */
    function init() {
        // Get DOM elements
        form = document.getElementById('invoice-form');
        formsetContainer = document.getElementById('formset-container');
        addButton = document.getElementById('add-item');
        totalFormsInput = document.getElementById('id_items-TOTAL_FORMS');
        emptyForm = document.getElementById('empty-form');
        calculationError = document.getElementById('calculation-error');

        if (!form || !formsetContainer || !addButton || !totalFormsInput || !emptyForm) {
            console.error('Required form elements not found');
            return;
        }

        // Extract formset prefix from the first form if it exists
        const firstForm = formsetContainer.querySelector('.formset-form');
        formsetPrefix = firstForm ? firstForm.dataset.formPrefix : 'items';

        // Set up event listeners
        setupEventListeners();

        // Initialize existing forms
        initializeExistingForms();

        // Update totals on page load
        updateInvoiceTotals();
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Add item button
        addButton.addEventListener('click', addForm);

        // Delegate events for dynamically added elements
        formsetContainer.addEventListener('click', function(e) {
            // Handle delete button clicks
            if (e.target.classList.contains('remove-item')) {
                e.preventDefault();
                removeForm(e.target.closest('.formset-form'));
            }
        });

        // Handle input changes for calculations
        formsetContainer.addEventListener('input', function(e) {
            const target = e.target;
            const formRow = target.closest('.formset-form');
            
            if (!formRow) return;

            // Update row total when quantity or unit price changes
            if (target.matches('input[name$="-quantity"], input[name$="-unit_price"]')) {
                updateRowTotal(formRow);
                updateInvoiceTotals();
            }
        });

        // Handle form submission
        if (form) {
            form.addEventListener('submit', validateForm);
        }
    }

    /**
     * Initialize existing forms in the formset
     */
    function initializeExistingForms() {
        const forms = formsetContainer.querySelectorAll('.formset-form');
        forms.forEach(form => {
            // Update row total for each existing row
            updateRowTotal(form);
            
            // Initialize delete button
            const deleteCheckbox = form.querySelector('input[type="checkbox"][id$="-DELETE"]');
            const removeButton = form.querySelector('.remove-item');
            
            if (deleteCheckbox && removeButton) {
                removeButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    removeForm(form);
                });
            }
        });
    }

    /**
     * Add a new form to the formset
     */
    function addForm() {
        // Get the current form count
        const totalForms = parseInt(totalFormsInput.value);
        const formNum = totalForms;
        
        // Create a new form by cloning the empty form
        const newForm = emptyForm.cloneNode(true);
        newForm.classList.remove('d-none');
        newForm.removeAttribute('id');
        
        // Update form field names and IDs
        const formHtml = newForm.innerHTML.replace(/__prefix__/g, formNum);
        newForm.innerHTML = formHtml;
        newForm.dataset.formIndex = formNum;
        
        // Add the new form to the container
        formsetContainer.appendChild(newForm);
        
        // Update the total forms count
        totalFormsInput.value = totalForms + 1;
        
        // Initialize the new form
        updateRowTotal(newForm);
        updateInvoiceTotals();
        
        // Scroll to the new form
        newForm.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Remove a form from the formset
     * @param {HTMLElement} formElement - The form element to remove
     */
    function removeForm(formElement) {
        const deleteCheckbox = formElement.querySelector('input[type="checkbox"][id$="-DELETE"]');
        
        if (deleteCheckbox) {
            // If this is an existing form, mark it for deletion
            deleteCheckbox.checked = !deleteCheckbox.checked;
            formElement.style.display = deleteCheckbox.checked ? 'none' : '';
            
            // If this is a new form, remove it completely
            if (!formElement.querySelector('input[name$="-id"]') || !formElement.querySelector('input[name$="-id"]').value) {
                formElement.remove();
                // No need to update total forms as we're not changing the count for new forms
            }
        } else {
            // For forms without a delete checkbox, just remove them
            formElement.remove();
        }
        
        // Update row indices and totals
        updateFormIndices();
        updateInvoiceTotals();
    }

    /**
     * Parse a numeric input value, handling various formats and locales
     * @param {string} value - The input value to parse
     * @returns {number} The parsed number or 0 if invalid
     */
    function parseNumericInput(value) {
        if (value === '' || value === null || value === undefined) {
            return 0;
        }
        
        // Convert to string and clean the value
        const strValue = String(value).trim()
            .replace(/\s+/g, '')  // Remove spaces (e.g., thousand separators)
            .replace(/,/g, '.')    // Replace comma with dot for decimal
            .replace(/[^\d.-]/g, ''); // Remove any non-numeric characters except minus and dot
        
        // Parse the cleaned value
        const numValue = parseFloat(strValue);
        return isNaN(numValue) ? 0 : numValue;
    }

    /**
     * Update the total for a single row
     * @param {HTMLElement} formRow - The form row to update
     */
    function updateRowTotal(formRow) {
        const quantityInput = formRow.querySelector('input[name$="-quantity"]');
        const unitPriceInput = formRow.querySelector('input[name$="-unit_price"]');
        const totalDisplay = formRow.querySelector('.row-total');
        
        if (quantityInput && unitPriceInput && totalDisplay) {
            const quantity = parseNumericInput(quantityInput.value);
            const unitPrice = parseNumericInput(unitPriceInput.value);
            
            // Update input values with cleaned numbers
            if (quantityInput.value !== '' && !isNaN(quantity)) {
                quantityInput.value = quantity % 1 === 0 ? quantity.toFixed(0) : quantity.toFixed(2);
            }
            
            if (unitPriceInput.value !== '' && !isNaN(unitPrice)) {
                unitPriceInput.value = unitPrice.toFixed(2);
            }
            
            // Calculate and display total
            const total = quantity * unitPrice;
            totalDisplay.textContent = formatCurrency(total);
            
            // Validate and update field states
            if (quantity < 0) {
                quantityInput.classList.add('is-invalid');
            } else {
                quantityInput.classList.remove('is-invalid');
            }
            
            if (unitPrice < 0) {
                unitPriceInput.classList.add('is-invalid');
            } else {
                unitPriceInput.classList.remove('is-invalid');
            }
        }
    }

    /**
     * Update all invoice totals (subtotal, tax, total)
     */
    function updateInvoiceTotals() {
        const rows = formsetContainer.querySelectorAll('.formset-form:not([style*="display: none"])');
        let subtotal = 0;
        let hasErrors = false;
        
        // Reset all row errors first
        rows.forEach(row => {
            const quantityInput = row.querySelector('input[name$="-quantity"]');
            const unitPriceInput = row.querySelector('input[name$="-unit_price"]');
            
            if (quantityInput && unitPriceInput) {
                quantityInput.classList.remove('is-invalid');
                unitPriceInput.classList.remove('is-invalid');
            }
        });
        
        // Calculate subtotal from all visible rows
        rows.forEach(row => {
            const quantityInput = row.querySelector('input[name$="-quantity"]');
            const unitPriceInput = row.querySelector('input[name$="-unit_price"]');
            
            if (quantityInput && unitPriceInput) {
                const quantity = parseNumericInput(quantityInput.value);
                const unitPrice = parseNumericInput(unitPriceInput.value);
                
                // Validate quantity
                if (quantity < 0) {
                    quantityInput.classList.add('is-invalid');
                    hasErrors = true;
                }
                
                // Validate unit price
                if (unitPrice < 0) {
                    unitPriceInput.classList.add('is-invalid');
                    hasErrors = true;
                }
                
                // Only add to subtotal if both values are valid
                if (quantity >= 0 && unitPrice >= 0) {
                    subtotal += quantity * unitPrice;
                } else if (quantityInput.value !== '' || unitPriceInput.value !== '') {
                    // Only show error if at least one field has a value
                    hasErrors = true;
                }
            }
        });
        
        // Round subtotal to 2 decimal places to avoid floating point issues
        subtotal = Math.round(subtotal * 100) / 100;
        
        // Calculate tax and total
        const tax = Math.round(subtotal * TAX_RATE * 100) / 100; // Round to 2 decimal places
        const total = Math.round((subtotal + tax) * 100) / 100; // Round to 2 decimal places
        
        // Update the UI
        updateTotalDisplay('subtotal', subtotal);
        updateTotalDisplay('tax', tax);
        updateTotalDisplay('total', total);
        
        // Also update hidden form fields
        const subtotalInput = document.querySelector('input[name="subtotal"]');
        const taxInput = document.querySelector('input[name="total_tax"]');
        const totalInput = document.querySelector('input[name="total_amount"]');
        
        if (subtotalInput) subtotalInput.value = subtotal.toFixed(2);
        if (taxInput) taxInput.value = tax.toFixed(2);
        if (totalInput) totalInput.value = total.toFixed(2);
        
        return { 
            subtotal, 
            tax, 
            total,
            hasErrors
        };
    }

    /**
     * Update a total display element
     * @param {string} type - The type of total (subtotal, tax, total)
     * @param {number} value - The value to display
     */
    function updateTotalDisplay(type, value) {
        // Map type to the correct element ID in the HTML
        const elementIds = {
            'subtotal': 'subtotal-display',
            'tax': 'tax-amount',
            'total': 'total-amount'
        };
        
        const elementId = elementIds[type];
        if (!elementId) {
            console.error(`Unknown total type: ${type}`);
            return;
        }
        
        const element = document.getElementById(elementId);
        if (element) {
            // Format the value with 2 decimal places and add the currency symbol
            const formattedValue = parseFloat(value).toFixed(2);
            element.textContent = `${formattedValue} €`;
            
            // Also update the corresponding hidden input if it exists
            const hiddenInput = element.nextElementSibling;
            if (hiddenInput && hiddenInput.tagName === 'INPUT' && hiddenInput.type === 'hidden') {
                hiddenInput.value = formattedValue;
            }
        } else {
            console.error(`Element with ID '${elementId}' not found`);
        }
    }

    /**
     * Format a number as currency
     * @param {number} amount - The amount to format
     * @returns {string} Formatted currency string
     */
    function formatCurrency(amount) {
        return `${CURRENCY}${amount.toFixed(DECIMAL_PLACES).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
    }

    /**
     * Update form indices for all forms in the formset
     */
    function updateFormIndices() {
        const forms = formsetContainer.querySelectorAll('.formset-form:not([style*="display: none"])');
        let formIndex = 0;
        
        forms.forEach((form, index) => {
            // Update data attributes and indices
            form.dataset.formIndex = index;
            
            // Update input names and IDs
            form.querySelectorAll('input, select, textarea, label').forEach(element => {
                if (element.id) {
                    element.id = element.id.replace(/\d+/, index);
                }
                if (element.name) {
                    element.name = element.name.replace(/\d+/, index);
                }
                if (element.htmlFor) {
                    element.htmlFor = element.htmlFor.replace(/\d+/, index);
                }
            });
            
            formIndex++;
        });
        
        // Update the total forms count
        totalFormsInput.value = formIndex;
    }

    /**
     * Validate the form before submission
     * @param {Event} e - The form submit event
     */
    function validateForm(e) {
        let isValid = true;
        const errorMessages = [];
        
        // Reset error display and validation states
        if (calculationError) {
            calculationError.classList.add('d-none');
            calculationError.innerHTML = '';
        }
        
        // Reset all invalid states
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        
        // Validate required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            // Skip validation for hidden fields that are marked as required
            if (field.type === 'hidden' && field.name.includes('items-') && field.name.includes('-id')) {
                return;
            }
            
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
                const fieldLabel = field.labels && field.labels.length > 0 
                    ? field.labels[0].textContent 
                    : field.name.split('-').pop().replace('_', ' ');
                errorMessages.push(`"${fieldLabel}" is required.`);
            }
        });
        
        // Validate invoice items
        const visibleForms = Array.from(formsetContainer.querySelectorAll('.formset-form:not([style*="display: none"])'));
        let hasValidItems = false;
        
        // First, check if there are any forms with data
        const formsWithData = visibleForms.filter(form => {
            const description = form.querySelector('input[name$="-description"]')?.value.trim();
            const quantity = form.querySelector('input[name$="-quantity"]')?.value;
            const unitPrice = form.querySelector('input[name$="-unit_price"]')?.value;
            
            return description || quantity || unitPrice;
        });
        
        // If there are forms but none with data, this is an error
        if (visibleForms.length > 0 && formsWithData.length === 0) {
            isValid = false;
            errorMessages.push('Please add at least one invoice item or remove all empty items.');
        }
        
        // Now validate each form that has data
        formsWithData.forEach((form, index) => {
            const description = form.querySelector('input[name$="-description"]')?.value.trim();
            const quantity = form.querySelector('input[name$="-quantity"]')?.value;
            const unitPrice = form.querySelector('input[name$="-unit_price"]')?.value;
            const quantityField = form.querySelector('input[name$="-quantity"]');
            const unitPriceField = form.querySelector('input[name$="-unit_price"]');
            
            // Validate description
            if (!description) {
                isValid = false;
                const descriptionField = form.querySelector('input[name$="-description"]');
                if (descriptionField) {
                    descriptionField.classList.add('is-invalid');
                    errorMessages.push(`Item ${index + 1}: Description is required.`);
                }
            }
            
            // Validate quantity
            if (!quantity || isNaN(parseFloat(quantity)) || parseFloat(quantity) <= 0) {
                isValid = false;
                if (quantityField) {
                    quantityField.classList.add('is-invalid');
                    errorMessages.push(`Item ${index + 1}: Quantity must be greater than 0.`);
                }
            }
            
            // Validate unit price
            if (!unitPrice || isNaN(parseFloat(unitPrice)) || parseFloat(unitPrice) < 0) {
                isValid = false;
                if (unitPriceField) {
                    unitPriceField.classList.add('is-invalid');
                    errorMessages.push(`Item ${index + 1}: Unit price must be a positive number.`);
                }
            }
            
            // If we got here and all fields are valid, we have at least one valid item
            if (description && quantity && unitPrice && 
                !isNaN(parseFloat(quantity)) && parseFloat(quantity) > 0 &&
                !isNaN(parseFloat(unitPrice)) && parseFloat(unitPrice) >= 0) {
                hasValidItems = true;
            }
        });
        
        // If we have forms but no valid items, show an error
        if (visibleForms.length > 0 && !hasValidItems) {
            isValid = false;
            if (!errorMessages.some(msg => msg.includes('at least one invoice item'))) {
                errorMessages.push('Please correct the errors in the invoice items.');
            }
        }
        
        // Validate numeric fields and ensure they're positive where required
        const numericFields = form.querySelectorAll('input[type="number"], input[data-type="number"]');
        numericFields.forEach(field => {
            const value = field.value.trim();
            const fieldName = field.labels[0]?.textContent.trim().replace('*', '') || field.name;
            
            // Check if field is required but empty
            if (field.required && value === '') {
                isValid = false;
                field.classList.add('is-invalid');
                errorMessages.push(`"${fieldName}" is required.`);
                return;
            }
            
            // Skip validation if field is empty and not required
            if (value === '') return;
            
            // Validate numeric value
            const numValue = parseFloat(value);
            if (isNaN(numValue)) {
                isValid = false;
                field.classList.add('is-invalid');
                errorMessages.push(`"${fieldName}" must be a valid number.`);
                return;
            }
            
            // Validate positive numbers (for quantity, unit price, etc.)
            if ((field.name.includes('quantity') || field.name.includes('unit_price')) && numValue < 0) {
                isValid = false;
                field.classList.add('is-invalid');
                errorMessages.push(`"${fieldName}" must be a positive number.`);
            }
        });
        
        // If validation fails, prevent form submission and show errors
        if (!isValid) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            // Display error messages
            if (calculationError) {
                calculationError.classList.remove('d-none');
                const errorList = document.createElement('ul');
                errorList.className = 'mb-0';
                
                // Remove duplicate messages
                const uniqueMessages = [...new Set(errorMessages)];
                
                uniqueMessages.forEach(message => {
                    const item = document.createElement('li');
                    item.textContent = message;
                    errorList.appendChild(item);
                });
                
                calculationError.innerHTML = '';
                calculationError.appendChild(document.createTextNode('Please correct the following errors:'));
                calculationError.appendChild(errorList);
                
                // Scroll to the first error
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                } else {
                    calculationError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            return false;
        }
        
        // If we get here, all validations passed
        return true;
    }

    // Public API
    return {
        init: init,
        updateInvoiceTotals: updateInvoiceTotals,
        addForm: addForm,
        removeForm: removeForm
    };
})();

// Initialize the form when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    window.invoiceForm.init();
});