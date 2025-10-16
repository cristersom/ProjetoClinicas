(function($) {
    $(document).ready(function() {
        function toggleOptions(row) {
            const selectElement = row.find('.field-tipo_resposta select');
            const optionsBlock = row.find('.inline-group');
            const selectedType = selectElement.val();
            const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

            if (typesWithOptions.includes(selectedType)) {
                optionsBlock.slideDown();
            } else {
                optionsBlock.slideUp();
            }
        }

        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                inline.row.find('.inline-group').hide();
            }
        });

        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150);
    });
})(django.jQuery);