// Test if script is loaded
alert('invoice-form.js is loaded!');

/**
 * Invoice Form Management
 * 
 * Handles all dynamic behavior of the invoice form including:
 * - Adding/removing items
 * - Calculating totals
 * - Form validation
 * - Event handling
 */
class InvoiceForm {
    /**
     * Initialize a new InvoiceForm instance
     */
    constructor() {
        // Cache DOM elements
        this.cacheElements();
        
        // Initialize form state
        this.formCount = this.totalForms ? parseInt(this.totalForms.value, 10) : 0;
        
        // Set up the form
        this.initialize();
    }
    
    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        this.form = document.getElementById('invoice-form');
        this.formsetContainer = document.getElementById('formset-container');
        this.totalForms = document.getElementById('id_items-TOTAL_FORMS');
        this.emptyFormTemplate = document.getElementById('empty-form');
    }
    
    /**
     * Initialize the invoice form
     * Sets up event listeners and initial state
     */
    initialize() {
        if (!this.form) {
            console.warn('Invoice form element not found');
            return;
        }
        
        this.setupEventDelegation();
        this.initializeExistingForms();
        
        // Add initial empty form if needed
        if (this.formCount === 0) {
            this.addNewItemRow();
        }
        
        this.updateInvoiceTotals();
    }
    
    /**
     * Set up event delegation for dynamic elements
     */
    setupEventDelegation() {
        const container = this.formsetContainer || document;
        
        // Handle all click events
        container.addEventListener('click', (e) => this.handleClickEvents(e));
        
        // Handle input changes for dynamic updates
        container.addEventListener('input', (e) => this.handleInputEvents(e));
        
        // Handle form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    }
    
    /**
     * Handle all click events in the form
     * @param {Event} event - The click event
     */
    handleClickEvents(event) {
        const target = event.target;
        console.log('Click event on:', target);
        
        // Handle quantity controls
        const quantityControl = target.closest('.quantity-control');
        if (quantityControl) {
            console.log('Quantity control clicked');
            event.preventDefault();
            event.stopPropagation();
            this.handleQuantityControl(quantityControl);
            return;
        }
        
        // Handle remove item
        const removeButton = target.closest('.remove-item');
        if (removeButton) {
            console.log('Remove button clicked');
            event.preventDefault();
            event.stopPropagation();
            this.handleRemoveItem(removeButton);
            return;
        }
        
        // Handle add item - check both the button and any child elements
        const addButton = target.closest('#add-item') || 
                         (target.matches('#add-item') && target) ||
                         (target.closest('button') && target.closest('button').id === 'add-item' && target.closest('button'));
        
        if (addButton) {
            console.log('Add item button clicked');
            event.preventDefault();
            event.stopPropagation();
            this.addNewItemRow();
            return;
        }
    }
    
    /**
     * Handle input events for dynamic updates
     * @param {Event} event - The input event
     */
    handleInputEvents(event) {
        const input = event.target;
        const isRelevantInput = input.matches('input[id$="-quantity"], input[id$="-unit_price"], input[id$="-vat_rate"]');
        
        if (isRelevantInput) {
            this.updateInvoiceTotals();
        }
    }
    
    /**
     * Initialize all existing form rows in the DOM
     */
    initializeExistingForms() {
        const forms = this.formsetContainer?.querySelectorAll('.formset-form');
        if (!forms) return;
        
        forms.forEach(form => this.initializeFormRow(form));
    }
    
    /**
     * Initialize a single form row with any necessary plugins
     * @param {HTMLElement} formRow - The form row element to initialize
     */
    initializeFormRow(formRow) {
        if (!formRow) return;
        
        // Initialize Select2 if available
        this.initializeSelect2(formRow);
    }
    
    /**
     * Initialize Select2 for select elements in the given container
     * @param {HTMLElement} container - The container element containing select elements
     */
    initializeSelect2(container) {
        if (!window.jQuery?.fn.select2) return;
        
        const selects = container.querySelectorAll('select');
        if (!selects.length) return;
        
        selects.forEach(select => {
            jQuery(select).select2({
                theme: 'bootstrap-5',
                width: '100%',
                dropdownParent: container.closest('.modal') || document.body
            });
        });
    }
    
    /**
     * Handle quantity control button clicks
     * @param {HTMLElement} button - The clicked quantity control button
     */
    handleQuantityControl(button) {
        const input = this.getQuantityInput(button);
        if (!input) return;
        
        const action = button.getAttribute('data-action');
        const newValue = this.calculateNewQuantity(input.value, action);
        
        input.value = newValue;
        this.updateInvoiceTotals();
    }
    
    /**
     * Get the quantity input element from a control button
     * @param {HTMLElement} button - The quantity control button
     * @returns {HTMLInputElement|null} The quantity input element or null if not found
     */
    getQuantityInput(button) {
        return button?.closest('.input-group')?.querySelector('input[type="number"]') || null;
    }
    
    /**
     * Calculate the new quantity based on the current value and action
     * @param {string|number} currentValue - The current input value
     * @param {string} action - The action to perform ('increase' or 'decrease')
     * @returns {number} The new quantity value
     */
    calculateNewQuantity(currentValue, action) {
        let value = parseFloat(currentValue) || 0;
        
        switch (action) {
            case 'increase':
                return value + 1;
            case 'decrease':
                return Math.max(1, value - 1); // Prevent going below 1
            default:
                return value;
        }
    }
    
    /**
     * Handle remove item button clicks
     * @param {HTMLElement} button - The clicked remove button
     */
    handleRemoveItem(button) {
        const formRow = button.closest('.formset-form');
        if (!formRow) return;
        
        const formRows = this.getVisibleFormRows();
        
        if (formRows.length > 1) {
            this.markFormRowForRemoval(formRow);
            this.updateFormIndexes();
            this.updateInvoiceTotals();
        } else {
            this.clearFormFields(formRow);
        }
    }
    
    /**
     * Get all visible form rows
     * @returns {NodeList} List of visible form row elements
     */
    getVisibleFormRows() {
        return this.formsetContainer?.querySelectorAll('.formset-form:not([style*="display: none"])') || [];
    }
    
    /**
     * Mark a form row for removal
     * @param {HTMLElement} formRow - The form row to mark for removal
     */
    markFormRowForRemoval(formRow) {
        const deleteInput = formRow.querySelector('input[type="checkbox"][name$="-DELETE"]');
        
        if (deleteInput) {
            deleteInput.checked = true;
            formRow.style.display = 'none'; // Hide instead of removing to keep in POST data
        } else {
            formRow.remove();
        }
    }
    
    /**
     * Clear all fields in a form row
     * @param {HTMLElement} formRow - The form row to clear
     */
    clearFormFields(formRow) {
        if (!formRow) return;
        
        this.resetTextFields(formRow);
        this.resetNumberFields(formRow);
        this.resetDeleteCheckbox(formRow);
        
        // Show the form if it was hidden
        formRow.style.display = '';
        
        this.updateInvoiceTotals();
    }
    
    /**
     * Reset all text input fields in a form row
     * @param {HTMLElement} formRow - The form row containing the fields
     */
    resetTextFields(formRow) {
        formRow.querySelectorAll('input[type="text"]').forEach(input => {
            if (input.name.includes('description')) {
                input.value = '';
            }
        });
    }
    
    /**
     * Reset all number input fields in a form row
     * @param {HTMLElement} formRow - The form row containing the fields
     */
    resetNumberFields(formRow) {
        formRow.querySelectorAll('input[type="number"]').forEach(input => {
            if (input.name.includes('quantity')) {
                input.value = '1';
            } else if (input.name.includes('unit_price') || input.name.includes('vat_rate')) {
                input.value = '0.00';
            }
        });
    }
    
    /**
     * Reset the delete checkbox in a form row
     * @param {HTMLElement} formRow - The form row containing the checkbox
     */
    resetDeleteCheckbox(formRow) {
        const deleteInput = formRow.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput) {
            deleteInput.checked = false;
        }
    }
    
    /**
     * Add a new item row to the form
     */
    addNewItemRow() {
        if (!this.emptyFormTemplate || !this.formsetContainer) return null;
        
        const formNum = this.formCount;
        const prefix = `items-${formNum}-`;
        
        // Create a new form element
        const newFormDiv = document.createElement('div');
        newFormDiv.className = 'formset-form row mb-3 border-bottom pb-3 align-items-end';
        
        // Get the empty form HTML and replace placeholders
        let newFormHTML = this.emptyFormTemplate.innerHTML
            .replace(/__prefix__/g, formNum)
            .replace(/items-\d+-/g, prefix)
            .replace(/id="id_items-\d+-/g, `id="id_${prefix}`)
            .replace(/name="items-\d+-/g, `name="${prefix}`)
            .replace(/for="id_items-\d+-/g, `for="id_${prefix}`);
        
        // Add required attributes to the new form's inputs
        newFormHTML = newFormHTML
            .replace(`name="${prefix}description"`, `name="${prefix}description" required`)
            .replace(`name="${prefix}quantity"`, `name="${prefix}quantity" required`)
            .replace(`name="${prefix}unit_price"`, `name="${prefix}unit_price" required`)
            .replace(`name="${prefix}vat_rate"`, `name="${prefix}vat_rate" required`);

        newFormDiv.innerHTML = newFormHTML;
        newFormDiv.setAttribute('data-form-prefix', prefix);
        
        // Insert the new form
        const addButtonContainer = document.getElementById('add-item-container');
        if (addButtonContainer) {
            this.formsetContainer.insertBefore(newFormDiv, addButtonContainer);
        } else {
            this.formsetContainer.appendChild(newFormDiv);
        }
        
        // Update the total number of forms
        this.formCount++;
        if (this.totalForms) {
            this.totalForms.value = this.formCount;
        }
        
        // Initialize the new form
        this.initializeFormRow(newFormDiv);
        
        // Focus on the description field
        const descriptionInput = newFormDiv.querySelector('input[id$="-description"]');
        if (descriptionInput) {
            descriptionInput.focus();
        }
        
        // Update form indexes and totals
        this.updateFormIndexes();
        this.updateInvoiceTotals();
        
        // Scroll to the new form
        newFormDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        return newFormDiv;
    }
    
    /**
     * Update form indexes for the management form
     */
    updateFormIndexes() {
        const forms = this.formsetContainer?.querySelectorAll('.formset-form');
        if (!forms) return;
        
        if (this.totalForms) {
            this.totalForms.value = forms.length;
        }
        
        let visibleCount = 0;
        
        forms.forEach((form, index) => {
            // Skip forms that are marked for deletion
            const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteInput && deleteInput.checked) {
                return;
            }
            
            const prefix = `items-${visibleCount}-`;
            form.setAttribute('data-form-prefix', prefix);
            
            // Update all inputs in the form
            form.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.name && input.name.includes('__prefix__')) {
                    input.name = input.name.replace(/__prefix__/g, visibleCount);
                }
                if (input.id && input.id.includes('__prefix__')) {
                    input.id = input.id.replace(/__prefix__/g, visibleCount);
                }
                if (input.id && input.id.includes('items-__prefix__')) {
                    input.id = input.id.replace('items-__prefix__', `items-${visibleCount}-`);
                }
            });
            
            // Update labels
            form.querySelectorAll('label').forEach(label => {
                if (label.htmlFor) {
                    if (label.htmlFor.includes('__prefix__')) {
                        label.htmlFor = label.htmlFor.replace(/__prefix__/g, visibleCount);
                    }
                    if (label.htmlFor.includes('items-__prefix__')) {
                        label.htmlFor = label.htmlFor.replace('items-__prefix__', `items-${visibleCount}-`);
                    }
                }
            });
            
            visibleCount++;
        });
        
        // Update the total number of forms
        if (this.totalForms) {
            this.totalForms.value = visibleCount;
        }
    }
    
    /**
     * Parse a number from a string, handling both . and , as decimal separators
     */
    parseNumber(value) {
        if (!value) return 0;
        // Replace comma with dot and parse as float
        return parseFloat(value.toString().replace(',', '.')) || 0;
    }
    
    /**
     * Format a number to 2 decimal places with . as decimal separator
     */
    formatNumber(value, withCurrency = true) {
        const formattedValue = parseFloat(value || 0).toFixed(2);
        if (withCurrency) {
            const currencySelect = document.querySelector('select[name="currency"]');
            const currency = currencySelect ? currencySelect.value : 'EUR';
            const currencySymbol = this.getCurrencySymbol(currency);
            return `${formattedValue} ${currencySymbol}`;
        }
        return formattedValue;
    }
    
    /**
     * Get currency symbol for a given currency code
     */
    getCurrencySymbol(currencyCode) {
        const symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CHF': 'CHF',
            'CAD': 'C$', 'AUD': 'A$', 'CNY': '¥', 'SEK': 'kr', 'NZD': 'NZ$',
            'MXN': 'MX$', 'SGD': 'S$', 'HKD': 'HK$', 'NOK': 'kr', 'KRW': '₩',
            'TRY': '₺', 'RUB': '₽', 'INR': '₹', 'BRL': 'R$', 'ZAR': 'R',
            'HUF': 'Ft', 'PLN': 'zł', 'CZK': 'Kč', 'DKK': 'kr', 'RON': 'lei',
            'HRK': 'kn', 'BGN': 'лв.', 'ISK': 'kr', 'UAH': '₴', 'ILS': '₪',
            'AED': 'د.إ', 'SAR': '﷼', 'QAR': 'ر.ق', 'KWD': 'د.ك', 'EGP': 'ج.م',
            'THB': '฿', 'IDR': 'Rp', 'MYR': 'RM', 'PHP': '₱', 'VND': '₫',
            'PKR': '₨', 'BDT': '৳', 'LKR': 'Rs', 'NGN': '₦', 'KES': 'KSh',
            'GHS': 'GH₵', 'MAD': 'د.م.', 'TND': 'د.ت', 'DZD': 'د.ج', 'MUR': '₨'
        };
        
        return symbols[currencyCode] || currencyCode;
    }
    
    /**
     * Calculate totals for a single row
     */
    calculateRowTotal(row) {
        const quantity = this.parseNumber(row.querySelector('input[id$="-quantity"]')?.value);
        const unitPrice = this.parseNumber(row.querySelector('input[id$="-unit_price"]')?.value);
        const vatRate = this.parseNumber(row.querySelector('input[id$="-vat_rate"]')?.value) / 100;
        
        const subtotal = quantity * unitPrice;
        const tax = subtotal * vatRate;
        const total = subtotal + tax;
        
        // Update the displayed totals
        const totalCell = row.querySelector('.row-total');
        if (totalCell) {
            totalCell.textContent = this.formatNumber(total);
        }
        
        return { subtotal, tax, total };
    }
    
    /**
     * Calculate and update all invoice totals
     */
    updateInvoiceTotals() {
        console.log('updateInvoiceTotals called');
        let subtotal = 0;
        let totalTax = 0;
        
        // Get all item rows
        const rows = this.formsetContainer?.querySelectorAll('.formset-form');
        console.log('Found', rows?.length, 'rows');
        if (!rows) return;
        
        rows.forEach((row, index) => {
            // Skip rows that are marked for deletion
            const deleteCheckbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) {
                console.log('Skipping deleted row', index);
                return;
            }
            
            // Get quantity, unit price, and VAT rate
            const quantityInput = row.querySelector('input[id$="-quantity"]');
            const unitPriceInput = row.querySelector('input[id$="-unit_price"]');
            const vatRateInput = row.querySelector('input[id$="-vat_rate"]');
            
            const quantity = this.parseNumber(quantityInput?.value);
            const unitPrice = this.parseNumber(unitPriceInput?.value);
            const vatRate = this.parseNumber(vatRateInput?.value);
            
            console.log('Row', index, 'values:', { quantity, unitPrice, vatRate });
            
            // Calculate row total
            const rowTotal = quantity * unitPrice;
            const rowTax = rowTotal * (vatRate / 100);
            
            console.log('Row', index, 'totals:', { rowTotal, rowTax });
            
            // Update row total display if it exists
            const rowTotalElement = row.querySelector('.row-total');
            if (rowTotalElement) {
                const formattedTotal = this.formatNumber(rowTotal);
                console.log('Updating row total display:', formattedTotal);
                rowTotalElement.textContent = formattedTotal;
            }
            
            // Update row tax display if it exists
            const rowTaxElement = row.querySelector('.row-tax');
            if (rowTaxElement) {
                const formattedTax = this.formatNumber(rowTax);
                console.log('Updating row tax display:', formattedTax);
                rowTaxElement.textContent = formattedTax;
            }
            
            // Add to subtotal and total tax
            subtotal += rowTotal;
            totalTax += rowTax;
        });
        
        // Calculate grand total
        const total = subtotal + totalTax;
        
        console.log('Invoice totals:', { subtotal, totalTax, total });
        
        // Update the summary
        const subtotalElement = document.getElementById('subtotal-display');
        const taxElement = document.getElementById('tax-amount');
        const totalElement = document.getElementById('total-amount');
        
        console.log('Summary elements:', { subtotalElement, taxElement, totalElement });
        
        // Get currency from the form or default to EUR
        const currencySelect = document.querySelector('select[name="currency"]');
        const currency = currencySelect ? currencySelect.value : 'EUR';
        const currencySymbol = this.getCurrencySymbol(currency);
        
        const formattedSubtotal = this.formatNumber(subtotal, false);
        const formattedTax = this.formatNumber(totalTax, false);
        const formattedTotal = this.formatNumber(total, false);
        
        console.log('Formatted values:', { formattedSubtotal, formattedTax, formattedTotal });
        
        if (subtotalElement) {
            subtotalElement.textContent = `${formattedSubtotal} ${currencySymbol}`;
            console.log('Updated subtotal element:', subtotalElement.textContent);
        } else {
            console.error('Could not find subtotal element');
        }
        
        if (taxElement) {
            taxElement.textContent = `${formattedTax} ${currencySymbol}`;
            console.log('Updated tax element:', taxElement.textContent);
        }
        
        if (totalElement) {
            totalElement.textContent = `${formattedTotal} ${currencySymbol}`;
            console.log('Updated total element:', totalElement.textContent);
        }
        
        // Update hidden inputs
        const subtotalInput = document.querySelector('input[name="subtotal"]');
        const taxInput = document.querySelector('input[name="total_tax"]');
        const totalInput = document.querySelector('input[name="total_amount"]');
        
        console.log('Hidden inputs:', { subtotalInput, taxInput, totalInput });
        
        if (subtotalInput) {
            subtotalInput.value = formattedSubtotal;
            console.log('Updated hidden subtotal input:', subtotalInput.value);
        }
        
        if (taxInput) {
            taxInput.value = formattedTax;
            console.log('Updated hidden tax input:', taxInput.value);
        }
        
        if (totalInput) {
            totalInput.value = formattedTotal;
            console.log('Updated hidden total input:', totalInput.value);
        }
        
        // Return the calculated values in case they're needed elsewhere
        return { subtotal, totalTax, total };
    }
    
    /**
     * Handle form submission
     */
    handleFormSubmit(e) {
        console.log('Form submission started');
        
        // Validate the form before submission
        if (!this.validateForm()) {
            console.log('Form validation failed');
            e.preventDefault();
            return false;
        }
        
        console.log('Form is valid, proceeding with submission');
        
        // Disable the submit button to prevent double submission
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            console.log('Disabling submit button');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
        } else {
            console.error('Submit button not found!');
        }
        
        // Add a small delay to ensure the button state is updated
        setTimeout(() => {
            console.log('Form should be submitting now');
        }, 100);
        
        return true;
    }
    
    /**
     * Validate the form
     */
    validateForm() {
        let isValid = true;
        // Only validate visible forms
        const visibleForms = this.formsetContainer.querySelectorAll('.formset-form:not([style*="display: none"])');
        
        // Reset all error states
        this.form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        // Validate each visible form
        visibleForms.forEach(form => {
            const requiredInputs = form.querySelectorAll('input[required]');
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    
                    // Add error message if it doesn't exist
                    if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = 'This field is required.';
                        input.parentNode.insertBefore(errorDiv, input.nextSibling);
                    }
                }
            });
        });
        
        // Validate main form fields
        const mainFormInputs = this.form.querySelectorAll('input[required]:not([data-form-prefix])');
        mainFormInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('is-invalid');
                
                if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'This field is required.';
                    input.parentNode.insertBefore(errorDiv, input.nextSibling);
                }
            }
        });
        
        // If form is invalid, scroll to the first error
        if (!isValid) {
            const firstInvalid = this.form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        
        return isValid;
    }
}

// Debug: Log when the script is loaded
console.log('invoice-form.js loaded');

// Initialize the invoice form when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');
    
    // Check if the form and button exist
    const form = document.getElementById('invoice-form');
    const addButton = document.getElementById('add-item');
    const formsetContainer = document.getElementById('formset-container');
    
    console.log('Form element:', form);
    console.log('Add button:', addButton);
    console.log('Formset container:', formsetContainer);
    
    if (form && addButton && formsetContainer) {
        console.log('All required elements found, initializing InvoiceForm');
        window.invoiceForm = new InvoiceForm();
        
        // Add a direct event listener for debugging
        addButton.addEventListener('click', (e) => {
            console.log('Direct click handler fired');
            e.preventDefault();
            e.stopPropagation();
            if (window.invoiceForm) {
                console.log('Calling addNewItemRow from direct handler');
                window.invoiceForm.addNewItemRow();
            } else {
                console.error('invoiceForm not initialized');
            }
        });
    } else {
        console.error('Required elements not found:', { 
            form: !!form, 
            addButton: !!addButton, 
            formsetContainer: !!formsetContainer 
        });
    }
});
