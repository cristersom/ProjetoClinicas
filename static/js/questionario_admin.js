// Usa o wrapper do Django Admin para garantir que django.jQuery esteja pronto
(function($) { // '$' aqui dentro agora é o 'django.jQuery'

    // Função que mostra ou esconde o bloco de "Opções"
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
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
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
        }
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            // Garante que a opção placeholder exista
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
        const optionInput = $optionRow.find('.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
        }
    }

    // --- LÓGICA PRINCIPAL ---
    function applyLogicToElement(element) {
         const $element = $(element);
         let isNew = !$element.data('logic-applied'); // Verifica se já foi processado

         // Se for um Card de Pergunta (.inline-related)
         if ($element.hasClass('inline-related')) {
             if (!isNew) return; // Sai se já processado

             addQuestionPlaceholders($element);
             toggleOptions($element); // Aplica estado inicial (esconder/mostrar)

             // Aplica placeholder a opções JÁ existentes
             $element.find('.inline-group .dynamic-opcaoresposta_set').each(function() {
                 if (!$(this).data('logic-applied')) { // Processa opções internas apenas uma vez
                    addOptionPlaceholder($(this));
                    $(this).data('logic-applied', true);
                 }
             });

             $element.data('logic-applied', true); // Marca pergunta como processada
         }
         // Se for uma Linha de Opção (.dynamic-opcaoresposta_set)
         else if ($element.hasClass('dynamic-opcaoresposta_set')) {
             if (!isNew) return; // Sai se já processado
             addOptionPlaceholder($element);
             $element.data('logic-applied', true);
         }
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        // Renomeia os botões (apenas uma vez, mais eficiente)
        function renameButtonsOnce() {
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
        }
        renameButtonsOnce(); // Roda uma vez no início

        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const $select = $(this);
            const row = $select.closest('.inline-related');
            toggleOptions(row);
            // Atualiza classe do placeholder
            if ($select.val()) { $select.removeClass('placeholder-selected'); }
            else { $select.addClass('placeholder-selected'); }
        });

        // --- OBSERVAR MUDANÇAS NO DOM ---
        const observerTargetNode = document.getElementById('perguntas-group');
        if (observerTargetNode) {
            const observer = new MutationObserver(function(mutations) {
                let addedNodes = [];
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Garante que é um elemento
                            addedNodes.push(node);
                        }
                    });
                });

                if (addedNodes.length > 0) {
                    // Aplica lógica aos nós adicionados e seus descendentes relevantes
                    $(addedNodes).each(function(){
                        const $node = $(this);
                        // Aplica ao nó principal se for um inline
                        if ($node.hasClass('inline-related') || $node.hasClass('dynamic-opcaoresposta_set')) {
                           applyLogicToElement($node);
                        }
                        // Aplica aos descendentes que são inlines
                        $node.find('.inline-related, .dynamic-opcaoresposta_set').each(function() {
                           applyLogicToElement(this);
                        });
                    });
                     // Garante que opções dentro de perguntas recém-adicionadas sejam escondidas se necessário
                    $(addedNodes).filter('.inline-related').each(function(){
                         toggleOptions(this);
                    });
                    renameButtonsOnce(); // Garante que novos botões sejam renomeados
                }
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        } else {
             console.error("Elemento #perguntas-group não encontrado para o MutationObserver.");
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

})(django.jQuery); // Passa django.jQuery como '$' para dentro da função