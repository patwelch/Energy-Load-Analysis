document.addEventListener('DOMContentLoaded', function () {
    const sourceTypeSelect = document.getElementById('source_type');
    const sourceIdSelect = document.getElementById('source_id');
    const newSourceCheckbox = document.getElementById('new_source_checkbox');
    const existingSourceDiv = document.getElementById('existing_source_div');
    const newSourceDiv = document.getElementById('new_source_div');
    const newLoadSourceDiv = document.getElementById('new_load_source');
    const newGenerationSourceDiv = document.getElementById('new_generation_source');


    let meters = [];
    let generationSources = [];


    function toggleNewSourceForm() {
        if (newSourceCheckbox.checked) {
            existingSourceDiv.style.display = 'none';
            newSourceDiv.style.display = 'block';
            sourceIdSelect.disabled = true;
        } else {
            existingSourceDiv.style.display = 'block';
            newSourceDiv.style.display = 'none';
            sourceIdSelect.disabled = false;
        }
    }

    // Populate on page load
    populateSources();

    // Repopulate on change
    sourceTypeSelect.addEventListener('change', populateSources);
    newSourceCheckbox.addEventListener('change', toggleNewSourceForm);
});