(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const selectElement = row.find('.field-tipo_resposta select');
        const optionsBlock = row.find('.inline-group'); // O bloco das Opções de Resposta
        const selectedType = selectElement.val();

        // Tipos de pergunta que PRECISAM de opções
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        if (typesWithOptions.includes(selectedType)) {
            optionsBlock.slideDown(); // Mostra
        } else {
            optionsBlock.slideUp(); // Esconde
        }
    }

    $(document).ready(function() {

        // --- Renomeia os botões para ficarem mais limpos ---
        // Usamos setInterval para garantir que pegamos botões adicionados dinamicamente
        setInterval(function() {
            $('.djn-add-item a').each(function() {
                // Renomeia "Adicionar outro(a) Opcao Resposta"
                if ($(this).text().includes('Opcao Resposta')) {
                    $(this).text('Adicionar Opção de Resposta');
                }
                // Renomeia "Adicionar outro(a) Pergunta"
                if ($(this).text().includes('Pergunta')) {
                    $(this).text('Adicionar Pergunta');
                }
            });
        }, 500); // Roda a cada 0.5 segundos

        // Ouve a mudança no dropdown "Tipo de Resposta"
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de uma nova pergunta (para esconder o bloco de opções)
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                // Esconde o bloco de opções por padrão
                inline.row.find('.inline-group').hide();
            }
        });

        // Roda a função para todas as perguntas já existentes quando a página carrega
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
            });
        }, 150);
    });
})(django.jQuery);