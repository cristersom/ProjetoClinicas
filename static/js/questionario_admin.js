(function($) { // '$' é django.jQuery
    console.log("[QAdmin V17 - Template Override] Script loaded.");

    // Função toggleOptions (Busca a partir do select, assume TR é o card)
    function toggleOptions(selectElement) {
        const $select = $(selectElement);
        const $questionRow = $select.closest('tr.dynamic-perguntas_set'); // TR da pergunta é o card

        if (!$questionRow.length) { console.error("[QAdmin V17] Toggle: Could not find parent TR."); return; }
        const rowId = $questionRow.attr('id') || $questionRow.index();

        // Container de opções está dentro da célula 'original' (que está oculta via CSS)
        const optionsContainer = $questionRow.find('td.original > .inline-group');

        if (!optionsContainer.length) { console.warn(`[QAdmin V17] Toggle: Options Container not found in ${rowId}`); return; }

        const selectedType = $select.val();
        const typesWithOptions = ['UNICA_ESCOLHA', 'MULTIPLA_ESCOLHA'];
        const shouldShow = typesWithOptions.includes(selectedType);

        console.log(`[QAdmin V17] Toggle: Row=${rowId}, Type=${selectedType}, ShouldShow=${shouldShow}`);
        optionsContainer.toggle(shouldShow);
    }

    // Função addQuestionPlaceholders (Busca dentro do TR)
    function addQuestionPlaceholders(row) {
        const $row = $(row); // TR da pergunta
        const qInput = $row.find('td.field-texto_pergunta input[type="text"]').not('[placeholder]');
        if(qInput.length) qInput.attr('placeholder', 'Digite sua pergunta aqui');

        const tSelect = $row.find('td.field-tipo_resposta select');
        if(tSelect.length) {
            if (tSelect.find('option[value=""][disabled]').length === 0) {
                 tSelect.prepend('<option value="" disabled style="color: #80868b;">-- Tipo --</option>');
            }
            if (!tSelect.val() || tSelect.val() === "") { tSelect.val(""); }
        }
    }

    // Função addOptionPlaceholder (Busca dentro do TR da opção)
    function addOptionPlaceholder(optionRow) {
        const $optionRow = $(optionRow); // TR da opção
        const oInput = $optionRow.find('td.field-texto input[type="text"]').not('[placeholder]');
        if(oInput.length) oInput.attr('placeholder', 'Opção');
    }

    // Aplica lógica (Placeholders + Toggle Inicial)
    function applyLogicToQuestionRow(row) {
        const $row = $(row);
        const logicFlag = 'logic-applied-v17';
        if ($row.data(logicFlag) || $row.hasClass('djn-empty-form')) return;

        console.log("[QAdmin V17] Applying logic to Pergunta:", $row.attr('id') || $row.index());
        addQuestionPlaceholders($row);
        // Aplica placeholder a opções internas
        $row.find('tr.dynamic-opcaoresposta_set').each(function() { applyLogicToOptionRow(this); });
        toggleOptions($row.find('td.field-tipo_resposta select')[0]); // Passa o select element
        $row.data(logicFlag, true);
    }

    function applyLogicToOptionRow(row) {
         const $row = $(row);
         const logicFlag = 'logic-applied-v17';
         if ($row.data(logicFlag) || $row.hasClass('djn-empty-form')) return;
         console.log("[QAdmin V17] Applying logic to Opção:", $row.attr('id') || $row.index());
         addOptionPlaceholder($row);
         $row.data(logicFlag, true);
    }

    // Renomeia botões
    function renameButtons() {
         // Botão Adicionar Pergunta (Fora da tabela, no div add-item principal)
         $('#perguntas-group > .djn-add-item a').text('Adicionar Pergunta');
         // Botão Adicionar Opção (Dentro de td.original > .inline-group > .djn-add-item)
         $('td.original > .inline-group .djn-add-item a').text('Adicionar Opção');
    }

    // --- Execução Principal ---
    $(document).ready(function() {
        console.log("[QAdmin V17] Document Ready");
        const perguntaPrefix = 'perguntas';

        // Aplica lógica inicial aos elementos já presentes
        function runInitialLogic() {
            console.log("[QAdmin V17] Running initial logic...");
            let count = 0;
             $(`tr.dynamic-${perguntaPrefix}_set`).not('.djn-empty-form').each(function() {
                 applyLogicToQuestionRow(this);
                 count++;
            });
             renameButtons();
             console.log(`[QAdmin V17] Initial logic applied to ${count} questions.`);
        }
        setTimeout(runInitialLogic, 500); // Delay menor agora

        // Ouve a mudança no dropdown Tipo Resposta
        $(document).on('change', 'select[name$="-tipo_resposta"]', function() {
             console.log("[QAdmin V17] Select change detected");
             toggleOptions(this); // Passa o select que mudou
        });

        // Ouve evento 'formset:added'
        $(document).on('formset:added', function(event, $row, formsetName) {
             if ($row && $row.length > 0) {
                 console.log(`[QAdmin V17] formset:added triggered for formset '${formsetName}'. Row ID: ${$row.attr('id')}`);
                 setTimeout(function() { // Delay para garantir DOM
                     if ($row.is(`tr.dynamic-${perguntaPrefix}_set`) && !$row.hasClass('djn-empty-form')) {
                        applyLogicToQuestionRow($row); // Aplica placeholders e toggle
                        // Garante esconder opções da nova pergunta
                        const optionsContainer = $row.find('td.original > .inline-group');
                        if(optionsContainer.length) {
                             optionsContainer.hide();
                             toggleOptions($row.find('td.field-tipo_resposta select')[0]); // Re-aplica toggle
                        }
                    } else if ($row.is("tr[id*='opcaoresposta']") && !$row.hasClass('djn-empty-form')) {
                        applyLogicToOptionRow($row);
                    }
                    renameButtons(); // Renomeia
                }, 50);
             } else { console.error("[QAdmin V17] formset:added event received invalid $row:", $row); }
        });

    }); // Fim Document Ready

})(django.jQuery); // Passa django.jQuery como '$'