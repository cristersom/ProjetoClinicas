(function($) { // '$' é django.jQuery aqui dentro

    // Função que mostra ou esconde o bloco de "Opções" SOMENTE para a linha (row) especificada
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        // Acha o container de opções DENTRO desta linha específica
        const optionsContainer = $row.find('> .inline-group'); // '>' garante que pegue só o filho direto

        // Se não encontrar os elementos DENTRO da linha, não faz nada
        if (!selectElement.length || !optionsContainer.length) return;

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Mostra/esconde o container de opções DESTA linha
        optionsContainer.toggle(typesWithOptions.includes(selectedType));
    }

    // Função para adicionar placeholders na Pergunta e Tipo (dentro da linha especificada)
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
                typeSelect.val("");
                typeSelect.addClass('placeholder-selected');
            } else {
                 typeSelect.removeClass('placeholder-selected');
            }
         }
    }

    // Função para adicionar placeholder na Opção (dentro da linha da opção especificada)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        const optionInput = $optionRow.find('.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
        }
    }

    // --- LÓGICA DE APLICAÇÃO ---
    // Aplica lógica a um elemento específico (Pergunta ou Opção)
    function applyLogicToElement(element) {
         const $element = $(element);
         if ($element.data('logic-applied-v2')) return; // Evita reprocessar

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             addQuestionPlaceholders($element);
             toggleOptions($element); // Aplica estado inicial correto
             // Placeholders para opções já existentes DENTRO desta pergunta
             $element.find('.dynamic-opcaoresposta_set').each(function() {
                if (!$(this).data('logic-applied-v2')) {
                    addOptionPlaceholder($(this));
                    $(this).data('logic-applied-v2', true);
                }
             });
             $element.data('logic-applied-v2', true);
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             addOptionPlaceholder($element);
             $element.data('logic-applied-v2', true);
         }
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        // Renomeia os botões UMA VEZ E REPETIDAMENTE (para garantir botões novos)
        function renameButtons() {
            // Renomeia botão "Adicionar Opção" (DENTRO do grupo de opções)
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
            // Renomeia botão "Adicionar Pergunta" (FORA dos cards)
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
        }
        renameButtons(); // Roda imediatamente
        setInterval(renameButtons, 700); // Roda periodicamente

        // Ouve a mudança no dropdown Tipo Resposta (APENAS DENTRO DESTA PERGUNTA)
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
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Garante que é um elemento
                            const $node = $(node);
                            // Se o nó adicionado for uma pergunta ou opção, processa
                            if ($node.hasClass('inline-related') || $node.hasClass('dynamic-opcaoresposta_set')) {
                                applyLogicToElement($node);
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
                                toggleOptions($node); // Aplica estado inicial correto
                            }
                        }
                    });
                });
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        }

        // Aplica a lógica inicial aos elementos já presentes (com delay)
        setTimeout(function() {
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
             // Garante estado inicial correto das opções
             $('#perguntas-group .inline-related').each(function(){
                 toggleOptions(this);
            });
        }, 500);
    });

})(django.jQuery); // Passa django.jQuery como '$'