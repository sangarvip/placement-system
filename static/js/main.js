// Campus Placement Management System - Main JS
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    function passwordChecks(value) {
        var v = String(value || '');
        return {
            len: v.length >= 8,
            upper: /[A-Z]/.test(v),
            lower: /[a-z]/.test(v),
            digit: /[0-9]/.test(v),
            special: /[^A-Za-z0-9]/.test(v)
        };
    }

    function updatePasswordUI(root, checks) {
        if (!root) return;
        root.querySelectorAll('[data-rule]').forEach(function(el) {
            var key = el.getAttribute('data-rule');
            var ok = Boolean(checks[key]);
            el.classList.remove('is-valid', 'is-invalid');
            el.classList.add(ok ? 'is-valid' : 'is-invalid');
            var icon = el.querySelector('.rule-icon');
            if (icon) {
                icon.innerHTML = ok ? '<i class="bi bi-check"></i>' : '<i class="bi bi-x"></i>';
            }
        });
    }

    function attachPasswordValidation(form) {
        var input = form.querySelector('input[type="password"][name="password"]');
        if (!input) return;
        var rules = form.querySelector('#passwordRules');
        var validate = function() {
            var checks = passwordChecks(input.value);
            updatePasswordUI(rules, checks);
            var ok = checks.len && checks.upper && checks.lower && checks.digit && checks.special;
            input.setCustomValidity(ok ? '' : 'Password does not meet requirements.');
            return ok;
        };
        input.addEventListener('input', validate);
        input.addEventListener('blur', validate);
        form.addEventListener('submit', function(e) {
            if (!validate()) {
                e.preventDefault();
                e.stopPropagation();
                input.focus();
            }
        });
        validate();
    }

    document.querySelectorAll('form[data-validate-password="true"]').forEach(function(form) {
        attachPasswordValidation(form);
    });
});
