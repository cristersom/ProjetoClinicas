(function($) { // '$' é django.jQuery
    console.log("[QAdmin V11] Script loaded.");

    // Função toggleOptions (Simplificada, assume que row é o TR)
    function toggleOptions(row) {
        const $row = $(row);
        const rowId = $row.attr('id') || $row.index();
        const selectElement = $row.find('td.field-tipo_resposta select');
        // Acha o container de opções dentro da célula 'original' da linha da pergunta
        const optionsContainer = $row.find('td.original .inline-group > fieldset.module, td.original .inline-group > .djn-group');

        if (!selectElement.length || !optionsContainer.length) {
             console.warn(`[QAdmin V11] Toggle: Elementos não encontrados em ${rowId}`); return;
        }

        const selectedType = selectElement.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V11] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        // Tenta show/hide simples
         optionsContainer.toggle(shouldShow);
    }

    // Função addQuestionPlaceholders (Simplificada)
    function addQuestionPlaceholders(row) {
        const $row = $(row);
        const qInput = $row.find('td.field-texto_pergunta input[type="text"]').not('[placeholder]');
        if(qInput.length) qInput.attr('placeholder', 'Digite sua pergunta aqui');

        const tSelect = $row.find('td.field-tipo_resposta select');
        if(tSelect.length && tSelect.find('option[value=""][disabled]').length === 0) {
            tSelect.prepend('<option value="" disabled style="color: #80868b;">-- Tipo --</option>');
            if(!tSelect.val()) tSelect.val("");
        }
    }

    // Função addOptionPlaceholder (Simplificada)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow);
        const oInput = $optionRow.find('td.field-texto input[type="text"]').not('[placeholder]');
        if(oInput.length) oInput.attr('placeholder', 'Opção');
    }

    // Aplica lógica (Placeholders + Toggle Inicial)
    function applyLogicToQuestionRow(row) {
        const $row = $(row);
        const logicFlag = 'logic-applied-v11';
        if ($row.data(logicFlag) || $row.hasClass('djn-empty-form')) return; // Já processado ou template vazio

        console.log("[QAdmin V11] Applying logic to Pergunta:", $row.attr('id') || $row.index());
        addQuestionPlaceholders($row);
        // Aplica a opções internas JÁ EXISTENTES
        $row.find('tr.dynamic-opcaoresposta_set').each(function() { // Busca opções DENTRO da pergunta
            applyLogicToOptionRow(this); // Aplica placeholder à opção
        });
        toggleOptions($row); // Aplica toggle inicial
        $row.data(logicFlag, true);
    }

    function applyLogicToOptionRow(row) {
         const $row = $(row);
         const logicFlag = 'logic-applied-v11';
         if ($row.data(logicFlag) || $row.hasClass('djn-empty-form')) return;

         console.log("[QAdmin V11] Applying logic to Opção:", $row.attr('id') || $row.index());
         addOptionPlaceholder($row);
         $row.data(logicFlag, true);
    }


    // Renomeia botões
    function renameButtons() {
        console.log("[QAdmin V11] Renaming buttons...");
        // Botão Adicionar Pergunta (ID padrão do nested_admin é add-row)
        // O seletor correto é mais complexo: link dentro do add-item que é irmão do .items
         const $addQuestionBtn = $('#perguntas-group > div.djn-fieldset > div.djn-add-item > a');
         if ($addQuestionBtn.length && !$addQuestionBtn.text().includes('Adicionar Pergunta')) {
            $addQuestionBtn.text('Adicionar Pergunta');
         }

        // Botão Adicionar Opção (dentro de .inline-group)
        $('.inline-group .djn-add-item a').each(function() {
             const $btn = $(this);
             if (!$btn.text().includes('Adicionar Opção')) {
                 $btn.text('Adicionar Opção');
             }
        });
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V11] Document Ready");

        const perguntaPrefix = 'perguntas'; // Prefixo do formset de perguntas
        const opcaoPrefix = 'opcaoresposta'; // Prefixo do formset de opções

        // Tenta aplicar lógica inicial aos elementos já presentes
        function runInitialLogic() {
            console.log("[QAdmin V11] Running initial logic...");
            let count = 0;
            $(`#${perguntaPrefix}-group tbody tr.dynamic-${perguntaPrefix}_set`).each(function() {
                applyLogicToQuestionRow(this);
                count++;
            });
            renameButtons();
            console.log(`[QAdmin V11] Initial logic applied to ${count} questions.`);
             // Se nenhum foi encontrado, tenta de novo (nested_admin pode ser lento)
             if (count === 0 && !$('#perguntas-group').data('initial-logic-failed')) {
                  $('#perguntas-group').data('initial-logic-failed', true); // Evita loop infinito
                  console.warn("[QAdmin V11] No initial questions found, retrying...");
                  setTimeout(runInitialLogic, 1500); // Tenta de novo mais tarde
             }
        }
        setTimeout(runInitialLogic, 500); // Delay inicial


        // Ouve a mudança no dropdown Tipo Resposta
        $('body').on('change', `#${perguntaPrefix}-group td.field-tipo_resposta select`, function() {
            console.log("[QAdmin V11] Select change detected");
            const row = $(this).closest(`tr.dynamic-${perguntaPrefix}_set`);
            toggleOptions(row);
        });

        // Ouve evento 'formset:added' do Django (melhor que MutationObserver?)
        $(document).on('formset:added', function(event, $row, formsetName) {
            console.log(`[QAdmin V11] formset:added event detected for formset '${formsetName}'`, $row);

            // Espera um pouco para garantir que o DOM esteja pronto
            setTimeout(function() {
                 if (formsetName && formsetName.startsWith(perguntaPrefix)) {
                    // É uma nova pergunta
                    applyLogicToQuestionRow($row);
                    // Garante que opções comecem escondidas
                     const optionsContainer = $row.find('> td.original > .inline-group > fieldset.module, > td.original > .inline-group > .djn-group');
                     if(optionsContainer.length) optionsContainer.hide();
                     toggleOptions($row); // Aplica estado correto
                } else if (formsetName && formsetName.includes(opcaoPrefix)) {
                    // É uma nova opção
                    applyLogicToOptionRow($row);
                }
                renameButtons(); // Renomeia botões
            }, 50); // Delay mínimo
        });

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'