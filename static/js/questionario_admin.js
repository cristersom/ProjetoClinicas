(function($) {
    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        // O container das opções agora é '.inline-group' DENTRO do '.inline-related'
        const optionsContainer = $row.find('.inline-group');

        if (!selectElement.length || !optionsContainer.length) return;

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Usar .toggle() é mais eficiente
        optionsContainer.toggle(typesWithOptions.includes(selectedType));
    }

    // Função para adicionar placeholder na Pergunta e Tipo
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        // O input da pergunta está dentro de um fieldset > form-row > field-texto_pergunta
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui'); // Placeholder mais descritivo
        }
         // O select do tipo está dentro de um fieldset > form-row > field-tipo_resposta
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled selected style="color: #80868b;">-- Selecione o Tipo --</option>');
            }
            // Garante que o placeholder esteja selecionado se nenhum valor real estiver
            if (!typeSelect.val() || typeSelect.val() === "") {
                typeSelect.val(""); // Força seleção do placeholder
                typeSelect.addClass('placeholder-selected');
            } else {
                 typeSelect.removeClass('placeholder-selected');
            }
         }
    }

    // Função para adicionar placeholder na Opção
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        // O input da opção está dentro de um fieldset > field-texto
        const optionInput = $optionRow.find('.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta'); // Placeholder mais descritivo
        }
    }

    // --- LÓGICA PRINCIPAL ---
    function applyLogicToElement(element) {
         const $element = $(element);

         // Se for um Card de Pergunta (.inline-related)
         if ($element.hasClass('inline-related')) {
             if ($element.data('logic-applied')) return; // Evita reprocessar

             addQuestionPlaceholders($element); // Aplica placeholder pergunta/tipo
             toggleOptions($element); // Esconde/mostra opções

             // Aplica placeholder a opções JÁ existentes dentro desta pergunta
             $element.find('.inline-group .dynamic-opcaoresposta_set').each(function() {
                 addOptionPlaceholder($(this));
                 $(this).data('logic-applied', true); // Marca opção como processada
             });

             $element.data('logic-applied', true); // Marca pergunta como processada
         }
         // Se for uma Linha de Opção (.dynamic-opcaoresposta_set)
         else if ($element.hasClass('dynamic-opcaoresposta_set')) {
             if ($element.data('logic-applied')) return; // Evita reprocessar
             addOptionPlaceholder($element);
             $element.data('logic-applied', true); // Marca opção como processada
         }
    }


    $(document).ready(function() {
        // Renomeia os botões (mantido)
        setInterval(function() {
            $('.djn-add-item a').each(function() { /* ... código mantido ... */ });
        }, 500);

        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const $select = $(this);
            const row = $select.closest('.inline-related');
            toggleOptions(row);
            // Atualiza classe do placeholder no select
             if ($select.val()) { $select.removeClass('placeholder-selected'); }
             else { $select.addClass('placeholder-selected'); }
        });

        // --- OBSERVAR MUDANÇAS NO DOM ---
        const observerTargetNode = document.getElementById('perguntas-group');
        if (observerTargetNode) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        // Aplica lógica ao nó adicionado e a qualquer inline dentro dele
                         if (node.nodeType === 1) { // Garante que é um elemento
                            applyLogicToElement(node); // Aplica ao próprio nó (se for .inline-related ou .dynamic-*)
                            $(node).find('.inline-related, .dynamic-opcaoresposta_set').each(function() {
                                applyLogicToElement(this); // Aplica aos descendentes
                            });
                        }
                    });
                });
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        } else {
             console.error("Elemento #perguntas-group não encontrado para o MutationObserver.");
        }


        // Aplica a lógica inicial aos elementos já presentes
        setTimeout(function() {
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
             // Garante que opções dentro de perguntas existentes sejam escondidas se necessário
            $('#perguntas-group .inline-related').each(function(){
                 toggleOptions(this);
            });
        }, 500); // Aumentado para segurança
    });

})(jQuery);