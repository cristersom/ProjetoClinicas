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
        // Renomeia o link "Adicionar" para algo mais intuitivo
        setInterval(function() {
            $('.djn-add-item a').each(function() {
                if ($(this).text().includes('Opcao Resposta')) {
                    $(this).text('Adicionar Opção de Resposta');
                }
            });
        }, 500);

        // Delega o evento 'change' para funcionar com perguntas novas e existentes
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Garante que novas perguntas comecem com as opções escondidas
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                inline.row.find('.inline-group').hide();
            }
        });

        // Roda a função para todas as perguntas já existentes ao carregar a página
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150);
    });
})(django.jQuery);