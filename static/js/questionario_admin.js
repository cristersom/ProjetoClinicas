(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        // --- REFORÇADO: Garante que row é jQuery ---
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsBlock = $row.find('.inline-group'); // Container das opções

        // Sai se não encontrar elementos essenciais
        if (!selectElement.length) {
            // console.warn("Select de tipo_resposta não encontrado.");
            return;
        }
        // Permite continuar mesmo sem bloco de opções (para aplicar placeholder)
        if (!optionsBlock.length) {
           // console.warn("Bloco de opções (.inline-group) não encontrado.");
        }


        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Só tenta mostrar/esconder se o bloco de opções existe
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
           // Adiciona opção vazia no topo se não existir
           typeSelect.prepend('<option value="" disabled selected>-- Selecione o Tipo --</option>');
           // Tenta definir o valor inicial como vazio (placeholder)
           if (!typeSelect.val()) { // Só define se nenhum valor estiver selecionado
                typeSelect.val("");
           }
        }
    }

    // --- NOVO: Função para adicionar placeholder na Opção ---
    function addOptionPlaceholder(row) {
        const $row = $(row);
        // Ajuste no seletor para ser mais específico
        const optionInput = $row.find('.field-texto input[type="text"]');
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
                 toggleOptions(newRow);
                 addQuestionPlaceholders(newRow); // Placeholder pergunta E tipo
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

                // Esconde opções se não for tipo com opções E se o bloco existir
                const optionsBlock = $questionRow.find('.inline-group');
                if (optionsBlock.length && !typesWithOptions.includes(selectVal)) {
                     optionsBlock.hide();
                }

                toggleOptions($questionRow); // Garante estado correto
                addQuestionPlaceholders($questionRow); // Placeholders pergunta/tipo

                // Placeholder para Opções existentes
                $questionRow.find('.inline-group .form-row.dynamic-opcaoresposta_set').each(function() {
                     addOptionPlaceholder($(this));
                });
            });
        }, 300);
    });
})(jQuery);