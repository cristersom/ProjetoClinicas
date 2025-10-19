// Usa o wrapper do Django Admin
(function($) { // '$' é django.jQuery
    console.log("[QAdmin V9] Script loaded.");

    // Função toggleOptions (Seletores ajustados para layout padrão)
    function toggleOptions(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || $row.index(); // Usa index como fallback ID
        // console.log(`[QAdmin V9] toggleOptions called for row: ${rowId}`);
        const selectElement = $row.find('.field-tipo_resposta select');
        // No layout padrão, o container é um fieldset DENTRO de .inline-group
        // nested_admin também pode usar uma div.djn-group em vez de fieldset às vezes
        const optionsContainer = $row.find('.inline-group > .module, .inline-group > .djn-group'); // Tenta pegar fieldset ou div

        if (!selectElement.length) { /* console.warn(`[QAdmin V9] Toggle: Select not found in ${rowId}`); */ return; }
        if (!optionsContainer.length) { /* console.warn(`[QAdmin V9] Toggle: Options Container not found in ${rowId}`); */ return; }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        // console.log(`[QAdmin V9] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Usar show/hide simples
        if (shouldShow) {
            optionsContainer.show();
        } else {
            optionsContainer.hide();
        }
    }

    // Função addQuestionPlaceholders (Adiciona placeholder Pergunta/Tipo)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || $row.index();
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
            // console.log(`[QAdmin V9] Placeholder Pergunta added to ${rowId}`);
        }
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Selecione o Tipo --</option>');
                 // console.log(`[QAdmin V9] Placeholder Tipo added to ${rowId}`);
            }
            // Força seleção do placeholder se valor for vazio
            if (!typeSelect.val() || typeSelect.val() === "") { typeSelect.val(""); }
         }
    }

    // Função addOptionPlaceholder (Adiciona placeholder Opção)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        const rowId = $optionRow.attr('id') || $optionRow.index();
        // No layout padrão, input está em td.field-texto
        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
            // console.log(`[QAdmin V9] Placeholder Opção added to ${rowId}`);
        }
    }

    // Aplica lógica a um elemento (Pergunta ou Opção)
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v9'; // Nova flag

         if ($element.data(logicFlag) || $element.hasClass('empty-form')) return; // Não processa template vazio

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             // console.log("[QAdmin V9] Applying logic to Pergunta:", $element.attr('id') || $element.index());
             addQuestionPlaceholders($element);
             // Aplica a opções internas JÁ EXISTENTES
             $element.find('.dynamic-opcaoresposta_set').each(function() { applyLogicToElement(this); });
             // Aplica toggle DEPOIS de processar filhos e placeholders
             toggleOptions($element);
             $element.data(logicFlag, true);
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             // console.log("[QAdmin V9] Applying logic to Opção:", $element.attr('id') || $element.index());
             addOptionPlaceholder($element);
             $element.data(logicFlag, true);
         }
    }

    // Renomeia botões (Seletores Corrigidos)
    function renameButtons() {
        // console.log("[QAdmin V9] Attempting to rename buttons...");
        // Botão Adicionar Pergunta (FORA de .inline-related, dentro de #perguntas-group > div.djn-fieldset > div.djn-add-item )
        const $addQuestionBtn = $('#perguntas-group > div.djn-fieldset > div.djn-add-item a');
        if ($addQuestionBtn.length && $addQuestionBtn.text() !== 'Adicionar Pergunta') {
            $addQuestionBtn.text('Adicionar Pergunta');
            // console.log("[QAdmin V9] Botão 'Adicionar Pergunta' RENAMED.");
        }

        // Botão Adicionar Opção (DENTRO de .inline-group > fieldset.module > div.djn-add-item OU .inline-group > div.djn-group > div.djn-add-item)
        $('.inline-group > fieldset.module > div.djn-add-item a, .inline-group > div.djn-group > div.djn-add-item a').each(function(){
            const $addOptionBtn = $(this);
            // Evita renomear o botão do template vazio
            if ($addOptionBtn.closest('.empty-form').length === 0 && $addOptionBtn.text() !== 'Adicionar Opção') {
                $addOptionBtn.text('Adicionar Opção');
                // console.log("[QAdmin V9] Botão 'Adicionar Opção' RENAMED.");
            }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V9] Document Ready");

        // Ouve a mudança no dropdown
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            // console.log("[QAdmin V9] Select change detected");
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve adição de inline
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row;
            // console.log("[QAdmin V9] Inline added:", $(newRow).attr('id') || $(newRow).index());

            // Espera um pouco para garantir que o DOM esteja completo
            setTimeout(function() {
                // Aplica lógica APENAS ao novo elemento
                applyLogicToElement(newRow);
                 // Se for uma PERGUNTA, garante que opções comecem escondidas
                 if ($(newRow).hasClass('inline-related')) {
                    const optionsContainer = $(newRow).find('> .inline-group > fieldset.module, > .inline-group > .djn-group');
                    if(optionsContainer.length) optionsContainer.hide();
                    // Chama toggle DEPOIS para garantir estado correto
                    toggleOptions(newRow);
                 }
                 // Renomeia botões DE NOVO
                renameButtons();
            }, 100); // Delay curto
        });

        // Aplica lógica inicial com delay maior
        setTimeout(function() {
            console.log("[QAdmin V9] Applying initial logic (Timeout)...");
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                 applyLogicToElement(this);
            });
            renameButtons(); // Renomeia botões iniciais
            console.log("[QAdmin V9] Initial logic (Timeout) completed.");
        }, 1200); // 1.2 segundos
    });

})(django.jQuery); // Passa django.jQuery como '$'