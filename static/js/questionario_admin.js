(function($) { // '$' é django.jQuery

    // Função toggleOptions (verifica container antes de agir)
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        // Acha o container de opções DENTRO desta linha específica
        const optionsContainer = $row.find('> .inline-group'); // '>' filho direto

        if (!selectElement.length || !optionsContainer.length) return; // Só age se ambos existirem

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Mostra/esconde o container de opções DESTA linha
        optionsContainer.toggle(typesWithOptions.includes(selectedType));
    }

    // Função addQuestionPlaceholders (adiciona placeholder pergunta/tipo)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
        }
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled selected style="color: #80868b;">-- Selecione o Tipo --</option>');
            }
            if (!typeSelect.val() || typeSelect.val() === "") {
                typeSelect.val(""); // Força seleção do placeholder
                typeSelect.addClass('placeholder-selected');
            } else {
                 typeSelect.removeClass('placeholder-selected');
            }
         }
    }

    // Função addOptionPlaceholder (adiciona placeholder opção)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        // Usa seletor que funciona no template sobrescrito (input dentro de td.field-texto)
        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
        }
    }

    // --- LÓGICA DE APLICAÇÃO (Marca elementos processados) ---
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v4'; // Nova flag para garantir reprocessamento

         // Não processa se já tiver a flag
         if ($element.data(logicFlag)) return;

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             addQuestionPlaceholders($element);
             // Aplica placeholders a opções já existentes DENTRO desta pergunta
             $element.find('.dynamic-opcaoresposta_set').each(function() {
                 addOptionPlaceholder($(this));
                 $(this).data(logicFlag, true); // Marca opção interna
             });
             // Chama toggleOptions DEPOIS de processar filhos
             toggleOptions($element);
             $element.data(logicFlag, true); // Marca pergunta
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             addOptionPlaceholder($element);
             $element.data(logicFlag, true); // Marca opção
         }
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        // Renomeia os botões (apenas uma vez, mais eficiente)
        function renameButtons() {
            // Botão Adicionar Pergunta (FORA de qualquer .inline-related)
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
            // Botão Adicionar Opção (DENTRO de um .inline-group)
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
        }
        renameButtons(); // Roda imediatamente

        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const $select = $(this);
            const row = $select.closest('.inline-related'); // Pega SÓ a linha pai
            toggleOptions(row); // Passa a linha específica
            // Atualiza classe do placeholder
            if ($select.val()) { $select.removeClass('placeholder-selected'); }
            else { $select.addClass('placeholder-selected'); }
        });

        // --- OBSERVAR MUDANÇAS NO DOM ---
        const observerTargetNode = document.getElementById('perguntas-group');
        if (observerTargetNode) {
            const observer = new MutationObserver(function(mutations) {
                let needsRename = false;
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Garante que é um elemento
                            const $node = $(node);
                            // Se o nó adicionado for uma pergunta ou opção, processa
                            if ($node.hasClass('inline-related') || $node.hasClass('dynamic-opcaoresposta_set')) {
                                applyLogicToElement($node);
                                needsRename = true;
                            }
                            // Processa também perguntas/opções DENTRO do nó adicionado
                            $node.find('.inline-related, .dynamic-opcaoresposta_set').each(function() {
                                applyLogicToElement(this);
                            });
                             // Garante que toggleOptions rode para a NOVA pergunta
                            if ($node.hasClass('inline-related')) {
                                // Esconder opções imediatamente ao adicionar
                                const optionsContainer = $node.find('> .inline-group');
                                if(optionsContainer.length) optionsContainer.hide();
                                // Chama toggle DEPOIS de esconder, para estado inicial correto
                                toggleOptions($node);
                            }
                        }
                    });
                });
                if(needsRename) {
                    // Renomeia botões DEPOIS que o DOM foi atualizado
                    setTimeout(renameButtons, 50);
                }
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        }

        // Aplica a lógica inicial aos elementos já presentes (com delay)
        setTimeout(function() {
            // console.log("Applying initial logic...");
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
            // console.log("Initial logic applied.");
        }, 700); // Aumentado um pouco mais para garantir
    });

})(django.jQuery); // Passa django.jQuery como '$'