(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const $row = $(row); // Garante que é jQuery object
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsBlock = $row.find('.inline-group'); // Container das opções

        // Sai se elementos não existem
        if (!selectElement.length) return;
        // Não sai se optionsBlock não existe, pois placeholders ainda precisam ser aplicados

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Só age se o bloco de opções existir
        if (optionsBlock.length) {
            if (typesWithOptions.includes(selectedType)) {
                optionsBlock.slideDown();
            } else {
                optionsBlock.slideUp();
            }
        }
    }

    // Função para adicionar placeholder na Pergunta e Tipo
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length > 0 && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Pergunta');
        }
         // Placeholder para Dropdown Tipo Resposta
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length > 0 && typeSelect.find('option[value=""]').length === 0) {
            typeSelect.prepend('<option value="" disabled selected>-- Selecione o Tipo --</option>');
            if (!typeSelect.val()) {
                typeSelect.val(""); // Garante que o placeholder seja selecionado inicialmente
            }
         }
    }

    // --- NOVO: Função para adicionar placeholder na Opção ---
    function addOptionPlaceholder(row) {
        const $row = $(row);
        // Seletor mais robusto para o input da opção
        const optionInput = $row.find('input[id$="-texto"]'); // Procura input cujo ID termina com '-texto'
        if (optionInput.length > 0 && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção');
        }
    }

    $(document).ready(function() {
        // Renomeia os botões
        setInterval(function() {
             $('.djn-add-item a').each(function() {
                const $button = $(this);
                if ($button.text().includes('Opcao Resposta')) {
                    $button.text('Adicionar Opção');
                }
                if ($button.text().includes('Pergunta') && !$button.text().includes('Opcao')) {
                    $button.text('Adicionar Pergunta');
                }
            });
        }, 500);

        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve a adição de um novo inline (Pergunta ou Opção)
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row;

            if (inline.prefix.includes('pergunta')) { // Se for uma Pergunta
                 const optionsBlock = newRow.find('.inline-group');
                 if (optionsBlock.length) {
                     optionsBlock.hide(); // Começa escondido
                 }
                 toggleOptions(newRow); // Aplica estado inicial (esconder/mostrar)
                 addQuestionPlaceholders(newRow); // Placeholders pergunta E tipo
            } else if (inline.prefix.includes('opcaoresposta')) { // Se for uma Opção
                addOptionPlaceholder(newRow); // Placeholder da opção
            }
        });

        // Roda as funções para elementos existentes ao carregar
        setTimeout(function() {
            // Para cada Pergunta existente
            $('#perguntas-group .inline-related').each(function() {
                const $questionRow = $(this);
                const selectVal = $questionRow.find('.field-tipo_resposta select').val();
                const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
                const optionsBlock = $questionRow.find('.inline-group');

                // Garante que opções comecem escondidas se necessário
                if (optionsBlock.length && !typesWithOptions.includes(selectVal)) {
                     optionsBlock.hide();
                }

                toggleOptions($questionRow); // Aplica estado
                addQuestionPlaceholders($questionRow); // Placeholders

                // Placeholder para Opções existentes
                optionsBlock.find('.dynamic-opcaoresposta_set').each(function() { // Busca opções dentro do bloco
                     addOptionPlaceholder($(this));
                });
            });
        }, 300);
    });
})(jQuery);