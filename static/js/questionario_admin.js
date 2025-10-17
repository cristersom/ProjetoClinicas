(function($) {
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

    $(document).ready(function() {
        // Renomeia o link "Adicionar"
        setInterval(function() {
            $('.djn-add-item a').each(function() {
                if ($(this).text().includes('Opcao Resposta')) {
                    $(this).text('Adicionar Opção de Resposta');
                }
            });
        }, 500);

        // Ouve a mudança no tipo de resposta
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de uma nova pergunta
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                inline.row.find('.inline-group').hide();
            }
        });

        // Roda a função para as perguntas já existentes ao carregar
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150);
    });
})(django.jQuery);