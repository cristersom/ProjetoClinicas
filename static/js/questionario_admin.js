(function($) { // '$' é django.jQuery aqui dentro

    // Função que mostra ou esconde o bloco de "Opções" SOMENTE para a linha (row) especificada
    function toggleOptions(row) {
        const $row = $(row);
        const selectElement = $row.find('.field-tipo_resposta select');
        // Acha o container de opções DENTRO desta linha específica
        const optionsContainer = $row.find('> .inline-group'); // '>' filho direto

        // Se não encontrar os elementos DENTRO da linha, não faz nada
        if (!selectElement.length || !optionsContainer.length) {
            // console.warn("Toggle: Elementos não encontrados para", $row.attr('id'));
            return;
        }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];

        // Mostra/esconde o container de opções DESTA linha
        // Usar 'fadeToggle' ou 'slideToggle' pode ser mais suave visualmente
        if (typesWithOptions.includes(selectedType)) {
            optionsContainer.slideDown(200); // Mostra suavemente
        } else {
            optionsContainer.slideUp(200); // Esconde suavemente
        }
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
            // Garante que a opção placeholder exista e seja a primeira
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Selecione o Tipo --</option>');
            }
            // Garante que o placeholder esteja selecionado se nenhum valor real estiver
            // E define a classe para estilização CSS
            if (!typeSelect.val() || typeSelect.val() === "") {
                typeSelect.val(""); // Força seleção do placeholder
                typeSelect.addClass('placeholder-selected');
            } else {
                 typeSelect.removeClass('placeholder-selected');
            }
         }
    }

    // Função para adicionar placeholder na Opção (dentro da linha da opção especificada)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        // Seletor ajustado para pegar input DENTRO da célula correta
        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
        }
    }

    // --- LÓGICA DE APLICAÇÃO ---
    // Aplica lógica a um elemento específico (Pergunta ou Opção)
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v5'; // Nova flag para esta versão

         // Não processa se já tiver a flag
         if ($element.data(logicFlag)) return;

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             addQuestionPlaceholders($element); // Placeholders pergunta/tipo
             // Aplica placeholders a opções já existentes DENTRO desta pergunta
             $element.find('.dynamic-opcaoresposta_set').each(function() {
                 if (!$(this).data(logicFlag)) { // Processa se não tiver flag
                    addOptionPlaceholder($(this));
                    $(this).data(logicFlag, true); // Marca opção interna
                 }
             });
             // Chama toggleOptions DEPOIS de processar filhos para estado inicial
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
        // Renomeia os botões dinamicamente
        function renameButtons() {
            // Botão Adicionar Pergunta (FORA de qualquer .inline-related)
            $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
            // Botão Adicionar Opção (DENTRO de um .inline-group)
            $('.inline-group .djn-add-item a').text('Adicionar Opção');
        }
        renameButtons(); // Roda imediatamente
        // Observador para renomear botões que aparecem depois
        const buttonObserver = new MutationObserver(renameButtons);
        const buttonTarget = document.getElementById('perguntas-group');
        if(buttonTarget) buttonObserver.observe(buttonTarget, { childList: true, subtree: true });


        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            const $select = $(this);
            const row = $select.closest('.inline-related'); // Pega SÓ a linha pai
            toggleOptions(row); // Passa a linha específica
            // Atualiza classe do placeholder
            if ($select.val()) { $select.removeClass('placeholder-selected'); }
            else { $select.addClass('placeholder-selected'); }
        });

        // Ouve a adição de um novo inline (evento do nested_admin)
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row; // A linha TR adicionada
            // Aplica lógica ao novo elemento (seja pergunta ou opção)
             applyLogicToElement(newRow);
             // Se for uma pergunta nova, garante que opções comecem escondidas
             if ($(newRow).hasClass('inline-related')) {
                 const optionsContainer = $(newRow).find('> .inline-group');
                 if(optionsContainer.length) optionsContainer.hide();
                 // Chama toggle DEPOIS de esconder, para estado inicial correto
                 toggleOptions(newRow);
             }
        });

        // Aplica a lógica inicial aos elementos já presentes (com delay)
        setTimeout(function() {
            // Aplica a todas as perguntas e opções existentes
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                applyLogicToElement(this);
            });
        }, 500); // Delay para garantir
    });

})(django.jQuery); // Passa django.jQuery como '$'