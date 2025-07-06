/**
 * Invoice Form Management
 * 
 * Combined and optimized version of invoice-form.js and invoice-form-new.js
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
        console.log('Initializing InvoiceForm');
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
        console.log('Caching DOM elements');
        this.form = document.getElementById('invoice-form');
        this.formsetContainer = document.getElementById('formset-container');
        this.totalForms = document.getElementById('id_items-TOTAL_FORMS');
        this.emptyFormTemplate = document.getElementById('empty-form');
        
        console.log('Cached elements:', {
            form: this.form,
            formsetContainer: this.formsetContainer,
            totalForms: this.totalForms,
            emptyFormTemplate: this.emptyFormTemplate
        });
    }
    
    /**
     * Initialize the invoice form
     * Sets up event listeners and initial state
     */
    initialize() {
        console.log('Initializing form');
        if (!this.form) {
            console.error('Invoice form element not found');
            return;
        }
        
        // Ensure the form has the correct attributes
        this.form.setAttribute('novalidate', 'novalidate');
        this.form.setAttribute('data-validate', 'true');
        
        this.setupEventDelegation();
        this.initializeExistingForms();
        
        // Add initial empty form if needed
        if (this.formCount === 0) {
            console.log('No forms found, adding initial form');
            this.addNewItemRow();
        } else {
            console.log(`Found ${this.formCount} existing forms`);
            // Ensure all existing forms are properly initialized
            const rows = this.formsetContainer?.querySelectorAll('.formset-form') || [];
            rows.forEach((row, index) => {
                this.initializeFormRow(row);
                // Ensure all required fields are properly set
                const requiredFields = row.querySelectorAll('[required]');
                requiredFields.forEach(field => {
                    if (!field.value) {
                        field.required = true;
                    }
                });
            });
        }
        
        // Ensure number inputs don't show spinners
        this.removeNumberInputSpinners();
        this.updateInvoiceTotals();
    }
    
    /**
     * Remove number input spinners from all number inputs
     */
    removeNumberInputSpinners() {
        // This is a fallback in case CSS doesn't work
        const numberInputs = document.querySelectorAll('input[type="number"]');
        numberInputs.forEach(input => {
            // Remove any existing spinners
            const spinnerButtons = input.parentElement.querySelectorAll('button.quantity-control');
            spinnerButtons.forEach(btn => btn.remove());
            
            // Ensure the input doesn't show spinners
            input.style.webkitAppearance = 'textfield';
            input.style.mozAppearance = 'textfield';
            input.style.appearance = 'textfield';
        });
    }
    
    /**
     * Set up event delegation for dynamic elements
     */
    setupEventDelegation() {
        console.log('Setting up event delegation');
        const container = this.formsetContainer || document;
        
        // Handle all click events - use document to catch events from dynamically added elements
        document.addEventListener('click', (e) => this.handleClickEvents(e));
        
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
        console.log('Click detected on:', target);
        
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
        
        // Handle add item - multiple ways to detect the button
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
        console.log('Initializing existing forms');
        const forms = this.formsetContainer?.querySelectorAll('.formset-form');
        if (!forms) return;
        
        console.log(`Found ${forms.length} existing forms`);
        forms.forEach(form => this.initializeFormRow(form));
    }
    
    /**
     * Initialize a single form row with any necessary plugins
     * @param {HTMLElement} formRow - The form row element to initialize
     */
    initializeFormRow(formRow) {
        if (!formRow) return;
        console.log('Initializing form row:', formRow);
        
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
        console.log('Handling quantity control');
        const input = this.getQuantityInput(button);
        if (!input) return;
        
        const action = button.getAttribute('data-action');
        const newValue = this.calculateNewQuantity(input.value, action);
        
        input.value = newValue;
        // Trigger change event to update totals
        input.dispatchEvent(new Event('change'));
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
     * Add a new item row to the form
     */
    addNewItemRow() {
        console.log('Adding new item row');
        
        if (!this.emptyFormTemplate || !this.formsetContainer) {
            console.error('Missing required elements', {
                emptyFormTemplate: this.emptyFormTemplate,
                formsetContainer: this.formsetContainer
            });
            return null;
        }
        
        // Get the current form count from the management form
        const managementForm = this.form?.querySelector('input[name$="-TOTAL_FORMS"]');
        if (managementForm) {
            this.formCount = parseInt(managementForm.value, 10);
        }
        
        const formNum = this.formCount;
        const prefix = `items-${formNum}-`;
        
        console.log(`Creating new form with prefix: ${prefix}`);
        
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
            .replace(`name="${prefix}unit_price"`, `name="${prefix}unit_price" required`);

        newFormDiv.innerHTML = newFormHTML;
        newFormDiv.setAttribute('data-form-prefix', prefix);
        
        // Insert the new form
        const addButtonContainer = document.getElementById('add-item-container');
        if (addButtonContainer) {
            this.formsetContainer.insertBefore(newFormDiv, addButtonContainer);
        } else {
            this.formsetContainer.appendChild(newFormDiv);
        }
        
        // Update the management form count
        const newFormCount = this.formCount + 1;
        if (managementForm) {
            managementForm.value = newFormCount;
            console.log(`Updated TOTAL_FORMS to: ${newFormCount}`);
        }
        
        // Update our internal form count
        this.formCount = newFormCount;
        
        // Initialize the new form
        this.initializeFormRow(newFormDiv);
        
        // Focus on the description field of the new form
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
     * Handle removal of an item row
     * @param {HTMLElement} button - The remove button that was clicked
     */
    handleRemoveItem(button) {
        console.log('Handling remove item');
        const formRow = button.closest('.formset-form');
        if (!formRow) return;
        
        const formRows = this.getVisibleFormRows();
        
        if (formRows.length > 1) {
            // Mark the form for deletion
            const deleteCheckbox = formRow.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                formRow.style.display = 'none';
                
                // Update the management form count
                const managementForm = this.form?.querySelector('input[name$="-TOTAL_FORMS"]');
                if (managementForm) {
                    const currentCount = parseInt(managementForm.value, 10);
                    if (currentCount > 1) {
                        managementForm.value = currentCount - 1;
                        console.log(`Updated TOTAL_FORMS to: ${currentCount - 1}`);
                    }
                }
                
                this.updateFormIndexes();
                this.updateInvoiceTotals();
            } else {
                // If no delete checkbox, just remove the row
                formRow.remove();
            }
        } else {
            // If it's the last form, just clear the values
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
        
        // Set default VAT rate to 20%
        const vatInput = formRow.querySelector('input[name$="-vat_rate"]');
        if (vatInput) {
            vatInput.value = '20.00';
        }
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
     * Update the indexes of all forms to ensure they're sequential
     */
    updateFormIndexes() {
        console.log('Updating form indexes');
        const forms = this.formsetContainer?.querySelectorAll('.formset-form:not([style*="display: none"])');
        if (!forms) return;
        
        let visibleIndex = 0;
        const managementForm = this.form?.querySelector('input[name$="-TOTAL_FORMS"]');
        
        // First pass: Update all visible forms
        forms.forEach((form, index) => {
            // Skip forms that are marked for deletion
            const deleteInput = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteInput && deleteInput.checked) {
                return;
            }
            
            const oldPrefix = form.getAttribute('data-form-prefix') || `items-${index}-`;
            const newPrefix = `items-${visibleIndex}-`;
            
            if (oldPrefix !== newPrefix) {
                // Update data attribute
                form.setAttribute('data-form-prefix', newPrefix);
                
                // Update all inputs, labels, and other elements with the old prefix
                form.querySelectorAll('*').forEach(element => {
                    ['id', 'name', 'for', 'data-form-prefix'].forEach(attr => {
                        if (element.hasAttribute(attr)) {
                            const value = element.getAttribute(attr);
                            if (value && value.includes(oldPrefix)) {
                                const newValue = value.replace(oldPrefix, newPrefix);
                                // Ensure we don't have double dashes
                                element.setAttribute(attr, newValue.replace('--', '-'));
                            }
                        }
                    });
                });
                
                // Update the form's ID if it exists
                const formIdInput = form.querySelector('input[id$="-id"]');
                if (formIdInput) {
                    formIdInput.name = `${newPrefix}id`;
                    formIdInput.id = `id_${newPrefix}id`;
                }
                
                // Update the DELETE checkbox if it exists
                const deleteCheckbox = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
                if (deleteCheckbox) {
                    deleteCheckbox.name = `${newPrefix}DELETE`;
                    deleteCheckbox.id = `id_${newPrefix}DELETE`;
                }
                
                // Update all form fields
                const fields = ['description', 'quantity', 'unit_price', 'vat_rate'];
                fields.forEach(field => {
                    const input = form.querySelector(`[name$="-${field}"]`);
                    if (input) {
                        input.name = `${newPrefix}${field}`;
                        input.id = `id_${newPrefix}${field}`;
                    }
                });
            }
            
            // Update the form's ID if it exists
            const formIdInput = form.querySelector('input[id$="-id"]');
            if (formIdInput) {
                formIdInput.name = `${newPrefix}id`;
                formIdInput.id = `id_${newPrefix}id`;
            }
            
            // Update the DELETE checkbox if it exists
            const deleteCheckbox = form.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.name = `${newPrefix}DELETE`;
                deleteCheckbox.id = `id_${newPrefix}DELETE`;
            }
            
            visibleIndex++;
        });
        
        // Update the management form with the new total number of forms
        if (managementForm) {
            managementForm.value = visibleIndex;
            console.log(`Updated TOTAL_FORMS to: ${visibleIndex}`);
        }
        
        // Update our internal form count
        this.formCount = visibleIndex;
    }
    
    /**
     * Update the invoice totals based on the current form values
     */
    updateInvoiceTotals() {
        console.log('Updating invoice totals');
        let subtotal = 0;
        const rows = this.formsetContainer?.querySelectorAll('.formset-form') || [];
        
        // Calculate subtotal from all visible rows
        rows.forEach(row => {
            // Skip hidden rows (marked for deletion)
            if (row.style.display === 'none') return;
            
            const quantityInput = row.querySelector('input[id$="-quantity"]');
            const priceInput = row.querySelector('input[id$="-unit_price"]');
            const totalInput = row.querySelector('input[id$="-total"]');
            
            if (quantityInput && priceInput) {
                const quantity = parseFloat(quantityInput.value) || 0;
                const price = parseFloat(priceInput.value) || 0;
                const rowTotal = quantity * price;
                
                // Update the row total if the input exists
                if (totalInput) {
                    totalInput.value = rowTotal.toFixed(2);
                }
                
                subtotal += rowTotal;
            }
        });
        
        // Update the subtotal in the UI
        const subtotalDisplay = document.getElementById('subtotal-display');
        const subtotalInput = document.querySelector('input[name="subtotal"]');
        
        if (subtotalDisplay) {
            subtotalDisplay.textContent = `${subtotal.toFixed(2)} €`;
        }
        
        if (subtotalInput) {
            subtotalInput.value = subtotal.toFixed(2);
        }
        
        // Get the VAT rate from the first visible row or use 20% as fallback
        let vatRate = 0.20; // Default to 20%
        const firstRow = this.formsetContainer?.querySelector('.formset-form:not([style*="display: none"])');
        if (firstRow) {
            const vatInput = firstRow.querySelector('input[id$="-vat_rate"]');
            if (vatInput && vatInput.value) {
                vatRate = parseFloat(vatInput.value) / 100;
            }
        }
        
        // Calculate tax and total
        const tax = subtotal * vatRate;
        const total = subtotal + tax;
        
        // Update tax and total in the UI
        const taxAmount = document.getElementById('tax-amount');
        const totalAmount = document.getElementById('total-amount');
        const taxInput = document.querySelector('input[name="total_tax"]');
        const totalInput = document.querySelector('input[name="total_amount"]');
        
        if (taxAmount) {
            taxAmount.textContent = `${tax.toFixed(2)} €`;
        }
        
        if (totalAmount) {
            totalAmount.textContent = `${total.toFixed(2)} €`;
        }
        
        if (taxInput) taxInput.value = tax.toFixed(2);
        if (totalInput) totalInput.value = total.toFixed(2);
    }
    
    /**
     * Handle form submission
     * @param {Event} event - The form submit event
     */
    handleFormSubmit(event) {
        console.log('Form submission started');
        
        // Update form indexes one last time before submission
        this.updateFormIndexes();
        
        // Ensure all required fields have values
        let isValid = true;
        const requiredInputs = this.form?.querySelectorAll('input[required]');
        
        if (requiredInputs) {
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
        }
        
        // Validate the form before submission
        if (!isValid || !this.validateForm()) {
            event.preventDefault();
            console.log('Form validation failed');
            
            // Show error message
            const errorDiv = document.getElementById('calculation-error');
            if (errorDiv) {
                errorDiv.textContent = 'Please fill in all required fields.';
                errorDiv.classList.remove('d-none');
                
                // Scroll to the first error
                const firstError = this.form?.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            return false;
        }
        
        // Ensure all form fields are properly formatted before submission
        const rows = this.formsetContainer?.querySelectorAll('.formset-form') || [];
        let formIndex = 0;
        
        rows.forEach((row, index) => {
            if (row.style.display === 'none' || row.classList.contains('d-none')) {
                return; // Skip hidden rows
            }
            
            // Update form field names to use the correct index
            const fields = row.querySelectorAll('input, select, textarea');
            fields.forEach(field => {
                if (field.name) {
                    field.name = field.name.replace(/items-\d+-/g, `items-${formIndex}-`);
                    field.id = field.id.replace(/items-\d+-/g, `items-${formIndex}-`);
                }
            });
            
            formIndex++;
        });
        
        // Update the management form with the correct count
        const managementForm = this.form?.querySelector('input[name$="-TOTAL_FORMS"]');
        if (managementForm) {
            managementForm.value = formIndex;
            console.log('Updated TOTAL_FORMS to:', formIndex);
        }
        
        // Log the form data for debugging
        console.log('Form data being submitted:', new FormData(this.form));
        
        return true;
    }
    
    /**
     * Validate the form before submission
     * @returns {boolean} True if the form is valid, false otherwise
     */
    /**
     * Normalize a number string to use dot as decimal separator
     * @param {string} value - The input value to normalize
     * @returns {string} The normalized number string
     */
    normalizeNumber(value) {
        if (!value) return '0';
        // Replace comma with dot and remove any non-numeric characters except dot and minus
        return String(value).replace(',', '.').replace(/[^0-9.-]/g, '');
    }

    /**
     * Parse a number from an input field, handling different formats
     * @param {string} value - The input value to parse
     * @returns {number} The parsed number
     */
    parseNumber(value) {
        return parseFloat(this.normalizeNumber(value)) || 0;
    }

    validateForm() {
        console.log('=== Validating form ===');
        let isValid = true;
        let hasAtLeastOneRow = false;
        
        // Check each form row
        const rows = this.formsetContainer?.querySelectorAll('.formset-form') || [];
        console.log(`Found ${rows.length} form rows`);
        
        // First pass: Check if we have at least one valid row
        for (const [index, row] of Array.from(rows).entries()) {
            // Skip hidden rows (marked for deletion)
            if (row.style.display === 'none' || row.classList.contains('d-none')) {
                console.log(`Row ${index}: Hidden or marked for deletion, skipping`);
                continue;
            }
            
            // Ensure the row is visible and has the correct index
            row.style.display = '';
            row.classList.remove('d-none');
            
            const descInput = row.querySelector('input[id$="-description"]');
            const qtyInput = row.querySelector('input[id$="-quantity"]');
            const priceInput = row.querySelector('input[id$="-unit_price"]');
            
            // Debug: Log all form fields in the row
            console.log(`Row ${index} inputs:`, {
                description: descInput,
                quantity: qtyInput,
                price: priceInput
            });
            
            const description = descInput?.value ? descInput.value.trim() : '';
            const quantity = this.parseNumber(qtyInput?.value);
            const price = this.parseNumber(priceInput?.value);
            
            // Update the input values to ensure consistent format
            if (qtyInput) qtyInput.value = this.normalizeNumber(qtyInput?.value);
            if (priceInput) priceInput.value = this.normalizeNumber(priceInput?.value);
            
            console.log(`Row ${index} values:`, {
                description: `"${description}"`,
                quantity: quantity,
                price: price
            });
            
            // Check if this row has valid data - be more permissive
            const hasDescription = description.length > 0;
            const hasValidQuantity = !isNaN(quantity) && quantity > 0;  // Require quantity > 0
            const hasValidPrice = !isNaN(price) && price >= 0;  // Allow 0 price
            
            console.log(`Row ${index} validation:`, {
                hasDescription,
                hasValidQuantity,
                hasValidPrice,
                'isValidRow': hasDescription && hasValidQuantity && hasValidPrice
            });
            
            // Consider a row valid if it has a description, quantity > 0, and valid price (can be 0)
            if (hasDescription && hasValidQuantity && hasValidPrice) {
                console.log(`Row ${index} is valid`);
                hasAtLeastOneRow = true;
                // Don't break, continue checking other rows for debugging
            } else if (description || quantity > 0 || price > 0) {
                // If any field has a value but the row isn't valid, log it
                console.log(`Row ${index} has partial data but is not valid`);
            } else {
                console.log(`Row ${index} is empty`);
            }
        }
        
        console.log('Validation result:', { 
            hasAtLeastOneRow,
            'formsetContainer': this.formsetContainer,
            'formsetForms': this.formsetContainer?.querySelectorAll('.formset-form')
        });
        
        // If no valid rows found, show error and return false
        if (!hasAtLeastOneRow) {
            const errorMsg = 'Please add at least one invoice item with a description.';
            console.error(errorMsg, { rows: Array.from(rows).map(r => ({
                display: r.style.display,
                classList: Array.from(r.classList),
                inputs: Array.from(r.querySelectorAll('input')).map(i => ({
                    id: i.id,
                    value: i.value,
                    type: i.type
                }))
            }))});
            alert(errorMsg);
            return false;
        }
        
        // Second pass: Validate individual fields for each row
        rows.forEach((row, index) => {
            // Skip hidden rows (marked for deletion)
            if (row.style.display === 'none') return;
            
            const descInput = row.querySelector('input[id$="-description"]');
            const qtyInput = row.querySelector('input[id$="-quantity"]');
            const priceInput = row.querySelector('input[id$="-unit_price"]');
            
            const description = descInput?.value ? descInput.value.trim() : '';
            const quantity = this.parseNumber(qtyInput?.value);
            const price = this.parseNumber(priceInput?.value);
            
            // Update the input values to ensure consistent format
            if (qtyInput) qtyInput.value = this.normalizeNumber(qtyInput?.value);
            if (priceInput) priceInput.value = this.normalizeNumber(priceInput?.value);
            
            // Only validate rows that have some data
            if (!description && quantity === 0 && price === 0) return;
            if (index > 0 && !description && quantity === 0 && price === 0) {
                return; // Skip validation for completely empty rows after the first one
            }
            
            // If we get here, we have at least one row with data
            hasAtLeastOneRow = true;
            
            // Validate required fields
            if (!description) {
                console.error(`Row ${index + 1}: Description is required`);
                isValid = false;
            }
            
            if (isNaN(quantity) || quantity <= 0) {
                console.error(`Row ${index + 1}: Quantity must be greater than 0`);
                isValid = false;
            }
            
            if (isNaN(price) || price < 0) {
                console.error(`Row ${index + 1}: Price must be zero or greater`);
                isValid = false;
            }
        });
        
        return isValid;
    }
}

// Initialize the invoice form when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing InvoiceForm');
    
    // Check if the invoice form exists on the page
    const form = document.getElementById('invoice-form');
    const formsetContainer = document.getElementById('formset-container');
    
    if (form && formsetContainer) {
        console.log('All required elements found, initializing InvoiceForm');
        window.invoiceForm = new InvoiceForm();
        
        // Add form submission handler to ensure consistent number formatting
        form.addEventListener('submit', function(e) {
            // Normalize all number inputs before submission
            const numberInputs = form.querySelectorAll('input[type="number"], input[data-type="number"]');
            numberInputs.forEach(input => {
                if (input.value) {
                    // Normalize the value to use dot as decimal separator
                    const normalizedValue = window.invoiceForm.normalizeNumber(input.value);
                    
                    // If the value changed, update the input
                    if (normalizedValue !== input.value) {
                        console.log(`Normalized ${input.id} from ${input.value} to ${normalizedValue}`);
                        input.value = normalizedValue;
                    }
                }
            });
            
            // Continue with form submission
            return true;
        });
    } else {
        console.warn('Invoice form elements not found on this page');
    }
});
