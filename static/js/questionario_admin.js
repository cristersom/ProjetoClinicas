(function($) { // '$' é django.jQuery

    // Função toggleOptions (sem alterações, deve funcionar se chamada corretamente)
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        const optionsContainer = $row.find('> .inline-group'); // Filho direto
        if (!selectElement.length || !optionsContainer.length) return;
        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        optionsContainer.toggle(typesWithOptions.includes(selectedType));
    }

    // Função addQuestionPlaceholders (sem alterações)
    function addQuestionPlaceholders(row) { /* ... código mantido ... */ }

    // Função addOptionPlaceholder (sem alterações)
    function addOptionPlaceholder(optionRow) { /* ... código mantido ... */ }

    // --- LÓGICA DE APLICAÇÃO ---
    function applyLogicToElement(element) {
         const $element = $(element);
         if ($element.data('logic-applied-v3')) return; // Evita reprocessar com nova flag

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             addQuestionPlaceholders($element);
             // --- CORREÇÃO IMPORTANTE: Chama toggleOptions AQUI ---
             // Garante que o estado inicial (escondido/mostrado) seja aplicado
             toggleOptions($element);
             $element.find('.dynamic-opcaoresposta_set').each(function() {
                if (!$(this).data('logic-applied-v3')) {
                    addOptionPlaceholder($(this));
                    $(this).data('logic-applied-v3', true);
                }
             });
             $element.data('logic-applied-v3', true);
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             addOptionPlaceholder($element);
             $element.data('logic-applied-v3', true);
         }
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        // --- CORREÇÃO: Renomear botões com seletores específicos ---
        function renameButtons() {
            // Botão Adicionar Pergunta (diretamente filho de #perguntas-group)
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
            // Botão Adicionar Opção (DENTRO de um .inline-group)
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
        }
        renameButtons(); // Roda imediatamente
        // Roda de novo após um tempo para pegar botões dinâmicos
        setTimeout(renameButtons, 700);


        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const $select = $(this);
            const row = $select.closest('.inline-related');
            toggleOptions(row); // Chama toggle SÓ para esta linha
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
                                // --- GARANTE QUE OPÇÕES DA NOVA PERGUNTA COMECEM ESCONDIDAS ---
                                if ($node.hasClass('inline-related')) {
                                    const optionsContainer = $node.find('> .inline-group');
                                    if(optionsContainer.length) optionsContainer.hide();
                                    // Chama toggle DEPOIS de esconder, para estado inicial correto
                                    toggleOptions($node);
                                }
                                needsRename = true; // Precisa renomear botões
                            }
                            // Processa também perguntas/opções DENTRO do nó adicionado
                            $node.find('.inline-related, .dynamic-opcaoresposta_set').each(function() {
                                applyLogicToElement(this);
                                if ($(this).hasClass('inline-related')) toggleOptions(this); // Aplica toggle inicial
                            });
                        }
                    });
                });
                if(needsRename) renameButtons(); // Renomeia se nós foram adicionados
            });
            const config = { childList: true, subtree: true };
            observer.observe(observerTargetNode, config);
        }

        // Aplica a lógica inicial aos elementos já presentes (com delay)
        setTimeout(function() {
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
            // Garante estado inicial correto das opções para TODAS as perguntas
             $('#perguntas-group .inline-related').each(function(){
                 toggleOptions(this);
            });
        }, 500);
    });

})(django.jQuery); // Passa django.jQuery como '$'