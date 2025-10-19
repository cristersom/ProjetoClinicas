// Usa o wrapper do Django Admin
(function($) { // '$' é django.jQuery
    console.log("[QAdmin] Script loaded.");

    // Função toggleOptions (com logs detalhados)
    function toggleOptions(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || 'unknown';
        console.log(`[QAdmin] toggleOptions called for row: ${rowId}`);
        const selectElement = $row.find('.field-tipo_resposta select');
        // No layout padrão, o container é um fieldset dentro do inline-group
        const optionsContainer = $row.find('.inline-group > fieldset.module'); // Seleciona o fieldset filho direto

        if (!selectElement.length) { console.warn(`[QAdmin] Toggle: Select not found in ${rowId}`); return; }
        // É normal não encontrar optionsContainer se a linha for o 'empty-form' template
        // if (!optionsContainer.length) { console.warn(`[QAdmin] Toggle: Options Container (.inline-group > fieldset.module) not found in ${rowId}`); return; }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Só tenta mostrar/esconder se o container existir
        if (optionsContainer.length) {
            optionsContainer.toggle(shouldShow);
        } else if (shouldShow) {
             console.warn(`[QAdmin] Toggle: Tentando mostrar opções, mas container não encontrado em ${rowId}`);
        }
    }

    // Função addQuestionPlaceholders (com logs)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || 'unknown';
        const questionInput = $row.find('.field-texto_pergunta input[type="text"]');
        if (questionInput.length && !questionInput.attr('placeholder')) {
            questionInput.attr('placeholder', 'Digite sua pergunta aqui');
            console.log(`[QAdmin] Placeholder Pergunta added to ${rowId}`);
        }
         const typeSelect = $row.find('.field-tipo_resposta select');
         if (typeSelect.length) {
            if (typeSelect.find('option[value=""][disabled]').length === 0) {
                 typeSelect.prepend('<option value="" disabled style="color: #80868b;">-- Selecione o Tipo --</option>');
                 console.log(`[QAdmin] Placeholder Tipo added to ${rowId}`);
            }
            if (!typeSelect.val() || typeSelect.val() === "") { typeSelect.val(""); }
         }
    }

    // Função addOptionPlaceholder (com logs)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        const rowId = $optionRow.attr('id') || 'unknown';
        // No layout padrão, input está em td.field-texto
        const optionInput = $optionRow.find('td.field-texto input[type="text"]');
        if (optionInput.length && !optionInput.attr('placeholder')) {
            optionInput.attr('placeholder', 'Opção de resposta');
            console.log(`[QAdmin] Placeholder Opção added to ${rowId}`);
        } else if (!optionInput.length) {
             // É normal não encontrar no 'empty-form' template
             // console.warn(`[QAdmin] Placeholder Opção: Input not found in ${rowId}`);
        }
    }

    // Aplica lógica a um elemento
    function applyLogicToElement(element) {
         const $element = $(element);
         const logicFlag = 'logic-applied-v8'; // Nova flag

         // Não processa se já tiver a flag OU se for o template vazio
         if ($element.data(logicFlag) || $element.hasClass('empty-form')) return;

         if ($element.hasClass('inline-related')) { // É uma Pergunta
             console.log("[QAdmin] Applying logic to Pergunta:", $element.attr('id'));
             addQuestionPlaceholders($element);
             // Aplica a opções internas
             $element.find('.dynamic-opcaoresposta_set').each(function() { applyLogicToElement(this); });
             // Aplica toggle DEPOIS
             toggleOptions($element);
             $element.data(logicFlag, true);
         }
         else if ($element.hasClass('dynamic-opcaoresposta_set')) { // É uma Opção
             console.log("[QAdmin] Applying logic to Opção:", $element.attr('id'));
             addOptionPlaceholder($element);
             $element.data(logicFlag, true);
         }
    }

    // Renomeia botões (com logs)
    function renameButtons() {
        console.log("[QAdmin] Attempting to rename buttons...");
        // Botão Adicionar Pergunta (FORA de .inline-related, dentro de #perguntas-group)
        const $addQuestionBtn = $('#perguntas-group > .djn-add-item a');
        if ($addQuestionBtn.length && $addQuestionBtn.text() !== 'Adicionar Pergunta') {
            $addQuestionBtn.text('Adicionar Pergunta');
            console.log("[QAdmin] Botão 'Adicionar Pergunta' RENAMED.");
        } else if ($addQuestionBtn.length === 0) {
             console.warn("[QAdmin] Botão 'Adicionar Pergunta' not found.");
        }

        // Botão Adicionar Opção (DENTRO de .inline-group)
        $('.inline-group .djn-add-item a').each(function(){
            const $addOptionBtn = $(this);
            // Evita renomear o botão do template vazio
            if ($addOptionBtn.closest('.empty-form').length === 0 && $addOptionBtn.text() !== 'Adicionar Opção') {
                $addOptionBtn.text('Adicionar Opção');
                console.log("[QAdmin] Botão 'Adicionar Opção' RENAMED in:", $addOptionBtn.closest('.inline-related').attr('id'));
            }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin] Document Ready");

        // Ouve a mudança no dropdown
        $('body').on('change', '#perguntas-group .field-tipo_resposta select', function() {
            console.log("[QAdmin] Select change detected");
            const row = $(this).closest('.inline-related');
            toggleOptions(row);
        });

        // Ouve adição de inline
        $(document).on('djnesting:added', function(event, inline) {
            const newRow = inline.row;
            console.log("[QAdmin] Inline added:", $(newRow).attr('id'));
            // Aplica lógica APENAS ao novo elemento adicionado
            applyLogicToElement(newRow);
            // Esconde opções da nova pergunta imediatamente
            if ($(newRow).hasClass('inline-related')) {
                 const optionsContainer = $(newRow).find('> .inline-group > fieldset.module');
                 if(optionsContainer.length) optionsContainer.hide();
                 toggleOptions(newRow); // Aplica estado correto
            }
            // Tenta renomear botões DE NOVO
            renameButtons();
        });

        // Aplica lógica inicial com delay
        setTimeout(function() {
            console.log("[QAdmin] Applying initial logic (Timeout)...");
            $('#perguntas-group .inline-related, #perguntas-group .dynamic-opcaoresposta_set').each(function() {
                 // Evita aplicar ao template vazio
                if (!$(this).hasClass('empty-form')) {
                    applyLogicToElement(this);
                }
            });
            renameButtons(); // Renomeia botões iniciais
            console.log("[QAdmin] Initial logic (Timeout) completed.");
        }, 1200); // 1.2 segundos de delay
    });

})(django.jQuery); // Passa django.jQuery como '$'