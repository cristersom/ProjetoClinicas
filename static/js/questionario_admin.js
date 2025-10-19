(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsBlock = $row.find('.inline-group');

        if (!selectElement.length) return;

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

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
         if (typeSelect.length > 0) {
            // Remove placeholder antigo se existir (para evitar duplicação)
            typeSelect.find('option[value=""][disabled]').remove();
            // Adiciona novo placeholder no topo
            typeSelect.prepend('<option value="" disabled selected style="color: #80868b;">-- Selecione o Tipo --</option>');
            // Define o valor para vazio SE NADA ESTIVER SELECIONADO AINDA
            if (!typeSelect.val()) {
                typeSelect.val("");
            }
            // Adiciona classe para estilizar o placeholder (opcional)
            if (!typeSelect.val()) {
                typeSelect.addClass('placeholder-selected');
            } else {
                typeSelect.removeClass('placeholder-selected');
            }
         }
    }

    // Função para adicionar placeholder na Opção
    function addOptionPlaceholder(row) {
        const $row = $(row);
        const optionInput = $row.find('input[id$="-texto"][type="text"]'); // Mais específico
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
            // Remove classe placeholder se algo for selecionado
             $(this).removeClass('placeholder-selected');
        });

        // Ouve a adição de um novo inline (Pergunta ou Opção)
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row;

            if (inline.prefix.includes('pergunta')) { // Se for uma Pergunta
                 const optionsBlock = newRow.find('.inline-group');
                 if (optionsBlock.length) { optionsBlock.hide(); }
                 toggleOptions(newRow);
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

                // Esconde opções se necessário
                if (optionsBlock.length && !typesWithOptions.includes(selectVal)) {
                     optionsBlock.hide();
                }

                toggleOptions($questionRow); // Garante estado
                addQuestionPlaceholders($questionRow); // Placeholders

                // Placeholder para Opções existentes
                optionsBlock.find('.dynamic-opcaoresposta_set').each(function() {
                     addOptionPlaceholder($(this));
                });
            });
        }, 350); // Aumentado um pouco mais
    });

    // CSS opcional para estilizar o placeholder do select (adicionar ao custom_admin.css se quiser)
    /*
    select.placeholder-selected {
        color: #80868b !important;
    }
    select option {
        color: #000 !important; // Cor normal das opções
    }
    select option[value=""][disabled] {
        display: none; // Esconde a opção placeholder da lista dropdown
    }
    */

})(jQuery);