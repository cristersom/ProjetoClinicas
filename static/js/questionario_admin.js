(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
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

    // --- NOVO: Função para adicionar placeholder ---
    function addPlaceholder(row) {
        // Encontra o input de texto_pergunta dentro da linha (row) específica
        const questionInput = row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length > 0 && !questionInput.attr('placeholder')) {
             // Adiciona o placeholder se não existir
            questionInput.attr('placeholder', 'Pergunta');
        }
    }

    $(document).ready(function() {

        // Renomeia os botões para ficarem mais limpos
        setInterval(function() {
            $('.djn-add-item a').each(function() {
                if ($(this).text().includes('Opcao Resposta')) {
                    $(this).text('Adicionar Opção de Resposta');
                }
                if ($(this).text().includes('Pergunta')) {
                    $(this).text('Adicionar Pergunta');
                }
            });
        }, 500);

        // Ouve a mudança no dropdown "Tipo de Resposta"
        $('#perguntas-group').on('change', '.field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de uma nova pergunta
        $(document).on('djnesting:added', function(event, inline) {
            if (inline.prefix.includes('pergunta')) {
                inline.row.find('.inline-group').hide();
                // --- NOVO: Adiciona placeholder na nova pergunta ---
                addPlaceholder(inline.row);
            }
        });

        // Roda as funções para as perguntas já existentes ao carregar
        setTimeout(function() {
            $('#perguntas-group .inline-related').each(function() {
                toggleOptions($(this));
                // --- NOVO: Adiciona placeholder nas perguntas existentes ---
                addPlaceholder($(this));
            });
        }, 150);
    });
})(django.jQuery);